"""Build the project symbol library ../kicad/logger.kicad_sym for parts KiCad doesn't ship.

Pin tables come from the manufacturers' datasheets; see the SOURCE lines.
Each pin: (number, name, type, side) with side 'L' or 'R'. Side 'L+'/'R+' stacks the pin, hidden, on the
row of the pin before it (for the many GND and NC pads of modules).
"""
import os
from sexpr import Sym, dump

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kicad", "logger.kicad_sym")

PARTS = {
    # SOURCE: TDK ICM-45686 datasheet DS-000577 rev 1.0, section 4.1 (pin-out). Pin names cross-checked against five
    # independent KiCad libraries; the land pattern is KiCad's LGA-14 3x2.5 mm, whose pads match those libraries.
    # RESV pins 2, 3, 10, 11 are the AUX1 interface (unused); pin 7 is reserved. All left unconnected.
    "ICM-45686": dict(ref="U", fp="Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y", desc="6-axis IMU, +-32 g, +-4000 dps", pins=[
        ("8", "VDD", "power_in", "L"), ("5", "VDDIO", "power_in", "L"),
        ("12", "AP_CS", "input", "L"), ("13", "AP_SCLK", "input", "L"), ("14", "AP_SDI", "bidirectional", "L"), ("1", "AP_SDO", "output", "L"),
        ("6", "GND", "power_in", "L"),
        ("4", "INT1", "output", "R"), ("9", "INT2/FSYNC/CLKIN", "bidirectional", "R"),
        ("2", "RESV/AUX1_SDIO", "passive", "R"), ("3", "RESV/AUX1_SCLK", "passive", "R"), ("7", "RESV", "passive", "R"),
        ("10", "RESV/AUX1_CS", "passive", "R"), ("11", "RESV/AUX1_SDO", "passive", "R")]),
    # SOURCE: GigaDevice DS-00846 GD5F4GM8UE rev 1.3, WSON8 8x6 connection diagram
    # (same pin order as Winbond W25N). EP to GND.
    "GD5F4GM8UE": dict(ref="U", fp="Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm", desc="4 Gbit (512 MB) SPI NAND flash, quad I/O, on-chip ECC", pins=[
        ("8", "VCC", "power_in", "L"), ("1", "~{CS}", "input", "L"), ("6", "CLK", "input", "L"),
        ("4", "GND", "power_in", "L"), ("9", "EP", "passive", "L"),
        ("5", "DI/IO0", "bidirectional", "R"), ("2", "DO/IO1", "bidirectional", "R"),
        ("3", "~{WP}/IO2", "bidirectional", "R"), ("7", "~{HOLD}/IO3", "bidirectional", "R")]),
    # SOURCE: Bosch BMP390 datasheet BST-BMP390-DS002, table 52 (verify against fig. pp.47-49).
    "BMP390": dict(ref="U", fp="logger:Bosch_LGA-10_2.0x2.0mm", desc="Barometric pressure sensor", pins=[
        ("10", "VDD", "power_in", "L"), ("1", "VDDIO", "power_in", "L"),
        ("6", "CSB", "input", "L"), ("2", "SCK", "input", "L"), ("4", "SDI", "bidirectional", "L"), ("5", "SDO", "output", "L"),
        ("3", "VSS", "power_in", "L"), ("8", "VSS", "passive", "L"), ("9", "VSS", "passive", "L"),
        ("7", "INT", "output", "R")]),
    # SOURCE: Bosch BMM350 datasheet BST-BMM350-DS002 rev 1.29, section 6. VDD is 1.72-1.98 V.
    "BMM350": dict(ref="U", fp="logger:Bosch_WLCSP-9_1.28x1.28mm_P0.4mm", desc="3-axis magnetometer, VDD 1.8 V", pins=[
        ("C1", "VDD", "power_in", "L"), ("B3", "VDDIO", "power_in", "L"),
        ("A3", "SCK", "input", "L"), ("A2", "SDA", "bidirectional", "L"), ("B2", "ADSEL", "input", "L"),
        ("B1", "GND", "power_in", "L"), ("C3", "BYPASS", "passive", "L"),
        ("A1", "INT", "output", "R"), ("C2", "CRST", "passive", "R")]),
    # SOURCE: u-blox NEO-F10N datasheet UBX-23002117 R05, table 10.
    # SOURCE: u-blox NEO-M9N data sheet UBX-19014285 R02, section 3 pin definition (cross-checked with SparkFun's symbol).
    "NEO-M9N": dict(ref="U", fp="RF_GPS:ublox_NEO", desc="u-blox M9 GNSS module, 25 Hz, NEO footprint", pins=[
        ("23", "VCC", "power_in", "L"), ("22", "V_BCKP", "power_in", "L"),
        ("21", "RXD1", "input", "L"), ("20", "TXD1", "output", "L"), ("8", "RESET_N", "input", "L"),
        ("1", "SAFEBOOT_N", "input", "L"), ("4", "EXTINT", "input", "L"), ("2", "D_SEL", "input", "L"),
        ("10", "GND", "power_in", "L"), ("12", "GND", "passive", "L"), ("13", "GND", "passive", "L"), ("24", "GND", "passive", "L"),
        ("11", "RF_IN", "input", "R"), ("9", "VCC_RF", "power_out", "R"), ("14", "LNA_EN", "output", "R"),
        ("3", "TIMEPULSE", "output", "R"), ("7", "VDD_USB", "power_in", "R"),
        ("5", "USB_DM", "bidirectional", "R"), ("6", "USB_DP", "bidirectional", "R"),
        ("18", "SDA", "bidirectional", "R"), ("19", "SCL", "bidirectional", "R"),
        ("15", "RSVD", "no_connect", "R"), ("16", "RSVD", "no_connect", "R"), ("17", "RSVD", "no_connect", "R")]),
    # SOURCE: Espressif ESP32-C6-MINI-1/MINI-1U datasheet v1.5, table 3-1 (pin definitions) and section 4 (strapping).
    "ESP32-C6-MINI-1": dict(ref="U", fp="logger:ESP32-C6-MINI-1", desc="Wi-Fi 6 + BLE 5 module, PCB antenna", pins=[
        ("3", "3V3", "power_in", "L"),
        ("8", "EN", "input", "L"),
        ("23", "IO9/BOOT", "bidirectional", "L"), ("22", "IO8", "bidirectional", "L"), ("20", "IO15", "bidirectional", "L"),
        ("31", "TXD0", "bidirectional", "L"), ("30", "RXD0", "bidirectional", "L"),
        ("18", "IO13/USB_D-", "bidirectional", "L"), ("17", "IO12/USB_D+", "bidirectional", "L"),
        ("1", "GND", "power_in", "L")] + [(n, "GND", "passive", "L+") for n in
        ["2", "11", "14"] + [str(i) for i in range(36, 54)]] + [
        ("15", "IO6/FSPICLK", "bidirectional", "R"), ("16", "IO7/FSPID", "bidirectional", "R"),
        ("5", "IO2/FSPIQ", "bidirectional", "R"), ("24", "IO18", "bidirectional", "R"), ("25", "IO19", "bidirectional", "R"),
        ("9", "IO4/MTMS", "bidirectional", "R"), ("10", "IO5/MTDI", "bidirectional", "R"),
        ("12", "IO0", "bidirectional", "R"), ("13", "IO1", "bidirectional", "R"), ("6", "IO3", "bidirectional", "R"),
        ("19", "IO14", "bidirectional", "R"), ("26", "IO20", "bidirectional", "R"), ("27", "IO21", "bidirectional", "R"),
        ("28", "IO22", "bidirectional", "R"), ("29", "IO23", "bidirectional", "R"),
        ("4", "NC", "no_connect", "R")] + [(n, "NC", "no_connect", "R+") for n in ["7", "21", "32", "33", "34", "35"]]),
    # SOURCE: ST MP34DT06J datasheet DS12698 rev 3 (July 2021), table 1: 1 VDD, 2 LR, 3 CLK, 4 DOUT, ground ring GND.
    # Land pattern fig. 12; the ring is split into four pads (5-8), all GND. LR has an internal 200k pull-down.
    "MP34DT06J": dict(ref="MK", fp="logger:ST_HCLGA-4_3x4mm_MP34DT06J", desc="MEMS PDM microphone, top port, AOP 122.5 dB SPL", pins=[
        ("1", "VDD", "power_in", "L"), ("2", "LR", "input", "L"), ("3", "CLK", "input", "L"),
        ("5", "GND", "power_in", "L")] + [(n, "GND", "passive", "L+") for n in ["6", "7", "8"]] + [
        ("4", "DOUT", "output", "R")]),
    # SOURCE: Taoglas SGGP.18.4.A.08 datasheet (feed pad and ground pads; RHCP, 3.02 dBic on a 50 x 50 mm ground).
    "SGGP.18.4.A.08": dict(ref="AE", fp="logger:Taoglas_SGGP.18.4.A.08", desc="GNSS ceramic patch antenna, 18 x 18 x 4 mm, L1", pins=[
        ("1", "FEED", "passive", "R"), ("2", "GND", "passive", "L")]),
}

