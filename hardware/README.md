# Hardware

Rev A draft schematic and board for the logger, in KiCad 7 format. Both are generated from code:

- `tools/design.py`: every part and every pin's net. **Edit this, not the `.kicad_sch` files.**
- `tools/mklib.py`: builds `kicad/logger.kicad_sym` for parts KiCad doesn't ship (ICM-45686, BMP390, BMM350, NEO-M9N, ESP32-C6-MINI-1, GD5F4GM8UE), with pin tables from the datasheets.
- `tools/gen.py`: writes the sheets under `kicad/`, joining nets with global labels and flagging unused pins.
- `tools/check.py`: connectivity checks on the exported netlist (every assigned pin is on its net, power nets are driven, no output conflicts). It stands in for ERC, which the KiCad 7 command line doesn't have.

```sh
cd hardware/tools
python3 mklib.py && python3 gen.py
kicad-cli sch export netlist ../kicad/logger.kicad_sch -o /tmp/logger.net
python3 check.py /tmp/logger.net
kicad-cli sch export pdf ../kicad/logger.kicad_sch -o ../kicad/logger.pdf
```

`kicad/logger.pdf` is the latest export, for review without KiCad.

## Board

![Board, top](renders/board-hero.png)

- 124 x 62 mm (2:1), 4 layers, 1.6 mm: F.Cu signals and GND pour, In1 solid GND, In2 +3V3 pour with a few signal runs, B.Cu signals and GND pour. Every part is SMD; the only parts on the back are the three key sockets.
- Rules: 0.15 mm track and clearance, 0.5/0.25 mm vias, 0.4 mm for the power path.
- Front face: the Sharp 2.7-inch memory LCD centred at the top, the three keys (UP, OK / PWR, DOWN) centred under it. Under the panel only parts up to 2.9 mm tall: the MCU with its crystals, the log flash, the 3.3 V buck and the LCD's 5 V boost and FPC socket.
- Floor plan around the panel: radio (top-left corner, antenna up) and GNSS on the left, sensors below them; USB-C and microSD on the right short edge (the card goes in through the case wall), the charger, USB protection and power latch beside them; the battery socket and its protection in the bottom-right corner, with the logo beside the DOWN key. Passives sit in straight rows and columns next to the pins they serve.
- Top edge: radio antenna, Qwiic socket (J63), camera/marker socket (J62, JST SUR, for a lead inside the case) and the LCD's FPC fold.
- The IMU moved from the Bosch BMI563 (still not on sale) to the TDK ICM-45686 on 2026-11-25.
- The magnetometer sits at the left end, as far as possible from the buck and the battery currents; the barometer sits bottom-left beside the UP key and needs the case's hose chamber over it.
- Storage: flights are logged to the soldered 512 MB GigaDevice GD5F4GM8UE flash next to the MCU (about 4.5 hours of raw logging; stocked at JLCPCB); the microSD keeps a backup copy and serves firmware updates and export.
- GNSS antenna feed: hand-routed 0.25 mm on F.Cu from the U.FL to the module, short and direct over the In1 ground.
- Radio: ESP32-C6-MINI-1 in the top-left corner, flush with the top edge. Its antenna sits over a cut-out in the board, as Espressif's guidelines ask, so there is no board material under it. The case wall in front of it must be plastic. It may stay on in flight (fine from an avionics point of view); bulk Wi-Fi transfers happen on the ground. Planned uses: camera start/stop over Bluetooth, wireless firmware updates for both chips, compressed flight download.
- Silkscreen: references only for ICs, connectors with function labels instead (UP, OK / PWR, DOWN, CHG, BAT 1S +/−, SWD, CAM/MRK, I2C, LCD, ANT, D+/D-), IMU axes left of U6. Passive references are on F.Fab for assembly. Dwgs.User carries the LCD outline, its active area and FPC, and the 20 x 16 mm key caps for the case design.
- Top: the Unicornlines logo (9.5 mm, bottom-right, outside the panel) with "UNICORNLINES®" and "Never Stop Dreaming". Back: "AEROBATICS LOGGER", the revision, and *PER PERFECTIONEM AD FELICITATEM*.
- The logo is `art/unicornlines-logo.svg`, turned into the `logger:Unicornlines_Logo` silkscreen footprint by `tools/mklogo.py` (strokes thickened to the 0.16 mm silk minimum). Re-run it only when the artwork changes: `python3 mklogo.py ../art/unicornlines-logo.svg Unicornlines_Logo 9.5`.
- Five M3 holes, grounded: the corners, 4 mm in, and a fifth at (50, 41), 6 mm from the IMU, to hold the IMU's area rigid. Each has a 7 mm grounded copper ring on every layer, so no parts, tracks or vias come closer than 3.65 mm to its centre; the case bosses clamp on it. The fifth sits under the panel, so its boss comes from the back.

