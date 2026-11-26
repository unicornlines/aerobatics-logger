"""Build the rev A board (../kicad/logger.kicad_pcb) from design.py and the placement below.

Nets come straight from design.py, so the board and schematic share one source.
Placement is by hand, block by block, on a 0.5 mm grid. A few fanouts are placed by hand and locked
(MCU and IMU ground pins, crystal load caps, every R/C ground pad), then route.py autoroutes the rest.

Board: 124 x 62 mm, 4 layers: F.Cu signal, In1 GND plane, In2 +3V3 pour with some signal routing, B.Cu signal.
"""
import math, os, sys
import pcbnew
import design

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD = os.path.join(HERE, "..", "kicad")
SYSFP = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0          # board top-left on the page
W, H = 124.0, 62.0
MM = pcbnew.FromMM

# Extra pads the footprint has but the symbol doesn't.
EXTRA_PADS = {("J60", "11"): "GND", ("J61", "MP"): "GND", ("J62", "MP"): "GND", ("J63", "MP"): "GND", ("J2", "MP"): "GND"}

# ref: (x, y, rotation, side)  -- board coordinates in mm from the top-left corner; side "F" or "B"
P = {}
def at(ref, x, y, rot=0, side="F"):
    P[ref] = (x, y, rot, side)
def row(refs, x, y, dx, dy, rot=0, side="F"):
    for i, r in enumerate(refs):
        at(r, x + i * dx, y + i * dy, rot, side)

# Floor plan. Front face: the Sharp 2.7" memory LCD centred at the top (rotated 180 deg so its FPC leaves at the top edge
# and folds back under the glass into J61), and the three Choc keys centred under it. Only low parts (<= 3 mm) sit under the
# panel. Left of the panel: radio (top-left corner, antenna up) and GNSS, sensors below them. Right of the panel: USB-C
# and microSD flush on the right short edge, charger and USB protection; battery and its protection in the
# bottom-right corner. MCU, log flash, 3.3 V buck and LCD supply under the panel.
DX = W / 2                       # panel and key centre line
LCD = (DX - 31.4, 2.5, DX + 31.4, 2.5 + 42.82)        # LS027B7DH01 module outline on the board (x0, y0, x1, y1)
KEYS = {"SW1": DX - 22.0, "SW2": DX, "SW3": DX + 22.0}  # UP, OK / PWR, DOWN
KY = 53.9

# --- MCU block (under the panel) and its crystals, decoupling on every side
MX, MY = 50.0, 26.0
at("U5", MX, MY)
row(["C20", "C21"], MX - 10.5, MY - 7.5, 0, 2.0, 0)       # left side decoupling
row(["C22", "C23"], MX + 10.5, MY + 5.0, 0, 2.0, 0)       # right side decoupling
row(["C24", "C25"], MX + 4.0, MY + 10.5, 2.5, 0, 90)      # bottom
row(["C26", "C27"], MX - 10.5, MY + 7.0, 0, 2.0, 0)       # VCAP, near pins 48/73
at("C28", MX - 4.0, MY - 10.5, 90); at("C29", MX - 6.5, MY - 10.5, 90); at("R20", MX + 6.0, MY - 10.5, 90)
at("FB1", MX - 1.5, MY - 10.5, 0); at("C10", MX + 1.0, MY - 10.5, 90); at("C11", MX + 3.5, MY - 10.5, 90)
at("Y1", MX - 14.0, MY, 90); at("C30", MX - 14.0, MY - 2.9, 0); at("C31", MX - 14.0, MY + 2.9, 0)
at("Y2", MX - 14.0, MY - 7.1, 90); at("C32", MX - 14.0, MY - 9.3, 0); at("C33", MX - 14.0, MY - 4.9, 0)
# RTC / GNSS backup: D20 - R21 by the crystals, the 0.1 F cap (5.4 mm tall) outside the panel, bottom-left
at("D20", 30.3, 30.2, 90); at("R21", 30.3, 32.9, 90); at("C34", 14.0, 54.5, 0)
# SWD (Tag-Connect pads, no height) right of the MCU; status LED bottom-left, visible beside the keys
at("J20", MX + 17.0, MY - 6.0, 0)
at("D21", 28.0, 59.2, 0); at("R22", 24.8, 59.2, 0)

