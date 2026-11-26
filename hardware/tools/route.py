"""Route the board with Freerouting, then pour copper, close the gaps and run DRC.

    python3 pcb.py && python3 route.py /path/to/freerouting.jar      # tested with Freerouting 2.1.0
    python3 pcb.py && python3 route.py --import                       # re-import the last SES only

1. Export Specctra DSN with only the In1 GND plane. In2 is a routing layer (the +3V3 pour fills
   around its tracks afterwards) and the high-current nets get a wider class.
2. Run Freerouting headless (fanout on, telemetry off, 5-minute job limit).
3. Import the SES, dropping the router's dead-end stubs; fan out GND pads it left unwired; stitch the
   outer GND pours to In1 on a 3 mm grid; give every via-less pour piece a via; fill zones.
4. Run DRC, repair what it still reports (forced fanout, straight joins, solid thermals), DRC again.

Freerouting is not deterministic, so two runs give different copper. The committed board is one
run that came out DRC-clean.
"""
import math
import os, re, subprocess, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "kicad", "logger.kicad_pcb")
WORK = os.environ.get("ROUTE_WORK", "/tmp/logger-route")
# High-current nets get a wider class. Plane nets (GND, +3V3) keep the default width so they
# can fan out of 0.4-0.5 mm pitch pads.
POWER_NETS = ["VBUS", "VSYS", "BUCK_SW", "VBAT", "BAT_CONN", "BAT_CELL", "BAT_NEG", "PROT_MID"]
POWER_WIDTH_UM = 400
RF_NETS = ["GNSS_RF_IN", "ANT_INT", "ANT_EXT_SW", "GNSS_EXT_RF"]   # same list as kicad/logger.kicad_dru
RF_CLEARANCE_UM = 450
PASSES = os.environ.get("PASSES", "25")


def export_dsn(board, path):
    # Only the In1 GND plane goes to the router as a plane. In2 is a signal layer for the router;
    # the +3V3 pour on In2 is filled around those tracks afterwards.
    strip = [z for z in board.Zones() if z.GetLayer() != pcbnew.In1_Cu]
    for z in strip:
        board.Remove(z)
    assert pcbnew.ExportSpecctraDSN(board, path)
    s = open(path).read()
    s = s.replace("(layer In1.GND\n      (type signal)", "(layer In1.GND\n      (type power)")
    # pull power nets out of the default class into a wider one
    m = re.search(r'\(class kicad_default ""(.*?)\n\s*\(circuit', s, re.S)
    names = m.group(1).split()
    power = [n for n in names if n in POWER_NETS]
    rf = [n for n in names if n in RF_NETS]
    rest = [n for n in names if n not in POWER_NETS and n not in RF_NETS]
    s = s.replace(m.group(1), " " + " ".join(rest))
    via = re.search(r"\(use_via ([^)]+)\)", s).group(1)
    cls = (f'    (class power {" ".join(power)}\n      (circuit\n        (use_via {via})\n      )\n'
           f'      (rule\n        (width {POWER_WIDTH_UM})\n        (clearance 150)\n      )\n    )\n')
    # GNSS RF lines are hand-routed and locked; the router keeps its own copper 0.45 mm off them (CPW gap)
    cls += (f'    (class rf {" ".join(rf)}\n      (circuit\n        (use_via {via})\n      )\n'
            f'      (rule\n        (width 340)\n        (clearance {RF_CLEARANCE_UM})\n      )\n    )\n')
    s = s.replace("    (class kicad_default", cls + "    (class kicad_default", 1)
    # Freerouting ignores KiCad rule areas: spell the patch feed keep-out (nothing on In2 or B.Cu, In1 is a plane)
    # out as Specctra keep-outs. DSN units are um, origin as the page, y up.
    import pcb as layout
    x0, y0, x1, y1 = layout.FEED_KEEPOUT
    ko = "".join(f'    (keepout "" (rect {L} {(layout.OX + x0) * 1000:.0f} {-(layout.OY + y1) * 1000:.0f} '
                 f'{(layout.OX + x1) * 1000:.0f} {-(layout.OY + y0) * 1000:.0f}))\n' for L in ("In2.3V3", "B.Cu"))
    i = s.index("\n    (via ", s.index("  (structure")) + 1      # after the layers and the boundary
    s = s[:i] + ko + s[i:]
    open(path, "w").write(s)
    return strip


