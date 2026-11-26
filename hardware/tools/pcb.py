"""Build the rev A board (../kicad/logger.kicad_pcb) from design.py and the placement below.

Nets come straight from design.py, so the board and schematic share one source.
Placement is by hand, block by block, on a 0.5 mm grid. A few fanouts are placed by hand and locked
(MCU and IMU ground pins, crystal load caps, every R/C ground pad), then route.py autoroutes the rest.

Board: 112 x 54 mm, 4 layers: F.Cu signal, In1 GND plane, In2 +3V3 pour with some signal routing, B.Cu signal.
"""
import os, sys
import pcbnew
import design

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD = os.path.join(HERE, "..", "kicad")
SYSFP = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0          # board top-left on the page
W, H = 112.0, 54.0
MM = pcbnew.FromMM

# Extra pads the footprint has but the symbol doesn't.
EXTRA_PADS = {("J60", "11"): "GND", ("J61", "MP"): "GND", ("J63", "MP"): "GND", ("J2", "MP"): "GND",
              **{(f"SW{i}", "MP"): "GND" for i in range(1, 6)}}

# ref: (x, y, rotation, side)  -- board coordinates in mm from the top-left corner; side "F" or "B"
P = {}
def at(ref, x, y, rot=0, side="F"):
    P[ref] = (x, y, rot, side)
def row(refs, x, y, dx, dy, rot=0, side="F"):
    for i, r in enumerate(refs):
        at(r, x + i * dx, y + i * dy, rot, side)

# Floor plan, left to right: radio (top-left corner) and GNSS, then the MCU with its crystals and log flash,
# then power (3.3 V buck, charger, USB protection) with USB-C and microSD flush on the right short edge.
# Top edge: the radio antenna, the two cable sockets and the e-paper FPC. Bottom edge: the five side-push buttons,
# MARKER at the left end, UP / OK / DOWN in the middle, PWR at the right; hold-up and battery in the bottom-right.

# --- MCU block (centre) and its crystals, decoupling on every side
MX, MY = 50.0, 32.0
at("U5", MX, MY)
row(["C20", "C21"], MX - 10.5, MY - 7.5, 0, 2.0, 0)       # left side decoupling
row(["C22", "C23"], MX + 10.5, MY + 5.0, 0, 2.0, 0)       # right side decoupling
row(["C24", "C25"], MX + 4.0, MY + 10.5, 2.5, 0, 90)      # bottom
row(["C26", "C27"], MX - 10.5, MY + 7.0, 0, 2.0, 0)       # VCAP, near pins 48/73
at("C28", MX - 4.0, MY - 10.5, 90); at("C29", MX - 6.5, MY - 10.5, 90); at("R20", MX + 6.0, MY - 10.5, 90)
at("FB1", MX - 1.5, MY - 10.5, 0); at("C10", MX + 1.0, MY - 10.5, 90); at("C11", MX + 3.5, MY - 10.5, 90)
at("Y1", MX - 14.0, MY, 90); at("C30", MX - 14.0, MY - 2.9, 0); at("C31", MX - 14.0, MY + 2.9, 0)
at("Y2", MX - 14.0, MY - 7.1, 90); at("C32", MX - 14.0, MY - 9.3, 0); at("C33", MX - 14.0, MY - 4.9, 0)
# RTC / GNSS backup: one column D20 - R21 - C34, between the GNSS and the crystals
at("D20", 30.3, 24.2, 90); at("R21", 30.3, 26.9, 90); at("C34", 30.3, 31.5, 0)
# SWD header and status LED, right of the MCU
at("J20", 67.5, 19.5, 0)
at("D21", 34.0, 44.5, 0); at("R22", 34.0, 46.5, 0)

# --- Log flash (bottom-right of the MCU, next to its OCTOSPI pins); decoupling and pull-ups in a row on top
at("U12", MX + 16.2, MY + 5.9, 90)
row(["C90", "C91", "R90", "R91", "R92"], MX + 15.0, MY - 0.1, 1.6, 0, 90)

# --- Radio (top-left corner). Module flush with the top edge, antenna over the notch in the board.
at("U11", 17.0, 8.3, 0)
at("C80", 8.4, 9.0, 90); row(["C81", "R80", "C82", "R84"], 8.4, 11.8, 0, 2.0, 90)   # 3V3 bulk + HF at pin 3, then the EN pull-down, RC, 1k
row(["TP81", "TP80"], 12.0, 19.0, 2.4, 0, 0)                      # USB-Serial-JTAG pads under pins 17/18
row(["R83", "R82", "R81"], 17.4, 19.0, 1.6, 0, 90)                # strapping pull-ups (IO15, IO8, IO9)
at("R85", 25.6, 10.2, 0)                                          # U0TXD series resistor, next to pin 31

