"""Build the rev A board (../kicad/logger.kicad_pcb) from design.py and the placement below.

Nets come straight from design.py, so the board and schematic share one source.
Placement is by hand, block by block, on a 0.5 mm grid. A few fanouts are placed by hand and locked
(MCU and IMU ground pins, crystal load caps, every R/C ground pad), then route.py autoroutes the rest.

Board: 138 x 62 mm, 4 layers: F.Cu signal, In1 GND plane, In2 +3V3 pour with some signal routing, B.Cu signal.
"""
import math, os, sys
import pcbnew
import design

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD = os.path.join(HERE, "..", "kicad")
SYSFP = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0          # board top-left on the page
W, H = 138.0, 62.0
MM = pcbnew.FromMM
# The board grew 14 mm at its left end for the built-in GNSS patch (owner, 2026-11-26). Placements right of the old
# left column are still written in the old 124 mm frame (W0) and shifted by X(); the new left-column parts are
# placed in board coordinates (fixed=True).
W0, SHIFT, SPLIT = 124.0, 14.0, 29.0
def X(x):
    return x if x < SPLIT else x + SHIFT
def XY(pt):
    return (X(pt[0]), pt[1])

# Extra pads the footprint has but the symbol doesn't.
EXTRA_PADS = {("J60", "11"): "GND", ("J61", "MP"): "GND", ("J62", "MP"): "GND", ("J63", "MP"): "GND", ("J2", "MP"): "GND"}

# ref: (x, y, rotation, side)  -- board coordinates in mm from the top-left corner; side "F" or "B"
P = {}
def at(ref, x, y, rot=0, side="F", fixed=False):
    P[ref] = (x if fixed else X(x), y, rot, side)
def row(refs, x, y, dx, dy, rot=0, side="F", fixed=False):
    for i, r in enumerate(refs):
        at(r, x + i * dx, y + i * dy, rot, side, fixed)

# Floor plan. Front face: the Sharp 2.7" memory LCD centred at the top (rotated 180 deg so its FPC leaves at the top edge
# and folds back under the glass into J61), and the three Choc keys centred under it. Only low parts (<= 3 mm) sit under the
# panel. Left of the panel: radio (top-left corner, antenna up), GNSS module and its 18 mm patch, sensors below them. Right of the panel: USB-C
# and microSD flush on the right short edge, charger and USB protection; battery and its protection in the
# bottom-right corner. MCU, log flash, 3.3 V buck and LCD supply under the panel.
DX = W0 / 2                      # panel and key centre line (old frame; X(DX) on the board)
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
at("D21", 28.0 + SHIFT, 59.2, 0, fixed=True); at("R22", 24.8 + SHIFT, 59.2, 0, fixed=True)   # moves with the keys

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

