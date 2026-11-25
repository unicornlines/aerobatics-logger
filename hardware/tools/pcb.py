"""Build the rev A board (../kicad/logger.kicad_pcb) from design.py and the placement below.

Nets come straight from design.py, so the board and schematic share one source.
Placement is by hand, block by block, on a 0.5 mm grid. A few fanouts are placed by hand and locked
(MCU and IMU ground pins, crystal load caps, every R/C ground pad), then route.py autoroutes the rest.

Board: 88 x 62 mm, 4 layers: F.Cu signal, In1 GND plane, In2 +3V3 pour with some signal routing, B.Cu signal.
"""
import os, sys
import pcbnew
import design

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD = os.path.join(HERE, "..", "kicad")
SYSFP = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0          # board top-left on the page
W, H = 88.0, 62.0
MM = pcbnew.FromMM

# Extra pads the footprint has but the symbol doesn't.
EXTRA_PADS = {("J60", "11"): "GND", ("J61", "MP"): "GND", ("J63", "MP"): "GND"}

# ref: (x, y, rotation, side)  -- board coordinates in mm from the top-left corner; side "F" or "B"
P = {}
def at(ref, x, y, rot=0, side="F"):
    P[ref] = (x, y, rot, side)
def row(refs, x, y, dx, dy, rot=0, side="F"):
    for i, r in enumerate(refs):
        at(r, x + i * dx, y + i * dy, rot, side)

# --- MCU block (centre). Sits 2.1 mm lower than first drawn, to make room for the radio flush with the top edge.
at("U5", 42, 29.1)
row(["C20", "C21"], 31.5, 21.6, 0, 2.0, 0)           # left side decoupling
row(["C22", "C23"], 52.5, 34.1, 0, 2.0, 0)           # right side decoupling
row(["C24", "C25"], 46.0, 39.6, 2.5, 0, 90)          # bottom
row(["C26", "C27"], 31.5, 36.1, 0, 2.0, 0)           # VCAP, near pins 48/73
at("C28", 38.0, 18.6, 90); at("C29", 35.5, 18.6, 90); at("R20", 48.0, 18.6, 90)
at("Y1", 28.0, 29.1, 90); at("C30", 28.0, 26.2, 0); at("C31", 28.0, 32.0, 0)
at("Y2", 28.0, 22.0, 90); at("C32", 28.0, 19.8, 0); at("C33", 28.0, 24.2, 0)   # one column with the HSE crystal
at("FB1", 40.5, 18.6, 0); at("C10", 43.0, 18.6, 90); at("C11", 45.5, 18.6, 90)   # top row on a 2.5 mm pitch
# backup supercap and charger
at("C34", 53.5, 43.5, 0); at("D20", 47.0, 43.5, 0); at("R21", 43.5, 43.5, 0)   # one row: R21 - D20 - C34

# --- Log flash (right of the MCU, next to its OCTOSPI pins); decoupling and pull-ups in a row along its top edge
at("U12", 58.2, 35.0, 90)
row(["C90", "C91", "R90", "R91", "R92"], 57.0, 29.0, 1.6, 0, 90)

# --- Radio (top edge, centred over the MCU). Module flush with the edge; the antenna sits over the footprint's
# copper keepout (all layers), the second of the two placements Espressif allows (the first overhangs the edge).
at("U11", 42.0, 8.3, 0)
row(["C80", "C81"], 33.0, 8.0, 0, 2.0, 0)                       # 3V3 bulk + HF, next to pin 3
row(["R84", "R80", "C82"], 31.4, 12.0, 0, 1.6, 0)                # EN: 1k from the MCU, pulled low, RC
row(["R81", "R82", "R83"], 50.5, 11.5, 0, 1.6, 0)                # strapping pull-ups (IO9, IO8, IO15)
at("TP80", 50.5, 4.6, 0); at("TP81", 50.5, 6.8, 0)              # USB-Serial-JTAG pads
at("R85", 50.5, 10.0, 0)                                        # U0TXD series resistor, next to pin 31

