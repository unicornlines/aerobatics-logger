"""Grid maze router for a few leftover connections on a routed board (KiCad 7).

    python3 maze.py board.kicad_pcb [REF:PAD=NET ...] NET  REF:PAD|x,y[@L]  REF:PAD|x,y[@L]  [NET ...]

x,y are board mm; @L pins a free point to a layer (0 F.Cu, 1 In2, 2 B.Cu). REF:PAD=NET (or =-) moves a pad to
another net first, for a pin swap that the schematic (design.py) must then repeat.
Used after route.py when Freerouting leaves a few links open. Paths are string-pulled into 45-degree segments.
Refill zones and run DRC with the board inside hardware/kicad afterwards (the DRU rules only load there).

Each job: route NET from the first item to the second on F.Cu / In2 / B.Cu, 0.15 mm tracks, 0.5/0.25 vias,
0.15 mm clearance (0.45 to RF nets), keep-outs respected. Writes the board back with the new copper locked."""
import heapq, sys, math
import numpy as np, cv2, pcbnew

RES = 0.05                       # mm per cell
MM = pcbnew.FromMM
W_TR, CLR, V_D = 0.15, 0.15, 0.5
RF = {"GNSS_RF_IN", "ANT_INT", "ANT_EXT_SW", "GNSS_EXT_RF"}
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]

board = pcbnew.LoadBoard(sys.argv[1])
bb = board.GetBoardEdgesBoundingBox()
X0, Y0 = bb.GetX(), bb.GetY()
NX, NY = int(bb.GetWidth() / MM(RES)) + 1, int(bb.GetHeight() / MM(RES)) + 1


def cell(p):
    return int(round((p.x - X0) / MM(RES))), int(round((p.y - Y0) / MM(RES)))


def raster(m, poly):
    for i in range(poly.OutlineCount()):
        ol = poly.Outline(i)
        pts = np.array([[(ol.CPoint(j).x - X0) / MM(RES), (ol.CPoint(j).y - Y0) / MM(RES)] for j in range(ol.PointCount())], np.int32)
        cv2.fillPoly(m, [pts], 1)


def obstacles(net, extra):
    """extra = half width of what we place (track or via) beyond the clearance."""
    maps = {L: np.zeros((NY, NX), np.uint8) for L in LAYERS}
    items = [(p, p.GetNetname()) for f in board.GetFootprints() for p in f.Pads()]
    items += [(t, t.GetNetname()) for t in board.GetTracks()]
    for it, n in items:
        if n == net and n:
            continue
        c = (0.45 if n in RF else CLR) + extra
        for L in LAYERS:
            if not it.IsOnLayer(L):
                continue
            if it.GetClass() == "PCB_VIA":
                q = it.GetPosition()
                r = (it.GetWidth() / 2 + MM(c)) / MM(RES)
                cv2.circle(maps[L], (round((q.x - X0) / MM(RES)), round((q.y - Y0) / MM(RES))), int(math.ceil(r)), 1, -1)
                continue
            if it.GetClass() == "PCB_TRACK":
                a_, b_ = it.GetStart(), it.GetEnd()
                th = 2 * int(math.ceil((it.GetWidth() / 2 + MM(c)) / MM(RES))) + 1
                cv2.line(maps[L], (round((a_.x - X0) / MM(RES)), round((a_.y - Y0) / MM(RES))),
                         (round((b_.x - X0) / MM(RES)), round((b_.y - Y0) / MM(RES))), 1, th)
                continue
            buf = pcbnew.SHAPE_POLY_SET()
            it.TransformShapeToPolygon(buf, L, MM(c), MM(0.005))
            raster(maps[L], buf)
        if it.GetClass() == "PAD" and it.GetDrillSize().x:       # holes block every layer
            for L in LAYERS:
                buf = pcbnew.SHAPE_POLY_SET()
                it.TransformShapeToPolygon(buf, pcbnew.F_Cu, MM(c), MM(0.005))
                raster(maps[L], buf)
    zones = list(board.Zones()) + [z for f in board.GetFootprints() for z in f.Zones()]
    for z in zones:
        if not z.GetIsRuleArea() or not z.GetDoNotAllowTracks():
            continue
        for L in LAYERS:
            if z.IsOnLayer(L):
                buf = pcbnew.SHAPE_POLY_SET(z.Outline()); buf.Inflate(MM(extra), 8)
                raster(maps[L], buf)
    edge = np.ones((NY, NX), np.uint8)
    inside = pcbnew.SHAPE_POLY_SET(); board.GetBoardPolygonOutlines(inside); inside.Deflate(MM(0.5 + extra), 8)
    tmp = np.zeros((NY, NX), np.uint8); raster(tmp, inside); edge[tmp == 1] = 0
    for L in LAYERS:
        maps[L] |= edge
    return maps