def main():
    jar = sys.argv[1]
    os.makedirs(WORK, exist_ok=True)
    dsn, ses = os.path.join(WORK, "logger.dsn"), os.path.join(WORK, "logger.ses")
    board = pcbnew.LoadBoard(PCB)
    export_dsn(board, dsn)
    if os.path.exists(ses):
        os.remove(ses)
    cmd = ["java", "-Xmx6g", "-jar", jar, "-de", dsn, "-do", ses, "--gui.enabled=false",
           f"--router.max_passes={PASSES}", "--router.fanout.enabled=true", "--router.optimizer.max_passes=20", f"--router.job_timeout={os.environ.get('JOB_TIMEOUT', '00:10:00')}",
           "--profile.allow_telemetry=false", "--usage_and_diagnostic_data.disable_analytics=true"]
    print(" ".join(cmd))
    # Freerouting 2.1's fanout pass sometimes dies on a null corner and the job then hangs forever; the run is
    # random, so a fresh start usually goes through. Watch its output and restart it (up to 4 tries).
    for attempt in range(4):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        crashed = False
        for line in p.stdout:
            sys.stdout.write(line)
            if "from_corner" in line:
                crashed = True
                p.kill()
                break
        p.wait(timeout=1500)
        if not crashed:
            break
        print(f"freerouting fanout crash, restarting (attempt {attempt + 2})", flush=True)
    else:
        raise SystemExit("freerouting crashed four times")
    # import in a fresh process: a second LoadBoard after the export's zone removal returns a broken object
    subprocess.run([sys.executable, os.path.abspath(__file__), "--import"], check=True)