Mechanical data for the case (mm from the board's top-left corner, y down; heights above F.Cu or below B.Cu):

| Item | Position | Height | Notes |
| --- | --- | --- | --- |
| LCD module LS027B7DH01 | x 30.6-93.4, y 2.5-45.32 | glass back at 3.5, top about 4.8 | 62.8 x 42.82 x 1.3; active area 58.80 x 35.28, 2.0 mm from the FPC-far edge. Hold it on its border with a spacer frame and the bezel. FPC 9.5 mm wide, centred, leaves the top edge and folds 180° under the glass (never toward the front polariser) into J61 at (62, 6.5); the fold may stand 0-1 mm past the top board edge |
| Keys SW1-3 | (40 / 62 / 84, 53.9) | Choc V1 switch on F.Cu; socket 1.85 below B.Cu | Kailh hotswap sockets on B.Cu (the only parts on the back); the case front is the switch plate (13.8 mm square cut-outs, Choc plate thickness 1.2 mm). Caps 20 x 16 |
| Tallest front part outside the panel | C34 (14, 54.5) | 5.4 | RTC/GNSS backup cap |
| USB-C J1 | right edge, centred y 14 | 3.3 | lip about 0.2 past the edge |
| microSD J60 | right edge, centred y 31.5 | 1.7 | body ends about 1 mm inside the edge; an inserted card stands about 4.5 mm out |
| Battery J2 (JST PH) | (116, 46) | 4.85 | cable towards the bottom edge |
| Camera/marker J62 (JST SUR) | (46.5, 2.9) | 1.75 | plug from the top edge |
| Qwiic J63 (JST SH) | (35, 3.4) | 2.9 | plug from the top edge |


Rebuild (needs KiCad 7 Python and a Freerouting 2.x jar):

```sh
cd hardware/tools
python3 pcb.py && python3 route.py /path/to/freerouting.jar
```

`pcb.py` builds the placed, unrouted board from `design.py` plus its placement table, and `route.py` routes, pours and runs DRC. The committed board is DRC-clean (0 errors, 0 unconnected). The only warnings are the "library not in this configuration" notes from a headless KiCad without the global footprint table.

Renders: `tools/render/` turns the board into a GLB (KiCad STEP export, then OCCT), plots the layers into board textures and renders the views with three.js in headless Chromium. Parts KiCad has no 3D model for here (NEO-M9N, ESP32-C6 module, TPS62130, BQ24074, BQ29700, TPS61222, Choc switches and their hotswap sockets, battery fuse, BMP390, BMM350, flash, inductors, JST and FPC sockets, 32 kHz crystal) are drawn as plain boxes. The LCD panel is left off so the parts under it show.

| Top | Bottom |
| --- | --- |
| ![](renders/board-top.png) | ![](renders/board-bottom.png) |

## Sheets

| Sheet | Contents |
| --- | --- |
| Power | USB-C sink (CC level read by the ADC to set the input current), TVS and USB ESD, TI BQ24074 1S Li-ion linear charger with power path (charge current and input limit set by resistors: 0.25 A / 0.44 A by hardware, 1.0 A / 1.39 A switched in by the MCU; 0-50 °C window from the NTC in the battery pack; safety timer), soft power latch on the buck's EN (OK key, MCU hold line, USB power), charge LED, on-board cell protection (TI BQ29700 with two low-side AO3400A FETs) and a 3 A fuse, 3-pin JST-PH battery socket (1 cell −, 2 NTC, 3 cell +) with reverse-polarity PMOS, battery voltage to the ADC, TPS62130 buck to 3.3 V, VDDA filter, MCP65R41 power-fail comparator |
| MCU | STM32H723VGT6, decoupling, 25 MHz and 32.768 kHz crystals, RTC/GNSS backup supercap, SWD on Tag-Connect TC2030-NL pads (no part height under the panel), status LED |
| Sensors | TDK ICM-45686 IMU (SPI1, ±32 g, ±4000 °/s), BMP390 barometer (SPI2), BMM350 magnetometer (I2C1) with its 1.8 V LDO |
| GNSS | NEO-M9N (25 Hz, JLCPCB stock), active antenna feed (u-blox VCC_RF bias circuit), U.FL. VDD_USB grounded (USB unused). A NEO-F9P drops in with the same wiring |
| IO | GD5F4GM8UEYIG 4 Gbit (512 MB) log flash on OCTOSPI1 (quad): the main flight log. microSD (SDMMC1) as backup copy, firmware update and export path. Sharp LS027B7DH01 2.7-inch 400 x 240 memory LCD on SPI4 (Panasonic AYF531035 FPC socket, TPS61222 5 V boost, VCOM toggled by TIM15_CH1), three Kailh Choc keys in hotswap sockets (UP, OK / PWR, DOWN; OK is also the power key on the power sheet), camera-sync and marker socket (J62, JST SUR: sync out, GND, marker in), Qwiic I2C expansion socket (J63, I2C4, PTC-fused 3V3) for an optional airspeed sensor |
| Radio | ESP32-C6-MINI-1 (Wi-Fi 6, BLE 5) as an SPI4 slave sharing SCK/MOSI with the LCD, IRQ line, EN and boot straps driven by the MCU, UART0 to the MCU for flashing, USB D-/D+ test pads |

## Open items

- [x] ICM-45686: pin table checked against DS-000577 section 4.1 (via a page-referenced extraction of the datasheet): RESV pins 2, 3, 7, 10, 11 may be NC, VDDIO or GND, so they stay open with their internal pull-ups on; 0.1 uF X7R on VDD and on VDDIO as specified; VDD 1.71 to 3.6 V and VDDIO 1.08 to 3.6 V cover 3.3 V. Axis arrows (pin 1 top-left, +X right, +Y up, +Z out of the top) match TDK's convention and CogniPilot's footprint silk for this part. Firmware: turn off the internal pull-ups on the four active SPI pins.
- [x] BMP390 pin table (DS002 table 52) and BMM350 ball table (DS001 section 6, top view) match the symbols. BMM350: BYPASS to GND, CRST 2.2 uF to GND, ADSEL low = 0x14, VDD 1.72 to 1.98 V (AP2112K-1.8 gives 1.77 to 1.83 V). Ball map matches four independent footprints.
- [x] Memory LCD (2026-11-26): Sharp LS027B7DH01 pin table and timing from Sharp's LD-28305A spec (SPI write-only, LSB first, SCS active high, up to 1-2 MHz; EXTMODE high, EXTCOMIN 1-20 Hz from TIM15_CH1 on PE5, DISP on PD10, pulled low so the panel stays blank until firmware runs). FPC pin order checked against the Adafruit 2.7-inch breakout and two other open designs. 5 V from a TPS61222 (4.82-5.13 V) per its datasheet; the panel draws 50-350 µW.
- [x] LCD socket Panasonic AYF531035 (Y5B, 10 pins, 0.5 mm, 1.0 mm high, Sharp's recommended part): signal lands 0.3 x 0.8 mm, 3.30 mm pattern depth, FPC enters on the signal-land side. The holding lands (1.0 x 0.8 mm, centres 6.36 mm apart) are read from Panasonic's dimension table, whose drawing could not be fetched as an image; they cover the community variants. Worth a look at the drawing before ordering.
- [x] GNSS: NEO-M9N pin table from data sheet UBX-19014285 section 3 (same as SparkFun's symbol). Antenna feed per u-blox's VCC_RF bias circuit (NEO-F9P integration manual 4.4.4.3): 10 ohm, BLM15HB121SH1 ferrite, 100 nF, 47 nH LQG15HS47NJ02 (was 27 nH and 10 nF; 47 nH keeps >500 ohm down to L5 for the F9P). NEO-F9P drop-in checked pin by pin against three independent symbols and its integration manual: same VCC, V_BCKP, UART1, RESET_N, SAFEBOOT_N, TIMEPULSE, RF and GND pins; D_SEL open keeps UART; V_USB (pin 7) grounded as u-blox requires when USB is unused.
- [x] Custom footprints (`logger:` library): WLCSP-9 for the BMM350 drawn from the datasheet. The ICM-45686 uses KiCad's LGA-14 3x2.5 mm.
- [x] BMP390 land pattern fixed: the placeholder had the wrong pad arrangement. Now 2-3-2-3 pads at 0.5 mm pitch, counter-clockwise from pin 1 at top-right, 0.25 x 0.275 mm, matching four independent footprints made from Bosch's data.
- [ ] Rev A layout review: the autorouter's copper is DRC-clean but not hand-polished. Worth a pass in KiCad on the SPI/SDMMC runs around the MCU and the crystal traces.
- [x] ESP32-C6-MINI-1 checked against datasheet v1.5 and the hardware design guidelines: pins match; IO9 10k pull-up (SPI boot), IO8 10k pull-up (needed for download), IO15 10k pull-up (no internal pull, must not float). Added a 499 ohm on U0TXD and 1k between the MCU and EN (EN keeps its 10k pull-down, so the radio is off until the MCU enables it). Board cut-out under the antenna as the guidelines ask; the module stays flush with the top edge. Firmware: RADIO_BOOT high before EN rises and for 3 ms after.
- [x] GD5F4GM8UE checked: pin-out as the family table (DS-01328 section 2.2, same order as Winbond W25N); WSON8 8x6 drawing from its own datasheet (DS-00846 rev 1.3, fig. 20-1: D 8.00, E 6.00, D2 3.40, E2 4.30, b 0.40, L 0.50, e 1.27 nom). KiCad's WSON-8 8x6 EP 3.4x4.3 (made from GigaDevice's drawing) covers the terminals at max and min tolerance. EP tied to GND. OCTOSPI1 pins checked against ST's pin data: PB2 (36) P1_CLK, PE11 (41) P1_NCS, PD11 (58) P1_IO0, PD12 (59) P1_IO1, PE2 (1) P1_IO2, PD13 (60) P1_IO3. Firmware: wait tVSL = 2 ms after power-up; 2 KB pages, 64 pages per block, 4096 blocks with at least 4016 good; on-chip ECC on by default.
- [x] Battery charger (changed 2026-11-26 to support small and large cells): TI BQ24074RGT (RGT0016B), checked against SLUS810N: pin table 7-1 (1 TS, 2/3 BAT, 4 /CE, 5 EN2, 6 EN1, 7 /PGOOD, 8 VSS, 9 /CHG, 10/11 OUT, 12 ILIM, 13 IN, 14 TMR, 15 ITERM, 16 ISET, pad = VSS) matches KiCad's BQ24074RGT symbol. ICHG = KISET / RISET with KISET 797/890/975 A·Ω: 3.57k gives 0.25 A (0.22-0.27 A), so any cell from 250 mAh charges at 1C or less before firmware runs; Q5 adds 1.18k in parallel for 1.0 A (0.90-1.10 A), switched on only for a cell of 1000 mAh or more as entered in setup. Input limit (EN2 high, EN1 low = ILIM mode, table 7-2): IIN = KILIM / RILIM, 3.48k gives 0.38-0.49 A (inside USB's 500 mA), Q6 adds 1.74k for 1.39 A (1.29-1.48 A) on a 1.5 A or 3 A source. Timer: RTMR 71.5k gives 57 min pre-charge and 9.5 h fast charge (KTMR 48 s/kΩ typ). ITERM open: 10 % termination. TS: the pack's 10k NTC (103AT type) straight to TS gives TI's 0-50 °C window; no NTC means no charging. The charge LED is fed from VBUS so it can never drain the cell. Thermal: up to about 1.3 W in the charger at 1 A (θJA 44.5 °C/W), so it sits on a solid ground pour with vias and TI's thermal regulation throttles it in a hot cockpit. Land pattern checked 2026-11-26 against JLCPCB's own footprint for C54313 (BQ24074RGTR): exposed pad 1.70 x 1.70 mm, signal pads 0.85 x 0.28 mm on 0.5 mm pitch at ±1.50 mm. KiCad's VQFN-16 3x3 EP1.68 land (pads 0.825 x 0.25 at ±1.46) is within 0.05 mm of it everywhere, so it stays. TI's RGT0016B drawing itself could not be fetched here; JLCPCB's footprint is the one their assembly line is tuned to.
- [x] Power latch (added 2026-11-26): the TPS62130's EN is driven by a BAT54C (OK key from VSYS, MCU hold line PD4) and a BAT54W from VBUS through 100k, with 1M and 1 µF to ground: plugging in USB or pressing OK turns the logger on, firmware holds it on, and EN stays up for about 2 s across a firmware reset. PD7 reads the button through 100k / 470k (3.6 V at VSYS 4.4 V, 2.5 V at 3.0 V).
- [x] Keys (2026-11-26): Kailh Choc V1 tactile (CPG135001D02 brown: 3.0 mm travel, 1.5 mm to actuation, 50 gf) in Kailh hotswap sockets CPG135001S30 (JLCPCB C5333465) soldered on the back, so the board is all SMD. Footprint `logger:SW_Kailh_Choc_V1_Hotswap`: switch pin holes 3.05 mm at (0, -5.9) and (5, -3.8), socket lands 2.55 x 2.5 mm at (-3.5, -6) and (8.5, -3.8), centre post 3.45 mm, guide posts 1.9 mm at ±5.5; the kiswitch library and an independent keyboard design agree. The switches are pressed in at case assembly; the case front holds them as the plate. JLCPCB assembles both sides.
- [x] Camera/marker socket J62 (2026-11-26): JST SUR SM03B-SURS-TF (JLCPCB C265338), 0.8 mm pitch, 4.6 x 2.7 mm, 1.75 mm high, for a lead inside the case. Land = KiCad's generator frame for this part (signal 0.5 x 1.0 mm at 0.8 pitch, tabs 1.2 x 1.7 mm at ±2.1), which matches JST's eSUR p3 per an independent dimension-by-dimension derivation.
- [x] Hold-up supercaps removed (owner decision 2026-11-26, to make the board all SMD; no reflow-rated supercap with low enough ESR and JLCPCB stock was found). With a cell fitted the cell rides through USB loss. Without one, a pulled cable loses only the log not yet flushed: firmware writes the log power-loss-safe and flushes every 0.1 s.
- [x] Cell protection (added 2026-11-25): TI BQ29700 checked against SLUSBU9I rev I: pin table 5-1 (DSE: 1 NC, 2 COUT, 3 DOUT, 4 VSS, 5 BAT, 6 V−) matches KiCad's BQ297xy symbol; thresholds from the device comparison table (OVP 4.275 V / 1.25 s, UVP 2.800 V / 144 ms, OCC −100 mV / 8 ms, OCD 100 mV / 20 ms, SCD 0.5 V / 250 µs; 0 V charging inhibited below 0.75 V); application values from fig. 9-1 (330 Ω and 100 nF on BAT, 2.2 kΩ on V−, 5.1 MΩ gate pull-downs). KiCad's WSON-6 1.5 x 1.5 land pattern (0.5 mm pitch, longer pin-1 pad) matches the DSE0006A example board layout. FETs: two AO3400A (already on the board), about 50-60 mΩ in series, so the over-current trips sit at roughly 1.7-2 A at room temperature, above the logger's load (under 0.7 A) and the firmware charge current (1 A maximum). Fuse: Littelfuse 0466003.NR, 3 A very fast, 1206, as the last layer behind the charger and the protector. The pack carries a 10k NTC on pin 2; a pack without one is never charged. The hold-up Schottky D2 is now a B5819W (SOD-123, 1 A 40 V) to free board space.
- [x] ESD: SRV05-4 on J62 (camera sync, marker) and J63 (I2C expansion and its fused 3.3 V), for IEC 61000-4-2 / DO-160 section 25.
- [ ] Run full ERC in KiCad 8 or later on a desktop.