# --- Display (top-left) and buttons (left edge) -------------------------------
at("J61", 17.0, 5.5, 180)
row(["C63", "C64", "C65", "C66", "C67", "C68", "C69"], 8.5, 10.5, 2.0, 0, 90)
at("C62", 23.0, 10.5, 90); at("C70", 25.0, 10.5, 90)
at("L60", 9.2, 14.3, 0); at("Q60", 13.6, 14.3, 0); at("R67", 16.5, 14.3, 90); at("C71", 18.5, 14.3, 90)
row(["D60", "D61", "D62"], 10.5, 18.2, 5.0, 0, 0)                 # booster diodes side by side
row(["SW1", "SW2", "SW3"], 3.6, 22.0, 0, 7.0, 90)

# --- GNSS (bottom-left) ---------------------------------------------------------
at("U10", 16.0, 50.0, 0)
at("J50", 4.0, 46.0, 0)                               # U.FL; pigtail to the SMA bulkhead in the case wall
at("R50", 7.5, 39.5, 0); at("L50", 7.5, 46.0, 0); at("C52", 7.5, 43.5, 0); at("FB51", 7.5, 41.5, 0)
at("FB2", 25.0, 44.0, 90); at("C50", 25.0, 48.0, 90); at("C51", 25.0, 51.0, 90)
at("TP50", 25.0, 53.0, 0)

# --- Sensors (below the MCU, near the board centre) ---------------------------
at("U6", 44.0, 49.0, 0)                               # IMU, close to the centre
at("C40", 41.0, 48.0, 90); at("C41", 41.0, 50.5, 90)
at("U7", 55.0, 57.5, 0)                               # barometer at the bottom edge, under the hose chamber
at("C42", 52.5, 57.5, 90); at("C43", 57.5, 57.5, 90)
at("U9", 32.0, 52.0, 0)                               # magnetometer, far from buck and supercaps
at("C46", 30.0, 54.5, 0); at("C47", 32.5, 54.5, 0); at("C48", 35.0, 54.5, 0)
row(["R40", "R41"], 30.0, 48.5, 2.0, 0, 90)
at("U8", 36.0, 48.0, 90); at("C44", 36.5, 44.5, 0); at("C45", 36.5, 51.5, 90)

# --- microSD (top edge, right of the MCU) --------------------------------------
at("J60", 60.0, 11.5, 180)
row(["R60", "R61", "R62", "R63", "R64", "R65"], 55.0, 21.5, 0, 1.6, 0)
at("C60", 69.5, 19.5, 90); at("C61", 69.5, 16.5, 90)

# --- Power (right column) -------------------------------------------------------
at("J1", 84.5, 33.0, 90)                              # USB-C opening on the right edge
row(["R1", "R2"], 78.0, 28.0, 0, 2.0, 0)
at("U1", 74.0, 36.0, 90); at("D1", 79.5, 41.0, 90); at("R3", 82.5, 41.0, 90); at("C1", 84.0, 41.0, 90)
at("U2", 78.0, 23.0, 0); at("C2", 82.0, 23.0, 90)
at("U3", 77.0, 13.0, 0); at("L1", 77.0, 7.5, 0)
row(["C5", "C6"], 82.5, 11.0, 0, 3.6, 90)
row(["C8", "C9"], 71.5, 5.0, 0, 2.5, 0)
row(["C7", "R7", "R8", "R9"], 72.5, 13.5, 0, 1.6, 0)
# hold-up: supercaps in the bottom-right corner
at("C3", 62.0, 55.5, 0); at("C4", 72.0, 55.5, 0)
at("R4", 64.0, 48.0, 0); at("D2", 70.5, 48.0, 0); row(["R5", "R6"], 76.0, 47.2, 0, 1.6, 0)
# power-fail comparator
at("U4", 66.0, 36.0, 0); row(["R10", "R11", "R12"], 66.0, 40.0, 0, 1.6, 0); row(["C12", "C13"], 62.5, 34.5, 0, 2.0, 90)