def read_ses(board, path):
    """Add the SES wires and vias to the board (pcbnew.ImportSpecctraSES needs the GUI's board).
    Router leftovers (stubs that end nowhere, vias with copper on one side only) are pruned first."""
    from sexpr import parse
    ses = parse(open(path).read())[0]
    routes = next(e for e in ses if isinstance(e, list) and e[0] == "routes")
    res = next(e for e in routes if isinstance(e, list) and e[0] == "resolution")
    scale = {"um": 1e-3, "mm": 1.0, "mil": 0.0254}[res[1]] / float(res[2])   # file units -> mm
    nm = lambda v: pcbnew.FromMM(float(v) * scale)
    layers = {board.GetLayerName(l): l for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)}
    net_out = next(e for e in routes if isinstance(e, list) and e[0] == "network_out")
    segs, vias = [], []          # (net, layer, a, b, width) / (net, pos, size, drill), points as (x, y) nm
    for net in net_out[1:]:
        for item in net[2:]:
            if item[0] == "wire":
                p = item[1]
                xy = [(nm(p[3 + i]), -nm(p[4 + i])) for i in range(0, len(p) - 4, 2)]
                segs += [(net[1], layers[p[1]], a, b, nm(p[2])) for a, b in zip(xy, xy[1:])
                         if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 10000]     # drop sub-10 um crumbs (DRC: dangling)
            elif item[0] == "via":
                m = re.search(r"_(\d+):(\d+)_um", item[1])
                vias.append((net[1], (nm(item[2]), -nm(item[3])), int(m.group(1)) * 1000, int(m.group(2)) * 1000))
    segs = list(dict.fromkeys((n, L, *sorted((a, b)), w) for n, L, a, b, w in segs))   # drop duplicate wires
    # Freerouting ignores the edge clearance on inner board cut-outs (the humidity sensor's notch) for the power class.
    # Pour nets don't need those runs: the pours, the planes and the fanout vias carry them, so drop the offenders.
    outline = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(outline)
    inner = {}

    def in_board(a, b, w):
        if w not in inner:
            inner[w] = pcbnew.SHAPE_POLY_SET(outline); inner[w].Deflate(MM(0.5) + w // 2, 16)
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // MM(0.1)))
        return all(inner[w].Contains(pcbnew.VECTOR2I(a[0] + (b[0] - a[0]) * i // k, a[1] + (b[1] - a[1]) * i // k)) for i in range(k + 1))
    n0 = len(segs)
    segs = [s_ for s_ in segs if s_[0] not in ("GND", "+3V3") or in_board(s_[2], s_[3], s_[4])]
    if len(segs) < n0:
        print(f"  dropped {n0 - len(segs)} pour-net segments too close to the board edge")
    pads = [(p.GetNetname(), p) for f in board.GetFootprints() for p in f.Pads()]

    def on_pad(net, L, q):
        return any(n == net and p.IsOnLayer(L) and p.HitTest(pcbnew.VECTOR2I(*q)) for n, p in pads)

    def on_seg(q, a, b):
        ax, ay, bx, by = *a, *b
        L2 = (bx - ax) ** 2 + (by - ay) ** 2
        t = max(0, min(1, ((q[0] - ax) * (bx - ax) + (q[1] - ay) * (by - ay)) / L2))
        return (q[0] - ax - t * (bx - ax)) ** 2 + (q[1] - ay - t * (by - ay)) ** 2 < 1000 ** 2

    zone_nets = ("GND", "+3V3")
    fixed_vias = {(v.GetNetname(), (v.GetPosition().x, v.GetPosition().y)) for v in board.GetTracks() if v.GetClass() == "PCB_VIA"}
    while True:
        vpos = {(n, q) for n, q, _, _ in vias} | fixed_vias     # pcb.py's locked vias count as anchors too
        keep = []
        for k, (n, L, a, b, w) in enumerate(segs):
            if n == "GND" or (n == "+3V3" and L == pcbnew.In2_Cu):     # these may end in their pour
                keep.append(segs[k]); continue
            ok = all((n, q) in vpos or on_pad(n, L, q) or
                     any(i != k and m == n and M == L and on_seg(q, c, d) for i, (m, M, c, d, _) in enumerate(segs))
                     for q in (a, b))
            if ok:
                keep.append(segs[k])
        kv = []
        for v in vias:
            n, q = v[0], v[1]
            ls = {L for m, L, a, b, _ in keep if m == n and on_seg(q, a, b)}
            ls |= {L for L in layers.values() if on_pad(n, L, q)}
            if n in zone_nets or len(ls) >= 2:
                kv.append(v)
        if len(keep) == len(segs) and len(kv) == len(vias):
            break
        print(f"  pruned {len(segs) - len(keep)} stub segments, {len(vias) - len(kv)} vias")
        segs, vias = keep, kv
    tracks, out_vias = [], []
    for n, L, a, b, w in segs:
        t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(*a)); t.SetEnd(pcbnew.VECTOR2I(*b))
        t.SetWidth(w); t.SetLayer(L); t.SetNet(board.FindNet(n)); board.Add(t); tracks.append(t)
    for n, q, size, drill in vias:
        v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(*q)); v.SetWidth(size); v.SetDrill(drill)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(board.FindNet(n)); board.Add(v); out_vias.append(v)
    print(f"imported {len(tracks)} track segments, {len(out_vias)} vias")
    return tracks, out_vias   # keep our own lists: board.Tracks() comes back unwrapped after these Adds (KiCad 7 SWIG)


STITCH_PITCH = 3.0          # mm, GND stitching via grid
STITCH_AVOID = ("J1", "J60", "J61", "SW1", "SW2", "SW3", "SW4")   # metal shells / FPC: no vias underneath
MM = pcbnew.FromMM
OUTER = (pcbnew.F_Cu, pcbnew.B_Cu)


class Copper:
    """Copper already on the board, for placing extra GND vias and short fanout tracks without DRC errors."""

    def __init__(self, board, tracks, vias):
        self.board, self.gnd = board, board.FindNet("GND")
        self.pads = [p for f in board.GetFootprints() for p in f.Pads()]
        self.tracks = list(tracks)
        self.vias = [(v.GetPosition(), v.GetNetname()) for v in vias]
        fps = list(board.GetFootprints())
        self.avoid = [f.GetCourtyard(pcbnew.F_CrtYd) for f in fps if f.GetReference() in STITCH_AVOID]
        self.avoid += [z.Outline() for f in fps for z in f.Zones() if z.GetIsRuleArea()]
        for z in board.Zones():                     # board-level keep-outs (the humidity sensor's copper-free island)
            if z.GetIsRuleArea():
                o = pcbnew.SHAPE_POLY_SET(z.Outline()); o.Inflate(MM(0.6), 16); self.avoid.append(o)
        self.inside = pcbnew.SHAPE_POLY_SET()       # the board outline shrunk by edge clearance + via radius
        board.GetBoardPolygonOutlines(self.inside)
        self.inside.Deflate(MM(0.8), 16)

    def near(self, a, b, r):
        return abs(a.x - b.x) < r and abs(a.y - b.y) < r

    def via_fits(self, c, margin=MM(1.0), net="GND"):
        import pcb as layout
        x, y = pcbnew.ToMM(c.x) - layout.OX, pcbnew.ToMM(c.y) - layout.OY
        if not (1.2 < x < layout.W - 1.2 and 1.2 < y < layout.H - 1.2):
            return False
        if not self.inside.Contains(c):
            return False
        if any(a.Contains(c) for a in self.avoid):
            return False
        circ, R = pcbnew.SHAPE_CIRCLE(c, MM(0.25)), MM(4)
        for v, n in self.vias:
            if (c - v).EuclideanNorm() < (margin if n == net else MM(0.75)):
                return False
        for p in self.pads:
            if not self.near(p.GetPosition(), c, R):
                continue
            g = p.GetNetname() == net
            if any(p.GetEffectiveShape(l).Collide(circ, MM(0.1) if g else MM(0.2)) for l in OUTER if p.IsOnLayer(l)):
                return False
            if p.GetDrillSize().x and (c - p.GetPosition()).EuclideanNorm() < p.GetDrillSize().x / 2 + MM(0.45):
                return False
        return not any(t.GetNetname() != net and t.GetEffectiveShape().Collide(circ, MM(0.2)) for t in self.tracks
                       if self.near(t.GetStart(), c, R) or self.near(t.GetEnd(), c, R) or t.GetLength() > R)

    def track_fits(self, a, b, layer, own, w=MM(0.25)):
        net = own.GetNetname()
        seg = pcbnew.SHAPE_SEGMENT(a, b, w)
        mid, R = (a + b) / 2, MM(4) + (a - b).EuclideanNorm() // 2
        for p in self.pads:
            if p is own or p.GetNetname() == net or not p.IsOnLayer(layer) or not self.near(p.GetPosition(), mid, R):
                continue
            if p.GetEffectiveShape(layer).Collide(seg, MM(0.15)):
                return False
        for t in self.tracks:
            if t.GetLayer() == layer and t.GetNetname() != net and t.GetEffectiveShape().Collide(seg, MM(0.15)):
                return False
        return not any(n != net and seg.Collide(pcbnew.SHAPE_CIRCLE(v, MM(0.25)), MM(0.15)) for v, n in self.vias)

    def add_via(self, c, net="GND"):
        v = pcbnew.PCB_VIA(self.board); v.SetPosition(c); v.SetWidth(MM(0.5)); v.SetDrill(MM(0.25))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(self.board.FindNet(net)); self.board.Add(v)
        self.vias.append((c, net))

    def add_track(self, a, b, layer, w=MM(0.25), net="GND"):
        t = pcbnew.PCB_TRACK(self.board); t.SetStart(a); t.SetEnd(b); t.SetWidth(w)
        t.SetLayer(layer); t.SetNet(self.board.FindNet(net)); self.board.Add(t); self.tracks.append(t)


def fanout_pad(cu, p):
    """Short track from a GND pad to a new via: try the 8 directions first (tidy), then any free spot nearby."""
    import math
    layer = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    c0, half = p.GetPosition(), max(p.GetSize().x, p.GetSize().y) // 2
    cands = []
    for d in (MM(0.45), MM(0.7), MM(1.0), MM(1.4), MM(2.0), MM(2.6), MM(3.2)):
        for k in range(8):
            ang = math.radians(p.GetOrientationDegrees()) + k * math.pi / 4
            cands.append(c0 + pcbnew.VECTOR2I(int((half + d) * math.cos(ang)), int(-(half + d) * math.sin(ang))))
    grid = [pcbnew.VECTOR2I(c0.x + MM(dx / 10), c0.y + MM(dy / 10)) for dx in range(-20, 21) for dy in range(-20, 21)]
    cands += sorted(grid, key=lambda c: (c - c0).EuclideanNorm())
    net = p.GetNetname()
    for c in cands:
        if cu.via_fits(c, margin=MM(0.7), net=net) and cu.track_fits(c0, c, layer, p, w=MM(0.2)):
            cu.add_via(c, net); cu.add_track(c0, c, layer, w=MM(0.2), net=net)
            return True
    if maze_fanout(cu, p.GetPosition(), layer, p, f"{p.GetParent().GetReference()} {p.GetNumber()}",
                   max(p.GetSize().x, p.GetSize().y) / 2e6 + 0.3, net=net):
        return True
    print("  no fanout room for", p.GetParent().GetReference(), p.GetNumber())
    return False


def maze_fanout(cu, c0, layer, p=None, label="", half=0.3, R=25, step=0.1, w=MM(0.2), net="GND"):
    """Grid search (0.1 mm, 8 directions) from a boxed-in GND pad or stub to the nearest spot a via fits."""
    from collections import deque
    near = lambda q: cu.near(q, c0, MM(R * step + 1.5))
    pads = [q for q in cu.pads if q is not p and q.IsOnLayer(layer) and q.GetNetname() != net and near(q.GetPosition())]
    tracks = [t for t in cu.tracks if t.GetLayer() == layer and t.GetNetname() != net
              and (near(t.GetStart()) or near(t.GetEnd()) or t.GetLength() > MM(3))]
    vias = [v for v, n in cu.vias if n != net and near(v)]
    pt = lambda i, j: pcbnew.VECTOR2I(c0.x + MM(i * step), c0.y + MM(j * step))
    free = {}
    def ok(i, j):
        if (i, j) not in free:
            dot = pcbnew.SHAPE_CIRCLE(pt(i, j), w // 2)
            free[(i, j)] = not (any(q.GetEffectiveShape(layer).Collide(dot, MM(0.15)) for q in pads)
                                or any(t.GetEffectiveShape().Collide(dot, MM(0.15)) for t in tracks)
                                or any((pt(i, j) - v).EuclideanNorm() < MM(0.25 + 0.15) + w // 2 for v in vias))
        return free[(i, j)]
    prev, q = {(0, 0): None}, deque([(0, 0)])
    while q:
        i, j = q.popleft()
        if (i * i + j * j) ** 0.5 * step > half and cu.via_fits(pt(i, j), margin=MM(0.7), net=net):
            path = [(i, j)]
            while prev[path[-1]] is not None:
                path.append(prev[path[-1]])
            path.reverse()
            corners = [path[0]] + [b for a, b, c in zip(path, path[1:], path[2:])
                                   if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1])] + [path[-1]]
            for a, b in zip(corners, corners[1:]):
                cu.add_track(pt(*a), pt(*b), layer, w, net=net)
            cu.add_via(pt(i, j), net)
            print("  maze fanout", label, f"{len(corners) - 1} segments")
            return True
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            n = (i + di, j + dj)
            if n not in prev and abs(n[0]) <= R and abs(n[1]) <= R and ok(*n):
                prev[n] = (i, j); q.append(n)
    return False


def fanout(cu):
    """Every GND SMD pad the router didn't wire gets its own short track to a GND via, so no pour island
    has to carry it to the plane."""
    import math
    wired = {(t.GetStart().x, t.GetStart().y) for t in cu.tracks if t.GetNetname() == "GND"}
    wired |= {(t.GetEnd().x, t.GetEnd().y) for t in cu.tracks if t.GetNetname() == "GND"}
    n = 0
    for p in cu.pads:
        if p.GetNetname() != "GND" or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        layer = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        if any(p.HitTest(pcbnew.VECTOR2I(*e)) for e in wired if cu.near(pcbnew.VECTOR2I(*e), p.GetPosition(), MM(3))):
            continue
        n += fanout_pad(cu, p)
    print("GND fanout vias:", n)


def stitch(cu):
    """GND vias on a regular grid wherever one fits: ties the outer pours to the In1 plane."""
    import pcb as layout
    added = 0
    y = STITCH_PITCH / 2
    while y < layout.H:
        x = STITCH_PITCH / 2
        while x < layout.W:
            c = pcbnew.VECTOR2I(MM(layout.OX + x), MM(layout.OY + y))
            if cu.via_fits(c):
                cu.add_via(c); added += 1
            x += STITCH_PITCH
        y += STITCH_PITCH
    print("stitching vias:", added)


def island_vias(board, cu):
    """Give every outer GND pour piece that has no via its own via to the plane."""
    have = [v for v, n in cu.vias if n == "GND"]
    have += [p.GetPosition() for p in cu.pads if p.GetNetname() == "GND" and p.GetDrillSize().x]
    added, step = 0, MM(0.25)
    for z in board.Zones():
        L = z.GetLayer()
        if L not in OUTER:
            continue
        polys = z.GetFilledPolysList(L)
        for i in range(polys.OutlineCount()):
            ol = polys.Outline(i)
            if any(ol.PointInside(v) for v in have):
                continue
            bb = ol.BBox()
            best = None
            for x in range(bb.GetLeft(), bb.GetRight(), step):
                for y in range(bb.GetTop(), bb.GetBottom(), step):
                    c = pcbnew.VECTOR2I(x, y)
                    ring = [c + pcbnew.VECTOR2I(dx, dy) for dx, dy in ((MM(.3), 0), (-MM(.3), 0), (0, MM(.3)), (0, -MM(.3)))]
                    if all(ol.PointInside(r) for r in ring) and cu.via_fits(c, margin=MM(0.7)):
                        best = c; break
                if best:
                    break
            if best:
                cu.add_via(best); have.append(best); added += 1
    print("island vias:", added)
    return added


def drc():
    rpt = os.path.join(WORK, "drc.rpt")
    board = pcbnew.LoadBoard(PCB)
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    return open(rpt).read()


def isolated_pads(board, net="GND"):
    """Pads of `net` whose copper (fill pieces, tracks, vias) never reaches the main body of the net.
    DRC reports such a piece as 'Zone - Zone' without a location, so find it by our own union-find."""
    par = {}
    def root(a):
        while par.setdefault(a, a) != a: a = par[a]
        return a
    def join(a, b): par[root(a)] = root(b)
    frags = []
    for z in board.Zones():
        if z.GetNetname() != net or z.GetIsRuleArea(): continue
        for L in z.GetLayerSet().Seq():
            fp = z.GetFilledPolysList(L)
            for i in range(fp.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(fp.Outline(i))
                for h in range(fp.HoleCount(i)): one.AddHole(fp.Hole(i, h))
                frags.append((("Z", len(frags)), L, one)); root(frags[-1][0])
    pads = [(("P", i), p) for i, p in enumerate(p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == net)]
    trs = [(("T", i), t) for i, t in enumerate(t for t in board.GetTracks() if t.GetNetname() == net)]
    for k, _ in pads + trs: root(k)
    for k, t in trs:
        via = t.GetClass() == "PCB_VIA"
        for pt in ([t.GetPosition()] if via else [t.GetStart(), t.GetEnd()]):
            for kf, L, one in frags:
                if (via or L == t.GetLayer()) and one.Collide(pt, 1000): join(k, kf)
            for kp, p in pads:
                if (via or p.IsOnLayer(t.GetLayer())) and p.HitTest(pt): join(k, kp)
            for k2, t2 in trs:
                if k2 != k and (via or t2.GetClass() == "PCB_VIA" or t2.GetLayer() == t.GetLayer()) and t2.HitTest(pt, 0): join(k, k2)
    for kp, p in pads:                     # a pad joins a fill piece only where the copper really overlaps (spokes)
        for kf, L, one in frags:
            if p.IsOnLayer(L):
                pp = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(pp, L, 0, 5000)
                pp.BooleanIntersection(one, pcbnew.SHAPE_POLY_SET.PM_FAST)
                if pp.OutlineCount(): join(kp, kf)
    groups = {}
    for k in par: groups.setdefault(root(k), []).append(k)
    main = max(groups.values(), key=len)
    out = []
    for g in groups.values():
        has_zone = any(k[0] == "Z" for k in g)
        if g is not main and has_zone:
            out += [p for kp, p in pads if kp in g and not p.HasHole()]
    return out


def repair(txt):
    """Second pass on what DRC still reports: GND pads left off the plane get a forced fanout, two pads of
    one net still apart get a straight track on the first layer where it fits, starved thermals go solid."""
    board = pcbnew.LoadBoard(PCB)
    items = list(board.GetTracks())
    cu = Copper(board, [t for t in items if t.GetClass() == "PCB_TRACK"], [t for t in items if t.GetClass() == "PCB_VIA"])
    pads = {(p.GetParent().GetReference(), p.GetNumber()): p for p in cu.pads}
    pad_re = r"(?i:pad) (\S+) \[([^\]]+)\] of (\S+)"
    fanned = set()
    for block in re.split(r"\n(?=\[)", txt):
        found = [(r, n, net) for n, net, r in re.findall(pad_re, block)]
        if block.startswith("[starved_thermal]"):
            for r, n, net in found:
                pads[(r, n)].SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL); print("  solid GND connection:", r, n)
        elif block.startswith("[unconnected_items]") and not found and "Zone [GND]" in block and "Track [GND]" not in block:
            for p in isolated_pads(board):
                print("  isolated GND piece at", p.GetParent().GetReference(), p.GetNumber()); fanout_pad(cu, p)
        elif block.startswith("[unconnected_items]") and not found:
            for x, y, L in re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\): Track \[GND\] on ([FB]\.Cu)", block):
                maze_fanout(cu, pcbnew.VECTOR2I(MM(float(x)), MM(float(y))), {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}[L], label=f"GND stub at {x},{y}")
        elif block.startswith("[unconnected_items]"):
            if len(found) == 2 and found[0][2] == found[1][2]:
                a, b = pads[found[0][:2]], pads[found[1][:2]]
                for L in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu):
                    if a.IsOnLayer(L) and b.IsOnLayer(L) and cu.track_fits(a.GetPosition(), b.GetPosition(), L, a, w=MM(0.4)):
                        t = pcbnew.PCB_TRACK(board); t.SetStart(a.GetPosition()); t.SetEnd(b.GetPosition())
                        t.SetWidth(MM(0.4)); t.SetLayer(L); t.SetNet(a.GetNet()); board.Add(t); cu.tracks.append(t)
                        print("  direct track", found[0][2], board.GetLayerName(L)); break
                else:
                    print("  could not join", found)
            else:
                for r, n, net in found:
                    if net in ("GND", "+3V3"):
                        at = (pads[(r, n)].GetPosition().x, pads[(r, n)].GetPosition().y, net)
                        if at not in fanned:       # stacked pads (USB-C A12/B1) need one fanout, not two
                            fanned.add(at); fanout_pad(cu, pads[(r, n)])
                    else:
                        a = pads[(r, n)]
                        others = sorted((q for q in cu.pads if q.GetNetname() == net and q is not a),
                                        key=lambda q: (q.GetPosition() - a.GetPosition()).EuclideanNorm())
                        for b in others[:2]:
                            L = next((L for L in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu) if a.IsOnLayer(L) and b.IsOnLayer(L)
                                      and cu.track_fits(a.GetPosition(), b.GetPosition(), L, a, w=MM(0.4))), None)
                            if L is not None:
                                t = pcbnew.PCB_TRACK(board); t.SetStart(a.GetPosition()); t.SetEnd(b.GetPosition())
                                t.SetWidth(MM(0.4)); t.SetLayer(L); t.SetNet(a.GetNet()); board.Add(t); cu.tracks.append(t)
                                print("  direct track", net, r, n, "->", b.GetParent().GetReference(), b.GetNumber(), board.GetLayerName(L))
                                break
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)