# --- GNSS (left end, under the radio), board coordinates ----------------------------------
# NEO-M9N at the left edge (rotated: RF_IN top-right), the 18 x 18 mm Taoglas patch right of it (feed facing the
# module, part-free and with the ground plane all round it), the RF switch in the channel between them. The edge SMA
# for an external antenna sits on the left edge under the radio; its line runs round the module's top (50 ohm
# grounded CPW on F.Cu, hand-routed in RF_TRACKS) with ESD and the bias tee next to the jack. The bias switch and
# current sense sit in a row along the top edge right of the radio; the module's supply filter in the strip at the left edge.
NEO = (9.6, 31.0)
at("U10", *NEO, 180, fixed=True)
PATCH = (32.5, 27.5)
at("AE1", *PATCH, 270, fixed=True)                    # feed pad 7.6 mm left of the centre, at (24.9, 27.5)
SMA_Y = 13.0
at("J50", 2.1, SMA_Y, 270, fixed=True)                # edge-mount SMA, board edge at x 0
at("D50", 5.3, SMA_Y + 0.75, 270, fixed=True)          # ESD, on the line at the jack
at("L50", 5.45, 17.8, 0, fixed=True); at("C52", 4.97, 19.3, 270, fixed=True); at("FB51", 3.8, 18.9, 90, fixed=True)   # bias tee
SW = (19.2, 25.1)
at("U18", *SW, 180, fixed=True)                       # RFIN left (to the module), RF1 up (SMA), RF2 down (patch)
at("C55", 19.4, 22.9, 90, fixed=True)                  # DC block on the SMA branch
at("C58", 17.3, 23.3, 90, fixed=True); at("R53", 17.3, 26.9, 90, fixed=True)
at("TP50", 17.8, 36.0, 0, fixed=True)
at("FB2", 1.5, 26.0, 90, fixed=True); at("C50", 1.5, 30.0, 90, fixed=True); at("C51", 1.5, 37.6, 90, fixed=True)
# antenna feed switch and current sense: a row along the top edge right of the radio, out of the busy corridor
# under the patch (sensors to MCU) and close to the MCU's top-left pins (PE0 / PE1)
at("Q50", 28.6, 3.0, 0, fixed=True)
row(["R54", "R51"], 31.4, 3.0, 1.4, 0, 90, fixed=True)
at("U19", 35.6, 3.0, 0, fixed=True)
row(["C56", "R52", "C57"], 38.6, 3.0, 1.4, 0, 90, fixed=True)
at("R50", 30.6, 7.2, 0, fixed=True)
# Taoglas: no copper on any layer within 3 x 4 mm of the feed pad (the feed line itself on F.Cu only)
FEED_KEEPOUT = (PATCH[0] - 9.7, PATCH[1] - 2.0, PATCH[0] - 6.1, PATCH[1] + 2.0)
# RF lines, board coordinates: (net, points, width). Corners at 45 deg; 0.2 mm where they meet the 0.4 mm-pitch switch.
RF_TRACKS = [
    ("GNSS_EXT_RF", [(1.9, SMA_Y), (5.9, SMA_Y), (6.4, SMA_Y + 0.5), (6.4, 20.9), (6.9, 21.4), (18.9, 21.4), (19.4, 21.9), (19.4, 22.42)], 0.34),
    ("GNSS_EXT_RF", [(5.3, SMA_Y), (5.3, SMA_Y + 0.27)], 0.3), ("GNSS_EXT_RF", [(5.93, 17.8), (6.4, 17.8)], 0.3),
    ("ANT_EXT_SW", [(19.4, 23.38), (19.4, 24.7)], 0.2),
    ("GNSS_RF_IN", [(NEO[0] + 6.0, 25.1), (18.4, 25.1)], 0.34), ("GNSS_RF_IN", [(18.4, 25.1), (19.0, 25.1)], 0.2),
    ("ANT_INT", [(19.4, 25.5), (19.4, 25.9), (21.0, 27.5)], 0.2), ("ANT_INT", [(21.0, 27.5), (PATCH[0] - 7.6, 27.5)], 0.34),
]
# Switch and bias-tee hand wiring (net, points, side, width): supply and select to vias left of the switch, ground out
# to the right between the two RF ports.
GNSS_TRACKS = [("+3V3", [(19.0, 24.7), (19.0, 24.35), (18.1, 24.35)], "F", 0.15), ("+3V3", [(17.3, 23.78), (18.1, 24.35)], "F", 0.2),
               ("ANT_SEL", [(19.0, 25.5), (19.0, 25.85), (18.1, 25.85)], "F", 0.15), ("ANT_SEL", [(17.3, 26.42), (18.1, 25.85)], "F", 0.15),
               ("GND", [(19.4, 25.1), (20.1, 25.1)], "F", 0.2),
               ("ANT_BIAS", [(4.97, 17.8), (4.97, 18.82)], "F", 0.25), ("ANT_BIAS", [(3.8, 18.42), (4.97, 18.42)], "F", 0.25)]
GNSS_VIAS = [("+3V3", 18.1, 24.35), ("ANT_SEL", 18.1, 25.85), ("GND", 20.1, 25.1)]