# --- GNSS (left edge, under the radio) -------------------------------------------
GX, GY = 16.0, 31.0
at("U10", GX, GY, 0)
at("J50", GX - 12.0, GY - 4.0, 0)                     # U.FL; pigtail to the SMA bulkhead in the case wall
at("R50", GX - 8.5, GY - 10.5, 0); at("FB51", GX - 8.5, GY - 8.5, 0); at("C52", GX - 8.5, GY - 6.5, 0); at("L50", GX - 8.5, GY - 4.0, 0)
at("FB2", GX + 9.0, GY - 6.0, 90); at("C50", GX + 9.0, GY - 2.0, 90); at("C51", GX + 9.0, GY + 1.0, 90)
at("TP50", GX + 9.0, GY + 3.0, 0)

# --- Sensors (bottom band, between the GNSS and the buttons) -------------------
at("U6", 44.0, 45.0, 0)                               # IMU, under the MCU's SPI1 corner
at("C40", 41.0, 44.0, 90); at("C41", 41.0, 46.5, 90)
at("U7", 58.0, 46.2, 0)                               # barometer, under the MCU's SPI2 corner; hose chamber over it
at("C42", 55.5, 46.2, 90); at("C43", 60.5, 46.2, 90)
at("U9", 20.0, 45.0, 0)                               # magnetometer, far from the buck, supercaps and battery
at("C46", 18.0, 47.5, 0); at("C47", 20.5, 47.5, 0); at("C48", 23.0, 47.5, 0)
row(["R40", "R41"], 18.0, 42.0, 2.0, 0, 90)
at("U8", 12.5, 44.5, 90); at("C44", 12.5, 41.0, 0); at("C45", 12.5, 48.0, 90)

# --- Top edge: Qwiic and camera/marker sockets, e-paper FPC with its booster ------
at("J63", 31.0, 3.4, 180)                              # I2C expansion (Qwiic), cable out of the top edge
row(["F1", "R70", "R71"], 28.8, 9.0, 1.6, 0, 90)
at("U14", 37.3, 3.6, 0)                                # ESD array for J62 and J63, between the two
at("J62", 41.5, 3.0, 90)                               # 1 sync out, 2 GND, 3 marker in (pin 1 left)
row(["R66", "R68", "R69", "C72"], 41.5, 7.6, 1.6, 0, 90)
EX = 59.0                                              # e-paper FPC centre
at("J61", EX, 5.5, 180)
row(["C63", "C64", "C65", "C66", "C67", "C68", "C69"], EX - 7.5, 10.5, 2.0, 0, 90)
at("C62", EX + 6.5, 10.5, 90); at("C70", EX + 8.5, 10.5, 90)
at("L60", EX - 6.8, 14.3, 0); at("Q60", EX - 2.4, 14.3, 0); at("R67", EX + 0.5, 14.3, 90); at("C71", EX + 2.5, 14.3, 90)
row(["D60", "D61", "D62"], EX - 5.5, 18.2, 5.0, 0, 0)

# --- Buttons: five side-push switches on the bottom edge, actuators flush with it ----
BY = H - 2.1
at("SW5", 14.0, BY, 0)                                 # MARKER (large cap in the case)
row(["SW1", "SW2", "SW3"], 28.0, BY, 10.0, 0, 0)       # UP, OK, DOWN
at("SW4", 62.0, BY, 0)                                 # PWR (recessed in the case)

# --- Power: 3.3 V buck (top band) -----------------------------------------------
UX = 78.0
at("U3", UX, 12.0, 0); at("L1", UX, 6.5, 0)
row(["C5", "C6"], UX + 5.5, 10.0, 0, 3.6, 90)
row(["C8", "C9"], UX - 5.5, 4.0, 0, 2.5, 0)
row(["C7", "R7", "R8", "R9"], UX - 4.5, 11.9, 0, 1.6, 0)
# soft power latch, under the buck: USB diode + 100k, button/hold diode pair, 1M || 1u on EN, button divider
row(["R119", "D24"], 70.5, 20.5, 2.5, 0, 90)
at("D23", 76.6, 20.5, 0); row(["R120", "C110", "R121", "R122"], 79.4, 20.5, 1.6, 0, 90)

