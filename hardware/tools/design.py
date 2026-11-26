"""Aerobatics Flight Logger, rev A schematic as code.

Every part lists every pin's net. "NC" puts a no-connect flag on the pin.
Pin numbers follow the KiCad library symbol (or mklib.py for project parts).
"""
REV = "A-draft"

R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"


def R(ref, value, a, b, fp=R0402, **kw):
    return dict(ref=ref, lib="Device:R", value=value, fp=fp, nets={"1": a, "2": b}, **kw)


def C(ref, value, a, b, fp=C0402, **kw):
    return dict(ref=ref, lib="Device:C", value=value, fp=fp, nets={"1": a, "2": b}, **kw)


def FLAG(ref, net):
    return dict(ref=ref, lib="power:PWR_FLAG", value="PWR_FLAG", nets={"1": net})


# ---------------------------------------------------------------- power
POWER = dict(file="power.kicad_sch", title="Power: USB-C, Li-ion charger, cell protection, 3.3 V", paper="A2", parts=[
    dict(ref="J1", lib="Connector:USB_C_Receptacle_USB2.0_16P", value="USB-C",
         fp="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
         nets={"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
               "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND",
               "A5": "USB_CC1", "B5": "USB_CC2",
               "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM",
               "A8": "NC", "B8": "NC", "S1": "USB_SHIELD"}),
    R("R1", "5.1k", "USB_CC1", "GND"),
    R("R2", "5.1k", "USB_CC2", "GND"),
    R("R3", "1M", "USB_SHIELD", "GND"),
    C("C1", "4.7n 100V", "USB_SHIELD", "GND", fp=C0603),
    dict(ref="D1", lib="Device:D_TVS", value="SMF5.0CA", fp="Diode_SMD:D_SOD-123F",
         nets={"1": "VBUS", "2": "GND"}),
    dict(ref="U1", lib="Power_Protection:USBLC6-2SC6", value="USBLC6-2SC6", fp="Package_TO_SOT_SMD:SOT-23-6",
         nets={"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM", "2": "GND", "5": "VBUS"}),
    # Charger and power path: TI BQ24074 (SLUS810N), linear, 1S Li-ion. IN (VBUS) -> OUT (VSYS, regulated to 4.4 V)
    # with dynamic power-path management; BAT is charged from OUT and feeds OUT through its own FET when IN is gone.
    # Charge current and input limit are set by resistors, so the hardware default is safe for the smallest cell;
    # firmware only switches in a second resistor once the owner has entered the cell size.
    dict(ref="U13", lib="Battery_Management:BQ24074RGT", value="BQ24074", mpn="BQ24074RGTR",
         fp="Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm",
         nets={"13": "VBUS", "10": "VSYS", "11": "VSYS", "2": "VBAT", "3": "VBAT", "1": "CHG_TS",
               "4": "GND", "6": "GND", "5": "CHG_EN2", "7": "NC", "8": "GND", "17": "GND",
               "9": "CHG_STAT_N", "12": "CHG_ILIM", "14": "CHG_TMR", "15": "NC", "16": "CHG_ISET"}),
    C("C2", "1u 25V", "VBUS", "GND", fp=C0603),
    C("C104", "10u 10V", "VSYS", "GND", fp=C0805), C("C105", "10u 10V", "VSYS", "GND", fp=C0805),
    C("C106", "10u 10V", "VBAT", "GND", fp=C0805),
    # EN2 high, EN1 low: input current limit from ILIM (table 7-2). CE low: charging enabled.
    R("R100", "10k", "VSYS", "CHG_EN2"),
    # ISET: ICHG = 890 A-ohm / RISET. 3.57k = 0.25 A (any cell from 250 mAh at 1C); with Q5 on, 3.57k || 1.18k = 1.0 A.
    R("R101", "3.57k 1%", "CHG_ISET", "GND"), R("R102", "1.18k 1%", "CHG_ISET", "ISET_SW"),
    dict(ref="Q5", lib="Transistor_FET:2N7002", value="2N7002", mpn="2N7002", fp="Package_TO_SOT_SMD:SOT-23",
         nets={"1": "ISET_HI", "2": "GND", "3": "ISET_SW"}),
    R("R103", "100k", "ISET_HI", "GND"),
    # ILIM: IIN = 1525-1610 A-ohm / RILIM. 3.48k = 0.44 A (USB default 500 mA); with Q6 on, 3.48k || 1.74k = 1.39 A
    # (only when the CC level shows a 1.5 A or 3 A source).
    R("R114", "3.48k 1%", "CHG_ILIM", "GND"), R("R115", "1.74k 1%", "CHG_ILIM", "ILIM_SW"),
    dict(ref="Q6", lib="Transistor_FET:2N7002", value="2N7002", mpn="2N7002", fp="Package_TO_SOT_SMD:SOT-23",
         nets={"1": "ILIM_HI", "2": "GND", "3": "ILIM_SW"}),
    R("R116", "100k", "ILIM_HI", "GND"),
    # Safety timer: pre-charge 48 s/k x 71.5k = 57 min, fast charge 10x = 9.5 h. ITERM open: 10 % termination.
    R("R117", "71.5k 1%", "CHG_TMR", "GND"),
    # Charge LED from VBUS (so it can never leak from the cell), CHG also read by the MCU (PD6, 5 V tolerant).
    # The weak pull-up holds the node near 3.3 V when not charging, so the LED sees under 1.7 V and stays dark.
    R("R104", "1.5k", "VBUS", "CHG_LED_A"),
    dict(ref="D22", lib="Device:LED", value="orange", fp="LED_SMD:LED_0603_1608Metric",
         nets={"2": "CHG_LED_A", "1": "CHG_STAT_N"}),
    R("R118", "100k", "CHG_STAT_N", "+3V3"),
    # Soft power latch on the 3.3 V buck's EN: the OK key (SW2, on the IO sheet, from VSYS to PWR_KEY), the MCU's hold
    # line or USB power turns it on.
    # 1M / 1u keeps EN up for about 2 s, so a firmware reset never drops power. USB enters through 100k so EN
    # stays below VSYS (about 4.3 V).
    dict(ref="D23", lib="Diode:BAT54C", value="BAT54C", mpn="BAT54C", fp="Package_TO_SOT_SMD:SOT-23",
         nets={"1": "PWR_KEY", "2": "PWR_HOLD", "3": "PWR_EN"}),
    R("R119", "100k", "VBUS", "PWR_VBUS"),
    dict(ref="D24", lib="Diode:BAT54W", value="BAT54W", mpn="BAT54W", fp="Package_TO_SOT_SMD:SOT-323_SC-70",
         nets={"1": "PWR_VBUS", "2": "NC", "3": "PWR_EN"}),
    R("R120", "1M", "PWR_EN", "GND"), C("C110", "1u", "PWR_EN", "GND"),
    # Button sense for the MCU (PD7): 100k / 470k keeps the pin under 3.7 V at VSYS 4.4 V and above VIH at 3.0 V.
    R("R121", "100k", "PWR_KEY", "PWR_BTN"), R("R122", "470k", "PWR_BTN", "GND"),
    # Battery: JST PH 3-pin (1 cell -, 2 NTC, 3 cell +), fuse, reverse-polarity PMOS (conducts both ways once its
    # body diode lets the gate see -VBAT).
    dict(ref="J2", lib="Connector_Generic:Conn_01x03", value="BATTERY 1S",
         fp="Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal", mpn="S3B-PH-SM4-TB(LF)(SN)",
         nets={"1": "BAT_NEG", "2": "CHG_TS", "3": "BAT_CELL"}),
    dict(ref="F2", lib="Device:Fuse", value="3A fast", mpn="0466003.NR", fp="Fuse:Fuse_1206_3216Metric",
         nets={"1": "BAT_CELL", "2": "BAT_CONN"}),
    # Cell protection on the board (TI BQ29700, SLUSBU9I fig. 9-1): OVP 4.275 V, UVP 2.8 V, OCC -100 mV, OCD 100 mV,
    # SCD 0.5 V across the two low-side FETs (2 x AO3400A, about 50-60 mohm together: charge/discharge trip about
    # 1.7-2 A at room temperature). Independent of the charger and the firmware.
    dict(ref="U15", lib="Battery_Management:BQ297xy", value="BQ29700", mpn="BQ29700DSER",
         fp="Package_SON:WSON-6_1.5x1.5mm_P0.5mm",
         nets={"1": "NC", "2": "PROT_COUT", "3": "PROT_DOUT", "4": "BAT_NEG", "5": "PROT_VDD", "6": "PROT_VM"}),
    R("R110", "330R", "BAT_CONN", "PROT_VDD"), C("C109", "100n", "PROT_VDD", "BAT_NEG"),
    R("R111", "2.2k", "PROT_VM", "GND"),
    R("R112", "5.1M", "PROT_DOUT", "BAT_NEG"), R("R113", "5.1M", "PROT_COUT", "GND"),
    dict(ref="Q3", lib="Device:Q_NMOS_GSD", value="AO3400A", mpn="AO3400A", fp="Package_TO_SOT_SMD:SOT-23",
         nets={"1": "PROT_DOUT", "2": "BAT_NEG", "3": "PROT_MID"}),     # discharge FET
    dict(ref="Q4", lib="Device:Q_NMOS_GSD", value="AO3400A", mpn="AO3400A", fp="Package_TO_SOT_SMD:SOT-23",
         nets={"1": "PROT_COUT", "2": "GND", "3": "PROT_MID"}),         # charge FET
    dict(ref="Q1", lib="Device:Q_PMOS_GSD", value="AO3401A", mpn="AO3401A", fp="Package_TO_SOT_SMD:SOT-23",
         nets={"1": "BAT_GATE", "2": "VBAT", "3": "BAT_CONN"}),
    R("R105", "100k", "BAT_GATE", "GND"),
    # Battery voltage for the ADC (half of VBAT), and the USB-C CC levels to read the source's current advertisement.
    R("R106", "1M 1%", "VBAT", "VBAT_SENSE"), R("R107", "1M 1%", "VBAT_SENSE", "GND"),
    C("C107", "100n", "VBAT_SENSE", "GND"),
    # One ADC pin for both CC lines: the open one sits at 0 V on its 5.1k, so the node reads about half the active one
    # (0.51 x Vcc). 2 x 100k loads Rd by 2.5 %, inside the USB-C vRd windows for Default, 1.5 A and 3 A.
    R("R108", "100k", "USB_CC1", "CC_SENSE"), R("R109", "100k", "USB_CC2", "CC_SENSE"), C("C108", "100n", "CC_SENSE", "GND"),
    # 3.3 V buck, TPS62130 adjustable: Vout = 0.8 V x (1 + R7/R8) = 3.33 V
    dict(ref="U3", lib="Regulator_Switching:TPS62130", value="TPS62130", fp="Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm",
         nets={"10": "VSYS", "11": "VSYS", "12": "VSYS", "13": "PWR_EN",
               "1": "BUCK_SW", "2": "BUCK_SW", "3": "BUCK_SW",
               "14": "+3V3", "5": "BUCK_FB", "4": "PG_3V3",
               "7": "GND", "8": "GND", "9": "BUCK_SS",
               "6": "GND", "15": "GND", "16": "GND", "17": "GND"}),
    C("C5", "10u", "VSYS", "GND", fp=C0805),
    C("C6", "10u", "VSYS", "GND", fp=C0805),
    C("C7", "3.3n", "BUCK_SS", "GND"),
    dict(ref="L1", lib="Device:L", value="2.2u 2A", fp="Inductor_SMD:L_1210_3225Metric",
         nets={"1": "BUCK_SW", "2": "+3V3"}),
    R("R7", "316k 1%", "+3V3", "BUCK_FB"),
    R("R8", "100k 1%", "BUCK_FB", "GND"),
    C("C8", "22u", "+3V3", "GND", fp=C0805),
    C("C9", "22u", "+3V3", "GND", fp=C0805),
    R("R9", "100k", "PG_3V3", "+3V3"),
    # Analog 3.3 V for the MCU's VDDA / VREF+
    dict(ref="FB1", lib="Device:FerriteBead_Small", value="600R@100MHz", fp="Inductor_SMD:L_0603_1608Metric",
         nets={"1": "+3V3", "2": "+3V3A"}),
    C("C10", "1u", "+3V3A", "GND"),
    C("C11", "100n", "+3V3A", "GND"),
    # Power-fail alert: VBUS/3.56 vs 1.21 V internal reference -> trips at about 4.3 V
    dict(ref="U4", lib="Comparator:MCP65R41", value="MCP65R41T-1202", fp="Package_TO_SOT_SMD:SOT-23-6",
         nets={"6": "+3V3", "2": "GND", "3": "VBUS_SENSE", "4": "VREF_1V2", "5": "VREF_1V2", "1": "PWR_FAIL_N"}),
    R("R10", "100k 1%", "VBUS", "VBUS_SENSE"),
    R("R11", "39k 1%", "VBUS_SENSE", "GND"),
    R("R12", "1M", "PWR_FAIL_N", "VBUS_SENSE"),
    C("C12", "100n", "+3V3", "GND"),
    C("C13", "100n", "VREF_1V2", "GND"),
    FLAG("#FLG01", "VBUS"), FLAG("#FLG02", "VSYS"), FLAG("#FLG03", "+3V3"),
    FLAG("#FLG04", "GND"), FLAG("#FLG05", "+3V3A"), FLAG("#FLG06", "VBAT"), FLAG("#FLG07", "BAT_NEG"),
], notes=[
    "Battery optional: one 1S Li-ion/LiPo cell from 250 mAh up, with a 10k NTC (103AT type) in the pack (3-wire JST PH: 1 -, 2 NTC, 3 +).",
    "Three independent layers: charger (4.2 V, resistor-set current, 0-50 C window from the pack NTC, safety timer), BQ29700 + 2 FETs (OV 4.275 V, UV 2.8 V, OC about 2 A, short), 3 A fuse.",
    "Charge current: 0.25 A by hardware; firmware turns on Q5 (1.0 A) only for a cell of 1000 mAh or more as entered in setup. No NTC: no charging.",
    "Input limit: 0.44 A by hardware; Q6 raises it to 1.39 A when CC_SENSE shows a 1.5 A or 3 A source.",
    "No supercap hold-up (owner decision 2026-11-26): with a cell fitted the cell rides through USB loss. Without one, a pulled cable loses only the log not yet flushed (the log is written power-loss-safe, flushed every 0.1 s).",
    "PWR_FAIL_N goes low when VBUS falls below about 4.3 V. With a cell fitted the firmware keeps logging and watches VBAT_SENSE instead.",
    "On: hold OK (it is also the power key), or plug in USB. The MCU then drives PWR_HOLD high. Off: hold OK about 3 s (read on PWR_BTN), firmware releases PWR_HOLD; ignored while logging.",
])