# --- Sensors (bottom-left, outside the panel and keys) ----------------------------
at("U9", 20.0, 45.0, 0)                               # magnetometer, far from the buck and the battery currents
at("C46", 18.0, 47.5, 0); at("C47", 20.5, 47.5, 0); at("C48", 23.0, 47.5, 0)
row(["R40", "R41"], 18.0, 42.0, 2.0, 0, 90)
at("U8", 12.5, 44.5, 90); at("C44", 12.5, 41.0, 0); at("C45", 12.5, 48.0, 90)
# Environmental chamber at the left edge (x 0.5-7.5, y 40.5-52.5, nothing else within 1.2 mm): the case walls it off
# with baffles and vents it through the left side wall. Temperature / humidity on top, on a copper-free island
# (SHT_ISLAND: no pour on any layer, thin traces) instead of a milled slot, since the board takes repeated g loads;
# the top-port PDM microphone below it. Clock series resistor at PB0.
at("U17", 3.0, 43.0, 180); at("C49", 1.3, 43.0, 270)
at("MK1", 3.8, 49.3, 0); at("C53", 2.3, 46.4, 180)
at("R42", 48.8, 36.8, 90)
SHT_ISLAND = (1.9, 40.8, 6.5, 45.2)
# Barometer: the case seals a hood onto the board around it (cockpit air, or a hose to the static port), so the front
# keeps a part-free ring of 1.8 mm round its courtyard (x 19.45-25.55, y 50.45-56.55) and stays left of the key
# bridge at x 27.2; its decoupling caps sit just above that ring.
at("U7", 22.5, 53.5, 0)
at("C42", 21.9, 49.4, 90); at("C43", 23.3, 49.4, 90)

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
JX = W0 - 3.5
at("J1", JX, 14.0, 90)
at("U1", JX - 8.0, 14.0, 0); at("D1", JX - 8.0, 9.6, 0)
row(["R2", "R1"], JX - 8.9, 17.6, 2.0, 0, 0)
row(["R3", "C1"], JX - 3.5, 21.6, 1.6, 0, 90)
row(["R108", "R109", "C108"], JX - 8.7, 21.6, 1.6, 0, 90)     # CC level to the ADC
# power-fail comparator, then the VBAT/2 divider: one column left of the microSD pull-ups
at("U4", 101.0, 26.2, 90); row(["C12", "C13"], 98.0, 24.8, 0, 1.6, 0)
row(["R10", "R11", "R12", "R106", "R107", "C107"], 101.0, 29.4, 0, 1.5, 0)

# --- microSD (right edge, under the USB-C), card in through the case wall --------
at("J60", W0 - 9.2, 31.5, 90)
row(["R60", "R61", "R62", "R63", "R64", "R65"], W0 - 19.4, 24.5, 0, 1.6, 0)
at("C60", W0 - 19.4, 35.0, 90); at("C61", W0 - 19.4, 37.8, 90)

# --- Battery and cell protection (bottom-right corner) ---------
# JST PH side entry, plug in from the right edge (opening at x 115): the free strip x 115-124, y 43-49 in front of it
# carries the lead, which the case turns down into a wall gully to the cell. Clear of the corner screw H4.
at("J2", 109.9, 45.5, 90)
at("Q3", 97.0, 42.5, 0); at("Q4", 97.0, 45.9, 0)          # discharge / charge FETs
row(["R113", "R112", "C109"], 100.2, 42.0, 1.4, 0, 90)
at("U15", 100.9, 45.2, 0); row(["R111", "R110"], 103.6, 44.2, 0, 2.0, 90)
at("F2", 109.5, 52.6, 0)                                 # fuse right below the cell's pins
at("Q1", 92.0, 40.6, 0); at("R105", 92.0, 43.8, 0)        # reverse-polarity PMOS

# Hand fanouts, placed before autorouting and locked: (ref, pad or net, dx, dy) -> GND via at pad + (dx, dy) mm.
# U9 C3 is a corner ball the router boxes in; the crystal load caps get their own GND via on the far side from
# the crystal so the oscillator loop can't enclose them; the barometer's GND pins are walled in by its 3V3 pair.
FANOUT = [("U9", "C3", 0.55, 0.55), ("C58", "2", -0.7, 0.0), ("D50", "2", 0.0, 0.65), ("C30", "GND", 0.0, -0.95), ("C31", "GND", 0.0, 0.95),
          ("U6", "6", 0.0, 0.9),            # IMU GND, straight down between VDDIO and a reserved pin
          ("U7", "9", 0.75, 0.0),           # baro GND (right side, middle pad), straight out to a via
          ("U11", "51", 0.6, 0.75),
          # environmental chamber: the humidity sensor's cap and the mic's cap get their 3V3 via just outside the
          # copper-free island; the mic's ground ring gets a via on every side
          ("C49", "1", 0.0, -0.9), ("C53", "1", 0.0, -0.8),
          ("MK1", "5", 0.75, 0.0), ("MK1", "6", 0.0, -0.8), ("MK1", "7", -0.75, 0.0), ("MK1", "8", 0.0, 0.8),
          ("C62", "1", 0.7, 0.0), ("U16", "1", 0.0, -0.7)]   # LCD boost input and its cap: straight to the 3V3 plane          # mic decoupling (back): its GND via between the cap and the mic, off the 3V3 run
