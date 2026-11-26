"""Write scene.json for render.html: board outline, mounting holes, and stand-in bodies for parts
whose 3D model KiCad doesn't ship (custom Bosch packages, NEO module, VQFN-16, 2012 crystal, SHT40, IM69D130).

    python3 scene.py ../../kicad/logger.kicad_pcb out/scene.json
"""
import json, os, sys
import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pcb as layout   # board size, origin and holes

# ref: (width, length, height, colour, label) in mm, before footprint rotation
STANDINS = {
    "U10": (12.2, 16.0, 2.4, "#c9ccd0", "u-blox NEO-M9N"),   # shielded module
    "U3": (3.0, 3.0, 0.9, "#1b1b1d", "TPS62130"),
    "U7": (2.0, 2.0, 0.75, "#d7d9dc", "BMP390"),               # metal lid with vent hole
    "U9": (1.28, 1.28, 0.6, "#1b1b1d", "BMM350"),
    "Y2": (2.0, 1.2, 0.6, "#cfd2d6", "32.768 kHz"),
    "U12": (8.0, 6.0, 0.75, "#1b1b1d", "GD5F4GM8"),                # log flash, WSON-8 8x6
    "L60": (4.0, 4.0, 2.0, "#2a2a2c", "4R7"),                     # LCD boost inductor, FNR4020S
    "J63": [(6.0, 4.4, 2.9, "#ece6d4", "", 0.0, 0.3, 0.0)],       # JST-SH 4-pin side entry (Qwiic)
    "J62": [(4.6, 2.7, 1.75, "#ece6d4", "", 0.0, -0.05, 0.0)],    # JST-SUR 3-pin side entry (camera / marker)
    "J61": [(7.0, 3.2, 1.0, "#e8e2cf", "", 0.0, 1.9, 0.0)],       # Panasonic AYF531035 FPC socket
    "U16": (2.0, 1.25, 0.9, "#1b1b1d", ""),                       # TPS61222 LCD boost, SC-70-6
    "U13": (3.0, 3.0, 0.9, "#1b1b1d", "BQ24074"),                 # charger, VQFN-16 3x3
    "J2": [(9.9, 6.0, 4.8, "#ece6d4", "", 0.0, 1.4, 0.0)],        # JST-PH 3-pin side entry (battery)
    "U15": (1.5, 1.5, 0.75, "#1b1b1d", ""),                       # cell protector, WSON-6 1.5x1.5
    "F2": (3.2, 1.6, 0.6, "#ece6d4", "3A"),                       # battery fuse, 1206
    # Kailh Choc V1 switches without caps (the hotswap sockets are on the back: see SOCKET)
    **{f"SW{i}": [(15.0, 15.0, 2.2, "#2a2a2c", "", 0.0, 0.0, 0.0), (13.8, 13.8, 0.8, "#3a3a3d", "", 0.0, 0.0, 2.2),
                  (1.2, 3.0, 2.8, "#8a5a3c", "", -2.85, 0.0, 3.0), (1.2, 3.0, 2.8, "#8a5a3c", "", 2.85, 0.0, 3.0)]
       for i in (1, 2, 3)},                                       # brown twin-prong stem
    "F1": (1.6, 0.8, 0.5, "#ece6d4", ""),                         # expansion PTC, 0603
    "D24": (2.0, 1.25, 0.9, "#1b1b1d", ""),                       # BAT54W, SOT-323
    "U17": (1.5, 1.5, 0.5, "#3a3a3d", ""),                        # SHT40 humidity / temperature, DFN-4 1.5x1.5
    "MK1": (3.0, 4.0, 1.0, "#cfd2d6", ""),                        # MP34DT06J PDM mic, metal lid, top port
    # radio module: its own 0.8 mm PCB (antenna end bare, over the board edge) with the shield can on it.
    # Several boxes per part: (w, l, h, colour, label, dx, dy, dz) relative to the footprint origin.
    "U11": [(13.2, 16.6, 0.8, "#1b1b1d", "", 0.0, 0.0, 0.0),
            (12.4, 10.6, 1.6, "#c9ccd0", "ESP32-C6", 0.0, 2.75, 0.8)],
}
# Kailh hotswap sockets on the back of each key footprint, as two lobes around the switch pins (footprint coordinates)
SOCKET = [(4.85, 5.0, 1.85, "#1b1b1d", "", -0.03, -5.95, 0.0), (5.15, 4.85, 1.85, "#1b1b1d", "", 5.18, -3.68, 0.0)]


def main():
    src, out = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(src)
    parts = []
    for f in board.GetFootprints():
        ref = f.GetReference()
        p = f.GetPosition()
        if ref in ("SW1", "SW2", "SW3"):
            for w, l, h, col, label, dx, dy, dz in SOCKET:   # flipped: the bottom group mirrors y
                parts.append(dict(ref=ref, x=pcbnew.ToMM(p.x) - layout.OX, y=pcbnew.ToMM(p.y) - layout.OY,
                                  rot=f.GetOrientationDegrees(), w=w, l=l, h=h, color=col, label=label,
                                  dx=dx, dy=-dy, dz=dz, bottom=True))
        if ref not in STANDINS:
            continue
        boxes = STANDINS[ref] if isinstance(STANDINS[ref], list) else [STANDINS[ref] + (0.0, 0.0, 0.0)]
        p = f.GetPosition()
        for w, l, h, col, label, dx, dy, dz in boxes:
            parts.append(dict(ref=ref, x=pcbnew.ToMM(p.x) - layout.OX, y=pcbnew.ToMM(p.y) - layout.OY,
                              rot=f.GetOrientationDegrees(), w=w, l=l, h=h, color=col, label=label,
                              dx=dx, dy=dy, dz=dz, bottom=f.GetLayer() == pcbnew.B_Cu))
    scene = dict(width=layout.W, height=layout.H, thickness=1.6, corner=2.0,
                 holes=[dict(x=x, y=y, d=3.2) for x, y in layout.HOLES], standins=parts)
    with open(out, "w") as fh:
        json.dump(scene, fh, indent=1)
    print("wrote", out, len(parts), "stand-ins")


if __name__ == "__main__":
    main()