# --- Debug, LED, camera sync (bottom edge) -------------------------------------
at("J20", 59.5, 44.0, 0)
at("D21", 49.0, 58.5, 0); at("R22", 49.0, 56.5, 0)
at("J62", 40.0, 58.5, 90); at("R66", 40.0, 55.0, 0)
row(["R68", "R69", "C72"], 43.5, 55.0, 1.6, 0, 90)                # marker input: series, pull-up, filter
at("J63", 30.3, 58.6, 0)                                         # I2C expansion (Qwiic), cable exits the bottom edge
row(["F1", "R70", "R71"], 24.8, 56.6, 0, 1.6, 0)                  # expansion PTC and pull-ups, column left of J63

# Hand fanouts, placed before autorouting and locked: (ref, pad or net, dx, dy) -> GND via at pad + (dx, dy) mm.
# U9 C3 is a corner ball the router boxes in with the VDDIO escape; the crystal load caps get their own
# GND via on the far side from the crystal so the oscillator loop can't enclose them.
FANOUT = [("U9", "C3", 0.55, 0.55), ("C30", "GND", 0.0, -0.95), ("C31", "GND", 0.0, 0.95),
          ("U6", "6", 0.0, 0.9),            # IMU GND, straight down between VDDIO and a reserved pin
          ("U7", "9", 0.75, 0.0),           # baro GND (right side, middle pad), straight out to a via
          ("U11", "51", 0.6, 0.75),
          ("J1", "A12", -1.0, -0.6),        # USB-C GND pair A12/B1, boxed in by VBUS and the shield tab
          ("J60", "11#2", -1.1, 0.0)]       # microSD shell tab nearest the MCU         # radio GND corner pad, between the strap resistors and the MCU decoupling row
# GND pins of these packages get a locked stub inwards to a via under the body before autorouting.
FANOUT_INWARD = ["U5"]
# Single pins the router tends to box in: (ref, pad, +1 outwards / -1 inwards under the body)
FANOUT_AXIAL = [("U1", "2", +1), ("U10", "24", -1)]
# Hand routes, locked: (ref, pad, ref, pad, layer, width mm). The supercap mid-point link is a straight bar.
PREROUTE = [("C3", "2", "C4", "1", "B", 0.6)]
# Hand routes along a path of board points (mm): (ref, pad, [(x, y), ...], ref, pad, layer, width mm).
# The GNSS antenna feed runs short and direct on F.Cu over the In1 ground, clear of the corner hole; the router
# only adds the bias-tee stub from L50.
PREROUTE_PATH = [("J50", "1", [(2.95, 48.26), (2.95, 50.5), (7.0, 54.55), (8.35, 55.9)], "U10", "11", "F", 0.25),
                 ("L50", "2", [(5.72, 48.26), (2.95, 48.26)], None, None, "F", 0.15)]   # bias-tee stub, ends on the feed

HOLES = [(4.0, 4.0), (W - 4.0, 4.0), (4.0, H - 4.0), (W - 4.0, H - 4.0)]


def load(fp):
    lib, name = fp.split(":")
    path = os.path.join(KICAD, "logger.pretty") if lib == "logger" else os.path.join(SYSFP, lib + ".pretty")
    f = pcbnew.FootprintLoad(path, name)
    if f is None:
        raise SystemExit(f"footprint not found: {fp}")
    f.SetFPID(pcbnew.LIB_ID(lib, name))
    return f


def edge_line(board, x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(OX + x1), MM(OY + y1)))
    s.SetEnd(pcbnew.VECTOR2I(MM(OX + x2), MM(OY + y2)))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
    board.Add(s)