# ---------------------------------------------------------------- MCU
MCU_NETS = {
    "11": "+3V3", "27": "+3V3", "50": "+3V3", "75": "+3V3", "100": "+3V3",
    "10": "GND", "26": "GND", "49": "GND", "74": "GND", "99": "GND", "19": "GND",
    "21": "+3V3A", "20": "+3V3A", "6": "VBAT_BKP", "48": "VCAP_CORE", "73": "VCAP_CORE",
    "14": "NRST", "94": "BOOT0", "12": "HSE_IN", "13": "HSE_OUT", "8": "LSE_IN", "9": "LSE_OUT",
    # timer capture (TIM2): one clock for PPS and every data-ready edge
    "22": "GNSS_PPS", "23": "IMU_INT1", "46": "BARO_INT", "47": "MAG_INT",
    # IMU on SPI1
    "28": "IMU_CS", "29": "IMU_SCK", "30": "IMU_MISO", "31": "IMU_MOSI", "32": "IMU_INT2",
    # barometer on SPI2
    "51": "BARO_CS", "52": "BARO_SCK", "53": "BARO_MISO", "54": "BARO_MOSI",
    # I2C1: magnetometer (0x14) and temperature / humidity (SHT40, 0x44)
    "92": "I2C1_SCL", "93": "I2C1_SDA", "95": "EXP_SCL", "96": "EXP_SDA", "77": "MARKER",
    # GNSS on USART2 (names from the module's side)
    "24": "GNSS_RXD", "25": "GNSS_TXD", "15": "GNSS_RESET_N",
    # microSD on SDMMC1
    "65": "SD_D0", "66": "SD_D1", "78": "SD_D2", "79": "SD_D3", "80": "SD_CLK", "83": "SD_CMD", "84": "SD_DET",
    # SPI4: memory LCD and the radio share SCK/MOSI; LCD chip select is active high (SCS). MISO (PE13) is the radio's only.
    # EXTCOMIN on PE5 = TIM15_CH1, so a timer toggles the LCD's VCOM with no CPU; DISP on PD10.
    "42": "SPI4_SCK", "5": "SPI4_MOSI", "3": "LCD_SCS", "4": "LCD_EXTCOMIN", "57": "LCD_DISP",
    "43": "RADIO_MISO", "62": "RADIO_CS", "44": "RADIO_IRQ",
    # log flash on OCTOSPI1 in quad mode: CLK PB2, NCS PE11, IO0 PD11, IO1 PD12, IO2 PE2, IO3 PD13
    "36": "FLASH_CLK", "41": "FLASH_CS", "58": "FLASH_IO0", "59": "FLASH_IO1", "1": "FLASH_IO2", "60": "FLASH_IO3",
    # radio control and its UART0 (USART3: bootloader, console); names from the module's side
    "45": "RADIO_EN_MCU", "61": "RADIO_BOOT", "55": "RADIO_RXD", "56": "RADIO_TXD",
    # buttons, power fail, camera sync, LED
    # keys: UP on PE8 (EXTI8), DOWN on PE9 (EXTI9); OK is the power key and is read on PD7 (PWR_BTN, EXTI7).
    # Every EXTI line has one pin only: PWR_FAIL_N on PA10 (EXTI10), marker PA15 (EXTI15), IMU INT2 PC4 (EXTI4).
    "38": "BTN_UP", "39": "BTN_DOWN", "69": "PWR_FAIL_N",
    # power latch and charger: PD4 hold, PD7 button sense, PD6 CHG status, PD5 / PD0 charge and input current steps
    "85": "PWR_HOLD", "88": "PWR_BTN", "87": "CHG_STAT_N", "86": "ISET_HI", "81": "ILIM_HI",
    # ADC: battery voltage (PC1, ADC1_INP11) and the USB-C CC level (PC5, ADC12_INP8)
    "16": "VBAT_SENSE", "33": "CC_SENSE", "91": "CAM_SYNC", "40": "LED_STATUS",   # camera sync on PB5 = TIM3_CH2
    # PDM microphone on DFSDM1 channel 1: the DFSDM's own clock out on PB0 (DFSDM1_CKOUT), data in on PB1
    # (DFSDM1_DATIN1). Both sit on the MCU's bottom-left side, toward the mic; clear of the PC2_C/PC3_C analog switch.
    "34": "MIC_CLK_SRC", "35": "MIC_DATA",
    # USB and debug
    "70": "USB_DM", "71": "USB_DP", "72": "SWDIO", "76": "SWCLK", "89": "SWO",
}
for _n in range(1, 101):
    MCU_NETS.setdefault(str(_n), "NC")

