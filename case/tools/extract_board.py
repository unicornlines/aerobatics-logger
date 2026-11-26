#!/usr/bin/env python3
"""Read the board from KiCad and write case/board.scad for the OpenSCAD case.

    python3 case/tools/extract_board.py [path/to/logger.kicad_pcb]

Nothing in the case is typed in by hand: the outline, the mounting holes and
every part the case has to meet (connectors, keys, display, LEDs, sensors) come
from the .kicad_pcb, so a new board revision only needs this script re-run.

Coordinates in board.scad: millimetres, origin at the lower-left corner of the
board outline, x to the right, y up (towards the radio edge), z up out of the
front (F.Cu) side. KiCad's y points down, so y is flipped here.
"""
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "hardware" / "tools"))
import sexpr  # noqa: E402  (the repo's own KiCad S-expression reader)

PCB = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[1] / "hardware" / "kicad" / "logger.kicad_pcb"
OUT = HERE.parent / "board.scad"

# Which footprints the case cares about. First match wins: (role, footprint regex, reference regex).
ROLES = [
    ("hole",     r"MountingHole", r"^H"),
    ("usb_c",    r"USB_C", r"^J"),
    ("microsd",  r"microSD|Card", r"^J"),
    ("lcd_fpc",  r"FFC|FPC|AYF53", r"^J"),
    ("key",      r"Choc|PG1350|Kailh|SW_Push", r"^SW"),
    ("radio",    r"ESP32", r"^U"),
    ("gnss_rf",  r"U\.FL", r"^J"),
    ("battery",  r"JST_PH", r"^J"),
    ("qwiic",    r"JST_SH", r"^J"),
    ("camera",   r"JST_SUR|SUR_|PinHeader_1x03", r"^J"),
    ("led",      r"LED_", r"^D"),
    ("baro",     r"Bosch_LGA-10|BMP390", r"^U"),
    ("imu",      r"LGA-14|ICM-4568", r"^U"),
    ("mag",      r"WLCSP-9|BMM350", r"^U"),
    ("swd",      r"PinHeader_1x06", r"^J"),
    ("rh",       r"SHT4x|Sensirion_DFN", r"^U"),
    ("mic",      r"Sensor_Audio|PG-LLGA-5|MP34|HCLGA", r"^(MK|U)"),
]

# Part heights above their copper side (mm). Used for clearance checks and for the
# stand-in boxes in the renders. Matched against the footprint name, first match wins.
HEIGHTS = [
    (r"CP_Radial_D8", 11.5), (r"CP_Elec_5x5", 5.4), (r"USB_C", 3.31), (r"microSD", 1.98),
    (r"JST_PH", 4.85), (r"JST_SH", 2.9), (r"JST_SUR|SUR_", 1.75), (r"PinHeader_1x03", 8.5),
    (r"PinHeader_1x06", 4.5), (r"FFC|FPC|AYF53", 1.0), (r"ESP32", 2.55), (r"ublox_NEO", 2.4),
    (r"U\.FL", 1.25), (r"LQFP", 1.6), (r"WSON-8", 0.8), (r"Hotswap|hotswap|CPG1350", 1.85),
    (r"Choc|PG1350|Kailh", 5.0), (r"SW_Push", 1.9), (r"L_Changjiang|FNR4020", 2.0),
    (r"L_1210", 2.2), (r"Crystal", 0.8), (r"0805|1206|SOT-23|SOD-123", 1.2),
    (r"PG-LLGA-5", 1.2), (r"SHT4x|Sensirion_DFN", 0.6),
    (r"MountingHole", 0.0), (r"Logo|TestPoint", 0.0),
]
DEFAULT_H = 1.0
HOTSWAP_H = 1.85   # Kailh CPG135001S30 below B.Cu (hardware/README.md)

# Mechanical drawings on Dwgs.User (closed rectangles), recognised by size in mm (w, h, tolerance).
DRAWINGS = [("lcd", (62.8, 42.82), 0.3), ("lcd_active", (58.8, 35.28), 0.3), ("lcd_flex", (9.48, 3.0), 0.6)]


def kids(node, tag):
    return [e for e in node if isinstance(e, list) and e and e[0] == tag]


def kid(node, tag):
    k = kids(node, tag)
    return k[0] if k else None


def xy(node):
    return float(node[1]), float(node[2])


def arc_points(s, m, e, step_deg=6):
    """Points along a 3-point arc, start to end (excluding start)."""
    (x1, y1), (x2, y2), (x3, y3) = s, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / d
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1, a2, a3 = (math.atan2(p[1] - uy, p[0] - ux) for p in (s, m, e))

    def ccw(a, b):
        return (b - a) % (2 * math.pi)
    sweep = ccw(a1, a3)
    if ccw(a1, a2) > sweep:          # the mid point says we go the other way round
        sweep -= 2 * math.pi
    n = max(2, int(abs(math.degrees(sweep)) / step_deg))
    return [(ux + r * math.cos(a1 + sweep * i / n), uy + r * math.sin(a1 + sweep * i / n)) for i in range(1, n + 1)]