def edge_arc(board, cx, cy, sx, sy, angle):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(pcbnew.VECTOR2I(MM(OX + cx), MM(OY + cy)))
    s.SetStart(pcbnew.VECTOR2I(MM(OX + sx), MM(OY + sy)))
    s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T), True)
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
    board.Add(s)


# Cut-out under the radio antenna (Espressif guidelines 1.4.7: no board material under or beside the antenna).
# The module still sits flush with the top edge; the notch is hidden under it.
ANT_NOTCH = (35.4, 48.6, 5.0, 0.5)      # x from, x to, depth, inner corner radius


def outline(board, r=2.0):
    x0, x1, d, rr = ANT_NOTCH
    edge_line(board, r, 0, x0, 0); edge_line(board, x0, 0, x0, d - rr); edge_arc(board, x0 + rr, d - rr, x0, d - rr, -90)
    edge_line(board, x0 + rr, d, x1 - rr, d); edge_arc(board, x1 - rr, d - rr, x1 - rr, d, -90); edge_line(board, x1, d - rr, x1, 0)
    edge_line(board, x1, 0, W - r, 0); edge_line(board, W, r, W, H - r)
    edge_line(board, W - r, H, r, H); edge_line(board, 0, H - r, 0, r)
    edge_arc(board, W - r, r, W - r, 0, 90); edge_arc(board, W - r, H - r, W, H - r, 90)
    edge_arc(board, r, H - r, r, H, 90); edge_arc(board, r, r, 0, r, 90)


def zone(board, net, layer, inset=0.3):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(net)
    pts = [(inset, inset), (W - inset, inset), (W - inset, H - inset), (inset, H - inset)]
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts:
        ol.Append(MM(OX + x), MM(OY + y))
    z.SetMinThickness(MM(0.2)); z.SetLocalClearance(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.3))
    board.Add(z)
    return z


SILK_REF_PREFIXES = ("U", "J")          # ICs and connectors keep their reference on the silkscreen
LABELLED = {"J20", "J50", "J60", "J61", "J62", "J63"}   # ...unless a function label replaces it (see LABELS)
REF_POS = {"U5": (42.0, 29.1)}            # reference centred in the MCU outline

# Silkscreen labels: (text, x, y, rotation, size_mm, layer)
LABELS = [
    ("UP", 7.2, 22.0, 0, 1.0, "F"), ("OK", 7.2, 29.0, 0, 1.0, "F"), ("DN", 7.2, 36.0, 0, 1.0, "F"),
    ("SWD", 59.5, 42.3, 0, 0.9, "F"), ("CAM", 40.0, 61.1, 0, 0.8, "F"), ("MRK", 45.08, 61.1, 0, 0.8, "F"), ("I2C", 24.8, 61.2, 0, 0.8, "F"),
    ("ANT", 4.0, 49.6, 0, 0.9, "F"), ("microSD", 60.0, 21.2, 0, 0.9, "F"), ("E-PAPER", 29.2, 2.2, 0, 0.9, "F"), ("D-", 50.5, 2.8, 0, 0.8, "F"), ("D+", 50.5, 8.6, 0, 0.8, "F"),
    ("UNICORNLINES\u00ae", 17.0, 35.6, 0, 1.2, "F"), ("Never Stop Dreaming", 17.0, 37.6, 0, 0.9, "F", True),
    ("AEROBATICS LOGGER", 44.0, 27.0, 0, 2.0, "B"), ("rev A  2026-11", 44.0, 30.5, 0, 1.2, "B"),
    ("PER PERFECTIONEM AD FELICITATEM", 44.0, 34.5, 0, 1.1, "B", True),
]
LOGO = ("Unicornlines_Logo", 17.0, 27.5)   # tools/mklogo.py, from art/unicornlines-logo.svg
IMU_AXES = (49.0, 51.5)   # origin of the IMU axis arrows (ICM-45686, pin 1 top-left: +X right, +Y up, +Z out of the top; as TDK fig. 14 and CogniPilot's footprint)