MCU = dict(file="mcu.kicad_sch", title="MCU: STM32H723", paper="A2", parts=[
    dict(ref="U5", lib="MCU_ST_STM32H7:STM32H723VGTx", value="STM32H723VGT6",
         fp="Package_QFP:LQFP-100_14x14mm_P0.5mm", nets=MCU_NETS),
    C("C20", "100n", "+3V3", "GND"), C("C21", "100n", "+3V3", "GND"), C("C22", "100n", "+3V3", "GND"),
    C("C23", "100n", "+3V3", "GND"), C("C24", "100n", "+3V3", "GND"), C("C25", "4.7u", "+3V3", "GND", fp=C0603),
    C("C26", "2.2u", "VCAP_CORE", "GND", fp=C0603), C("C27", "2.2u", "VCAP_CORE", "GND", fp=C0603),
    C("C28", "100n", "+3V3A", "GND"),
    C("C29", "100n", "NRST", "GND"),
    R("R20", "10k", "BOOT0", "GND"),
    dict(ref="Y1", lib="Device:Crystal_GND24", value="25MHz", fp="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
         nets={"1": "HSE_IN", "3": "HSE_OUT", "2": "GND", "4": "GND"}),
    C("C30", "12p", "HSE_IN", "GND"), C("C31", "12p", "HSE_OUT", "GND"),
    dict(ref="Y2", lib="Device:Crystal", value="32.768kHz", fp="Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm",
         nets={"1": "LSE_IN", "2": "LSE_OUT"}),
    C("C32", "6.8p", "LSE_IN", "GND"), C("C33", "6.8p", "LSE_OUT", "GND"),
    # RTC and GNSS backup: small supercap kept charged from 3.3 V
    dict(ref="D20", lib="Device:D_Schottky", value="BAT54J", fp="Diode_SMD:D_SOD-323F",
         nets={"2": "+3V3", "1": "BKP_CHG"}),
    R("R21", "1k", "BKP_CHG", "VBAT_BKP"),
    dict(ref="C34", lib="Device:C_Polarized", value="0.1F 3.3V", fp="Capacitor_SMD:CP_Elec_5x5.4",
         nets={"1": "VBAT_BKP", "2": "GND"}),
    FLAG("#FLG20", "VBAT_BKP"), FLAG("#FLG21", "VCAP_CORE"),
    # SWD on a Tag-Connect TC2030-NL pad set (ARM Cortex pin-out of the TC2030-CTX cable): no part height under the display
    dict(ref="J20", lib="Connector_Generic:Conn_02x03_Odd_Even", value="SWD (TC2030)", fp="Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
         nets={"1": "+3V3", "2": "SWDIO", "3": "NRST", "4": "SWCLK", "5": "GND", "6": "SWO"}, dnp=False),
    R("R22", "1k", "LED_STATUS", "LED_A"),
    dict(ref="D21", lib="Device:LED", value="green", fp="LED_SMD:LED_0603_1608Metric",
         nets={"2": "LED_A", "1": "GND"}),
], notes=[
    "Pin map from the spec, step 2. All data-ready lines and GNSS PPS are captured on TIM2.",
])