ONLY = {}


def endpoint(spec):
    if ":" in spec:
        ref, pad = spec.split(":")
        p = next(q for q in board.FindFootprintByReference(ref).Pads() if q.GetNumber() == pad)
        return p
    L = None
    if "@" in spec:
        spec, L = spec.split("@"); L = int(L)
    x, y = map(float, spec.split(","))
    v = pcbnew.VECTOR2I(MM(100 + x), MM(100 + y)); ONLY[(v.x, v.y)] = L
    return v


def route(net, a_spec, b_spec):
    tr = obstacles(net, W_TR / 2)
    vi = obstacles(net, V_D / 2)
    via_ok = (vi[LAYERS[0]] | vi[LAYERS[1]] | vi[LAYERS[2]]) == 0
    a, b = endpoint(a_spec), endpoint(b_spec)
    def cells_of(e):
        if isinstance(e, pcbnew.PAD):
            m = np.zeros((NY, NX), np.uint8)
            Ls = [i for i, L in enumerate(LAYERS) if e.IsOnLayer(L)]
            buf = pcbnew.SHAPE_POLY_SET(); e.TransformShapeToPolygon(buf, pcbnew.F_Cu if 0 in Ls else pcbnew.B_Cu, 0, MM(0.005))
            raster(m, buf)
            ys, xs = np.nonzero(m)
            return {(l, x, y) for l in Ls for x, y in zip(xs, ys)}, e.GetPosition()
        x, y = cell(e)
        L = ONLY.get((e.x, e.y))
        return {(l, x, y) for l in (range(3) if L is None else [L])}, e
    S, sp = cells_of(a); T, tp = cells_of(b)
    for l, x, y in S | T:          # own pads are free
        tr[LAYERS[l]][y, x] = 0
    tx, ty = cell(tp)
    start = [(0.0, s) for s in S]
    g = {s: 0.0 for s in S}
    prev = {}
    pq = [(math.hypot(s[1] - tx, s[2] - ty), 0.0, s) for s in S]
    heapq.heapify(pq)
    VIA = 40.0
    steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    end = None
    while pq:
        f, gc, u = heapq.heappop(pq)
        if gc > g.get(u, 1e18):
            continue
        if u in T:
            end = u; break
        l, x, y = u
        nb = []
        for dx, dy, c in steps:
            nx, ny = x + dx, y + dy
            if 0 <= nx < NX and 0 <= ny < NY and not tr[LAYERS[l]][ny, nx]:
                nb.append(((l, nx, ny), c + (0.3 if l == 1 else 0)))
        if via_ok[y, x]:
            for l2 in range(3):
                if l2 != l and not tr[LAYERS[l2]][y, x]:
                    nb.append(((l2, x, y), VIA))
        for v, c in nb:
            ng = gc + c
            if ng < g.get(v, 1e18):
                g[v] = ng; prev[v] = u
                heapq.heappush(pq, (ng + math.hypot(v[1] - tx, v[2] - ty), ng, v))
    if not end:
        print(net, "NO PATH"); return False
    path = [end]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    # segments: break on layer change or direction change
    nets = board.FindNet(net)
    def pt(c):
        return pcbnew.VECTOR2I(int(X0 + c[1] * MM(RES)), int(Y0 + c[2] * MM(RES)))
    segs, vias = [], []
    run = [path[0]]
    for c in path[1:]:
        if c[0] != run[-1][0]:
            segs.append(run); vias.append(c); run = [c]; continue
        run.append(c)
    segs.append(run)
    def free(l, p, q):
        n = int(max(abs(q[1] - p[1]), abs(q[2] - p[2])) * 2) + 1
        m = tr[LAYERS[l]]
        for k in range(n + 1):
            x = round(p[1] + (q[1] - p[1]) * k / n); y = round(p[2] + (q[2] - p[2]) * k / n)
            if m[y, x] and (l, x, y) not in S and (l, x, y) not in T:
                return False
        return True
    def ok45(p, q):
        dx, dy = q[1] - p[1], q[2] - p[2]
        return dx == 0 or dy == 0 or abs(dx) == abs(dy)
    def bends(p, q):
        dx, dy = q[1] - p[1], q[2] - p[2]
        dx, dy = int(dx), int(dy)
        d = min(abs(dx), abs(dy)); sx = (dx > 0) - (dx < 0); sy = (dy > 0) - (dy < 0)
        a1 = (p[0], p[1] + sx * d, p[2] + sy * d)          # diagonal first
        a2 = (p[0], q[1] - sx * d, q[2] - sy * d)          # straight first
        return [a1, a2]
    smooth = []
    for r in segs:
        out = [r[0]]; i = 0
        while i < len(r) - 1:
            best = None
            for j in range(len(r) - 1, i, -1):
                if ok45(r[i], r[j]) and free(r[i][0], r[i], r[j]):
                    best = [r[j]]; break
                for m in bends(r[i], r[j]):
                    if free(r[i][0], r[i], m) and free(r[i][0], m, r[j]):
                        best = [m, r[j]]; break
                if best:
                    break
            out += best; i = r.index(best[-1])
        smooth.append([c for k, c in enumerate(out) if k == 0 or c != out[k - 1]])
    segs = []
    for out in smooth:
        segs += [[a_, b_] for a_, b_ in zip(out, out[1:])] if len(out) > 1 else [out]
    # snap the ends onto the pad centres
    n = 0
    for k, r in enumerate(segs):
        if len(r) < 2:
            continue
        s_, e_ = pt(r[0]), pt(r[-1])
        if k == 0 and isinstance(a, pcbnew.PAD): s_ = sp
        if k == len(segs) - 1 and isinstance(b, pcbnew.PAD): e_ = tp
        t = pcbnew.PCB_TRACK(board); t.SetStart(s_); t.SetEnd(e_); t.SetWidth(MM(W_TR))
        t.SetLayer(LAYERS[r[0][0]]); t.SetNet(nets); t.SetLocked(True); board.Add(t); n += 1
    for c in vias:
        v = pcbnew.PCB_VIA(board); v.SetPosition(pt(c)); v.SetWidth(MM(V_D)); v.SetDrill(MM(0.25))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets); v.SetLocked(True); board.Add(v)
    print(net, "routed:", n, "segments,", len(vias), "vias, length %.1f mm" % (g[end] * RES))
    return True


args = []
for a_ in sys.argv[2:]:
    if "=" in a_:
        rp, n_ = a_.split("="); ref, pad = rp.split(":")
        for q in board.FindFootprintByReference(ref).Pads():
            if q.GetNumber() == pad:
                q.SetNet(board.FindNet(n_) if n_ != "-" else board.FindNet(""))
        print("pad", rp, "->", n_)
    else:
        args.append(a_)
for i in range(0, len(args), 3):
    route(*args[i:i + 3])
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(sys.argv[1])