def tidy_refs(f, ref):
    """Small references on silk for ICs, connectors and buttons; everything else goes to F.Fab only."""
    t = f.Reference()
    t.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); t.SetTextThickness(MM(0.12))
    if ref in REF_POS:
        t.SetPosition(pcbnew.VECTOR2I(MM(OX + REF_POS[ref][0]), MM(OY + REF_POS[ref][1])))
        t.SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T)); t.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2)))
    if not ref.startswith(SILK_REF_PREFIXES) or ref in LABELLED:
        t.SetLayer(pcbnew.F_Fab if f.GetLayer() == pcbnew.F_Cu else pcbnew.B_Fab)


def text(board, s, x, y, rot, size, layer, italic=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s); t.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)))
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(size * 0.15))
    t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    t.SetLayer(pcbnew.F_SilkS if layer == "F" else pcbnew.B_SilkS)
    t.SetItalic(italic)
    if layer == "B":
        t.SetMirrored(True)
    board.Add(t)


def silk_line(board, x1, y1, x2, y2, w=0.15):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(OX + x1), MM(OY + y1))); s.SetEnd(pcbnew.VECTOR2I(MM(OX + x2), MM(OY + y2)))
    s.SetLayer(pcbnew.F_SilkS); s.SetWidth(MM(w))
    board.Add(s)


def axes(board, x, y, L=3.0, a=0.6):
    silk_line(board, x, y, x + L, y); silk_line(board, x + L, y, x + L - a, y - a / 2); silk_line(board, x + L, y, x + L - a, y + a / 2)
    silk_line(board, x, y, x, y - L); silk_line(board, x, y - L, x - a / 2, y - L + a); silk_line(board, x, y - L, x + a / 2, y - L + a)
    text(board, "X", x + L + 0.9, y, 0, 0.8, "F"); text(board, "Y", x, y - L - 0.9, 0, 0.8, "F")
    c = pcbnew.PCB_SHAPE(board); c.SetShape(pcbnew.SHAPE_T_CIRCLE); c.SetLayer(pcbnew.F_SilkS); c.SetWidth(MM(0.15))
    c.SetCenter(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))); c.SetEnd(pcbnew.VECTOR2I(MM(OX + x + 0.45), MM(OY + y)))
    board.Add(c)
    silk_line(board, x - 0.05, y, x + 0.05, y, 0.25)          # dot: Z points out of the board
    text(board, "Z", x - 1.0, y + 1.0, 0, 0.8, "F")


def passive_gnd_vias(board, taken):
    """Every 2-pad R/C with a GND end gets its own via just beyond that pad, in line with the part
    (or to the side when that spot is taken). Done before autorouting, so ground never depends on the pour."""
    import math
    done = {(r, n) for r, n, _, _ in taken}
    pads = [p for f in board.GetFootprints() for p in f.Pads()]
    vias = []
    out = []
    for f in board.GetFootprints():
        ref = f.GetReference()
        if not ref.startswith(("C", "R")) or len(f.Pads()) != 2:
            continue
        g = [p for p in f.Pads() if p.GetNetname() == "GND"]
        if len(g) != 1 or (ref, g[0].GetNumber()) in done or g[0].GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        gp = g[0]; other = next(p for p in f.Pads() if p is not gp)
        d = gp.GetPosition() - other.GetPosition()
        L = math.hypot(d.x, d.y); ux, uy = d.x / L, d.y / L
        along = (abs(ux) * gp.GetSize().x + abs(uy) * gp.GetSize().y) / 2e6 if f.GetOrientationDegrees() % 180 == 0 else \
                (abs(ux) * gp.GetSize().y + abs(uy) * gp.GetSize().x) / 2e6
        across = max(gp.GetSize().x, gp.GetSize().y) / 2e6
        for vx, vy in ((ux * (along + 0.45), uy * (along + 0.45)),
                       (-uy * (across + 0.45), ux * (across + 0.45)), (uy * (across + 0.45), -ux * (across + 0.45))):
            c = gp.GetPosition() + pcbnew.VECTOR2I(MM(vx), MM(vy))
            circ = pcbnew.SHAPE_CIRCLE(c, MM(0.25))
            if any(p.GetEffectiveShape(l).Collide(circ, MM(0.1) if p.GetNetname() == "GND" else MM(0.2))
                   for p in pads if p is not gp for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)):
                continue
            if any((c - v).EuclideanNorm() < MM(0.75) for v in vias):
                continue
            x, y = pcbnew.ToMM(c.x) - OX, pcbnew.ToMM(c.y) - OY
            if not (1.0 < x < W - 1.0 and 1.0 < y < H - 1.0):
                continue
            vias.append(c); out.append((ref, gp.GetNumber(), vx, vy)); break
    print("passive GND vias:", len(out))
    return out