# ---------------------------------------------------------------- sensors
SENSORS = dict(file="sensors.kicad_sch", title="Sensors: IMU, barometer, magnetometer, humidity, microphone", parts=[
    dict(ref="U6", lib="logger:ICM-45686", value="ICM-45686", fp="Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
         nets={"8": "+3V3", "5": "+3V3", "6": "GND",
               "12": "IMU_CS", "13": "IMU_SCK", "14": "IMU_MOSI", "1": "IMU_MISO",
               "4": "IMU_INT1", "9": "IMU_INT2", "2": "NC", "3": "NC", "7": "NC", "10": "NC", "11": "NC"}),
    C("C40", "100n", "+3V3", "GND"), C("C41", "100n", "+3V3", "GND"),
    dict(ref="U7", lib="logger:BMP390", value="BMP390", fp="logger:Bosch_LGA-10_2.0x2.0mm",
         nets={"10": "+3V3", "1": "+3V3", "6": "BARO_CS", "2": "BARO_SCK", "4": "BARO_MOSI", "5": "BARO_MISO",
               "3": "GND", "8": "GND", "9": "GND", "7": "BARO_INT"}),
    C("C42", "100n", "+3V3", "GND"), C("C43", "100n", "+3V3", "GND"),
    # BMM350 core runs at 1.8 V; I/O at 3.3 V
    dict(ref="U8", lib="Regulator_Linear:AP2112K-1.8", value="AP2112K-1.8", fp="Package_TO_SOT_SMD:SOT-23-5",
         nets={"1": "+3V3", "2": "GND", "3": "+3V3", "5": "+1V8_MAG"}),
    C("C44", "1u", "+3V3", "GND"), C("C45", "1u", "+1V8_MAG", "GND"),
    dict(ref="U9", lib="logger:BMM350", value="BMM350", fp="logger:Bosch_WLCSP-9_1.28x1.28mm_P0.4mm",
         nets={"C1": "+1V8_MAG", "B3": "+3V3", "A3": "I2C1_SCL", "A2": "I2C1_SDA", "B2": "GND",
               "B1": "GND", "C3": "GND", "A1": "MAG_INT", "C2": "MAG_CRST"}),
    C("C46", "100n", "+1V8_MAG", "GND"), C("C47", "100n", "+3V3", "GND"),
    C("C48", "2.2u X7R", "MAG_CRST", "GND", fp=C0603),   # BMM350 CRST: low-ESL, non-magnetic MLCC, close to C2
    R("R40", "2.2k", "I2C1_SCL", "+3V3"), R("R41", "2.2k", "I2C1_SDA", "+3V3"),
    FLAG("#FLG40", "+1V8_MAG"),
    # Temperature and humidity for density altitude: Sensirion SHT40 (I2C 0x44) at the left board edge, in the case's
    # vented side chamber. No slot (the board takes repeated g loads): a copper-free island and thin traces keep the
    # board's heat away.
    dict(ref="U17", lib="Sensor_Humidity:SHT4x", value="SHT40-AD1B", mpn="SHT40-AD1B-R3",
         fp="Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad",
         nets={"1": "I2C1_SDA", "2": "I2C1_SCL", "3": "+3V3", "4": "GND"}),
    C("C49", "100n", "+3V3", "GND"),
    # PDM microphone: ST MP34DT06J (JLCPCB C503097), top port, on the front next to the SHT40 so one chamber vented
    # through the case's left wall serves both (no board hole, no part on the back). AOP 122.5 dB SPL. LR to GND: left
    # channel, the mic drives DOUT while CLK is low.
    dict(ref="MK1", lib="logger:MP34DT06J", value="MP34DT06J", mpn="MP34DT06JTR",
         fp="logger:ST_HCLGA-4_3x4mm_MP34DT06J",
         nets={"1": "+3V3", "2": "GND", "3": "MIC_CLK", "4": "MIC_DATA", "5": "GND", "6": "GND", "7": "GND", "8": "GND"}),
    C("C53", "100n", "+3V3", "GND"), R("R42", "33R", "MIC_CLK_SRC", "MIC_CLK"),
], notes=[
    "IMU: TDK ICM-45686 on SPI. RESV pins 2, 3, 7, 10, 11 left open (datasheet: NC, VDDIO or GND); keep their internal pull-ups on.",
    "INT2 can also take an external clock (CLKIN) or FSYNC if the firmware wants it.",
    "BMM350 I2C address 0x14 (ADSEL low). BYPASS (C3) to GND, CRST 2.2 uF to GND per the datasheet pin table.",
    "SHT40-AD1B: I2C address 0x44, shares I2C1 and its 2.2k pull-ups with the BMM350. Centre pad left unsoldered (Sensirion allows it).",
    "MP34DT06J (ST DS12698 rev 3): PDM, 1.6-3.6 V, clock 1.2-3.25 MHz from DFSDM1_CKOUT (PB0) through 33R into DFSDM1 channel 1 (PB1). LR to GND = left channel: DOUT valid while CLK is low (table 6), so DFSDM samples on the rising edge.",
])