# --- Log flash (bottom-right of the MCU, next to its OCTOSPI pins); decoupling and pull-ups in a row on top
at("U12", MX + 16.2, MY + 5.9, 90)
row(["C90", "C91", "R90", "R91", "R92"], MX + 15.0, MY - 0.1, 1.6, 0, 90)

# --- IMU under the MCU's SPI1 corner, near the board's middle
at("U6", MX - 6.0, MY + 15.0, 0)
at("C40", MX - 9.0, MY + 14.0, 90); at("C41", MX - 9.0, MY + 16.5, 90)

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

# --- Sensors (bottom-left, outside the panel and keys) ----------------------------
at("U9", 20.0, 45.0, 0)                               # magnetometer, far from the buck and the battery currents
at("C46", 18.0, 47.5, 0); at("C47", 20.5, 47.5, 0); at("C48", 23.0, 47.5, 0)
row(["R40", "R41"], 18.0, 42.0, 2.0, 0, 90)
at("U8", 12.5, 44.5, 90); at("C44", 12.5, 41.0, 0); at("C45", 12.5, 48.0, 90)
# Temperature / humidity at the left edge, outside the panel, on a tongue cut free by an L-shaped milled notch (SLOT_L) so the
# board's heat reaches it only through the narrow bottom neck; the case vents the wall in front of it.
at("U17", 3.2, 45.8, 0); at("C49", 3.2, 48.4, 0)
# PDM microphone on the back, its sound port through the board to the front, just left of the panel and as close to
# PB0/PB1 as the panel allows; the case ports the bezel over it. Clock series resistor at PB0.
at("MK1", 26.5, 41.0, 90, "B"); at("C53", 26.2, 37.9, 0, "B")
at("R42", 48.8, 36.8, 90)
at("U7", 24.5, 53.5, 0)                               # barometer: hose chamber over it, barb out of the bottom wall
at("C42", 22.0, 53.5, 90); at("C43", 27.0, 53.5, 90)

# --- Top edge, under the panel: Qwiic and camera/marker sockets (cables out of the top) ------
at("J63", 35.0, 3.4, 180)                              # I2C expansion (Qwiic)
row(["F1", "R70", "R71"], 32.8, 9.0, 1.6, 0, 90)
at("U14", 41.0, 3.6, 0)                                # ESD array for J62 and J63, between the two
at("J62", 46.5, 2.9, 180)                              # JST SUR 3: 1 sync out, 2 GND, 3 marker in
row(["R66", "R68", "R69", "C72"], 44.3, 9.0, 1.6, 0, 90)

# --- LCD: FPC socket under the panel's top edge (the FPC enters from the top), 5 V boost beside it ----
at("J61", DX, 6.5, 0)
row(["R67", "R72"], DX - 5.2, 6.4, 0, 1.6, 0)          # SCS and DISP pull-downs
row(["C64", "C65"], DX + 5.0, 6.4, 0, 1.6, 0)          # at VDD / VDDA
at("U16", DX + 9.0, 8.0, 0); at("L60", DX + 9.0, 3.6, 90)
at("C62", DX + 12.2, 6.3, 90); at("C63", DX + 12.2, 9.9, 90)

# --- Keys: three Choc switches centred under the panel ------------------------------
for r, x in KEYS.items():
    at(r, x, KY, 0)

# --- Power: 3.3 V buck (top band, under the panel) ------------------------------
UX = 84.0
at("U3", UX, 12.0, 0); at("L1", UX, 6.5, 0)
row(["C5", "C6"], UX + 5.5, 10.0, 0, 3.6, 90)
row(["C8", "C9"], UX - 5.5, 4.0, 0, 2.5, 0)
row(["C7", "R7", "R8", "R9"], UX - 4.5, 11.9, 0, 1.6, 0)
# soft power latch, under the buck: USB diode + 100k, key/hold diode pair, 1M || 1u on EN, key divider
row(["R119", "D24"], UX - 7.5, 20.5, 2.5, 0, 90)
at("D23", UX - 1.4, 20.5, 0); row(["R120", "C110", "R121", "R122"], UX + 1.4, 20.5, 1.6, 0, 90)