def main():
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))
    ds.m_TrackMinWidth = MM(0.127); ds.m_MinClearance = MM(0.127)
    ds.m_ViasMinSize = MM(0.45); ds.m_MinThroughDrill = MM(0.2)
    ds.m_HoleClearance = MM(0.15)   # GCT USB4105 footprint places GND pads 0.2 mm from its locating holes
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetTrackWidth(MM(0.15)); nc.SetClearance(MM(0.15)); nc.SetViaDiameter(MM(0.5)); nc.SetViaDrill(MM(0.25))
    board.SetLayerName(pcbnew.In1_Cu, "In1.GND"); board.SetLayerName(pcbnew.In2_Cu, "In2.3V3")

    nets = {}
    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name); board.Add(n); nets[name] = n
        return nets[name]

    missing = []
    for sh in design.SHEETS:
        for p in sh["parts"]:
            ref = p["ref"]
            if ref.startswith("#"):
                continue
            if ref not in P:
                missing.append(ref); continue
            f = load(p["fp"])
            f.SetReference(ref); f.SetValue(p["value"])
            board.Add(f)
            x, y, rot, side = P[ref]
            if side == "B":
                f.Flip(f.GetPosition(), False)
            f.SetOrientationDegrees(rot)
            f.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)))
            if p.get("dnp"):
                f.SetAttributes(f.GetAttributes() | getattr(pcbnew, "FP_DNP", 0) | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
            for pad in f.Pads():
                num = pad.GetNumber()
                n = p["nets"].get(num) or EXTRA_PADS.get((ref, num))
                if n and n != "NC":
                    pad.SetNet(net(n))
            tidy_refs(f, ref)
    if missing:
        raise SystemExit(f"no placement for: {', '.join(missing)}")

    for i, (x, y) in enumerate(HOLES):
        h = load("MountingHole:MountingHole_3.2mm_M3_Pad_Via")
        h.SetReference(f"H{i+1}"); h.SetValue("M3"); h.Reference().SetVisible(False)
        h.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)))
        board.Add(h)
        for pad in h.Pads():
            pad.SetNet(net("GND"))

    for ra, pa, rb, pb, side, w in PREROUTE:
        a = next(p for p in board.FindFootprintByReference(ra).Pads() if p.GetNumber() == pa)
        b = next(p for p in board.FindFootprintByReference(rb).Pads() if p.GetNumber() == pb)
        t = pcbnew.PCB_TRACK(board); t.SetStart(a.GetPosition()); t.SetEnd(b.GetPosition()); t.SetWidth(MM(w))
        t.SetLayer(pcbnew.F_Cu if side == "F" else pcbnew.B_Cu); t.SetNet(a.GetNet()); t.SetLocked(True); board.Add(t)
    for ra, pa, pts, rb, pb, side, w in PREROUTE_PATH:
        a = next(p for p in board.FindFootprintByReference(ra).Pads() if p.GetNumber() == pa)
        path = [a.GetPosition()] + [pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)) for x, y in pts]
        if rb:
            path.append(next(p for p in board.FindFootprintByReference(rb).Pads() if p.GetNumber() == pb).GetPosition())
        for s, e in zip(path, path[1:]):
            t = pcbnew.PCB_TRACK(board); t.SetStart(s); t.SetEnd(e); t.SetWidth(MM(w))
            t.SetLayer(pcbnew.F_Cu if side == "F" else pcbnew.B_Cu); t.SetNet(a.GetNet()); t.SetLocked(True); board.Add(t)
    fan = list(FANOUT)
    axial = [(r, None, -1) for r in FANOUT_INWARD] + FANOUT_AXIAL
    for ref, only, sign in axial:
        f = board.FindFootprintByReference(ref); fc = f.GetPosition()
        for pad in f.Pads():
            if pad.GetNetname() != "GND" or (only and pad.GetNumber() != only):
                continue
            d = pad.GetPosition() - fc
            half = max(pad.GetSize().x, pad.GetSize().y) / 2e6
            bb = pad.GetBoundingBox()
            if bb.GetWidth() > bb.GetHeight():          # along the pad's long axis
                fan.append((ref, pad.GetNumber(), sign * (half + 0.55) * (1 if d.x > 0 else -1), 0.0))
            else:
                fan.append((ref, pad.GetNumber(), 0.0, sign * (half + 0.55) * (1 if d.y > 0 else -1)))
    fan += passive_gnd_vias(board, fan)
    for ref, num, dx, dy in fan:
        num, _, k = num.partition("#")           # "11#2": the third pad numbered 11 (shell tabs share a number)
        pad = [p for p in board.FindFootprintByReference(ref).Pads() if num in (p.GetNumber(), p.GetNetname())][int(k or 0)]
        a = pad.GetPosition(); c = pcbnew.VECTOR2I(a.x + MM(dx), a.y + MM(dy))
        t = pcbnew.PCB_TRACK(board); t.SetStart(a); t.SetEnd(c); t.SetWidth(MM(0.15)); t.SetLayer(pcbnew.F_Cu)
        t.SetNet(pad.GetNet()); t.SetLocked(True); board.Add(t)
        v = pcbnew.PCB_VIA(board); v.SetPosition(c); v.SetWidth(MM(0.5)); v.SetDrill(MM(0.25))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(pad.GetNet()); v.SetLocked(True); board.Add(v)   # GND or +3V3 plane
    logo = load("logger:" + LOGO[0]); logo.SetReference("LOGO1"); logo.Reference().SetVisible(False)
    logo.SetPosition(pcbnew.VECTOR2I(MM(OX + LOGO[1]), MM(OY + LOGO[2]))); board.Add(logo)
    outline(board)
    for lb in LABELS:
        text(board, *lb)
    axes(board, *IMU_AXES)
    zone(board, net("GND"), pcbnew.In1_Cu)
    zone(board, net("+3V3"), pcbnew.In2_Cu)
    zone(board, net("GND"), pcbnew.F_Cu).SetAssignedPriority(0)
    zone(board, net("GND"), pcbnew.B_Cu).SetAssignedPriority(0)

    out = os.path.join(KICAD, "logger.kicad_pcb")
    if "--drc" in sys.argv:
        board.Save(out)
        board = pcbnew.LoadBoard(out)
        rpt = "/tmp/logger-drc_place.rpt"
        pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, False)
        import re
        txt = open(rpt).read()
        skip = ("unconnected_items", "lib_footprint_issues", "silk_over_copper", "silk_overlap", "silk_edge_clearance")
        for b in re.split(r"\n(?=\[)", txt):
            m = re.match(r"\[(\w+)\]", b)
            if m and m.group(1) not in skip:
                ls = [l.strip() for l in b.split("\n")[2:4]]
                print(m.group(1), "|", " || ".join(ls)[:220])
    board.Save(out)
    print("wrote", out, len(board.GetFootprints()), "footprints")


if __name__ == "__main__":
    main()