# ---------------------------------------------------------------- GNSS
GNSS = dict(file="gnss.kicad_sch", title="GNSS: NEO-M9N", parts=[
    dict(ref="U10", lib="logger:NEO-M9N", value="NEO-M9N", fp="RF_GPS:ublox_NEO", mpn="NEO-M9N-00B",
         nets={"23": "+3V3_GNSS", "22": "VBAT_BKP", "21": "GNSS_RXD", "20": "GNSS_TXD", "8": "GNSS_RESET_N",
               "1": "GNSS_SAFEBOOT_N", "4": "NC", "10": "GND", "12": "GND", "13": "GND", "24": "GND",
               "11": "GNSS_RF_IN", "9": "GNSS_VCC_RF", "14": "NC", "3": "GNSS_PPS", "7": "GND", "2": "NC", "5": "NC", "6": "NC", "18": "NC", "19": "NC"}),
    dict(ref="FB2", lib="Device:FerriteBead_Small", value="600R@100MHz", fp="Inductor_SMD:L_0603_1608Metric",
         nets={"1": "+3V3", "2": "+3V3_GNSS"}),
    C("C50", "10u", "+3V3_GNSS", "GND", fp=C0805), C("C51", "100n", "+3V3_GNSS", "GND"),
    # Active antenna feed per u-blox NEO-F9P integration manual 4.4.4.3 (fig. 42, table 36): VCC_RF -> 10R current
    # limit -> ferrite -> 100n filter -> 47 nH bias-T inductor (>500 ohm across 1-1.8 GHz, so L5 too) onto RF_IN.
    # The DC block is inside the module (u-blox NEO data sheets).
    R("R50", "10R", "GNSS_VCC_RF", "ANT_BIAS_R"),
    dict(ref="FB51", lib="Device:FerriteBead_Small", value="BLM15HB121SH1", fp="Inductor_SMD:L_0402_1005Metric",
         mpn="BLM15HB121SH1D", nets={"1": "ANT_BIAS_R", "2": "ANT_BIAS"}),
    dict(ref="L50", lib="Device:L", value="47n", fp="Inductor_SMD:L_0402_1005Metric", mpn="LQG15HS47NJ02D",
         nets={"1": "ANT_BIAS", "2": "GNSS_RF_IN"}),
    C("C52", "100n", "ANT_BIAS", "GND"),
    dict(ref="J50", lib="Connector:Conn_Coaxial", value="U.FL", fp="Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical",
         nets={"1": "GNSS_RF_IN", "2": "GND"}),
    dict(ref="TP50", lib="Connector:TestPoint", value="SAFEBOOT", fp="TestPoint:TestPoint_Pad_D1.0mm",
         nets={"1": "GNSS_SAFEBOOT_N"}),
    FLAG("#FLG50", "+3V3_GNSS"), FLAG("#FLG51", "GNSS_VCC_RF"),
], notes=[
    "RF_IN trace: 50 ohm coplanar waveguide, as short as possible.",
    "VDD_USB (pin 7) to GND: USB unused (u-blox: connect V_USB to ground when USB is not used). D_SEL open = UART1 + I2C.",
    "Standard NEO footprint: the NEO-F9P (L1/L5 RTK) drops in with the same pins and wiring."
])

