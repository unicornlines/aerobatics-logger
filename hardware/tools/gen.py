"""Generate the KiCad 7 schematic from design.py.

The schematic is written as code: every part lists every pin's net, so a
missing connection is an error here rather than a silent gap in KiCad.
Nets are joined with global labels; unused pins get a no-connect flag.

Run:  python3 gen.py   (writes ../kicad/*.kicad_sch)
"""
import os, uuid, hashlib
from sexpr import Sym, dump, find, first, fmt
from libs import symbol, pins
import design

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kicad")
PROJECT = "logger"
GRID = 2.54
PAPERS = {"A3": (420.0, 297.0), "A2": (594.0, 420.0)}


def uid(*parts):
    """Deterministic UUID so regenerating doesn't churn the files."""
    h = hashlib.sha1("/".join(parts).encode()).hexdigest()
    return str(uuid.UUID(h[:32]))


def snap(v):
    return round(v / GRID) * GRID


def font(size=1.27, justify=None, hide=False):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    if hide:
        e.append(Sym("hide"))
    return e


def label_len(text):
    return len(text) * 1.1 + 4


def part_geometry(p):
    sym = symbol(p["lib"])
    pp = pins(sym, p.get("unit", 1))
    xs = [x for v in pp.values() for (x, y, a, n, t) in v]
    ys = [y for v in pp.values() for (x, y, a, n, t) in v]
    side = {0: 0.0, 180: 0.0, 90: 0.0, 270: 0.0}
    for num, lst in pp.items():
        net = p["nets"].get(num)
        if net and net != "NC":
            for (x, y, a, n, t) in lst:
                side[a] = max(side[a], label_len(net))
    w = (max(xs) - min(xs)) + side[0] + side[180] + 12
    h = (max(ys) - min(ys)) + side[90] + side[270] + 14
    return sym, pp, min(xs), max(xs), min(ys), max(ys), side, w, h