# --- Charger (BQ24074, rotated: OUT pins face the buck, BAT pins face the USB side, IN bottom-left) ----
CX, CY = 105.0, 14.0
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
at("U1", JX - 8.0, 14.0, 0); at("D1", JX - 8.0, 9.6, 0)
row(["R2", "R1"], JX - 8.9, 17.6, 2.0, 0, 0)
row(["R3", "C1"], JX - 3.5, 21.6, 1.6, 0, 90)
row(["R108", "R109", "C108"], JX - 8.7, 21.6, 1.6, 0, 90)     # CC level to the ADC
# power-fail comparator, then the VBAT/2 divider: one column left of the microSD pull-ups
at("U4", 101.0, 26.2, 90); row(["C12", "C13"], 98.0, 24.8, 0, 1.6, 0)
row(["R10", "R11", "R12", "R106", "R107", "C107"], 101.0, 29.4, 0, 1.5, 0)

# --- microSD (right edge, under the USB-C), card in through the case wall --------
at("J60", W - 9.2, 31.5, 90)
row(["R60", "R61", "R62", "R63", "R64", "R65"], W - 19.4, 24.5, 0, 1.6, 0)
at("C60", W - 19.4, 35.0, 90); at("C61", W - 19.4, 37.8, 90)

# --- Battery and cell protection (bottom-right corner) ---------
at("J2", 116.0, 46.0, 0)                                  # JST PH, cable towards the bottom edge
at("Q3", 97.0, 42.5, 0); at("Q4", 97.0, 45.9, 0)          # discharge / charge FETs
row(["R113", "R112", "C109"], 100.2, 42.0, 1.4, 0, 90)
at("U15", 104.9, 43.2, 0); row(["R111", "R110"], 107.2, 42.0, 1.4, 0, 90)
at("F2", 108.6, 45.6, 90)                                # fuse right at the cell's + pin
at("Q1", 92.0, 40.6, 0); at("R105", 92.0, 43.8, 0)        # reverse-polarity PMOS

# Hand fanouts, placed before autorouting and locked: (ref, pad or net, dx, dy) -> GND via at pad + (dx, dy) mm.
# U9 C3 is a corner ball the router boxes in; the crystal load caps get their own GND via on the far side from
# the crystal so the oscillator loop can't enclose them; the barometer's GND pins are walled in by its 3V3 pair.
FANOUT = [("U9", "C3", 0.55, 0.55), ("C30", "GND", 0.0, -0.95), ("C31", "GND", 0.0, 0.95),
          ("U6", "6", 0.0, 0.9),            # IMU GND, straight down between VDDIO and a reserved pin
          ("U7", "9", 0.75, 0.0),           # baro GND (right side, middle pad), straight out to a via
          ("U11", "51", 0.6, 0.75),
          ("C53", "2", 0.0, 0.75)]          # mic decoupling (back): its GND via between the cap and the mic, off the 3V3 run
# Hand tracks (net, points, side, width) and vias (net, x, y), locked. The humidity sensor's I2C pair leaves its tongue
# on the back through the neck below the notch and climbs to the pull-ups R40 (SCL) / R41 (SDA), in two parallel
# lanes (pads exit sideways: the sensor's footprint keeps tracks off its body); the router kept missing this branch. SDA joins the bus at the via under R41.
SDA_VIA = (20.0, 43.3325)
TRACKS = [("I2C1_SDA", [(2.5, 45.4), (1.3, 45.4)], "F", 0.2),
          ("I2C1_SDA", [(1.3, 45.4), (1.3, 52.6), (16.0, 52.6), (20.0, 48.6), SDA_VIA], "B", 0.2),
          ("I2C1_SDA", [SDA_VIA, (20.0, 42.51)], "F", 0.2),
          ("I2C1_SCL", [(2.5, 46.2), (2.05, 46.2), (2.05, 46.95)], "F", 0.2),
          ("I2C1_SCL", [(2.05, 46.95), (2.05, 52.0), (14.0, 52.0), (18.0, 48.0), (18.0, 43.3)], "B", 0.2),
          ("I2C1_SCL", [(18.0, 43.3), (18.0, 42.51)], "F", 0.2)]