# Hand tracks (net, points, side, width) and vias (net, x, y), locked. Environmental chamber: the humidity sensor's
# pads exit sideways (its footprint keeps tracks off the body), supply and ground to C49 at the edge, the I2C pair east
# across the island and on the back in two parallel lanes to the pull-ups R40 (SCL) / R41 (SDA). The mic's four inner
# pads leave its ground ring through the corner gaps at 45 deg; LR is tied to the ring (left channel).
SDA_VIA = (20.0, 43.3325)
TRACKS = [("+3V3", [(2.3, 42.6), (1.3, 42.52)], "F", 0.15), ("GND", [(2.3, 43.4), (1.3, 43.48)], "F", 0.15),
          ("I2C1_SDA", [(3.7, 43.4), (7.0, 43.4)], "F", 0.15),
          ("I2C1_SDA", [(7.0, 43.4), (7.7, 44.1), (19.3, 44.1), SDA_VIA], "B", 0.2),
          ("I2C1_SDA", [SDA_VIA, (20.0, 42.51)], "F", 0.2), ("I2C1_SDA", [SDA_VIA, (20.0, 44.6)], "F", 0.15),
          # ...and on to the MCU (PB7, pad 93) along the router's earlier path, which it no longer finds on its own
          ("I2C1_SDA", [SDA_VIA, (35.5617, 43.3325), (42.0377, 36.8565)], "B", 0.15),
          ("I2C1_SDA", [(42.0377, 36.8565), (42.0377, 34.8722), (43.5231, 33.3868), (43.5231, 31.6012), (47.5, 27.6243), (47.5, 18.325)], "F", 0.15),
          ("I2C1_SCL", [(3.7, 42.6), (7.8, 42.6)], "F", 0.15),
          ("I2C1_SCL", [(7.8, 42.6), (17.3, 42.6), (18.0, 43.3)], "B", 0.2),
          ("I2C1_SCL", [(18.0, 43.3), (18.0, 42.51)], "F", 0.2),
          ("+3V3", [(3.375, 48.625), (3.375, 48.375), (2.78, 47.78), (2.78, 46.4)], "F", 0.15),
          ("GND", [(3.375, 49.975), (2.575, 49.975)], "F", 0.15),
          ("MIC_DATA", [(4.225, 48.625), (4.225, 48.375), (5.4, 47.2)], "F", 0.15),
          ("MIC_CLK", [(4.225, 49.975), (4.225, 50.225), (5.4, 51.4)], "F", 0.15)]
HAND_VIAS = [("I2C1_SDA", 7.0, 43.4), ("I2C1_SDA", *SDA_VIA), ("I2C1_SDA", 42.0377, 36.8565), ("I2C1_SCL", 7.8, 42.6), ("I2C1_SCL", 18.0, 43.3),
             ("MIC_DATA", 5.4, 47.2), ("MIC_CLK", 5.4, 51.4)]
FANOUT_INWARD = ["U5"]
FANOUT_AXIAL = [("U1", "2", +1), ("U10", "24", -1)]
PREROUTE = [("U16", "1", "U16", "6", "F", 0.25)]   # LCD boost: VIN and EN tied straight across the package
PREROUTE_PATH = []

HOLES = [(4.0, 4.0), (W - 4.0, 4.0), (4.0, H - 4.0), (W - 4.0, H - 4.0)]   # board coordinates   # corners only: the cell lies behind the middle
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


def outline(board, r=2.0):
    """Plain rounded rectangle: no cut-outs or slots anywhere, the board takes repeated g loads. The radio antenna has
    its copper keep-out (in the module footprint) instead of a notch."""
    edge_line(board, r, 0, W - r, 0); edge_line(board, W, r, W, H - r)
    edge_line(board, W - r, H, r, H); edge_line(board, 0, H - r, 0, r)
    edge_arc(board, W - r, r, W - r, 0, 90); edge_arc(board, W - r, H - r, W, H - r, 90)
    edge_arc(board, r, H - r, r, H, 90); edge_arc(board, r, r, 0, r, 90)


