# Hardware

Rev A draft schematic for the logger, in KiCad 7 format. The schematic is generated from code:

- `tools/design.py`: every part and every pin's net. **Edit this, not the `.kicad_sch` files.**
- `tools/mklib.py`: builds `kicad/logger.kicad_sym` for parts KiCad doesn't ship (BMI563, BMP390, BMM350, NEO-F10N), with pin tables from the datasheets.
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

## Sheets

| Sheet | Contents |
| --- | --- |
| Power | USB-C sink, TVS and USB ESD, MAX40200 ideal diode, 0.5 F hold-up (2 x 1 F in series), TPS62130 buck to 3.3 V, VDDA filter, MCP65R41 power-fail comparator |
| MCU | STM32H723VGT6, decoupling, 25 MHz and 32.768 kHz crystals, RTC/GNSS backup supercap, SWD header, status LED |
| Sensors | BMI563 IMU (SPI1), BMP390 barometer (SPI2), BMM350 magnetometer (I2C1) with its 1.8 V LDO |
| GNSS | NEO-F10N, active antenna feed, SMA |
| IO | microSD (SDMMC1), Sharp LS027B7DH01 FPC, 3 buttons, camera-sync header |

## Open items before layout

- [ ] BMI563 pinout is from Bosch's preliminary flyer; confirm against the full datasheet when released.
- [ ] Add the ICM-45686 alternate footprint once its pin table is checked (DS-000577, section 4.1).
- [ ] BMP390 and BMM350 pin tables: check against the datasheet figures.
- [ ] Sharp LS027B7DH01 supply voltage: drawn as 5 V from VSYS; confirm in the Sharp spec. EXTMODE (pin 8) is tied to VDD so EXTCOMIN drives COM inversion.
- [ ] NEO-F10N: confirm the active-antenna feed against the integration manual, and pin compatibility with NEO-F9P.
- [ ] Custom footprints (`logger:` library) still to draw: Bosch LGA-14, LGA-10, WLCSP-9.
- [ ] Run full ERC in KiCad 8 or later on a desktop.
