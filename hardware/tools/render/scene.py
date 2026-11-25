"""Write scene.json for render.html: board outline, mounting holes, and stand-in bodies for parts
whose 3D model KiCad doesn't ship (custom Bosch packages, NEO module, VQFN-16, 2012 crystal).

    python3 scene.py ../../kicad/logger.kicad_pcb out/scene.json
"""
import json, os, sys
import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pcb as layout   # board size, origin and holes

# ref: (width, length, height, colour, label) in mm, before footprint rotation
STANDINS = {
    "U10": (12.2, 16.0, 2.4, "#c9ccd0", "u-blox NEO-F10N"),   # shielded module
    "U3": (3.0, 3.0, 0.9, "#1b1b1d", "TPS62130"),
    "U7": (2.0, 2.0, 0.75, "#d7d9dc", "BMP390"),               # metal lid with vent hole
    "U9": (1.28, 1.28, 0.6, "#1b1b1d", "BMM350"),
    "Y2": (2.0, 1.2, 0.6, "#cfd2d6", "32.768 kHz"),
}


def main():
    src, out = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(src)
    parts = []
    for f in board.GetFootprints():
        ref = f.GetReference()
        if ref not in STANDINS:
            continue
        w, l, h, col, label = STANDINS[ref]
        p = f.GetPosition()
        parts.append(dict(ref=ref, x=pcbnew.ToMM(p.x) - layout.OX, y=pcbnew.ToMM(p.y) - layout.OY,
                          rot=f.GetOrientationDegrees(), w=w, l=l, h=h, color=col, label=label,
                          bottom=f.GetLayer() == pcbnew.B_Cu))
    scene = dict(width=layout.W, height=layout.H, thickness=1.6, corner=2.0,
                 holes=[dict(x=x, y=y, d=3.2) for x, y in layout.HOLES], standins=parts)
    with open(out, "w") as fh:
        json.dump(scene, fh, indent=1)
    print("wrote", out, len(parts), "stand-ins")


if __name__ == "__main__":
    main()
