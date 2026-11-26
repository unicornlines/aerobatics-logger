#!/usr/bin/env python3
"""Seed the unrouted board with the copper of an earlier, routed board, so Freerouting only has to finish the nets
that changed. Freerouting is random and this board sits near the edge of what it can finish in one go; a small
change (two parts more) can turn a clean result into dozens of open connections. Keeping the known-good routes
of every unchanged net avoids that.

    python3 pcb.py && python3 seed.py old.kicad_pcb && python3 route.py /path/to/freerouting.jar

A net's old copper comes across, locked like the hand fanouts, only when
  - every pad it connected on the old board still belongs to it (it may have gained pads: those get routed), and
  - none of its tracks or vias would touch a pad of another net or come within 0.5 mm of the board edge.
Otherwise the whole net is left to the router, so no half-net stubs remain. GND is never copied: pcb.py's fanouts,
the pours and the stitching vias carry it.
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "kicad", "logger.kicad_pcb")
EDGE = pcbnew.FromMM(0.5)
CLEAR = pcbnew.FromMM(0.15)


def pad_map(board):
    m = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname():
                m.setdefault(p.GetNetname(), set()).add((f.GetReference(), p.GetNumber()))
    return m


def main():
    old = pcbnew.LoadBoard(sys.argv[1])
    new = pcbnew.LoadBoard(PCB)
    assert all(t.IsLocked() for t in new.GetTracks()), "run pcb.py first: seed expects an unrouted board"
    old_pads, new_pads = pad_map(old), pad_map(new)
    pads = [p for f in new.GetFootprints() for p in f.Pads()]
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

    kept, dropped = [], []
    for net, items in sorted(by_net.items()):
        if net in ("", "GND"):
            continue
        if not old_pads.get(net, set()) <= new_pads.get(net, set()):
            dropped.append((net, "pads changed")); continue
        if any(collides(t) for t in items):
            dropped.append((net, "clashes with the new layout")); continue
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