def chain(segments):
    """Join edge segments (lists of points) into one closed outline."""
    segs = [list(s) for s in segments]
    poly = segs.pop(0)
    close = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1]) < 0.01
    while segs:
        for i, s in enumerate(segs):
            if close(s[0], poly[-1]):
                poly += s[1:]; segs.pop(i); break
            if close(s[-1], poly[-1]):
                poly += list(reversed(s))[1:]; segs.pop(i); break
        else:
            raise SystemExit(f"Edge.Cuts is not one closed outline ({len(segs)} pieces left over)")
    if close(poly[0], poly[-1]):
        poly.pop()
    return poly


def main():
    root = sexpr.parse(PCB.read_text())[0]
    general = kid(root, "general")
    thick = float(kid(general, "thickness")[1]) if general and kid(general, "thickness") else 1.6

    # Outline: board-level gr_line / gr_arc on Edge.Cuts. (Circles would be cut-outs; none yet.)
    segs = []
    for e in root:
        if not (isinstance(e, list) and e and e[0] in ("gr_line", "gr_arc")):
            continue
        if kid(e, "layer")[1] != "Edge.Cuts":
            continue
        s, en = xy(kid(e, "start")), xy(kid(e, "end"))
        if e[0] == "gr_line":
            segs.append([s, en])
        else:
            segs.append([s] + arc_points(s, xy(kid(e, "mid")), en))
    outline = chain(segs)
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    ox, oy_top = min(xs), min(ys)
    W, H = max(xs) - ox, max(ys) - oy_top
    tx = lambda x, y: (round(x - ox, 3), round(H - (y - oy_top), 3))   # KiCad -> case coordinates
    pts = [tx(*p) for p in outline]
    # Keep the polygon counter-clockwise (OpenSCAD does not care, but offsets read better).
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts.reverse()

    # Dwgs.User rectangles drawn from lines: group line ends into closed loops, keep the boxes
    dl = []
    for e in root:
        if isinstance(e, list) and e and e[0] in ("gr_line", "gr_rect") and kid(e, "layer")[1] == "Dwgs.User":
            a, b = xy(kid(e, "start")), xy(kid(e, "end"))
            if e[0] == "gr_rect":
                dl += [[a, (b[0], a[1])], [(b[0], a[1]), b], [b, (a[0], b[1])], [(a[0], b[1]), a]]
            else:
                dl.append([a, b])
    rects = []
    while dl:
        loop, rest = [dl.pop(0)], []
        grown = True
        while grown:
            grown = False
            for seg in dl:
                pts_ = [p for s_ in loop for p in s_]
                if any(math.hypot(seg[i][0] - q[0], seg[i][1] - q[1]) < 0.01 for i in (0, 1) for q in pts_):
                    loop.append(seg); dl.remove(seg); grown = True; break
        xs_ = [p[0] for s_ in loop for p in s_]; ys_ = [p[1] for s_ in loop for p in s_]
        rects.append((min(xs_), min(ys_), max(xs_), max(ys_)))
    drawings = []
    for x0, y0, x1, y1 in rects:
        for role, (dw, dh), tol in DRAWINGS:
            if abs((x1 - x0) - dw) < tol and abs((y1 - y0) - dh) < tol:
                a, b = tx(x0, y1), tx(x1, y0)
                drawings.append((role.upper(), role, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.0, "F", [a[0], a[1], b[0], b[1]], 0.0, 0.0))

    feats, parts = [], []
    for fp in kids(root, "footprint"):
        lib = fp[1]
        name = lib.split(":")[-1]
        at = kid(fp, "at")
        fx, fy = float(at[1]), float(at[2])
        rot = float(at[3]) if len(at) > 3 else 0.0
        side = "F" if kid(fp, "layer")[1].startswith("F") else "B"
        ref = "?"
        for t in kids(fp, "fp_text") + kids(fp, "property"):
            if t[1] in ("reference", "Reference"):
                ref = t[2]
        # Courtyard (or fab) bounding box in board coordinates.
        c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        local = []
        for layer_pref in ("CrtYd", "Fab"):
            for g in fp:
                if not (isinstance(g, list) and g and g[0] in ("fp_line", "fp_rect", "fp_arc", "fp_circle", "fp_poly")):
                    continue
                ly = kid(g, "layer")
                if not ly or not ly[1].endswith(layer_pref):
                    continue
                if g[0] == "fp_circle":
                    cx, cy = xy(kid(g, "center")); ex, ey = xy(kid(g, "end")); r = math.hypot(ex - cx, ey - cy)
                    local += [(cx - r, cy - r), (cx + r, cy + r)]
                elif g[0] == "fp_poly":
                    local += [xy(p) for p in kids(kid(g, "pts"), "xy")]
                else:
                    local += [xy(kid(g, "start")), xy(kid(g, "end"))]
            if local:
                break
        if not local:
            local = [(xy(kid(p, "at"))) for p in kids(fp, "pad")] or [(0, 0)]
        # KiCad: board = pos + rotate(local, -rot) in a y-down frame.
        world = [(fx + px * c + py * s_, fy - px * s_ + py * c) for px, py in local]
        bx = [tx(*w) for w in world]
        bb = [min(p[0] for p in bx), min(p[1] for p in bx), max(p[0] for p in bx), max(p[1] for p in bx)]
        h = next((v for pat, v in HEIGHTS if re.search(pat, name)), DEFAULT_H)
        cx, cy = tx(fx, fy)
        parts.append((ref, name, side, bb, h))
        if re.search(r"Hotswap|hotswap", name):        # Choc switch on the front, socket on the back
            parts[-1] = (ref, name, "F", bb, 5.0)
            parts.append((ref + "_skt", name, "B", bb, HOTSWAP_H))
        role = next((r for r, lp, rp in ROLES if re.search(lp, name) and re.search(rp, ref)), None)
        if role:
            extra = 0.0
            if role == "hole":
                pad = kid(fp, "pad")
                extra = float(kid(pad, "drill")[1]) if pad and kid(pad, "drill") else 3.2
            feats.append((ref, role, cx, cy, rot, side, bb, h, extra))
            if role == "mic":                          # bottom-port mic: its sound hole through the board
                for pad in kids(fp, "pad"):
                    if len(pad) > 2 and pad[2] == "np_thru_hole":
                        px, py = xy(kid(pad, "at"))
                        hx, hy = tx(fx + px * c + py * s_, fy - px * s_ + py * c)
                        d = float(kid(pad, "drill")[1])
                        feats.append((ref + "_port", "mic_port", hx, hy, rot, side, [hx - d / 2, hy - d / 2, hx + d / 2, hy + d / 2], 0, d))

    feats += drawings

    def v(p):
        return "[" + ", ".join(f"{x:g}" for x in p) + "]"

    out = [
        "// GENERATED by case/tools/extract_board.py from " + str(PCB.relative_to(HERE.parents[1])),
        "// Do not edit: re-run the script after every board change.",
        "// Origin: lower-left of the board outline, y up (towards the radio edge), z up out of F.Cu.",
        "",
        f"board_w = {W:g};",
        f"board_h = {H:g};",
        f"board_t = {thick:g};",
        "board_outline = [" + ", ".join(v(p) for p in pts) + "];",
        "",
        "// [ref, role, [x, y], rotation, side, [x0, y0, x1, y1] courtyard, height above its side, extra]",
        "// extra = drill diameter for holes and the mic port.",
        "board_features = [",
    ]
    out += [f'  ["{r}", "{ro}", [{x:g}, {y:g}], {rt:g}, "{sd}", {v(bb)}, {h:g}, {ex:g}],'
            for r, ro, x, y, rt, sd, bb, h, ex in sorted(feats, key=lambda f: (f[1], f[0]))]
    out += ["];", "", "// Every footprint, for stand-in boxes in renders and clearance checks: [ref, side, bbox, height]",
            "board_parts = ["]
    out += [f'  ["{r}", "{sd}", {v(bb)}, {h:g}],' for r, n, sd, bb, h in parts if h > 0]
    out += ["];", ""]
    hf = max((h for r, n, sd, bb, h in parts if sd == "F"), default=0)
    hb = max((h for r, n, sd, bb, h in parts if sd == "B"), default=0)
    out += [f"board_max_h_front = {hf:g};", f"board_max_h_back = {hb:g};", ""]
    OUT.write_text("\n".join(out))
    print(f"{PCB.name}: {W:g} x {H:g} mm, {len(pts)} outline points, {len(feats)} case features, "
          f"{len(parts)} parts; tallest front {hf:g} mm, back {hb:g} mm -> {OUT.relative_to(HERE.parents[1])}")
    for f in sorted(feats, key=lambda f: (f[1], f[0])):
        print(f"  {f[1]:8s} {f[0]:5s} at ({f[2]:7.2f}, {f[3]:6.2f}) rot {f[4]:5.0f} {f[5]}  bbox {v(f[6])}")


if __name__ == "__main__":
    main()