HAND_VIAS = [("I2C1_SDA", 1.3, 45.4), ("I2C1_SDA", *SDA_VIA), ("I2C1_SCL", 2.05, 46.95), ("I2C1_SCL", 18.0, 43.3)]
FANOUT_INWARD = ["U5"]
FANOUT_AXIAL = [("U1", "2", +1), ("U10", "24", -1)]
PREROUTE = []
PREROUTE_PATH = [("J50", "1", [(GX - 13.05, GY - 1.74), (GX - 13.05, GY + 0.5), (GX - 9.0, GY + 4.55), (GX - 7.65, GY + 5.9)], "U10", "11", "F", 0.25),
                 ("L50", "2", [(GX - 10.28, GY - 1.74), (GX - 13.05, GY - 1.74)], None, None, "F", 0.15)]

SLOT_L = (6.2, 41.0, 50.8, 1.0)   # L-shaped 1.0 mm milled notch around the humidity sensor: in from the left edge along y0 to x1, then down to y1; width
HOLES = [(4.0, 4.0), (W - 4.0, 4.0), (4.0, H - 4.0), (W - 4.0, H - 4.0)]   # corners only: the cell lies behind the middle
HOLE_KEEPOUT = 7.0             # mm: hole pad diameter (0.5 mm from the edge at the corners), so parts, tracks and vias stay off it on every layer; the case bosses clamp here


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
    edge_line(board, W - r, H, r, H)
    edge_line(board, 0, H - r, 0, SLOT_L[1] + SLOT_L[3] / 2); edge_line(board, 0, SLOT_L[1] - SLOT_L[3] / 2, 0, r)   # left edge, broken by the sensor notch
    edge_arc(board, W - r, r, W - r, 0, 90); edge_arc(board, W - r, H - r, W, H - r, 90)
    edge_arc(board, r, H - r, r, H, 90); edge_arc(board, r, r, 0, r, 90)


def slots(board):
    """The L-shaped milled notch that frees the humidity sensor's tongue: in from the left edge along y0 to the corner
    at x1, then down to y1, with a round end. The left edge (outline) stops on either side of it. The tool's radius
    rounds the outer corner of the L; the tongue's own corner stays sharp."""
    x1, y0, y1, w = SLOT_L
    h = w / 2
    edge_line(board, 0, y0 - h, x1, y0 - h); edge_arc(board, x1, y0, x1, y0 - h, 90)
    edge_line(board, x1 + h, y0, x1 + h, y1); edge_arc(board, x1, y1, x1 + h, y1, 180)
    edge_line(board, x1 - h, y1, x1 - h, y0 + h); edge_line(board, x1 - h, y0 + h, 0, y0 + h)


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
REF_POS = {"U16": (DX + 9.0, 10.4), "U5": (MX, MY), "U4": (98.0, 28.0), "U13": (103.0, 11.0), "U15": (104.3, 40.6), "U10": (19.5, 21.3)}            # reference centred in the MCU outline