# ---------------------------------------------------------------- IO
IO = dict(file="io.kicad_sch", title="IO: log flash, microSD, memory LCD, keys, camera sync", parts=[
    # Main flight log: 4 Gbit (512 MB) SPI NAND on OCTOSPI1 (quad), 3.3 V, -40 to 85 C. Stocked at JLCPCB (C41420154). The microSD is the backup copy, update and export path.
    dict(ref="U12", lib="logger:GD5F4GM8UE", value="GD5F4GM8UEYIG", mpn="GD5F4GM8UEYIG", fp="Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm",
         nets={"1": "FLASH_CS", "2": "FLASH_IO1", "3": "FLASH_IO2", "4": "GND", "5": "FLASH_IO0", "6": "FLASH_CLK",
               "7": "FLASH_IO3", "8": "+3V3", "9": "GND"}),
    C("C90", "100n", "+3V3", "GND"), C("C91", "1u", "+3V3", "GND"),
    # CS high and WP/HOLD inactive while the MCU is in reset or before OCTOSPI takes the pins
    R("R90", "10k", "FLASH_CS", "+3V3"), R("R91", "10k", "FLASH_IO2", "+3V3"), R("R92", "10k", "FLASH_IO3", "+3V3"),
    dict(ref="J60", lib="Connector:Micro_SD_Card_Det1", value="microSD", fp="Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5",
         nets={"1": "SD_D2", "2": "SD_D3", "3": "SD_CMD", "4": "+3V3", "5": "SD_CLK", "6": "GND",
               "7": "SD_D0", "8": "SD_D1", "9": "SD_DET", "10": "GND"}),
    R("R60", "47k", "SD_CMD", "+3V3"), R("R61", "47k", "SD_D0", "+3V3"), R("R62", "47k", "SD_D1", "+3V3"),
    R("R63", "47k", "SD_D2", "+3V3"), R("R64", "47k", "SD_D3", "+3V3"), R("R65", "100k", "SD_DET", "+3V3"),
    C("C60", "10u", "+3V3", "GND", fp=C0805), C("C61", "100n", "+3V3", "GND"),
    # Sharp LS027B7DH01 2.7" memory LCD (400 x 240, -20 to +70 C) on Sharp's recommended socket, Panasonic Y5B AYF531035
    # (10 pins, 0.5 mm, top and bottom contact). Pin table from Sharp LD-28305A table 4-1; EXTMODE high = VCOM from EXTCOMIN.
    dict(ref="J61", lib="Connector_Generic:Conn_01x10", value="LS027B7DH01", mpn="AYF531035",
         fp="logger:Panasonic_AYF531035_1x10-1MP_P0.50mm_Horizontal",
         nets={"1": "SPI4_SCK", "2": "SPI4_MOSI", "3": "LCD_SCS", "4": "LCD_EXTCOMIN", "5": "LCD_DISP",
               "6": "+5V_LCD", "7": "+5V_LCD", "8": "+5V_LCD", "9": "GND", "10": "GND"}),
    C("C64", "1u", "+5V_LCD", "GND"), C("C65", "100n", "+5V_LCD", "GND"),
    # SCS and DISP held low (panel deselected and blank) until firmware drives them
    R("R67", "100k", "LCD_SCS", "GND"), R("R72", "100k", "LCD_DISP", "GND"),
    # 5 V for the panel (VDD/VDDA 4.8-5.5 V, 50-350 uW): TPS61222 fixed 5 V boost from 3.3 V, as on TI's BOOSTXL-SHARP128.
    # FB to VOUT for the fixed version, EN tied high, 4.7 uH and 10 uF in/out per the datasheet (SLVS776B section 11.2).
    dict(ref="U16", lib="Regulator_Switching:TPS61222DCK", value="TPS61222", mpn="TPS61222DCKR", fp="Package_TO_SOT_SMD:Texas_R-PDSO-G6",
         nets={"1": "+3V3", "2": "+5V_LCD", "3": "GND", "4": "+5V_LCD", "5": "LCD_SW", "6": "+3V3"}),
    dict(ref="L60", lib="Device:L", value="4.7u", fp="Inductor_SMD:L_Changjiang_FNR4020S", mpn="FNR4020S4R7MT",
         nets={"1": "+3V3", "2": "LCD_SW"}),
    FLAG("#FLG60", "LCD_SW"),   # KiCad's symbol calls the L pin a power input; the inductor drives it
    C("C62", "10u", "+3V3", "GND", fp=C0603), C("C63", "10u", "+5V_LCD", "GND", fp=C0603),
    # Keys: three Kailh Choc V1 tactile switches (brown, CPG135001D02) with printed caps, pressed from the front. The board
    # carries only the Kailh hotswap sockets (CPG135001S30, JLCPCB C5333465, SMD on the back); the switches are pressed in at
    # case assembly and the case front holds them as the plate.
    # OK is also the power key: it pulls PWR_KEY to VSYS (latch on the power sheet) and is read on PWR_BTN.
    dict(ref="SW1", lib="Switch:SW_Push", value="UP", mpn="CPG135001S30",
         fp="logger:SW_Kailh_Choc_V1_Hotswap", nets={"1": "BTN_UP", "2": "GND"}),
    dict(ref="SW2", lib="Switch:SW_Push", value="OK / PWR", mpn="CPG135001S30",
         fp="logger:SW_Kailh_Choc_V1_Hotswap", nets={"1": "VSYS", "2": "PWR_KEY"}),
    dict(ref="SW3", lib="Switch:SW_Push", value="DOWN", mpn="CPG135001S30",
         fp="logger:SW_Kailh_Choc_V1_Hotswap", nets={"1": "BTN_DOWN", "2": "GND"}),
    R("R66", "100R", "CAM_SYNC", "CAM_SYNC_OUT"),
    # Camera sync out and the pilot's marker button share one socket: 1 sync out, 2 GND, 3 marker (button to GND).
    # JST SUR, 0.8 mm pitch, side entry, 1.75 mm high (JLCPCB C265338): the lead stays inside the case.
    dict(ref="J62", lib="Connector_Generic:Conn_01x03", value="CAM / MARK", mpn="SM03B-SURS-TF(LF)(SN)",
         fp="logger:JST_SUR_SM03B-SURS-TF_1x03-1MP_P0.80mm_Horizontal",
         nets={"1": "CAM_SYNC_OUT", "2": "GND", "3": "MARKER_IN"}),
    R("R68", "1k", "MARKER_IN", "MARKER"), R("R69", "10k", "MARKER", "+3V3"), C("C72", "100n", "MARKER", "GND"),
    # Expansion: Qwiic / STEMMA QT pin order (1 GND, 2 3V3, 3 SDA, 4 SCL) on I2C4, e.g. for an airspeed sensor
    dict(ref="J63", lib="Connector_Generic:Conn_01x04", value="I2C EXP (Qwiic)",
         fp="Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", mpn="SM04B-SRSS-TB",
         nets={"1": "GND", "2": "+3V3_EXP", "3": "EXP_SDA", "4": "EXP_SCL"}),
    dict(ref="F1", lib="Device:Polyfuse_Small", value="PTC 100mA", fp="Fuse:Fuse_0603_1608Metric",
         nets={"1": "+3V3", "2": "+3V3_EXP"}),
    R("R70", "2.2k", "EXP_SDA", "+3V3"), R("R71", "2.2k", "EXP_SCL", "+3V3"),
    # ESD on the outside-world lines of J62 and J63 (IEC 61000-4-2 / DO-160 section 25); VP also clamps the fused rail
    dict(ref="U14", lib="Power_Protection:SRV05-4", value="SRV05-4", mpn="SRV05-4", fp="Package_TO_SOT_SMD:SOT-23-6",
         nets={"1": "CAM_SYNC_OUT", "2": "GND", "3": "MARKER_IN", "4": "EXP_SDA", "5": "+3V3_EXP", "6": "EXP_SCL"}),
], notes=[
    "LCD: Sharp LS027B7DH01, 2.7 in, 400 x 240, reflective, -20 to +70 C. SPI write-only, LSB first, SCS active high, up to 1-2 MHz (LD-28305A table 6-3-1).",
    "LCD VCOM: EXTMODE high, TIM15_CH1 toggles EXTCOMIN at 1-20 Hz, below the frame rate (remark 6-3). Logic from 3.3 V (VIH min 2.7 V).",
    "LCD 5 V from a TPS61222 boost (4.82-5.13 V); the panel draws 50-350 uW. EN low would still leave 3.3 V on VOUT (body diode), so EN stays high.",
    "LCD FPC: 9.5 mm wide, about 12.9 mm long, centred on the panel; it folds 180 deg under the glass (never toward the front polariser) into J61.",
    "Keys: three Kailh Choc V1 tactile switches (3 mm travel, 1.5 mm to actuation, 50 gf) with printed caps, in SMD hotswap sockets on the back; the case front is the switch plate (13.8 mm square cut-outs). UP / DOWN use the MCU's internal pull-ups; debounce in firmware.",
    "OK doubles as the power key (latch on the power sheet). While logging, any key is a marker; the external marker on J62 stays.",
    "Marker input: 1k series, 10k pull-up, 100 nF (1 ms) against cable noise; EXTI15 on PA15, timestamped from TIM2.",
    "Expansion 3V3 goes through a 100 mA PTC so a shorted cable cannot pull down the logger.",
])

