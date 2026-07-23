#!/usr/bin/env python3
"""Generate the value-bearing PB-100 power, telemetry, and output sheets.

The top-level hierarchy, JPB1, CAN1 safety, and fog-switch entry sheets remain
separate reviewed sources.  This generator owns the four sheets that were
previously electrical scaffolds so schematic/netlist and PCB parity can be
checked deterministically.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from generate_lb_fb_schematics import Component, Schematic, c, passive


ROOT = Path(__file__).resolve().parents[1]
SHEET_DIR = ROOT / "hardware" / "power-board" / "PB-100" / "kicad" / "sheets"
SYMBOL_LIBRARY = ROOT / "hardware" / "power-board" / "PB-100" / "kicad" / "lib" / "PB100Gen.kicad_sym"
FP = "PB100:"

TI_TPS4811 = "https://www.ti.com/lit/ds/symlink/tps4811-q1.pdf"
TI_LM74930 = "https://www.ti.com/lit/ds/symlink/lm74930-q1.pdf"
TI_LM5164 = "https://www.ti.com/lit/ds/symlink/lm5164-q1.pdf"
TI_INA228 = "https://www.ti.com/lit/ds/symlink/ina228-q1.pdf"
INFINEON_80V = (
    "https://www.infineon.com/assets/row/public/documents/10/49/"
    "infineon-iaut300n08s5n012-datasheet-en.pdf"
)
INFINEON_150V = (
    "https://www.infineon.com/assets/row/public/documents/10/49/"
    "infineon-iautn15s6n025-datasheet-en.pdf"
)
TDK_NTC = (
    "https://product.tdk.com/en/search/sensor/ntc/chip-ntc-thermistor/"
    "info?part_no=NTCGS103JF103FT8"
)


def pb_sheet(
    title: str,
    notes: str,
    *,
    paper: str,
    identity: str,
) -> Schematic:
    return Schematic(
        "PB-100",
        title,
        notes,
        paper=paper,
        identity=identity,
        library_name="PB100Gen",
        symbol_prefix="PB100G",
    )


def two_pin(
    ref: str,
    value: str,
    footprint: str,
    net1: str,
    net2: str,
    datasheet: str = "",
    *,
    dnp: bool = False,
    on_board: bool = True,
) -> Component:
    return c(
        ref,
        value,
        footprint,
        datasheet,
        [
            ("1", "1", net1, "passive"),
            ("2", "2", net2, "passive"),
        ],
        dnp=dnp,
        on_board=on_board,
    )


def resistor(
    ref: str,
    value: str,
    net1: str,
    net2: str,
    *,
    dnp: bool = False,
    footprint: str = f"{FP}R0603",
) -> Component:
    return two_pin(ref, value, footprint, net1, net2, dnp=dnp)


def capacitor(
    ref: str,
    value: str,
    net1: str,
    net2: str,
    *,
    dnp: bool = False,
    footprint: str = f"{FP}C0603",
) -> Component:
    return two_pin(ref, value, footprint, net1, net2, dnp=dnp)


def test_point(ref: str, net: str) -> Component:
    return c(
        ref,
        f"TEST {net}",
        f"{FP}TestPoint_SMD_1.5mm",
        "../PB-100-test-point-plan.csv",
        [("1", net, net, "passive")],
        in_bom=False,
    )


def toll_mosfet(ref: str, value: str, gate: str, source: str, drain: str, datasheet: str) -> Component:
    pins = [("1", "G", gate, "passive")]
    pins.extend((str(number), "S", source, "passive") for number in range(2, 9))
    pins.append(("Tab", "D", drain, "passive"))
    return c(ref, value, f"{FP}PG-HSOF-8-1_TOLL_Infineon", datasheet, pins)


def build_input_protection() -> Schematic:
    schematic = pb_sheet(
        "PB-100 Input Protection and Total-Current Monitor — Rev.1 EVT",
        (
            "Work queue: CAP-INP. ADR-0018/0019/0020 implementation. The raw-side 150 V Q2 and protected-side "
            "80 V Q1 retain the reviewed LM74930-Q1 common-source hard-cutoff topology. "
            "RSH1 is a 0.5 mOhm four-terminal shunt. JISO1 is the mandatory removable "
            "input-stage isolation link; opening it prevents VBAT_PROT from energizing "
            "the remainder of the board. D1 is a legacy DNP comparison site and is never "
            "credited as the load-dump energy sink. Rev.1 EVT only; Q2 production "
            "qualification and routed-loop evidence remain open."
        ),
        paper="A2",
        identity="PB-100-input-protection",
    )

    # Garage-owned connector shell/fuse remain off-board. JIN1 is the actual
    # factory PCB pigtail termination.
    schematic.add(
        c(
            "J1",
            "INPUT_CONNECTOR_CLASS_PRELIM (OFF-BOARD)",
            "",
            "../PB-100-garage-connector-fuse-plan.md",
            [("1", "VBAT_RAW", "VBAT_RAW", "passive"), ("2", "GND", "GND", "passive")],
            on_board=False,
        )
    )
    schematic.add(
        c(
            "JIN1",
            "40A PCB PIGTAIL TO NEAR-BATTERY 50A FUSE",
            f"{FP}POWER_PIGTAIL_2xTH_40A",
            "../PB-100-garage-connector-fuse-plan.md",
            [("1", "VBAT_RAW", "VBAT_RAW", "passive"), ("2", "GND", "GND", "passive")],
        )
    )
    schematic.add(
        c(
            "D1",
            "SM8S33AHM3/I",
            f"{FP}DO-218AC_Vishay_SM8S",
            "https://www.vishay.com/docs/88392/sm8s.pdf",
            [("1", "K", "VBAT_RAW", "passive"), ("2", "A", "GND", "passive")],
            dnp=True,
        )
    )
    schematic.add(toll_mosfet("Q2", "IAUTN15S6N025ATMA1", "Q2_GATE", "INPUT_COMMON_SOURCE", "VBAT_RAW", INFINEON_150V))
    schematic.add(toll_mosfet("Q1", "IAUT300N08S5N012ATMA2", "Q1_GATE", "INPUT_COMMON_SOURCE", "VBAT_REV_PROT", INFINEON_80V))

    u1_pins = [
        ("1", "DGATE", "Q1_DGATE", "output"),
        ("2", "A", "INPUT_COMMON_SOURCE", "input"),
        ("3", "SW", None, "no_connect"),
        ("4", "UVLO", "LM74930_VS", "input"),
        ("5", "OV", "LM74930_OV", "input"),
        ("6", "EN", "LM74930_VS", "input"),
        ("7", "MODE", "LM74930_VS", "input"),
        ("8", "N.C.", None, "no_connect"),
        ("9", "TMR", "GND", "input"),
        ("10", "IMON", None, "no_connect"),
        ("11", "ILIM", "GND", "input"),
        ("12", "FLT", "INPUT_PROT_FAULT_N", "open_collector"),
        ("13", "GND", "GND", "passive"),
        ("14", "HGATE", "Q2_HGATE", "output"),
        ("15", "OUT", "INPUT_COMMON_SOURCE", "input"),
        ("16", "OVCLAMP", "GND", "input"),
        ("17", "N.C.", None, "no_connect"),
        ("18", "ISCP", "VBAT_REV_PROT", "input"),
        ("19", "CS-", "VBAT_REV_PROT", "input"),
        ("20", "CS+", "VBAT_REV_PROT", "input"),
        ("21", "N.C.", None, "no_connect"),
        ("22", "VS", "LM74930_VS", "passive"),
        ("23", "CAP", "LM74930_CAP", "output"),
        ("24", "C", "VBAT_REV_PROT", "input"),
        ("25", "RTN", None, "no_connect"),
    ]
    schematic.add(
        c(
            "U1",
            "LM74930QRGERQ1",
            f"{FP}VQFN-24_RGE_4x4mm_P0.5mm_EP2.4mm",
            TI_LM74930,
            u1_pins,
        )
    )

    # LM74930 local supply, threshold and replaceable gate/damping hooks.
    schematic.add(resistor("R3", "42.2k 1%", "VBAT_RAW", "LM74930_OV_TOP_MID"))
    schematic.add(resistor("R4", "42.2k 1%", "LM74930_OV_TOP_MID", "LM74930_OV"))
    schematic.add(resistor("R5", "1.00k 1%", "LM74930_OV", "GND"))
    schematic.add(resistor("R6", "10k 1%", "VBAT_RAW", "LM74930_VS"))
    schematic.add(resistor("R7", "0R REPLACEABLE Q1 GATE", "Q1_DGATE", "Q1_GATE"))
    schematic.add(resistor("R8", "0R REPLACEABLE Q2 GATE", "Q2_HGATE", "Q2_GATE"))
    schematic.add(capacitor("CCAP1", "100nF 25V X7R", "LM74930_CAP", "LM74930_VS"))
    schematic.add(
        capacitor(
            "CVS1",
            "CGA6N3X7R2A225M230AE 2.2uF 100V X7R; Ceff>=1uF@56V",
            "LM74930_VS",
            "GND",
            footprint=f"{FP}C1210",
        )
    )
    schematic.add(
        two_pin(
            "DZVS1",
            "56V AUTOMOTIVE ZENER",
            f"{FP}SOD-123F",
            "LM74930_VS",
            "GND",
        )
    )
    schematic.add(resistor("RSN1", "100R DNP Q1 DAMPING", "VBAT_REV_PROT", "Q1_SNUB", dnp=True))
    schematic.add(capacitor("CSN1", "1nF 100V C0G DNP", "Q1_SNUB", "INPUT_COMMON_SOURCE", dnp=True))
    schematic.add(resistor("RSN2", "100R DNP Q2 DAMPING", "VBAT_RAW", "Q2_SNUB", dnp=True))
    schematic.add(capacitor("CSN2", "1nF 200V C0G DNP", "Q2_SNUB", "INPUT_COMMON_SOURCE", dnp=True))

    schematic.add(
        c(
            "RSH1",
            "CSS4J-4026R-L500F 0.5mR 5W FOUR-TERMINAL",
            f"{FP}CSS4J-4026_Bourns",
            "https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf",
            [
                ("1", "PWR_IN", "VBAT_REV_PROT", "passive"),
                ("2", "PWR_OUT", "VBAT_PROT_PRELINK", "passive"),
                ("3", "SNS_IN", "IIN_SHUNT_HI", "passive"),
                ("4", "SNS_OUT", "IIN_SHUNT_LO", "passive"),
            ],
        )
    )
    schematic.add(
        c(
            "JISO1",
            "EVT INPUT-STAGE ISOLATION LINK — FITTED FOR NORMAL EVT",
            f"{FP}EVT_INPUT_ISOLATION_LINK_M4",
            "../PB-100-layout-progress.md",
            [
                ("1", "INPUT_STAGE", "VBAT_PROT_PRELINK", "passive"),
                ("2", "BOARD_LOADS", "VBAT_PROT", "passive"),
            ],
        )
    )

    schematic.add(
        c(
            "U2",
            "INA228AQDGSRQ1 TOTAL CURRENT MONITOR",
            f"{FP}VSSOP-10_L3.0-W3.0-P0.50-LS4.9-BL",
            TI_INA228,
            [
                ("1", "A1", "GND", "input"),
                ("2", "A0", "GND", "input"),
                ("3", "ALERT", "PB_I2C_INT", "open_collector"),
                ("4", "SDA", "PB_I2C_SDA", "bidirectional"),
                ("5", "SCL", "PB_I2C_SCL", "input"),
                ("6", "VS", "PB_5V_OUT", "passive"),
                ("7", "GND", "GND", "passive"),
                ("8", "VBUS", "IIN_VBUS_FILTERED", "input"),
                ("9", "IN-", "IIN_MON_N", "input"),
                ("10", "IN+", "IIN_MON_P", "input"),
            ],
        )
    )
    schematic.add(resistor("R20", "10R 0.1% SHUNT FILTER", "IIN_SHUNT_HI", "IIN_MON_P"))
    schematic.add(resistor("R21", "10R 0.1% SHUNT FILTER", "IIN_SHUNT_LO", "IIN_MON_N"))
    schematic.add(capacitor("C20", "100nF 50V X7R DIFF", "IIN_MON_P", "IIN_MON_N"))
    schematic.add(resistor("R22", "1k 1% VBUS FILTER", "VBAT_PROT", "IIN_VBUS_FILTERED"))
    schematic.add(capacitor("C21", "1nF 100V C0G", "IIN_VBUS_FILTERED", "GND"))
    schematic.add(capacitor("C22", "100nF 16V X7R", "PB_5V_OUT", "GND"))
    schematic.add(resistor("R23", "10k PB I2C SDA PULL DNP", "LB_3V3_IO", "PB_I2C_SDA", dnp=True))
    schematic.add(resistor("R24", "10k PB I2C SCL PULL DNP", "LB_3V3_IO", "PB_I2C_SCL", dnp=True))
    schematic.add(resistor("R25", "47k PB I2C INT PULL DNP", "LB_3V3_IO", "PB_I2C_INT", dnp=True))
    schematic.add(capacitor("C23", "1nF PB I2C INT FILTER DNP", "PB_I2C_INT", "GND", dnp=True))
    schematic.add(resistor("R26", "0R INPUT FAULT AGGREGATE", "INPUT_PROT_FAULT_N", "PB_FAULT"))

    # Battery-voltage ADC path. IIN_SENSE remains a reserved connector net;
    # total current is reported over PB_I2C by U2.
    schematic.add(resistor("R27", "200k 0.1% 100V", "VBAT_PROT", "VBAT_SENSE_RAW"))
    schematic.add(resistor("R28", "10k 0.1%", "VBAT_SENSE_RAW", "GND"))
    schematic.add(resistor("R29", "1k 0.1%", "VBAT_SENSE_RAW", "VBAT_SENSE"))
    schematic.add(capacitor("C24", "10nF 50V X7R", "VBAT_SENSE", "GND"))

    for ref, net in (
        ("TP001", "GND"),
        ("TP003", "VBAT_RAW"),
        ("TP004", "VBAT_REV_PROT"),
        ("TP005", "VBAT_PROT"),
        ("TP006", "IIN_SHUNT_HI"),
        ("TP007", "IIN_SHUNT_LO"),
        ("TP008", "VBAT_SENSE"),
        ("TP009", "IIN_SENSE"),
        ("TP062", "Q1_GATE"),
        ("TP063", "Q2_GATE"),
        ("TP064", "INPUT_COMMON_SOURCE"),
        ("TP065", "VBAT_PROT_PRELINK"),
    ):
        schematic.add(test_point(ref, net))
    return schematic


def build_logic_power() -> Schematic:
    schematic = pb_sheet(
        "PB-100 Protected 5 V Logic Supply — Rev.1 EVT",
        (
            "Work queue: CAP-LOGIC. LM5164-Q1 100 V synchronous buck, 5.0 V / 1 A planning limit. The "
            "300 kHz candidate uses 41.2k RON, 47uH shielded inductor, and a "
            "type-3 ripple-injection network. Switch-node copper must remain compact; "
            "thermal vias under the exposed pad and routed EMI evidence are required "
            "at EVT-FAB-REVIEW. PB_5V_OUT never powers accessory loads."
        ),
        paper="A3",
        identity="PB-100-logic-power",
    )
    schematic.add(
        c(
            "U3",
            "LM5164QDDATQ1 100V 1A BUCK",
            f"{FP}SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL-EP2.9",
            TI_LM5164,
            [
                ("1", "GND", "GND", "passive"),
                ("2", "VIN", "VBAT_PROT", "passive"),
                ("3", "EN/UVLO", "BUCK_EN_UVLO", "input"),
                ("4", "RON", "BUCK_RON_SET", "input"),
                ("5", "FB", "BUCK_FB", "input"),
                ("6", "PGOOD", "PB_PWR_GOOD", "open_collector"),
                ("7", "BST", "BUCK_BST", "passive"),
                ("8", "SW", "BUCK_SW", "power_out"),
                ("9", "EP", "GND", "passive"),
            ],
        )
    )
    schematic.add(
        two_pin(
            "L1",
            "47uH SHIELDED AEC-Q200; Isat>=2.2A Irms>=1.2A",
            f"{FP}Inductor_12x12mm",
            "BUCK_SW",
            "PB_5V_OUT",
        )
    )
    schematic.add(capacitor("C30", "2.2uF 100V X7R", "VBAT_PROT", "GND", footprint=f"{FP}C1210"))
    schematic.add(capacitor("C31", "100nF 100V X7R", "VBAT_PROT", "GND", footprint=f"{FP}C0805"))
    schematic.add(capacitor("C32", "10uF 100V BULK CANDIDATE", "VBAT_PROT", "GND", footprint=f"{FP}C1210"))
    schematic.add(resistor("R30", "332k 1%", "VBAT_PROT", "BUCK_EN_UVLO"))
    schematic.add(resistor("R31", "100k 1%", "BUCK_EN_UVLO", "GND"))
    schematic.add(resistor("R32", "41.2k 1%", "BUCK_RON_SET", "GND"))
    schematic.add(resistor("R33", "158k 0.1%", "PB_5V_OUT", "BUCK_FB"))
    schematic.add(resistor("R34", "49.9k 0.1%", "BUCK_FB", "GND"))
    schematic.add(capacitor("C33", "2.2nF 50V X7R", "BUCK_BST", "BUCK_SW"))
    schematic.add(capacitor("C34", "22uF 10V X7R", "PB_5V_OUT", "GND", footprint=f"{FP}C1210"))
    schematic.add(capacitor("C35", "22uF 10V X7R", "PB_5V_OUT", "GND", footprint=f"{FP}C1210"))
    schematic.add(capacitor("C36", "100nF 16V X7R", "PB_5V_OUT", "GND"))
    schematic.add(resistor("R35", "47k PGOOD PULL-UP", "LB_3V3_IO", "PB_PWR_GOOD"))
    schematic.add(capacitor("C37", "10nF PGOOD FILTER DNP", "PB_PWR_GOOD", "GND", dnp=True))

    # Type-3 ripple: CA from SW to RAMP, RA from RAMP to VOUT, CB into FB.
    schematic.add(capacitor("C38", "3.3nF 100V C0G TYPE3 CA", "BUCK_SW", "BUCK_RAMP"))
    schematic.add(resistor("R36", "110k 1% TYPE3 RA", "BUCK_RAMP", "PB_5V_OUT"))
    schematic.add(capacitor("C39", "180pF 50V C0G TYPE3 CB", "BUCK_RAMP", "BUCK_FB"))
    schematic.add(resistor("R37", "100R BUCK SNUBBER DNP", "BUCK_SW", "BUCK_SNUB", dnp=True))
    schematic.add(capacitor("C40", "1nF 100V C0G DNP", "BUCK_SNUB", "GND", dnp=True))
    schematic.add(test_point("TP010", "PB_5V_OUT"))
    schematic.add(test_point("TP011", "PB_PWR_GOOD"))
    return schematic


def build_telemetry() -> Schematic:
    schematic = pb_sheet(
        "PB-100 Thermal and Board-Identity Telemetry — Rev.1 EVT",
        (
            "Work queue: CAP-TEL. Three role-independent 10k AEC-Q200 NTC dividers use 4.7k pull-ups "
            "to LB_3V3_IO, 1k ADC isolation, and 10nF filters. Sensor placement "
            "targets board reference, input/OUT2 hot zone, and medium-output/buck "
            "zone. RID1 is a physical two-resistor board-ID divider. Calibration "
            "and thresholds remain configuration-owned and require EVT measurement."
        ),
        paper="A3",
        identity="PB-100-telemetry",
    )
    thermal = (
        (1, "TEMP_PCB", 61),
        (2, "TEMP_PWR_A", 64),
        (3, "TEMP_PWR_B", 67),
    )
    for number, output_net, base in thermal:
        raw = f"{output_net}_RAW"
        schematic.add(resistor(f"R{base}", "4.7k 1% AEC-Q200", "LB_3V3_IO", raw))
        schematic.add(
            two_pin(
                f"RT{number}",
                "NTCGS103JF103FT8 10k 1% B3435 AEC-Q200",
                f"{FP}R0402",
                raw,
                "GND",
                TDK_NTC,
            )
        )
        schematic.add(resistor(f"R{base + 1}", "1k 1% ADC SERIES", raw, output_net))
        schematic.add(capacitor(f"C{base}", "10nF 50V X7R", output_net, "GND"))

    schematic.add(
        c(
            "RID1",
            "PB REV1 ID: 10k/10k 0.1% DIVIDER",
            f"{FP}Board_ID_Divider_0603x2",
            "../PB-100-b2b-interface-trace.csv",
            [
                ("1", "LB_3V3_IO", "LB_3V3_IO", "passive"),
                ("2", "PB_ID_ADC", "PB_ID_ADC", "passive"),
                ("3", "GND", "GND", "passive"),
            ],
        )
    )
    for ref, net in (
        ("TP002", "AGND"),
        ("TP012", "LB_3V3_IO"),
        ("TP013", "PB_I2C_SCL"),
        ("TP014", "PB_I2C_SDA"),
        ("TP015", "PB_I2C_INT"),
        ("TP016", "TEMP_PCB"),
        ("TP017", "TEMP_PWR_A"),
        ("TP018", "TEMP_PWR_B"),
        ("TP019", "CAN1_TX_DISABLE_CMD"),
        ("TP020", "CAN1_TX_DISABLED_STATUS"),
        ("TP021", "CAN1_RX_ROUTE"),
    ):
        schematic.add(test_point(ref, net))
    return schematic


def output_limits(channel: int) -> tuple[str, str, str]:
    if channel == 2:
        return "0.5mR", "67.3k", "2.61k"
    if channel == 1:
        return "1.0mR", "49.9k", "3.40k"
    if channel in {3, 4, 6, 7, 10}:
        return "1.5mR", "49.9k", "3.83k"
    return "3.0mR", "49.9k", "3.74k"


def add_output_channel(schematic: Schematic, channel: int) -> None:
    out = f"OUT{channel}"
    base = 1000 + channel * 100
    shunt_value, iwrn_value, iscp_value = output_limits(channel)
    drain = f"{out}_FET_DRAIN"
    switched = f"{out}_SWITCHED"
    gate = f"{out}_GATE"
    imon_raw = f"{out}_IMON_RAW"

    schematic.add(
        c(
            f"U{100 + channel}",
            "TPS48110AQDGXRQ1",
            f"{FP}VSSOP-20_19P-L5.0-W3.0-P0.50-LS5.0-BL_PE16",
            TI_TPS4811,
            [
                ("1", "EN/UVLO", f"{out}_EN_UVLO", "input"),
                ("2", "OV", f"{out}_OV", "input"),
                ("3", "INP", f"{out}_CTL", "input"),
                ("4", "FLT_T", f"{out}_FLT", "open_collector"),
                ("5", "FLT_I", f"{out}_FLT", "open_collector"),
                ("6", "GND", "GND", "passive"),
                ("7", "IMON", imon_raw, "output"),
                ("8", "IWRN", f"{out}_IWRN", "input"),
                ("9", "TMR", f"{out}_TMR", "input"),
                ("10", "DIODE", f"{out}_DIODE", "input"),
                ("11", "N.C.", None, "no_connect"),
                ("12", "BST", f"{out}_BST", "passive"),
                ("13", "SRC", switched, "input"),
                ("14", "PD", f"{out}_PD", "output"),
                ("15", "PU", f"{out}_PU", "output"),
                ("17", "CS-", f"{out}_CS_N", "input"),
                ("18", "CS+", f"{out}_CS_P", "input"),
                ("19", "ISCP", f"{out}_ISCP", "input"),
                ("20", "VS", "VBAT_PROT", "passive"),
            ],
        )
    )
    schematic.add(toll_mosfet(f"Q{100 + channel}", "IAUT300N08S5N012ATMA2", gate, switched, drain, INFINEON_80V))
    schematic.add(
        c(
            f"RSH{100 + channel}",
            f"CSS4J-4026 {shunt_value} FOUR-TERMINAL",
            f"{FP}CSS4J-4026_Bourns",
            "https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf",
            [
                ("1", "PWR_IN", "VBAT_PROT", "passive"),
                ("2", "PWR_OUT", drain, "passive"),
                ("3", "SNS_IN", f"{out}_CS_P_KELVIN", "passive"),
                ("4", "SNS_OUT", f"{out}_CS_N", "passive"),
            ],
        )
    )
    schematic.add(
        c(
            f"DCL{100 + channel}",
            "STPS40170CGY-TR 2x20A 170V COMMON-CATHODE",
            f"{FP}D2PAK_3_CommonCathode",
            "https://www.st.com/resource/en/datasheet/stps40170c-y.pdf",
            [
                ("1", "A1", "GND", "passive"),
                ("2", "K", switched, "passive"),
                ("3", "A2", "GND", "passive"),
            ],
        )
    )
    schematic.add(
        c(
            f"QT{100 + channel}",
            "MMBT3904-Q REMOTE TEMP DIODE",
            f"{FP}SOT-23-3_DBZ_TI",
            "https://assets.nexperia.com/documents/data-sheet/MMBT3904.pdf",
            [
                ("1", "E", "GND", "passive"),
                ("2", "B", f"{out}_DIODE", "passive"),
                ("3", "C", f"{out}_DIODE", "passive"),
            ],
        )
    )

    # The fuse and sealed connector are garage/harness parts. W10x is the
    # actual board pigtail pad pair that carries the switched output and return.
    schematic.add(
        c(
            f"F{100 + channel}",
            "OUTPUT_FUSE_CLASS_PRELIM (OFF-BOARD)",
            "",
            "../PB-100-garage-connector-fuse-plan.md",
            [("1", "IN", switched, "passive"), ("2", "OUT", f"{out}_FUSED", "passive")],
            on_board=False,
        )
    )
    schematic.add(
        c(
            f"J{100 + channel}",
            "OUTPUT_CONNECTOR_CLASS_PRELIM (OFF-BOARD)",
            "",
            "../PB-100-garage-connector-fuse-plan.md",
            [("1", "POS", f"{out}_FUSED", "passive"), ("2", "GND", "GND", "passive")],
            on_board=False,
        )
    )
    pigtail_footprint = "POWER_PIGTAIL_2xTH_20A"
    schematic.add(
        c(
            f"W{100 + channel}",
            f"{out} PCB PIGTAIL TO OFF-BOARD FUSE/SEALED CONNECTOR",
            f"{FP}{pigtail_footprint}",
            "../PB-100-garage-connector-fuse-plan.md",
            [("1", "POS", switched, "passive"), ("2", "GND", "GND", "passive")],
        )
    )

    # Shared 470k/103k/12.4k ladder provides separate OV and UVLO taps.
    schematic.add(resistor(f"R{base + 1}", "470k 1%", "VBAT_PROT", f"{out}_OV"))
    schematic.add(resistor(f"R{base + 2}", "103k 1%", f"{out}_OV", f"{out}_EN_UVLO"))
    schematic.add(resistor(f"R{base + 3}", "12.4k 1%", f"{out}_EN_UVLO", "GND"))
    schematic.add(resistor(f"R{base + 4}", "100R 1% RSET", f"{out}_CS_P_KELVIN", f"{out}_CS_P"))
    schematic.add(resistor(f"R{base + 5}", f"{iwrn_value} 1% RIWRN", f"{out}_IWRN", "GND"))
    schematic.add(resistor(f"R{base + 6}", f"{iscp_value} 1% RISCP", f"{out}_CS_P_KELVIN", f"{out}_ISCP"))
    schematic.add(resistor(f"R{base + 7}", "12.1k 1% RIMON", imon_raw, "GND"))
    schematic.add(resistor(f"R{base + 8}", "1k 1% IMON ADC SERIES", imon_raw, f"{out}_IMON"))
    schematic.add(resistor(f"R{base + 9}", "100k CTL DEFAULT-OFF", f"{out}_CTL", "GND"))
    schematic.add(resistor(f"R{base + 10}", "3.3R 1% REPLACEABLE PU", f"{out}_PU", gate))
    schematic.add(resistor(f"R{base + 11}", "0R REPLACEABLE PD", f"{out}_PD", gate))
    schematic.add(resistor(f"R{base + 12}", "10k FLT PULL-UP", "LB_3V3_IO", f"{out}_FLT"))
    schematic.add(resistor(f"R{base + 13}", "100R DNP DRAIN-SOURCE SNUBBER", drain, f"{out}_SNUB", dnp=True))

    schematic.add(capacitor(f"C{base + 1}", "680nF 16V X7R TMR", f"{out}_TMR", "GND"))
    schematic.add(capacitor(f"C{base + 2}", "470nF 25V X7R BST", f"{out}_BST", switched))
    schematic.add(capacitor(f"C{base + 3}", "1nF 50V C0G ISCP", f"{out}_ISCP", f"{out}_CS_N"))
    schematic.add(capacitor(f"C{base + 4}", "100nF 100V X7R VS", "VBAT_PROT", "GND", footprint=f"{FP}C0805"))
    schematic.add(capacitor(f"C{base + 5}", "10nF 50V X7R IMON", f"{out}_IMON", "GND"))
    schematic.add(capacitor(f"C{base + 6}", "1nF 25V DNP GATE-SLEW", gate, switched, dnp=True))
    schematic.add(capacitor(f"C{base + 7}", "1nF 100V C0G DNP SNUBBER", f"{out}_SNUB", switched, dnp=True))

    tp_base = 22 + (channel - 1) * 4
    schematic.add(test_point(f"TP{tp_base:03d}", f"{out}_CTL"))
    schematic.add(test_point(f"TP{tp_base + 1:03d}", f"{out}_FLT"))
    schematic.add(test_point(f"TP{tp_base + 2:03d}", f"{out}_IMON"))
    schematic.add(test_point(f"TP{tp_base + 3:03d}", switched))


def build_outputs() -> Schematic:
    schematic = pb_sheet(
        "PB-100 Generic High-Side Outputs 1–10 — Rev.1 EVT",
        (
            "Work queue: CAP-OUT-INST. Ten role-free TPS48110-Q1 channels implement the accepted 80 V TOLL "
            "architecture. Each channel includes a four-terminal shunt, 55.7 V/6.0 V "
            "OV/UVLO ladder, hardware current thresholds, timer, bootstrap, replaceable "
            "PU/PD resistors, DNP slew/snubber sites, independent remote-temperature "
            "diode, local common-cathode inductive clamp, IMON scaling/filtering, "
            "default-off CTL pulldown, and PCB pigtail lands. F10x/J10x stay off-board "
            "garage parts. Hardware net names remain OUT1..OUT10; roles are configuration."
        ),
        paper="A0",
        identity="PB-100-outputs-1-10",
    )
    for channel in range(1, 11):
        add_output_channel(schematic, channel)
    return schematic


def render_symbol_library(schematics: tuple[Schematic, ...]) -> str:
    components = [component for schematic in schematics for component in schematic.components]
    names = [schematics[0]._symbol_name(component) for component in components]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"duplicate generated symbol names: {duplicates}")
    lines = [
        "(kicad_symbol_lib",
        "  (version 20230121)",
        '  (generator "svc-pb100-schematic-generator")',
    ]
    for component in components:
        block = schematics[0]._library_symbol(component, qualified=False)
        lines.append("\n".join(line[2:] if line.startswith("  ") else line for line in block.splitlines()))
    lines.append(")")
    return "\n".join(lines) + "\n"


def generated_outputs() -> dict[Path, str]:
    schematics = (
        build_input_protection(),
        build_logic_power(),
        build_telemetry(),
        build_outputs(),
    )
    return {
        SHEET_DIR / "input-protection.kicad_sch": schematics[0].render(),
        SHEET_DIR / "logic-power.kicad_sch": schematics[1].render(),
        SHEET_DIR / "telemetry.kicad_sch": schematics[2].render(),
        SHEET_DIR / "outputs-1-10.kicad_sch": schematics[3].render(),
        SYMBOL_LIBRARY: render_symbol_library(schematics),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale: list[Path] = []
    for path, content in generated_outputs().items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        else:
            path.write_text(content, encoding="utf-8")
    for path in stale:
        print(f"stale generated file: {path.relative_to(ROOT)}")
    return 1 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