# --- Charger (BQ24074, rotated: OUT pins face the buck, BAT pins face the USB side, IN bottom-left) ----
CX, CY = 93.0, 14.0
at("U13", CX, CY, 180)
row(["C105", "C104"], CX - 5.4, CY, 2.1, 0, 90)          # OUT 2 x 10u
at("C106", CX + 3.4, CY, 90)                             # BAT 10u
at("C2", CX - 2.0, CY + 3.8, 90)                         # IN 1u
row(["R117", "R101", "R102"], CX, CY + 3.8, 1.4, 0, 90)   # TMR, ISET, ISET step
at("Q5", CX + 2.5, CY + 7.2, 0); at("R103", CX + 5.0, CY + 7.2, 90)
row(["R115", "R114"], CX - 5.0, CY + 3.8, 1.4, 0, 90)     # ILIM step, ILIM
at("Q6", CX - 4.5, CY + 7.2, 0); at("R116", CX - 7.0, CY + 7.2, 90)
at("R100", CX + 1.2, CY - 3.2, 0)                        # EN2 pull-up
at("D22", CX - 2.0, CY - 5.2, 0); row(["R118", "R104"], CX + 1.2, CY - 5.2, 1.6, 0, 90)   # CHG LED

# --- USB-C (right edge, top) and its protection ------------------------------------
JX = W - 3.5
at("J1", JX, 14.0, 90)
at("U1", 100.5, 14.0, 0); at("D1", 100.5, 9.6, 0)
row(["R2", "R1"], 99.6, 17.6, 2.0, 0, 0)
row(["R3", "C1"], 105.0, 21.6, 1.6, 0, 90)
row(["R108", "R109", "C108"], 99.8, 21.6, 1.6, 0, 90)     # CC level to the ADC
# power-fail comparator, then the VBAT/2 divider: one column left of the microSD pull-ups
at("U4", 89.0, 26.2, 90); row(["C12", "C13"], 86.0, 24.8, 0, 1.6, 0)
row(["R10", "R11", "R12", "R106", "R107", "C107"], 89.0, 29.4, 0, 1.5, 0)

# --- microSD (right edge, under the USB-C), card in through the case wall --------
at("J60", W - 9.2, 31.5, 90)
row(["R60", "R61", "R62", "R63", "R64", "R65"], 92.6, 24.5, 0, 1.6, 0)
at("C60", 92.6, 35.0, 90); at("C61", 92.6, 37.8, 90)

# --- Hold-up supercaps and battery (bottom-right) -----------------------------------
at("C3", 69.25, 47.0, 0); at("C4", 79.25, 47.0, 0)       # origin is pin 1: bodies centred on x 71 and 81
row(["R5", "R6"], 76.0, 44.8, 0, 4.4, 90)                 # balancing pair between the two, clear of the mid-point bar
at("R4", 72.5, 41.3, 0); at("D2", 79.5, 41.3, 0)           # charge resistor and discharge diode above them
at("J2", 97.0, 48.3, 0)                                   # JST PH, cable out towards the bottom edge
at("Q3", 88.6, 45.8, 0); at("Q4", 88.6, 49.6, 0)          # discharge / charge FETs, left of the socket
row(["R113", "R112", "C109"], 91.0, 41.0, 1.4, 0, 90)
at("U15", 96.0, 41.0, 0); row(["R111", "R110"], 98.2, 41.0, 1.4, 0, 90)
at("F2", 102.5, 41.0, 0)                                 # fuse right at the cell's + pin
at("Q1", 88.0, 39.4, 0); at("R105", 88.0, 42.6, 0)        # reverse-polarity PMOS

# Hand fanouts, placed before autorouting and locked: (ref, pad or net, dx, dy) -> GND via at pad + (dx, dy) mm.
# U9 C3 is a corner ball the router boxes in; the crystal load caps get their own GND via on the far side from
# the crystal so the oscillator loop can't enclose them; the barometer's GND pins are walled in by its 3V3 pair.
FANOUT = [("U9", "C3", 0.55, 0.55), ("C30", "GND", 0.0, -0.95), ("C31", "GND", 0.0, 0.95),
          ("U6", "6", 0.0, 0.9),            # IMU GND, straight down between VDDIO and a reserved pin
          ("U7", "9", 0.75, 0.0),           # baro GND (right side, middle pad), straight out to a via
          ("U11", "51", 0.6, 0.75)]
TRACKS = []
FANOUT_INWARD = ["U5"]
FANOUT_AXIAL = [("U1", "2", +1), ("U10", "24", -1)]
PREROUTE = [("C3", "2", "C4", "1", "B", 0.6)]
PREROUTE_PATH = [("J50", "1", [(GX - 13.05, GY - 1.74), (GX - 13.05, GY + 0.5), (GX - 9.0, GY + 4.55), (GX - 7.65, GY + 5.9)], "U10", "11", "F", 0.25),
                 ("L50", "2", [(GX - 10.28, GY - 1.74), (GX - 13.05, GY - 1.74)], None, None, "F", 0.15)]

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
ANT_NOTCH = (10.4, 23.6, 5.0, 0.5)      # x from, x to, depth, inner corner radius


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
LABELLED = {"J2", "J20", "J50", "J60", "J61", "J62", "J63"}   # ...unless a function label replaces it (see LABELS)
REF_POS = {"U5": (MX, MY), "U4": (86.0, 28.0), "U13": (91.0, 11.0), "U15": (93.0, 39.6), "U10": (19.5, 21.3)}            # reference centred in the MCU outline