# Silkscreen labels: (text, x, y, rotation, size_mm, layer)
LABELS = [
    ("UP", KEYS["SW1"], KY + 4.6, 0, 0.8, "F"), ("OK / PWR", KEYS["SW2"], KY + 4.6, 0, 0.8, "F"),
    ("DOWN", KEYS["SW3"], KY + 4.6, 0, 0.8, "F"),
    ("CHG", CX - 4.7, CY - 5.2, 0, 0.8, "F"), ("SWD", MX + 17.0, MY - 3.2, 0, 0.8, "F"), ("ANT", 4.0, 30.7, 0, 0.8, "F"),
    ("I2C", 29.6, 4.0, 0, 0.8, "F"), ("CAM/MRK", 52.0, 3.4, 0, 0.8, "F"), ("LCD", DX, 11.9, 0, 0.8, "F"),
    ("D+", 12.0, 21.2, 0, 0.8, "F"), ("D-", 14.4, 21.2, 0, 0.8, "F"),
    ("BAT 1S", 122.7, 41.7, 90, 0.8, "F"), ("+", 119.6, 41.2, 0, 0.8, "F"), ("\u2212", 112.4, 41.2, 0, 0.8, "F"),
    ("UNICORNLINES\u00ae", 101.5, 58.7, 0, 1.0, "F"), ("Never Stop Dreaming", 101.5, 60.3, 0, 0.8, "F", True),
    ("AEROBATICS LOGGER", DX, 24.0, 0, 2.0, "B"), ("rev A  2026-11", DX, 27.5, 0, 1.2, "B"),
    ("PER PERFECTIONEM AD FELICITATEM", DX, 31.5, 0, 1.1, "B", True),
]
LOGO = ("Unicornlines_Logo", 101.5, 52.4)   # 9.5 mm, bottom-right beside DOWN, outside the panel (tools/mklogo.py)
IMU_AXES = (35.8, 44.2)   # left of the IMU; origin of the IMU axis arrows (ICM-45686, pin 1 top-left: +X right, +Y up, +Z out of the top; as TDK fig. 14 and CogniPilot's footprint)


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


def drawings(board):
    """Dwgs.User: the LCD module, its active area and FPC, and the printed key caps, for the case design."""
    def rect(x0, y0, x1, y1):
        for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            sh = pcbnew.PCB_SHAPE(board); sh.SetShape(pcbnew.SHAPE_T_SEGMENT); sh.SetLayer(pcbnew.Dwgs_User); sh.SetWidth(MM(0.1))
            sh.SetStart(pcbnew.VECTOR2I(MM(OX + a[0]), MM(OY + a[1]))); sh.SetEnd(pcbnew.VECTOR2I(MM(OX + b[0]), MM(OY + b[1])))
            board.Add(sh)
    x0, y0, x1, y1 = LCD
    rect(x0, y0, x1, y1)                                        # module 62.8 x 42.82
    rect(DX - 29.4, y1 - 2.0 - 35.28, DX + 29.4, y1 - 2.0)      # active area 58.8 x 35.28 (2.0 mm from the far edge)
    rect(DX - 4.74, y0 - 3.0, DX + 4.74, y0)                    # FPC root, 9.48 wide (folds under the glass)
    for x in KEYS.values():
        rect(x - 9.0, KY - 7.6, x + 9.0, KY + 7.6)              # 18 x 15.2 mm printed caps (case design)


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
        for pad in h.Pads():          # the grounded ring is the keep-out: the router and the via stitcher stay off it
            if pad.GetSize().x > MM(3):
                pad.SetSize(pcbnew.VECTOR2I(MM(HOLE_KEEPOUT), MM(HOLE_KEEPOUT)))

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
    for n, x, y in HAND_VIAS:
        v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))); v.SetWidth(MM(0.5)); v.SetDrill(MM(0.25))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net(n)); v.SetLocked(True); board.Add(v)
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
        t = pcbnew.PCB_TRACK(board); t.SetStart(a); t.SetEnd(c); t.SetWidth(MM(w))
        t.SetLayer(pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu)   # bottom-side parts fan out on B.Cu
        t.SetNet(pad.GetNet()); t.SetLocked(True); board.Add(t)
        v = pcbnew.PCB_VIA(board); v.SetPosition(c); v.SetWidth(MM(vd)); v.SetDrill(MM(vdr))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(pad.GetNet()); v.SetLocked(True); board.Add(v)   # GND or +3V3 plane
    logo = load("logger:" + LOGO[0]); logo.SetReference("LOGO1"); logo.Reference().SetVisible(False)
    logo.SetPosition(pcbnew.VECTOR2I(MM(OX + LOGO[1]), MM(OY + LOGO[2]))); board.Add(logo)
    outline(board)
    slots(board)
    for lb in LABELS:
        text(board, *lb)
    axes(board, *IMU_AXES)
    drawings(board)
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