# ---------------------------------------------------------------- radio
RADIO = dict(file="radio.kicad_sch", title="Radio: ESP32-C6 (Wi-Fi 6, BLE 5)", parts=[
    dict(ref="U11", lib="logger:ESP32-C6-MINI-1", value="ESP32-C6-MINI-1-N4", fp="logger:ESP32-C6-MINI-1",
         nets={"3": "+3V3", "8": "RADIO_EN", "23": "RADIO_BOOT", "22": "RADIO_IO8", "20": "RADIO_IO15",
               "31": "RADIO_TXD_ESP", "30": "RADIO_RXD", "18": "RADIO_USB_DM", "17": "RADIO_USB_DP",
               "15": "SPI4_SCK", "16": "SPI4_MOSI", "5": "RADIO_MISO", "24": "RADIO_CS", "25": "RADIO_IRQ",
               "9": "NC", "10": "NC", "12": "NC", "13": "NC", "6": "NC", "19": "NC",
               "26": "NC", "27": "NC", "28": "NC", "29": "NC",
               **{n: "GND" for n in ["1", "2", "11", "14"] + [str(i) for i in range(36, 54)]},
               **{n: "NC" for n in ["4", "7", "21", "32", "33", "34", "35"]}}),
    C("C80", "22u", "+3V3", "GND", fp=C0805), C("C81", "100n", "+3V3", "GND"),
    R("R80", "10k", "RADIO_EN", "GND"), C("C82", "100n", "RADIO_EN", "GND"),
    # 1k from the MCU: limits the GPIO charging current into C82; EN still sees 3.0 V (VIH 0.75 x 3V3 = 2.5 V)
    R("R84", "1k", "RADIO_EN_MCU", "RADIO_EN"),
    # Espressif guidelines 1.3.7: series resistor on U0TXD, close to the module
    R("R85", "499R", "RADIO_TXD_ESP", "RADIO_TXD"),
    R("R81", "10k", "RADIO_BOOT", "+3V3"), R("R82", "10k", "RADIO_IO8", "+3V3"), R("R83", "10k", "RADIO_IO15", "+3V3"),
    dict(ref="TP80", lib="Connector:TestPoint", value="USB_D-", fp="TestPoint:TestPoint_Pad_D1.0mm",
         nets={"1": "RADIO_USB_DM"}),
    dict(ref="TP81", lib="Connector:TestPoint", value="USB_D+", fp="TestPoint:TestPoint_Pad_D1.0mm",
         nets={"1": "RADIO_USB_DP"}),
], notes=[
    "ESP32-C6-MINI-1 pin table: Espressif datasheet v1.5, table 3-1. Footprint from Espressif's KiCad library.",
    "EN is pulled low: the radio stays off until the MCU turns it on (through R84). Set RADIO_BOOT high before EN rises and hold it 3 ms.",
    "Strapping: IO9 high = boot from flash; the MCU pulls RADIO_BOOT low with EN to enter the UART bootloader.",
    "IO8 must be high for download mode; IO15 must not float. Data: SPI slave on SPI4 (up to 40 MHz).",
    "Peak TX current about 0.38 A from +3V3. Antenna over the board edge, no copper under it; case wall there must be plastic.",
    "USB_D-/D+ test pads: USB-Serial-JTAG for bench debugging of the radio firmware.",
])

SHEETS = [POWER, MCU, SENSORS, GNSS, IO, RADIO]