# Silkscreen labels: (text, x, y, rotation, size_mm, layer)
LABELS = [
    ("MARKER", 14.0, 49.3, 0, 0.8, "F"), ("UP", 28.0, 49.3, 0, 0.8, "F"), ("OK", 38.0, 49.3, 0, 0.8, "F"),
    ("DOWN", 48.0, 49.3, 0, 0.8, "F"), ("PWR", 62.0, 49.3, 0, 0.8, "F"),
    ("CHG", 88.3, 8.8, 0, 0.8, "F"), ("SWD", 67.5, 27.6, 0, 0.8, "F"), ("ANT", 4.0, 30.7, 0, 0.8, "F"),
    ("CAM", 41.5, 5.6, 0, 0.8, "F"), ("MRK", 46.58, 5.6, 0, 0.8, "F"), ("I2C", 25.6, 4.0, 0, 0.8, "F"),
    ("E-PAPER", 47.4, 9.7, 0, 0.8, "F"),
    ("D+", 12.0, 21.2, 0, 0.8, "F"), ("D-", 14.4, 21.2, 0, 0.8, "F"),
    ("BAT 1S", 103.7, 44.0, 90, 0.8, "F"), ("+", 100.6, 45.2, 0, 0.8, "F"), ("\u2212", 93.4, 45.2, 0, 0.8, "F"),
    ("UNICORNLINES\u00ae", 78.5, 37.6, 0, 1.2, "F"), ("Never Stop Dreaming", 78.5, 39.3, 0, 0.85, "F", True),
    ("AEROBATICS LOGGER", 56.0, 24.0, 0, 2.0, "B"), ("rev A  2026-11", 56.0, 27.5, 0, 1.2, "B"),
    ("PER PERFECTIONEM AD FELICITATEM", 56.0, 31.5, 0, 1.1, "B", True),
]
LOGO = ("Unicornlines_Logo", 78.5, 29.7)   # tools/mklogo.py, from art/unicornlines-logo.svg
IMU_AXES = (48.0, 47.0)   # origin of the IMU axis arrows (ICM-45686, pin 1 top-left: +X right, +Y up, +Z out of the top; as TDK fig. 14 and CogniPilot's footprint)


def tidy_refs(f, ref):
    """Small references on silk for ICs, connectors and buttons; everything else goes to F.Fab only."""
    t = f.Reference()
    t.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); t.SetTextThickness(MM(0.12))
    if ref in REF_POS:
        t.SetPosition(pcbnew.VECTOR2I(MM(OX + REF_POS[ref][0]), MM(OY + REF_POS[ref][1])))
        t.SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
        if ref == "U5":
            t.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2)))
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
    text(board, "Z", x - 1.3, y, 0, 0.8, "F")


def passive_gnd_vias(board, taken):
    """Every 2-pad R/C with a GND end gets its own via just beyond that pad, in line with the part
    (or to the side when that spot is taken). Done before autorouting, so ground never depends on the pour."""
    import math
    done = {(r, n) for r, n, *_ in taken}
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
    for n, pts, side, w in TRACKS:
        pp = [pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)) for x, y in pts]
        for s_, e_ in zip(pp, pp[1:]):
            t = pcbnew.PCB_TRACK(board); t.SetStart(s_); t.SetEnd(e_); t.SetWidth(MM(w))
            t.SetLayer({"F": pcbnew.F_Cu, "B": pcbnew.B_Cu, "In2": pcbnew.In2_Cu}[side]); t.SetNet(net(n)); t.SetLocked(True); board.Add(t)
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
    for ref, num, dx, dy, *wide in fan:
        w, vd, vdr = wide or (0.15, 0.5, 0.25)
        num, _, k = num.partition("#")           # "11#2": the third pad numbered 11 (shell tabs share a number)
        pad = [p for p in board.FindFootprintByReference(ref).Pads() if num in (p.GetNumber(), p.GetNetname())][int(k or 0)]
        a = pad.GetPosition(); c = pcbnew.VECTOR2I(a.x + MM(dx), a.y + MM(dy))
        t = pcbnew.PCB_TRACK(board); t.SetStart(a); t.SetEnd(c); t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu)
        t.SetNet(pad.GetNet()); t.SetLocked(True); board.Add(t)
        v = pcbnew.PCB_VIA(board); v.SetPosition(c); v.SetWidth(MM(vd)); v.SetDrill(MM(vdr))
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