def build_sheet(sheet, root_uuid, sheet_uuid, page):
    PAPER_W, PAPER_H = PAPERS[sheet.get("paper", "A3")]
    path = f"/{root_uuid}" + (f"/{sheet_uuid}" if sheet_uuid else "")
    lib_syms = {}
    items = []
    x0, y0, row_h = 20.0, 30.0, 0.0
    for p in sheet["parts"]:
        sym, pp, minx, maxx, miny, maxy, side, w, h = part_geometry(p)
        # check every pin is assigned
        missing = [n for n, lst in pp.items() if n not in p["nets"] and all(t != "no_connect" for *_, t in lst)]
        if missing:
            raise SystemExit(f"{p['ref']} ({p['lib']}): unassigned pins {sorted(missing)}")
        extra = set(p["nets"]) - set(pp)
        if extra:
            raise SystemExit(f"{p['ref']}: unknown pins {sorted(extra)}")
        if x0 + w > PAPER_W - 15:
            x0 = 20.0
            y0 += row_h
            row_h = 0.0
        ox = snap(x0 + side[0] + 6 - minx)
        oy = snap(y0 + side[90] + 7 + maxy)
        x0 += w
        row_h = max(row_h, h)
        lib_syms[p["lib"]] = sym
        su = uid(sheet["file"], p["ref"])
        props = [
            ("Reference", p["ref"], ox + maxx + 1.5, oy - maxy - 1.5, False),
            ("Value", p["value"], ox + maxx + 1.5, oy - maxy + 1.0, False),
            ("Footprint", p.get("fp", ""), ox, oy, True),
            ("Datasheet", p.get("ds", ""), ox, oy, True),
        ]
        if p.get("mpn"):
            props.append(("MPN", p["mpn"], ox, oy, True))
        s = [Sym("symbol"), [Sym("lib_id"), p["lib"]], [Sym("at"), ox, oy, 0],
             [Sym("unit"), p.get("unit", 1)],
             [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
             [Sym("dnp"), Sym("yes" if p.get("dnp") else "no")],
             [Sym("uuid"), su]]
        for name, val, px, py, hide in props:
            s.append([Sym("property"), name, val, [Sym("at"), px, py, 0], font(justify="left", hide=hide)])
        for num in pp:
            s.append([Sym("pin"), num, [Sym("uuid"), uid(sheet["file"], p["ref"], "pin", num)]])
        s.append([Sym("instances"), [Sym("project"), PROJECT,
                  [Sym("path"), path, [Sym("reference"), p["ref"]], [Sym("unit"), p.get("unit", 1)]]]])
        items.append(s)
        # labels and no-connects at pin ends (schematic Y is inverted)
        seen = set()
        for num, lst in pp.items():
            net = p["nets"].get(num)
            for i, (x, y, a, n, t) in enumerate(lst):
                sx, sy = ox + x, oy - y
                if (round(sx, 2), round(sy, 2)) in seen:
                    continue  # stacked pins share one label
                seen.add((round(sx, 2), round(sy, 2)))
                tag = uid(sheet["file"], p["ref"], num, str(i))
                if t == "no_connect" and net is None:
                    continue
                if net == "NC":
                    items.append([Sym("no_connect"), [Sym("at"), sx, sy], [Sym("uuid"), tag]])
                    continue
                ang = {0: 180, 180: 0, 90: 270, 270: 90}[a]
                just = "left" if ang in (0, 90) else "right"
                items.append([Sym("global_label"), net, [Sym("shape"), Sym("passive")],
                              [Sym("at"), sx, sy, ang], [Sym("fields_autoplaced")],
                              font(justify=just), [Sym("uuid"), tag],
                              [Sym("property"), "Intersheetrefs", "${INTERSHEET_REFS}",
                               [Sym("at"), sx, sy, 0], font(hide=True)]])
    for i, note in enumerate(sheet.get("notes", [])):
        items.append([Sym("text"), note, [Sym("at"), 20, PAPER_H - 40 + i * 5, 0],
                      font(justify="left"), [Sym("uuid"), uid(sheet["file"], "note", str(i))]])
    if y0 + row_h > PAPER_H - 45:
        raise SystemExit(f"sheet {sheet['file']} overflows {sheet.get('paper', 'A3')}: {y0 + row_h:.0f} mm")
    return lib_syms, items


def header(file_uuid, title, page, paper="A3"):
    return [Sym("kicad_sch"), [Sym("version"), 20230121], [Sym("generator"), Sym("eeschema")],
            [Sym("uuid"), file_uuid], [Sym("paper"), paper],
            [Sym("title_block"), [Sym("title"), title], [Sym("company"), "Aerobatics Flight Logger"],
             [Sym("rev"), design.REV], [Sym("comment"), 1, "Generated by hardware/tools/gen.py - edit design.py, not this file"]]]


def write(name, tree):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(dump(tree) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    root_uuid = uid("root")
    root = header(root_uuid, "Aerobatics Flight Logger", "1")
    root.append([Sym("lib_symbols")])
    sheets_sexpr = []
    for i, sh in enumerate(design.SHEETS):
        su = uid("sheet", sh["file"])
        page = str(i + 2)
        libs, items = build_sheet(sh, root_uuid, su, page)
        tree = header(uid("file", sh["file"]), sh["title"], page, sh.get("paper", "A3"))
        tree.append([Sym("lib_symbols")] + list(libs.values()))
        tree += items
        write(sh["file"], tree)
        x, y = 30 + (i % 3) * 120, 50 + (i // 3) * 70
        sheets_sexpr.append([Sym("sheet"), [Sym("at"), x, y], [Sym("size"), 90, 40],
            [Sym("fields_autoplaced")], [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
            [Sym("fill"), [Sym("color"), 0, 0, 0, 0.0]], [Sym("uuid"), su],
            [Sym("property"), "Sheetname", sh["title"], [Sym("at"), x, y - 0.7, 0], font(justify="left bottom")],
            [Sym("property"), "Sheetfile", sh["file"], [Sym("at"), x, y + 40.6, 0], font(justify="left top")],
            [Sym("instances"), [Sym("project"), PROJECT, [Sym("path"), f"/{root_uuid}", [Sym("page"), page]]]]])
    root += sheets_sexpr
    root.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
    write(PROJECT + ".kicad_sch", root)
    print("wrote", len(design.SHEETS) + 1, "sheets")


if __name__ == "__main__":
    main()