def import_ses():
    ses = os.path.join(WORK, "logger.ses")
    board = pcbnew.LoadBoard(PCB)
    pre = list(board.GetTracks())
    assert all(t.IsLocked() for t in pre), "run pcb.py first: import expects an unrouted board"
    tracks, vias = read_ses(board, ses)
    tracks += [t for t in pre if t.GetClass() == "PCB_TRACK"]; vias += [t for t in pre if t.GetClass() == "PCB_VIA"]
    cu = Copper(board, tracks, vias)
    fanout(cu)
    stitch(cu)
    for z in board.Zones():
        if z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    for _ in range(4):
        if not island_vias(board, cu):
            break
        filler.Fill(board.Zones())
    board.Save(PCB)
    txt = drc()
    if "--no-repair" not in sys.argv:
        repair(txt)
        txt = drc()
    kinds = re.findall(r"^\[(\w+)\]", txt, re.M)
    print({k: kinds.count(k) for k in sorted(set(kinds))})
    nets = re.findall(r"\[unconnected_items\].*?\n(?:\s+Local.*\n)?.*?\[([^\]]+)\]", txt)
    print("unconnected by net:", {n: nets.count(n) for n in sorted(set(nets), key=nets.count, reverse=True)})
    print("tracks:", len(board.GetTracks()))


if __name__ == "__main__":
    import_ses() if sys.argv[1:] == ["--import"] else main()
