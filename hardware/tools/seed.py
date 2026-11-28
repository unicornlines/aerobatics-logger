#!/usr/bin/env python3
"""Seed the unrouted board with the copper of an earlier, routed board, so Freerouting only has to finish the nets
that changed. Freerouting is random and this board sits near the edge of what it can finish in one go; a small
change (two parts more) can turn a clean result into dozens of open connections. Keeping the known-good routes
of every unchanged net avoids that.

    python3 pcb.py && python3 seed.py old.kicad_pcb && python3 route.py /path/to/freerouting.jar

A net's old copper comes across whole, locked like the hand fanouts, when
  - every pad it connected on the old board still belongs to it, at the same place and side (it may have gained
    pads: those get routed), and
  - none of its tracks or vias would touch a pad of another net, pcb.py's hand copper, or come within 0.5 mm of the
    board edge.
Otherwise the router routes the whole net again. With --partial only its intact branches come across instead: the items
that clash or touched a pad that is gone are dropped, then dangling ends are trimmed until every track end sits on a
pad, a via or another track. That saves router work but the leftover branches can box it in, so it is off by default. GND is never copied: pcb.py's fanouts,
the pours and the stitching vias carry it.
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "kicad", "logger.kicad_pcb")
EDGE = pcbnew.FromMM(0.5)
PARTIAL = "--partial" in sys.argv     # also keep the intact branches of changed nets (stubs of them can box the router in)
CLEAR = pcbnew.FromMM(0.15)


def pad_map(board):
    m = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname():
                q = p.GetPosition()
                m.setdefault(p.GetNetname(), set()).add((f.GetReference(), p.GetNumber(), q.x, q.y, f.GetLayer()))
    return m


def main():
    old = pcbnew.LoadBoard(next(a for a in sys.argv[1:] if not a.startswith("--")))
    new = pcbnew.LoadBoard(PCB)
    assert all(t.IsLocked() for t in new.GetTracks()), "run pcb.py first: seed expects an unrouted board"
    old_pads, new_pads = pad_map(old), pad_map(new)
    pads = [p for f in new.GetFootprints() for p in f.Pads()]
    hand = list(new.GetTracks())                    # pcb.py's locked hand copper: old routes must not cross it
    inside = pcbnew.SHAPE_POLY_SET()
    new.GetBoardPolygonOutlines(inside)

    cache = {}

    def inner(half):
        if half not in cache:
            cache[half] = pcbnew.SHAPE_POLY_SET(inside)
            cache[half].Deflate(EDGE + half, 16)
        return cache[half]

    by_net = {}
    for t in old.GetTracks():
        by_net.setdefault(t.GetNetname(), []).append(t)

    def collides(t):
        net = t.GetNetname()
        layers = [l for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if t.IsOnLayer(l)]
        for l in layers:
            shape = t.GetEffectiveShape(l)
            for p in pads:
                if p.GetNetname() == net and p.GetNetname():
                    continue
                if p.IsOnLayer(l) and p.GetEffectiveShape(l).Collide(shape, CLEAR):
                    return True
                if p.GetDrillSize().x and p.GetEffectiveHoleShape().Collide(shape, CLEAR):
                    return True
            for h in hand:
                if h.GetNetname() != net and h.IsOnLayer(l) and h.GetEffectiveShape(l).Collide(shape, CLEAR):
                    return True
        bb = t.GetBoundingBox()
        r = max(bb.GetWidth(), bb.GetHeight())
        steps = max(1, int(r / pcbnew.FromMM(0.2)))
        a, b = (t.GetStart(), t.GetEnd()) if t.GetClass() == "PCB_TRACK" else (t.GetPosition(), t.GetPosition())
        shrunk = inner(t.GetWidth() // 2)
        for i in range(steps + 1):
            q = pcbnew.VECTOR2I(a.x + (b.x - a.x) * i // steps, a.y + (b.y - a.y) * i // steps)
            if not shrunk.Contains(q):
                return True
        return False

    new_by_net = {}
    for p in pads:
        new_by_net.setdefault(p.GetNetname(), []).append(p)
    PLANE = ("+3V3",)                                     # a via of a pour net is anchored by its plane...
    islands = [z.Outline() for z in new.Zones() if z.GetIsRuleArea()]   # ...unless it sits where the pour is kept out

    def plane_via(t):
        return t.GetNetname() in PLANE and not any(o.Contains(t.GetPosition()) for o in islands)

    def prune(net, items):
        """Drop what clashes or touched a pad that is gone, then trim the dangling ends until every track end sits on a
        pad of the net, a via or another track, so only whole branches come across."""
        gone = old_pads.get(net, set()) - new_pads.get(net, set())
        gone_xy = [(x, y) for _, _, x, y, _ in gone]
        def on_gone(t):
            pts = [t.GetStart(), t.GetEnd()] if t.GetClass() == "PCB_TRACK" else [t.GetPosition()]
            return any(abs(q.x - x) < pcbnew.FromMM(0.4) and abs(q.y - y) < pcbnew.FromMM(0.4) for q in pts for x, y in gone_xy)
        live, seen = [], set()
        for t in items:                                   # the old board can hold a wire twice: count it once
            k = (t.GetClass(), t.GetLayer(), *sorted([(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]))
            if k not in seen and not on_gone(t) and not collides(t):
                seen.add(k); live.append(t)
        own = new_by_net.get(net, [])
        while True:
            ends = {}
            for t in live:
                for q in ([t.GetStart(), t.GetEnd()] if t.GetClass() == "PCB_TRACK" else [t.GetPosition()]):
                    ends[(q.x, q.y)] = ends.get((q.x, q.y), 0) + 1
            def anchored(q, t):
                if any(p.HitTest(q) for p in own):
                    return True
                n = ends[(q.x, q.y)]
                return n >= 2 or (t.GetClass() == "PCB_VIA" and plane_via(t))
            keep = []
            for t in live:
                if t.GetClass() == "PCB_TRACK":
                    ok = anchored(t.GetStart(), t) and anchored(t.GetEnd(), t)
                else:
                    n = ends[(t.GetPosition().x, t.GetPosition().y)]   # itself and two tracks, or one into the plane
                    ok = n >= 3 or (n >= 2 and plane_via(t))
                if ok:
                    keep.append(t)
            if len(keep) == len(live):
                return live
            live = keep

    kept, dropped = [], []
    for net, items in sorted(by_net.items()):
        if net in ("", "GND"):
            continue
        whole = old_pads.get(net, set()) <= new_pads.get(net, set()) and not any(collides(t) for t in items)
        if not whole:
            items = prune(net, items) if PARTIAL else []
            if not items:
                dropped.append((net, "nothing left after the changes")); continue
            dropped.append((net, f"partly kept: {len(items)} items, the router finishes it"))
        else:
            kept.append(net)
        nn = new.FindNet(net)
        have = {(v.GetPosition().x, v.GetPosition().y) for v in new.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == net}
        for t in items:
            if t.GetClass() == "PCB_VIA" and (t.GetPosition().x, t.GetPosition().y) in have:
                continue                                  # pcb.py already places this via by hand
            if t.GetClass() == "PCB_TRACK" and t.GetLength() < pcbnew.FromMM(0.01):
                continue                                  # router crumbs: DRC calls them dangling once copied
            if t.GetClass() == "PCB_VIA":
                v = pcbnew.PCB_VIA(new); v.SetPosition(t.GetPosition()); v.SetWidth(t.GetWidth())
                v.SetDrill(t.GetDrill()); v.SetViaType(t.GetViaType())
                v.SetLayerPair(t.TopLayer(), t.BottomLayer()); c = v
            else:
                c = pcbnew.PCB_TRACK(new); c.SetStart(t.GetStart()); c.SetEnd(t.GetEnd())
                c.SetWidth(t.GetWidth()); c.SetLayer(t.GetLayer())
            c.SetNet(nn); c.SetLocked(True); new.Add(c)
    new.Save(PCB)
    print(f"seeded {len(kept)} nets; left to the router: {len(dropped)}")
    for net, why in dropped:
        print(f"  {net}: {why}")


if __name__ == "__main__":
    main()