def island(board, x0, y0, x1, y1, layers=None, tracks=True):
    """Copper-free island round the humidity sensor: no pour on any layer, tracks allowed (its own thin ones).
    Also the patch antenna's feed keep-out (layers and tracks given)."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True); z.SetLayerSet(layers or pcbnew.LSET.AllCuMask(4))
    z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(not tracks); z.SetDoNotAllowVias(not tracks)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(MM(OX + x), MM(OY + y))
    board.Add(z)


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
REF_FIXED = {"U19"}   # REF_POS entries already in board coordinates (no X() shift)
REF_POS = {"U16": (DX + 9.0, 10.4), "U5": (MX, MY), "U4": (98.0, 28.0), "U13": (103.0, 11.0), "U15": (99.2, 45.2, 90), "U10": (9.6, 39.9), "U18": (21.9, 22.7), "U19": (35.6, 5.6)}            # reference centred in the MCU outline

# Silkscreen labels: (text, x, y, rotation, size_mm, layer)
LABELS = [
    ("UP", KEYS["SW1"], KY + 4.6, 0, 0.8, "F"), ("OK / PWR", KEYS["SW2"], KY + 4.6, 0, 0.8, "F"),
    ("DOWN", KEYS["SW3"], KY + 4.6, 0, 0.8, "F"),
    ("CHG", CX - 4.7, CY - 5.2, 0, 0.8, "F"), ("SWD", MX + 17.0, MY - 3.2, 0, 0.8, "F"),
    ("I2C", 29.6, 4.0, 0, 0.8, "F"), ("CAM/MRK", 52.0, 3.4, 0, 0.8, "F"), ("LCD", DX, 11.9, 0, 0.8, "F"),
    ("D+", 12.0, 17.7, 0, 0.8, "F"), ("D-", 14.4, 17.7, 0, 0.8, "F"),
    ("+", 115.9, 43.5, 0, 0.8, "F"), ("\u2212", 115.9, 47.5, 0, 0.8, "F"), ("BAT 1S", 117.4, 45.5, 90, 0.8, "F"),
    ("UNICORNLINES\u00ae", 99.8, 58.7, 0, 1.0, "F"), ("Never Stop Dreaming", 99.8, 60.3, 0, 0.8, "F", True),
    ("AEROBATICS LOGGER", DX, 24.0, 0, 2.0, "B"), ("rev A  2026-11", DX, 27.5, 0, 1.2, "B"),
    ("PER PERFECTIONEM AD FELICITATEM", DX, 31.5, 0, 1.1, "B", True),
]
LOGO = ("Unicornlines_Logo", 99.8, 52.4)   # 9.5 mm, bottom-right beside DOWN, outside the panel (tools/mklogo.py)
IMU_AXES = (35.8, 44.2)   # left of the IMU; origin of the IMU axis arrows (ICM-45686, pin 1 top-left: +X right, +Y up, +Z out of the top; as TDK fig. 14 and CogniPilot's footprint)


def tidy_refs(f, ref):
    """Small references on silk for ICs, connectors and buttons; everything else goes to F.Fab only."""
    t = f.Reference()
    t.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); t.SetTextThickness(MM(0.12))
    if ref in REF_POS:
        t.SetPosition(pcbnew.VECTOR2I(MM(OX + (REF_POS[ref][0] if ref in REF_FIXED else X(REF_POS[ref][0]))), MM(OY + REF_POS[ref][1])))
        t.SetTextAngle(pcbnew.EDA_ANGLE(REF_POS[ref][2] if len(REF_POS[ref]) > 2 else 0, pcbnew.DEGREES_T))
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
    x0, x1, dx = X(x0), X(x1), X(DX)
    rect(x0, y0, x1, y1)                                        # module 62.8 x 42.82
    rect(dx - 29.4, y1 - 2.0 - 35.28, dx + 29.4, y1 - 2.0)      # active area 58.8 x 35.28 (2.0 mm from the far edge)
    rect(dx - 4.74, y0 - 3.0, dx + 4.74, y0)                    # FPC root, 9.48 wide (folds under the glass)
    for x in KEYS.values():
        rect(X(x) - 9.0, KY - 7.6, X(x) + 9.0, KY + 7.6)        # 18 x 15.2 mm printed caps (case design)


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


def snap_to_pads(board, r=0.06):
    """Hand track ends meant for a pad centre land exactly on it (pad positions carry um offsets; a um gap gives
    Freerouting a degenerate polyline)."""
    cs = [p.GetPosition() for f in board.GetFootprints() for p in f.Pads()]
    for t in board.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        for get, put in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
            q = get()
            for c in cs:
                if 0 < (c - q).EuclideanNorm() < MM(r):
                    put(c); break


def rf_fence(board, pitch=2.0, off=0.85):
    """GND vias along both sides of every RF line (RF_TRACKS), skipped where they would touch other copper,
    the feed keep-out or a part's body."""
    pads = [p for f in board.GetFootprints() for p in f.Pads()]
    tracks = [t for t in board.GetTracks()]
    keep = FEED_KEEPOUT
    placed = []
    for n, pts, w in RF_TRACKS:
        if w < 0.34:
            continue
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            L = math.hypot(bx - ax, by - ay)
            if L < 0.9:
                continue
            ux, uy = (bx - ax) / L, (by - ay) / L
            k = 0.5
            while k < L - 0.3:
                for sgn in (1, -1):
                    x, y = ax + ux * k - uy * off * sgn, ay + uy * k + ux * off * sgn
                    if keep[0] - 0.4 < x < keep[2] + 0.4 and keep[1] - 0.4 < y < keep[3] + 0.4:
                        continue
                    if not (0.8 < x < W - 0.8 and 0.8 < y < H - 0.8):
                        continue
                    c = pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))
                    circ = pcbnew.SHAPE_CIRCLE(c, MM(0.25))
                    if any(p.GetEffectiveShape(l).Collide(circ, MM(0.15) if p.GetNetname() == "GND" else MM(0.3))
                           for p in pads for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)):
                        continue
                    if any(t.GetEffectiveShape().Collide(circ, MM(0.2)) for t in tracks if t.GetNetname() != "GND"):
                        continue
                    if any((t.GetPosition() - c).EuclideanNorm() < MM(0.8) for t in tracks if t.GetClass() == "PCB_VIA"):
                        continue
                    if any(f.GetCourtyard(pcbnew.F_CrtYd).Collide(pcbnew.VECTOR2I(c.x, c.y), MM(0.25))
                           for f in board.GetFootprints() if f.GetReference() in ("AE1", "J50", "U18")):
                        continue
                    if any(math.hypot(x - px, y - py) < 0.8 for px, py in placed):
                        continue
                    placed.append((x, y))
                    v = pcbnew.PCB_VIA(board); v.SetPosition(c); v.SetWidth(MM(0.5)); v.SetDrill(MM(0.25))
                    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(board.FindNet("GND")); v.SetLocked(True); board.Add(v)
                k += pitch
    print("RF fence vias:", len(placed))


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
    for n, pts, side, w in [(n, [XY(q) for q in pts], side, w) for n, pts, side, w in TRACKS] + GNSS_TRACKS + \
            [(n, pts, "F", w) for n, pts, w in RF_TRACKS]:
        pp = [pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)) for x, y in pts]
        for s_, e_ in zip(pp, pp[1:]):
            t = pcbnew.PCB_TRACK(board); t.SetStart(s_); t.SetEnd(e_); t.SetWidth(MM(w))
            t.SetLayer({"F": pcbnew.F_Cu, "B": pcbnew.B_Cu, "In2": pcbnew.In2_Cu}[side]); t.SetNet(net(n)); t.SetLocked(True); board.Add(t)
    snap_to_pads(board)
    for n, x, y in [(n, X(x), y) for n, x, y in HAND_VIAS] + GNSS_VIAS:
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
    logo.SetPosition(pcbnew.VECTOR2I(MM(OX + X(LOGO[1])), MM(OY + LOGO[2]))); board.Add(logo)
    outline(board)
    island(board, *SHT_ISLAND)
    inner = pcbnew.LSET(); [inner.AddLayer(l) for l in (pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)]
    front = pcbnew.LSET(); front.AddLayer(pcbnew.F_Cu)
    island(board, *FEED_KEEPOUT, layers=inner, tracks=False)    # nothing at all under the feed
    island(board, *FEED_KEEPOUT, layers=front)                  # the feed line only on top
    rf_fence(board)
    for lb in LABELS:
        text(board, lb[0], X(lb[1]), *lb[2:])
    axes(board, X(IMU_AXES[0]), IMU_AXES[1])
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