LOADED = {}


def eff(hide=False, justify=None):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]
    if justify:
        e.append([Sym("justify"), Sym(justify)])
    if hide:
        e.append(Sym("hide"))
    return e


def build(name, d):
    left = [p for p in d["pins"] if p[3].startswith("L")]
    right = [p for p in d["pins"] if p[3].startswith("R")]
    rows = max(sum(p[3] == "L" for p in left), sum(p[3] == "R" for p in right))
    half_w = 10.16
    top = (rows + 1) * 2.54 / 2
    top = round(top / 2.54) * 2.54
    bottom = top - (rows + 1) * 2.54
    body = [Sym("symbol"), f"{name}_0_1",
            [Sym("rectangle"), [Sym("start"), -half_w, top], [Sym("end"), half_w, bottom],
             [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]],
             [Sym("fill"), [Sym("type"), Sym("background")]]]]
    pins = [Sym("symbol"), f"{name}_1_1"]
    for side, lst in (("L", left), ("R", right)):
        i = 0
        for num, pname, ptype, sd in lst:
            stacked = sd.endswith("+")
            if not stacked:
                i += 1
            y = top - 2.54 * i
            x = -half_w - 2.54 if side == "L" else half_w + 2.54
            ang = 0 if side == "L" else 180
            pin = [Sym("pin"), Sym(ptype), Sym("line"), [Sym("at"), x, y, ang], [Sym("length"), 2.54]]
            if stacked:
                pin.append(Sym("hide"))
            pins.append(pin + [[Sym("name"), pname, eff()], [Sym("number"), num, eff()]])
    return [Sym("symbol"), name, [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
            [Sym("property"), "Reference", d["ref"], [Sym("at"), -half_w, top + 1.27, 0], eff(justify="left")],
            [Sym("property"), "Value", name, [Sym("at"), half_w, top + 1.27, 0], eff(justify="right")],
            [Sym("property"), "Footprint", d["fp"], [Sym("at"), 0, 0, 0], eff(hide=True)],
            [Sym("property"), "Datasheet", "", [Sym("at"), 0, 0, 0], eff(hide=True)],
            [Sym("property"), "Description", d["desc"], [Sym("at"), 0, 0, 0], eff(hide=True)],
            body, pins]


def main():
    lib = [Sym("kicad_symbol_lib"), [Sym("version"), 20220914], [Sym("generator"), "logger-mklib"]]
    for name, d in PARTS.items():
        lib.append(build(name, d))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(dump(lib) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
