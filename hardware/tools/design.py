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
POWER = dict(file="power.kicad_sch", title="Power: USB-C, hold-up, 3.3 V", parts=[
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
    # Ideal diode: stops the hold-up capacitors feeding back into the USB cable.
    dict(ref="U2", lib="Analog_Switch:MAX40200AUK", value="MAX40200AUK", fp="Package_TO_SOT_SMD:SOT-23-5",
         nets={"1": "VBUS", "2": "GND", "3": "VBUS", "5": "VSYS"}),
    C("C2", "10u", "VBUS", "GND", fp=C0805),
    # Hold-up: 2 x 1 F / 2.7 V in series = 0.5 F, charged through R4, discharged through D2.
    R("R4", "10R 0.5W", "VSYS", "HOLD_TOP", fp="Resistor_SMD:R_1206_3216Metric"),
    dict(ref="D2", lib="Device:D_Schottky", value="SS14", fp="Diode_SMD:D_SMA",
         nets={"2": "HOLD_TOP", "1": "VSYS"}),
    dict(ref="C3", lib="Device:C_Polarized", value="1F 2.7V", fp="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
         nets={"1": "HOLD_TOP", "2": "HOLD_MID"}),
    dict(ref="C4", lib="Device:C_Polarized", value="1F 2.7V", fp="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
         nets={"1": "HOLD_MID", "2": "GND"}),
    R("R5", "100k", "HOLD_TOP", "HOLD_MID"),
    R("R6", "100k", "HOLD_MID", "GND"),
    # 3.3 V buck, TPS62130 adjustable: Vout = 0.8 V x (1 + R7/R8) = 3.33 V
    dict(ref="U3", lib="Regulator_Switching:TPS62130", value="TPS62130", fp="Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm",
         nets={"10": "VSYS", "11": "VSYS", "12": "VSYS", "13": "VSYS",
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
    FLAG("#FLG04", "GND"), FLAG("#FLG05", "+3V3A"),
], notes=[
    "Hold-up: 0.5 F from 5 V to 3.6 V stores about 3 J; a 1 s file close at 1.5 W needs 1.5 J.",
    "PWR_FAIL_N goes low when VBUS falls below about 4.3 V, before VSYS sags.",
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
    # magnetometer on I2C1
    "92": "MAG_SCL", "93": "MAG_SDA", "95": "EXP_SCL", "96": "EXP_SDA", "77": "MARKER",
    # GNSS on USART2 (names from the module's side)
    "24": "GNSS_RXD", "25": "GNSS_TXD", "15": "GNSS_RESET_N",
    # microSD on SDMMC1
    "65": "SD_D0", "66": "SD_D1", "78": "SD_D2", "79": "SD_D3", "80": "SD_CLK", "83": "SD_CMD", "84": "SD_DET",
    # SPI4: e-paper display and the radio share SCK/MOSI, each with its own CS; MISO (PE13) is the radio's only
    "42": "SPI4_SCK", "5": "SPI4_MOSI", "3": "EPD_CS", "2": "EPD_DC", "4": "EPD_BUSY", "57": "EPD_RST",
    "43": "RADIO_MISO", "62": "RADIO_CS", "44": "RADIO_IRQ",
    # log flash on OCTOSPI1 in quad mode: CLK PB2, NCS PE11, IO0 PD11, IO1 PD12, IO2 PE2, IO3 PD13
    "36": "FLASH_CLK", "41": "FLASH_CS", "58": "FLASH_IO0", "59": "FLASH_IO1", "1": "FLASH_IO2", "60": "FLASH_IO3",
    # radio control and its UART0 (USART3: bootloader, console); names from the module's side
    "45": "RADIO_EN_MCU", "61": "RADIO_BOOT", "55": "RADIO_RXD", "56": "RADIO_TXD",
    # buttons, power fail, camera sync, LED
    "37": "BTN_1", "38": "BTN_2", "39": "BTN_3", "34": "PWR_FAIL_N", "35": "CAM_SYNC", "40": "LED_STATUS",
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
    dict(ref="J20", lib="Connector_Generic:Conn_01x06", value="SWD", fp="Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical",
         nets={"1": "+3V3", "2": "SWDIO", "3": "SWCLK", "4": "SWO", "5": "NRST", "6": "GND"}),
    R("R22", "1k", "LED_STATUS", "LED_A"),
    dict(ref="D21", lib="Device:LED", value="green", fp="LED_SMD:LED_0603_1608Metric",
         nets={"2": "LED_A", "1": "GND"}),
], notes=[
    "Pin map from the spec, step 2. All data-ready lines and GNSS PPS are captured on TIM2.",
])

# ---------------------------------------------------------------- sensors
SENSORS = dict(file="sensors.kicad_sch", title="Sensors: IMU, barometer, magnetometer", parts=[
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
         nets={"C1": "+1V8_MAG", "B3": "+3V3", "A3": "MAG_SCL", "A2": "MAG_SDA", "B2": "GND",
               "B1": "GND", "C3": "GND", "A1": "MAG_INT", "C2": "MAG_CRST"}),
    C("C46", "100n", "+1V8_MAG", "GND"), C("C47", "100n", "+3V3", "GND"),
    C("C48", "2.2u X7R", "MAG_CRST", "GND", fp=C0603),   # BMM350 CRST: low-ESL, non-magnetic MLCC, close to C2
    R("R40", "2.2k", "MAG_SCL", "+3V3"), R("R41", "2.2k", "MAG_SDA", "+3V3"),
    FLAG("#FLG40", "+1V8_MAG"),
], notes=[
    "IMU: TDK ICM-45686 on SPI. RESV pins 2, 3, 7, 10, 11 left open (datasheet: NC, VDDIO or GND); keep their internal pull-ups on.",
    "INT2 can also take an external clock (CLKIN) or FSYNC if the firmware wants it.",
    "BMM350 I2C address 0x14 (ADSEL low). BYPASS (C3) to GND, CRST 2.2 uF to GND per the datasheet pin table.",
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
IO = dict(file="io.kicad_sch", title="IO: log flash, microSD, e-paper display, buttons, camera sync", parts=[
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
    # Good Display GDEY0213B74 2.13" e-paper (SSD1680) on a 24-pin 0.5 mm FPC, 4-wire SPI (BS1 low).
    # Booster per the Good Display reference circuit (datasheet section 12): values to verify.
    dict(ref="J61", lib="Connector_Generic:Conn_01x24", value="GDEY0213B74",
         fp="Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal",
         nets={"1": "NC", "2": "EPD_GDR", "3": "EPD_RESE", "4": "NC", "5": "EPD_VSH2", "6": "NC", "7": "NC",
               "8": "GND", "9": "EPD_BUSY", "10": "EPD_RST", "11": "EPD_DC", "12": "EPD_CS",
               "13": "SPI4_SCK", "14": "SPI4_MOSI", "15": "+3V3", "16": "+3V3", "17": "GND",
               "18": "EPD_VDD", "19": "NC", "20": "EPD_VSH1", "21": "EPD_VGH", "22": "EPD_VSL",
               "23": "EPD_VGL", "24": "EPD_VCOM"}),
    C("C62", "1u", "+3V3", "GND"),
    C("C63", "1u 50V", "EPD_VDD", "GND", fp=C0603), C("C64", "1u 50V", "EPD_VSH1", "GND", fp=C0603),
    C("C65", "1u 50V", "EPD_VSH2", "GND", fp=C0603), C("C66", "1u 50V", "EPD_VGH", "GND", fp=C0603),
    C("C67", "1u 50V", "EPD_VSL", "GND", fp=C0603), C("C68", "1u 50V", "EPD_VGL", "GND", fp=C0603),
    C("C69", "1u 50V", "EPD_VCOM", "GND", fp=C0603),
    dict(ref="L60", lib="Device:L", value="47u", fp="Inductor_SMD:L_Changjiang_FNR4020S", mpn="FNR4020S470MT",
         nets={"1": "+3V3", "2": "EPD_SW"}),
    C("C70", "4.7u", "+3V3", "GND", fp=C0603),
    dict(ref="Q60", lib="Device:Q_NMOS_GSD", value="AO3400A", mpn="AO3400A", fp="Package_TO_SOT_SMD:SOT-23",
         nets={"1": "EPD_GDR", "2": "EPD_RESE", "3": "EPD_SW"}),
    R("R67", "2.2R", "EPD_RESE", "GND"),
    dict(ref="D60", lib="Device:D_Schottky", value="MBR0530", fp="Diode_SMD:D_SOD-123",
         nets={"2": "EPD_SW", "1": "EPD_VGH"}),
    C("C71", "1u 50V", "EPD_SW", "EPD_PUMP", fp=C0603),
    dict(ref="D61", lib="Device:D_Schottky", value="MBR0530", fp="Diode_SMD:D_SOD-123",
         nets={"2": "EPD_PUMP", "1": "GND"}),
    dict(ref="D62", lib="Device:D_Schottky", value="MBR0530", fp="Diode_SMD:D_SOD-123",
         nets={"2": "EPD_VGL", "1": "EPD_PUMP"}),
    dict(ref="SW1", lib="Switch:SW_Push", value="BTN_1", fp="Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2",
         nets={"1": "BTN_1", "2": "GND"}),
    dict(ref="SW2", lib="Switch:SW_Push", value="BTN_2", fp="Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2",
         nets={"1": "BTN_2", "2": "GND"}),
    dict(ref="SW3", lib="Switch:SW_Push", value="BTN_3", fp="Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2",
         nets={"1": "BTN_3", "2": "GND"}),
    R("R66", "100R", "CAM_SYNC", "CAM_SYNC_OUT"),
    # Camera sync out and the pilot's marker button share one header: 1 sync out, 2 GND, 3 marker (button to GND)
    dict(ref="J62", lib="Connector_Generic:Conn_01x03", value="CAM / MARK",
         fp="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
         nets={"1": "CAM_SYNC_OUT", "2": "GND", "3": "MARKER_IN"}),
    R("R68", "1k", "MARKER_IN", "MARKER"), R("R69", "10k", "MARKER", "+3V3"), C("C72", "100n", "MARKER", "GND"),
    # Expansion: Qwiic / STEMMA QT pin order (1 GND, 2 3V3, 3 SDA, 4 SCL) on I2C4, e.g. for an airspeed sensor
    dict(ref="J63", lib="Connector_Generic:Conn_01x04", value="I2C EXP (Qwiic)",
         fp="Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", mpn="SM04B-SRSS-TB",
         nets={"1": "GND", "2": "+3V3_EXP", "3": "EXP_SDA", "4": "EXP_SCL"}),
    dict(ref="F1", lib="Device:Polyfuse_Small", value="PTC 100mA", fp="Fuse:Fuse_0603_1608Metric",
         nets={"1": "+3V3", "2": "+3V3_EXP"}),
    R("R70", "2.2k", "EXP_SDA", "+3V3"), R("R71", "2.2k", "EXP_SCL", "+3V3"),
], notes=[
    "E-paper pin table from the GDEY0213B74 datasheet, section 5 (pin 8 is BS1, tied low for 4-wire SPI; 6/7 TSCL/TSDA and 19 VPP unused, open).",
    "Booster as Good Display's reference: 47 uH, 30 V N-MOSFET, 2.2 ohm sense, MBR0530 diodes, 1 uF 50 V on the gate and source rails.",
    "Panel operating range is 0 to 50 C: firmware skips refreshes outside it (BMP390 temperature).",
    "Buttons use the MCU's internal pull-ups; debounce in firmware.",
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
