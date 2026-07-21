#!/usr/bin/env python3
"""Generate deterministic, netlist-bearing LB-100 and FB-100 schematics.

The generated KiCad files intentionally remain schematic-only.  This script
does not create board, placement, routing, or manufacturing artifacts.
"""

from __future__ import annotations

import argparse
import csv
import uuid
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UUID_NS = uuid.UUID("476f54d8-f47f-4f41-a42c-25ee10afaf0b")
PITCH = 2.54
ERC_GRID = 1.27


def uid(*parts: object) -> str:
    return str(uuid.uuid5(UUID_NS, ":".join(str(part) for part in parts)))


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


@dataclass(frozen=True)
class Pin:
    number: str
    name: str
    net: str | None


@dataclass(frozen=True)
class Component:
    ref: str
    value: str
    footprint: str
    datasheet: str
    pins: tuple[Pin, ...]
    dnp: bool = False
    in_bom: bool = True
    on_board: bool = True


class Schematic:
    def __init__(self, board: str, title: str, notes: str, paper: str = "A0") -> None:
        self.board = board
        self.prefix = board.replace("-", "")
        self.title = title
        self.notes = notes
        self.paper = paper
        self.components: list[Component] = []

    def add(self, component: Component) -> None:
        if any(existing.ref == component.ref for existing in self.components):
            raise ValueError(f"duplicate reference {component.ref}")
        self.components.append(component)

    @staticmethod
    def _pin_layout(component: Component) -> tuple[float, list[tuple[Pin, str, float, float]]]:
        count = len(component.pins)
        per_side = (count + 1) // 2
        half_width = 17.78 if count > 30 else 12.70 if count > 12 else 7.62
        start_y = (per_side - 1) * PITCH / 2
        layout: list[tuple[Pin, str, float, float]] = []
        for index, pin in enumerate(component.pins):
            if index < per_side:
                layout.append((pin, "left", -(half_width + 5.08), start_y - index * PITCH))
            else:
                right_index = index - per_side
                layout.append((pin, "right", half_width + 5.08, start_y - right_index * PITCH))
        return half_width, layout

    def _symbol_name(self, component: Component) -> str:
        return f"{self.prefix}_{component.ref.replace('#', 'PWR_').replace('-', '_')}"

    def _library_symbol(self, component: Component, qualified: bool) -> str:
        symbol_name = self._symbol_name(component)
        if qualified:
            symbol_name = f"{self.prefix}:{symbol_name}"
        half_width, layout = self._pin_layout(component)
        per_side = (len(component.pins) + 1) // 2
        half_height = max(5.08, ((per_side - 1) * PITCH / 2) + 2.54)
        lines = [
            f'    (symbol "{symbol_name}"',
            "      (pin_names (offset 0.8))",
            f"      (in_bom {'yes' if component.in_bom else 'no'})",
            f"      (on_board {'yes' if component.on_board else 'no'})",
            f'      (property "Reference" "{esc(component.ref.rstrip("0123456789") or component.ref)}" (at 0 {half_height + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))',
            f'      (property "Value" "{esc(component.value)}" (at 0 {half_height:.2f} 0) (effects (font (size 1.27 1.27))))',
            f'      (property "Footprint" "{esc(component.footprint)}" (at 0 {-half_height - 2.54:.2f} 0) (effects (font (size 1.27 1.27)) hide))',
            f'      (property "Datasheet" "{esc(component.datasheet)}" (at 0 {-half_height - 5.08:.2f} 0) (effects (font (size 1.27 1.27)) hide))',
            f"      (rectangle (start {-half_width:.2f} {half_height:.2f}) (end {half_width:.2f} {-half_height:.2f}) (stroke (width 0.254) (type default)) (fill (type background)))",
        ]
        for pin, side, x, y in layout:
            rotation = 0 if side == "left" else 180
            lines.append(
                f'      (pin passive line (at {x:.2f} {y:.2f} {rotation}) (length 5.08) '
                f'(name "{esc(pin.name)}" (effects (font (size 1.00 1.00)))) '
                f'(number "{esc(pin.number)}" (effects (font (size 1.00 1.00)))))'
            )
        lines.append("    )")
        return "\n".join(lines)

    def _positions(self) -> dict[str, tuple[float, float]]:
        positions: dict[str, tuple[float, float]] = {}
        start_y = 101.60
        x, y = 76.20, start_y
        column_width = 109.22
        # A0 landscape is 1189 x 841 mm. Keep component extents above the
        # lower border/title-block band rather than only checking their centre.
        max_y = 774.70

        def snap(value: float) -> float:
            return round(value / ERC_GRID) * ERC_GRID

        for component in self.components:
            per_side = (len(component.pins) + 1) // 2
            height = snap(max(35.56, per_side * PITCH + 17.78))
            if y + height > max_y:
                x = snap(x + column_width)
                y = start_y
            positions[component.ref] = (x, snap(y + height / 2))
            y = snap(y + height + 12.70)
        return positions

    def render(self) -> str:
        root_uuid = uid(self.board, "root")
        lines = [
            "(kicad_sch",
            "  (version 20230121)",
            '  (generator "svc-schematic-generator")',
            f'  (uuid "{root_uuid}")',
            f'  (paper "{self.paper}")',
            "  (title_block",
            f'    (title "{esc(self.title)}")',
            '    (date "2026-07-21")',
            '    (rev "value-bearing-rev1")',
            '    (company "SVC Platform")',
            '    (comment 1 "Reviewed value-bearing schematic capture; board import remains gated.")',
            '    (comment 2 "Generated deterministically from accepted contracts and component decisions.")',
            "  )",
            "  (lib_symbols",
        ]
        for component in self.components:
            lines.append(self._library_symbol(component, qualified=True))
        lines.extend(
            [
                "  )",
                f'  (text "{esc(self.notes)}"',
                "    (at 20 20 0)",
                "    (effects (font (size 1.6 1.6)) (justify left top))",
                f'    (uuid "{uid(self.board, "notes")}")',
                "  )",
            ]
        )

        positions = self._positions()
        for component in self.components:
            x, y = positions[component.ref]
            symbol_uuid = uid(self.board, component.ref, "symbol")
            _, layout = self._pin_layout(component)
            lines.extend(
                [
                    "  (symbol",
                    f'    (lib_id "{self.prefix}:{self._symbol_name(component)}")',
                    f"    (at {x:.2f} {y:.2f} 0)",
                    "    (unit 1)",
                    "    (exclude_from_sim no)",
                    f"    (in_bom {'yes' if component.in_bom else 'no'})",
                    f"    (on_board {'yes' if component.on_board else 'no'})",
                    f"    (dnp {'yes' if component.dnp else 'no'})",
                    f'    (uuid "{symbol_uuid}")',
                    f'    (property "Reference" "{esc(component.ref)}" (at {x:.2f} {y - 10.16:.2f} 0) (effects (font (size 1.27 1.27))))',
                    f'    (property "Value" "{esc(component.value)}" (at {x:.2f} {y - 7.62:.2f} 0) (effects (font (size 1.27 1.27))))',
                    f'    (property "Footprint" "{esc(component.footprint)}" (at {x:.2f} {y + 7.62:.2f} 0) (effects (font (size 1.27 1.27)) hide))',
                    f'    (property "Datasheet" "{esc(component.datasheet)}" (at {x:.2f} {y + 10.16:.2f} 0) (effects (font (size 1.27 1.27)) hide))',
                ]
            )
            for pin in component.pins:
                lines.append(f'    (pin "{esc(pin.number)}" (uuid "{uid(self.board, component.ref, pin.number, "pin")}"))')
            lines.extend(
                [
                    "    (instances",
                    f'      (project "{self.board}"',
                    f'        (path "/{root_uuid}/{symbol_uuid}/"',
                    f'          (reference "{esc(component.ref)}")',
                    "          (unit 1)",
                    "        )",
                    "      )",
                    "    )",
                    "  )",
                ]
            )
            for pin, side, dx, dy in layout:
                # KiCad's symbol-local Y axis is inverted when an unrotated
                # library symbol is placed on a schematic sheet.
                px, py = x + dx, y - dy
                if pin.net is None:
                    lines.append(f'  (no_connect (at {px:.2f} {py:.2f}) (uuid "{uid(self.board, component.ref, pin.number, "nc")}"))')
                    continue
                justify = "right" if side == "left" else "left"
                lines.append(
                    f'  (global_label "{esc(pin.net)}" (shape bidirectional) (at {px:.2f} {py:.2f} 0) '
                    f'(fields_autoplaced) (effects (font (size 1.00 1.00)) (justify {justify})) '
                    f'(uuid "{uid(self.board, component.ref, pin.number, "label")}") '
                    f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {px:.2f} {py:.2f} 0) '
                    f'(effects (font (size 1.00 1.00)) hide)))'
                )
        lines.append(")")
        return "\n".join(lines) + "\n"

    def render_library(self) -> str:
        lines = ["(kicad_symbol_lib", "  (version 20230121)", '  (generator "svc-schematic-generator")']
        for component in self.components:
            rendered = self._library_symbol(component, qualified=False)
            lines.append("\n".join(line[2:] if line.startswith("  ") else line for line in rendered.splitlines()))
        lines.append(")")
        return "\n".join(lines) + "\n"


def c(
    ref: str,
    value: str,
    footprint: str,
    datasheet: str,
    pins: list[tuple[str, str, str | None]],
    *,
    dnp: bool = False,
    in_bom: bool = True,
    on_board: bool = True,
) -> Component:
    return Component(ref, value, footprint, datasheet, tuple(Pin(*pin) for pin in pins), dnp, in_bom, on_board)


def passive(ref: str, value: str, footprint: str, net1: str, net2: str, datasheet: str = "") -> Component:
    return c(ref, value, footprint, datasheet, [("1", "1", net1), ("2", "2", net2)])


def lb_jpb_nets() -> dict[int, str]:
    path = ROOT / "hardware/logic-board/LB-100/LB-100-stm32h563-pin-binding-precheck.csv"
    result: dict[int, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["JPB1 pin"].isdigit():
                result[int(row["JPB1 pin"])] = row["Net"]
    if sorted(result) != list(range(1, 101)):
        raise ValueError("LB-100 JPB1 source must contain pins 1..100 exactly once")
    return result


STM32_NAMES = [
    "PE2", "PE3", "PE4", "PE5", "PE6", "VBAT", "PC13", "PC14-OSC32_IN", "PC15-OSC32_OUT", "VSS",
    "VDD", "PH0-OSC_IN", "PH1-OSC_OUT", "NRST", "PC0", "PC1", "PC2", "PC3", "VSSA", "VREF-",
    "VREF+", "VDDA", "PA0", "PA1", "PA2", "PA3", "VSS", "VDD", "PA4", "PA5", "PA6", "PA7",
    "PC4", "PC5", "PB0", "PB1", "PB2", "PE7", "PE8", "PE9", "PE10", "PE11", "PE12", "PE13",
    "PE14", "PE15", "PB10", "VCAP1", "VSS", "VDD", "PB12", "PB13", "PB14", "PB15", "PD8", "PD9",
    "PD10", "PD11", "PD12", "PD13", "PD14", "PD15", "PC6", "PC7", "PC8", "PC9", "PA8", "PA9",
    "PA10", "PA11-USB_DM", "PA12-USB_DP", "PA13-SWDIO", "VDDUSB", "VSS", "VDD", "PA14-SWCLK",
    "PA15", "PC10", "PC11", "PC12", "PD0", "PD1", "PD2", "PD3", "PD4", "PD5", "PD6", "PD7",
    "PB3-SWO", "PB4", "PB5", "PB6", "PB7", "BOOT0", "PB8", "PB9", "PE0", "VCAP2", "VSS", "VDD",
]


def build_lb() -> Schematic:
    notes = (
        "LB-100 reviewed value-bearing Rev.1 capture. STM32H563VIT6 LQFP100; exact ST package positions; "
        "JPB1 100 signals plus four GND MF circuits; PB_5V_OUT 500 mA allocation with reviewed 229.2 mA "
        "sustained and 381.2 mA service-peak budgets including FB-100 worst-case indication; ADR-0015 "
        "CAN1 FDCAN/read-only ownership with no LB "
        "transceiver; CAN1_TX_ROUTE remains the PB DNP/open route. TCA9539-Q1 maps the approved JFB1 role-free "
        "UI signals and powers up with all ports as inputs. CAN2/LIN/RS485 footprints are DNP by default. "
        "USB VBUS is sense-only and cannot back-power PB_5V_OUT, LB_3V3_MAIN, or LB_3V3_IO. Reviewed footprint "
        "binding and mechanical envelope remain governed by LB-100-pcb-layout-start-checklist.csv, "
        "LB-100-footprint-binding-inventory.csv, and LB-100-mechanical-envelope-inventory.csv. Do not create "
        "LB-100.kicad_pcb, Gerbers, drills, pick-place, BOM/CPL order package, or manufacturing outputs from this "
        "schematic. PCB layout and manufacturing outputs remain separate."
    )
    sch = Schematic("LB-100", "LB-100 Logic Board — Value-Bearing Rev.1", notes)
    jpb = lb_jpb_nets()
    mcu_nets: dict[int, str | None] = {}
    with (ROOT / "hardware/logic-board/LB-100/LB-100-stm32h563-pin-binding-precheck.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["Package position"].isdigit():
                mcu_nets[int(row["Package position"])] = row["Net"]
    mcu_nets.update({
        6: "LB_3V3_MAIN", 8: "MCU_LSE_IN", 9: "MCU_LSE_OUT", 10: "GND", 11: "LB_3V3_MAIN",
        12: "MCU_HSE_IN", 13: "MCU_HSE_OUT", 14: "NRST", 19: "AGND", 20: "AGND", 21: "ADC_REF",
        22: "LB_3V3_ANALOG", 27: "GND", 28: "LB_3V3_MAIN", 48: "VCAP1", 49: "GND",
        50: "LB_3V3_MAIN", 54: "IOX_INT_N", 57: "USB_VBUS_SENSE", 70: "USB_D_N", 71: "USB_D_P",
        72: "SWDIO", 73: "LB_3V3_MAIN", 74: "GND",
        75: "LB_3V3_MAIN", 80: "MICROSD_CS_N", 81: "MICROSD_PWR_EN", 82: "RADIO_SENSOR_EN",
        76: "SWCLK", 88: None, 94: "BOOT0", 97: "BLE_RESET_N", 98: "VCAP2", 99: "GND",
        100: "LB_3V3_MAIN",
    })
    sch.add(c(
        "U1", "STM32H563VIT6", "LB100:LQFP-100_L14.0-W14.0-P0.50-LS16.0-BL",
        "https://www.st.com/resource/en/datasheet/stm32h563vi.pdf",
        [(str(pos), STM32_NAMES[pos - 1], mcu_nets.get(pos)) for pos in range(1, 101)],
    ))
    sch.add(c(
        "JPB1", "FX18-100S-0.8SV10", "LB100:FX18-100S-0.8SV10_Hirose",
        "https://www.hirose.com/en/product/document?documentid=0000954081",
        [(str(pin), jpb[pin], None if jpb[pin].startswith("SPARE_") else jpb[pin]) for pin in range(1, 101)] + [
            ("MF_A_PIN1_51_END", "MF_A_PIN1_51_END", "GND"),
            ("MF_B_PIN1_51_END", "MF_B_PIN1_51_END", "GND"),
            ("MF_A_PIN50_100_END", "MF_A_PIN50_100_END", "GND"),
            ("MF_B_PIN50_100_END", "MF_B_PIN50_100_END", "GND"),
        ],
    ))
    jfb_nets = [
        "GND", "FB_3V3_OR_IO", "GND", "USB_D_P", "USB_D_N", "USB_CC1", "USB_CC2", "USB_VBUS_SENSE",
        "STATUS_RGB_DATA", *[f"CH_LED_{index}" for index in range(1, 11)], "SERVICE_BTN", "RESET_BTN",
        "OLED_SCL", "OLED_SDA", "OLED_RST_OR_INT_DNP",
    ]
    sch.add(c(
        "JFB1", "AFC07-S24ECA-00", "LB100:FPC-SMD_AFC07-S24ECA-00",
        "https://jlcpcb.com/partdetail/AFC07-S24ECA-00/C262643",
        [(str(index), net, net) for index, net in enumerate(jfb_nets, 1)] + [("25", "SHIELD_A", "GND"), ("26", "SHIELD_B", "GND")],
    ))
    sch.add(c("U2", "XC6220B331MR-G", "LB100:SOT-25_L3.0-W1.6-P0.95-LS2.8-TL", "https://product.torexsemi.com/system/files/series/xc6220.pdf", [
        ("1", "VIN", "PB_5V_OUT"), ("2", "VSS", "GND"), ("3", "CE", "PB_PWR_GOOD"),
        ("4", "NC", None), ("5", "VOUT", "LB_3V3_MAIN"),
    ]))
    sch.add(c("U3", "TCA9539QPWRQ1", "LB100:TSSOP-24_4.4x7.8mm_P0.65mm", "https://www.ti.com/lit/ds/symlink/tca9539-q1.pdf", [
        ("1", "INT_N", "IOX_INT_N"), ("2", "A1", "GND"), ("3", "RESET_N", "NRST"),
        *[(str(4 + index), f"P0{index}", f"CH_LED_{index + 1}") for index in range(8)],
        ("12", "GND", "GND"), ("13", "P10", "CH_LED_9"), ("14", "P11", "CH_LED_10"),
        ("15", "P12", "STATUS_RGB_DATA"), ("16", "P13", "SERVICE_BTN"),
        ("17", "P14", "MICROSD_CARD_DETECT"), ("18", "P15", "IMU_INT1"),
        ("19", "P16", "RTC_INT_N"), ("20", "P17", "OLED_RST_OR_INT_DNP"),
        ("21", "A0", "GND"), ("22", "SCL", "PB_I2C_SCL"), ("23", "SDA", "PB_I2C_SDA"),
        ("24", "VCC", "LB_3V3_MAIN"),
    ]))
    sch.add(c("U4", "TJA1051TK/3,118", "LB100:HVSON-8_L3.0-W3.0-P0.65-BL-EP", "https://www.nxp.com/docs/en/data-sheet/TJA1051.pdf", [
        ("1", "TXD", "CAN2_TX_ROUTE"), ("2", "GND", "GND"), ("3", "VCC", "PB_5V_OUT"),
        ("4", "RXD", "CAN2_RX_ROUTE"), ("5", "VIO", "LB_3V3_MAIN"), ("6", "CANL", None),
        ("7", "CANH", None), ("8", "S", "LB_3V3_MAIN"), ("9", "EP", "GND"),
    ], dnp=True))
    sch.add(c("U5", "TJA1021T/20/CM,118", "LB100:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL", "https://www.nxp.com/docs/en/data-sheet/TJA1021.pdf", [
        ("1", "RXD", "LIN_RX"), ("2", "SLP_N", "GND"), ("3", "WAKE_N", "LB_3V3_MAIN"),
        ("4", "TXD", "LIN_TX"), ("5", "GND", "GND"), ("6", "LIN", None),
        ("7", "VBAT", None), ("8", "INH", None),
    ], dnp=True))
    sch.add(c("U6", "SP3485EN-L/TR", "LB100:SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL", "https://www.maxlinear.com/ds/sp3485.pdf", [
        ("1", "RO", "RS485_RX"), ("2", "RE_N", "RS485_DE"), ("3", "DE", "RS485_DE"),
        ("4", "DI", "RS485_TX"), ("5", "GND", "GND"), ("6", "A", None),
        ("7", "B", None), ("8", "VCC", "LB_3V3_MAIN"),
    ], dnp=True))
    e73_names = ["P1.11", "P1.10", "P0.03", "P0.28", "GND", "P1.13", "P0.02", "P0.29", "P0.31", "P0.30", "XL1", "P0.26", "XL2", "P0.06", "P0.05", "P0.08", "P1.09", "P0.04", "VCC", "P0.12", "GND", "P0.07", "VDDH", "GND", "DCCH", "RESET", "VBUS", "P0.15", "USB_DM", "P0.17", "USB_DP", "P0.20", "P0.13", "P0.22", "P0.24", "P1.00", "SWDIO", "P1.02", "SWDCLK", "P1.04", "NFC1", "P1.06", "NFC2"]
    e73_nets: dict[int, str | None] = {5: "GND", 19: "RADIO_SENSOR_3V3", 20: "UART_RX", 21: "GND", 22: "UART_TX", 24: "GND", 26: "BLE_RESET_N"}
    sch.add(c("U7", "E73-2G4M08S1C", "LB100:WIRELM-SMD_E73-2G4M08S1C", "https://www.ebyte.com/product/444.html", [(str(index), name, e73_nets.get(index)) for index, name in enumerate(e73_names, 1)]))
    sch.add(c("U8", "FM24CL64B-GTR", "LB100:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL", "https://www.infineon.com/assets/row/public/documents/10/57/infineon-fm24cl64b-64-kbit-8-k-8-serial-i2c-automotive-f-ram-datasheet-additionaltechnicalinformation-en.pdf", [
        ("1", "A0", "GND"), ("2", "A1", "GND"), ("3", "A2", "GND"), ("4", "VSS", "GND"),
        ("5", "SDA", "PB_I2C_SDA"), ("6", "SCL", "PB_I2C_SCL"), ("7", "WP", "GND"), ("8", "VDD", "LB_3V3_MAIN"),
    ]))
    sch.add(c("U9", "DS3231MZ+TRL", "LB100:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL", "https://www.analog.com/media/en/technical-documentation/data-sheets/DS3231M.pdf", [
        ("1", "32KHZ", None), ("2", "VCC", "LB_3V3_MAIN"), ("3", "INT_SQW_N", "RTC_INT_N"),
        ("4", "RST_N", "NRST"), ("5", "GND", "GND"), ("6", "VBAT", "BACKUP_AON"),
        ("7", "SDA", "PB_I2C_SDA"), ("8", "SCL", "PB_I2C_SCL"),
    ]))
    sch.add(c("U10", "BMI270", "LB100:LGA-14_L3.0-W2.5-P0.50-BR", "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf", [
        ("1", "SDO", "GND"), ("2", "ASDx", None), ("3", "ASCx", None), ("4", "INT1", "IMU_INT1"),
        ("5", "VDDIO", "RADIO_SENSOR_3V3"), ("6", "GNDIO", "GND"), ("7", "GND", "GND"),
        ("8", "VDD", "RADIO_SENSOR_3V3"), ("9", "INT2", None), ("10", "OCSB", None), ("11", "OSDO", None),
        ("12", "CSB", "RADIO_SENSOR_3V3"), ("13", "SCL", "PB_I2C_SCL"), ("14", "SDA", "PB_I2C_SDA"),
    ]))
    sch.add(c("U11", "VEML7700-TT", "LB100:SENSOR-SMD_EML7700-TT", "https://www.vishay.com/doc?84286=", [
        ("1", "SCL", "PB_I2C_SCL"), ("2", "VDD", "RADIO_SENSOR_3V3"), ("3", "GND", "GND"), ("4", "SDA", "PB_I2C_SDA"),
    ]))
    sch.add(c("JSD1", "TF-015", "LB100:TF-SMD_TF-015", "https://www.lcsc.com/datasheet/lcsc_datasheet_2112221030_SOFNG-TF-015_C113206.pdf", [
        ("1", "DAT2", "MICROSD_DAT2"), ("2", "CD_DAT3", "MICROSD_CS_N"), ("3", "CMD", "PB_SPI_MOSI"),
        ("4", "VDD", "MICROSD_3V3"), ("5", "CLK", "PB_SPI_SCK"), ("6", "VSS", "GND"),
        ("7", "DAT0", "PB_SPI_MISO"), ("8", "DAT1", "MICROSD_DAT1"), ("9", "CARD_DETECT", "MICROSD_CARD_DETECT"),
        ("10", "SHELL1", "GND"), ("11", "SHELL2", "GND"), ("12", "SHELL3", "GND"), ("13", "SHELL4", "GND"),
    ]))
    for ref, output, enable in (("U12", "MICROSD_3V3", "MICROSD_PWR_EN"), ("U13", "RADIO_SENSOR_3V3", "RADIO_SENSOR_EN")):
        sch.add(c(ref, "TPS22918TDBVRQ1", "LB100:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL", "https://www.ti.com/lit/ds/symlink/tps22918-q1.pdf", [
            ("1", "VIN", "LB_3V3_MAIN"), ("2", "GND", "GND"), ("3", "ON", enable),
            ("4", "CT", f"{output}_CT"), ("5", "QOD", output), ("6", "VOUT", output),
        ]))
    sch.add(c("JBT1", "BACKUP_BATTERY_2V3_TO_3V6_DNP", "LB100:PinHeader_1x02_P2.54mm_Vertical", "../LB-100-component-decision-record.md", [
        ("1", "BACKUP_AON", "BACKUP_AON"), ("2", "GND", "GND"),
    ], dnp=True))
    sch.add(c("JDBG1", "SWD_2x3_1.27mm", "LB100:PinHeader_2x03_P1.27mm_Vertical", "https://developer.arm.com/documentation/101416/latest/", [
        ("1", "VTREF", "LB_3V3_MAIN"), ("2", "SWDIO", "SWDIO"), ("3", "GND", "GND"),
        ("4", "SWCLK", "SWCLK"), ("5", "GND", "GND"), ("6", "SWO", "PB_SPI_SCK"),
    ]))
    sch.add(c("Y1", "ABM8AIG-25.000MHZ-12-2Z-T3", "LB100:Crystal_SMD_3225-4Pin", "https://abracon.com/Resonators/ABM8AIG.pdf", [
        ("1", "XIN", "MCU_HSE_IN"), ("2", "GND1", "GND"), ("3", "XOUT", "MCU_HSE_OUT"), ("4", "GND2", "GND"),
    ]))
    sch.add(c("Y2", "ABS07AIG-32.768kHz-7-T", "LB100:Crystal_SMD_3215-2Pin", "https://abracon.com/Resonators/ABS07AIG.pdf", [
        ("1", "XIN", "MCU_LSE_IN"), ("2", "XOUT", "MCU_LSE_OUT"),
    ]))

    r0603 = "LB100:R_C_0603_1608Metric"
    c0603 = r0603
    passives = [
        passive("C1", "1uF 10V X7R", c0603, "PB_5V_OUT", "GND"),
        passive("C2", "1uF 6.3V X7R", c0603, "LB_3V3_MAIN", "GND"),
        passive("C3", "10uF 6.3V X7R", "LB100:R_C_0805_2012Metric", "LB_3V3_MAIN", "GND"),
        passive("R1", "100k 1%", r0603, "PB_PWR_GOOD", "GND"),
        passive("R2", "0R", r0603, "LB_3V3_MAIN", "LB_3V3_IO"),
        passive("R3", "0R", r0603, "LB_3V3_MAIN", "FB_3V3_OR_IO"),
        passive("FB1", "600R@100MHz 0.2A", r0603, "LB_3V3_MAIN", "LB_3V3_ANALOG"),
        passive("C4", "1uF 6.3V X7R", c0603, "LB_3V3_ANALOG", "AGND"),
        passive("C5", "100nF 6.3V X7R", c0603, "LB_3V3_ANALOG", "AGND"),
        passive("C6", "2.2uF 6.3V X7R", c0603, "VCAP1", "GND"),
        passive("C7", "2.2uF 6.3V X7R", c0603, "VCAP2", "GND"),
        passive("R4", "10k 1%", r0603, "LB_3V3_MAIN", "NRST"),
        passive("C8", "100nF 6.3V X7R", c0603, "NRST", "GND"),
        passive("R5", "10k 1%", r0603, "BOOT0", "GND"),
        passive("R6", "2.2k 1%", r0603, "LB_3V3_IO", "PB_I2C_SCL"),
        passive("R7", "2.2k 1%", r0603, "LB_3V3_IO", "PB_I2C_SDA"),
        passive("R8", "4.7k 1%", r0603, "LB_3V3_MAIN", "IOX_INT_N"),
        passive("R9", "10k 1%", r0603, "LB_3V3_MAIN", "BLE_RESET_N"),
        passive("R10", "47k 1%", r0603, "MICROSD_3V3", "MICROSD_DAT1"),
        passive("R11", "47k 1%", r0603, "MICROSD_3V3", "MICROSD_DAT2"),
        passive("R12", "10k 1%", r0603, "MICROSD_3V3", "MICROSD_CS_N"),
        passive("R13", "0R", r0603, "PB_I2C_SCL", "OLED_SCL"),
        passive("R14", "0R", r0603, "PB_I2C_SDA", "OLED_SDA"),
        passive("R15", "0R", r0603, "NRST", "RESET_BTN"),
        passive("C9", "18pF 50V C0G", c0603, "MCU_HSE_IN", "GND"),
        passive("C10", "18pF 50V C0G", c0603, "MCU_HSE_OUT", "GND"),
        passive("C11", "8.2pF 50V C0G", c0603, "MCU_LSE_IN", "GND"),
        passive("C12", "8.2pF 50V C0G", c0603, "MCU_LSE_OUT", "GND"),
        passive("C13", "1nF 50V C0G", c0603, "MICROSD_3V3_CT", "GND"),
        passive("C14", "1nF 50V C0G", c0603, "RADIO_SENSOR_3V3_CT", "GND"),
    ]
    for index in range(15, 28):
        rail = "LB_3V3_MAIN" if index < 22 else "RADIO_SENSOR_3V3" if index < 26 else "MICROSD_3V3"
        passives.append(passive(f"C{index}", "100nF 6.3V X7R", c0603, rail, "GND"))
    for item in passives:
        sch.add(item)
    return sch


def build_fb() -> Schematic:
    notes = (
        "FB-100 reviewed value-bearing Rev.1 capture. USB-C is USB2 device-only with two 5.1k Rd resistors, "
        "USBLC6-2SC6 flow-through ESD, VBUS sense-only divider, and no connection from USB VBUS to FB_3V3_OR_IO. "
        "LTC3212 converts the approved STATUS_RGB_DATA single wire into three regulated cathode currents for the "
        "common-anode RGB LED. CH_LED_1..CH_LED_10 remain role-free and default off while LB TCA9539-Q1 ports "
        "are inputs. OLED is an optional four-wire I2C module header and is DNP by default. JFB1 uses the approved "
        "24-pin contract. Reviewed footprint binding and mechanical envelope remain governed by "
        "FB-100-pcb-layout-start-checklist.csv, FB-100-footprint-binding-inventory.csv, and "
        "FB-100-mechanical-envelope-inventory.csv. Do not create FB-100.kicad_pcb, Gerbers, drills, pick-place, "
        "BOM/CPL order package, or manufacturing outputs from this schematic. PCB layout and manufacturing outputs "
        "remain separate."
    )
    sch = Schematic("FB-100", "FB-100 Front Panel — Value-Bearing Rev.1", notes)
    sch.add(c("J1", "USB4105-GF-A", "FB100:TYPE-C-SMD_SBC-160S1A-20-S412", "https://gct.co/connector/usb4105", [
        ("1", "SHIELD1", "USB_SHIELD"), ("2", "SHIELD2", "USB_SHIELD"), ("3", "SHIELD3", "USB_SHIELD"), ("4", "SHIELD4", "USB_SHIELD"),
        ("A1", "GND", "GND"), ("A4", "VBUS", "USB_VBUS"), ("A5", "CC1", "USB_CC1"), ("A6", "D+", "USB_D_P_CONN"),
        ("A7", "D-", "USB_D_N_CONN"), ("A8", "SBU1", None), ("A9", "VBUS", "USB_VBUS"), ("A12", "GND", "GND"),
        ("B1", "GND", "GND"), ("B4", "VBUS", "USB_VBUS"), ("B5", "CC2", "USB_CC2"), ("B6", "D+", "USB_D_P_CONN"),
        ("B7", "D-", "USB_D_N_CONN"), ("B8", "SBU2", None), ("B9", "VBUS", "USB_VBUS"), ("B12", "GND", "GND"),
    ]))
    sch.add(c("D1", "USBLC6-2SC6", "FB100:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL", "https://www.st.com/resource/en/datasheet/usblc6-2.pdf", [
        ("1", "I_O1_IN", "USB_D_P_CONN"), ("2", "GND", "GND"), ("3", "I_O2_IN", "USB_D_N_CONN"),
        ("4", "I_O2_OUT", "USB_D_N"), ("5", "VBUS", "USB_VBUS"), ("6", "I_O1_OUT", "USB_D_P"),
    ]))
    jfb_nets = [
        "GND", "FB_3V3_OR_IO", "GND", "USB_D_P", "USB_D_N", "USB_CC1", "USB_CC2", "USB_VBUS_SENSE",
        "STATUS_RGB_DATA", *[f"CH_LED_{index}" for index in range(1, 11)], "SERVICE_BTN", "RESET_BTN",
        "OLED_SCL", "OLED_SDA", "OLED_RST_OR_INT_DNP",
    ]
    sch.add(c("JFB1", "AFC07-S24ECA-00", "FB100:FPC-SMD_AFC07-S24ECA-00", "https://jlcpcb.com/partdetail/AFC07-S24ECA-00/C262643", [(str(index), net, net) for index, net in enumerate(jfb_nets, 1)] + [("25", "SHIELD_A", "GND"), ("26", "SHIELD_B", "GND")]))
    sch.add(c("U1", "LTC3212EDDB#TRPBF", "FB100:DFN-12-1EP_2x3mm_P0.45mm", "https://www.analog.com/media/en/technical-documentation/data-sheets/3212fb.pdf", [
        ("1", "CP", "RGB_CP"), ("2", "CPO", "RGB_LED_ANODE"), ("3", "LEDEN", "STATUS_RGB_DATA"),
        ("4", "ISETB", "FB_3V3_OR_IO"), ("5", "ISETR", "FB_3V3_OR_IO"), ("6", "ISETG", "RGB_ISETG"),
        ("7", "LEDG", "RGB_G_K"), ("8", "LEDR", "RGB_R_K"), ("9", "LEDB", "RGB_B_K"),
        ("10", "GND", "GND"), ("11", "CM", "RGB_CM"), ("12", "VIN", "FB_3V3_OR_IO"), ("13", "EP", "GND"),
    ]))
    sch.add(c("D2", "19-237/R6GHBHC-A01/2T", "FB100:LED-ARRAY-SMD_4P-L1.6-W1.6-BL_1", "https://en.everlight.com/wp-content/uploads/2025/05/EVERLIGHT_2025-2026_Catalogue-.pdf", [
        ("1", "COMMON_ANODE", "RGB_LED_ANODE"), ("2", "RED_K", "RGB_R_K"), ("3", "GREEN_K", "RGB_G_K"), ("4", "BLUE_K", "RGB_B_K"),
    ]))
    for index in range(1, 11):
        sch.add(c(f"D{index + 2}", "KT-0805Y", "FB100:LED0805-R-RD", "https://jlcpcb.com/parts/componentSearch?searchTxt=KT-0805Y", [
            ("1", "A", f"CH_LED_{index}_A"), ("2", "K", f"CH_LED_{index}"),
        ]))
        sch.add(passive(f"R{index}", "1k 1%", "FB100:R_C_0603_1608Metric", "FB_3V3_OR_IO", f"CH_LED_{index}_A"))
    sch.add(c("SW1", "EVPBB4A9B000 SERVICE", "FB100:KEY-SMD_L2.6-W1.6-P0.75-LS3.0", "https://industrial.panasonic.com/cdbs/www-data/pdf/ATK0000/ATK0000C20.pdf", [
        ("A", "A", "SERVICE_BTN"), ("A1", "A1", "SERVICE_BTN"), ("B", "B", "GND"), ("B1", "B1", "GND"),
    ]))
    sch.add(c("SW2", "EVPBB4A9B000 RESET", "FB100:KEY-SMD_L2.6-W1.6-P0.75-LS3.0", "https://industrial.panasonic.com/cdbs/www-data/pdf/ATK0000/ATK0000C20.pdf", [
        ("A", "A", "RESET_BTN"), ("A1", "A1", "RESET_BTN"), ("B", "B", "GND"), ("B1", "B1", "GND"),
    ]))
    sch.add(c("J2", "SSD1306_I2C_MODULE_DNP", "FB100:PinHeader_1x04_P2.54mm_Vertical", "../FB-100-component-decision-record.md", [
        ("1", "GND", "GND"), ("2", "VCC", "FB_3V3_OR_IO"), ("3", "SCL", "OLED_SCL"), ("4", "SDA", "OLED_SDA"),
    ], dnp=True))
    extra = [
        passive("R11", "5.1k 1%", "FB100:R_C_0603_1608Metric", "USB_CC1", "GND"),
        passive("R12", "5.1k 1%", "FB100:R_C_0603_1608Metric", "USB_CC2", "GND"),
        passive("R13", "100k 1%", "FB100:R_C_0603_1608Metric", "USB_VBUS", "USB_VBUS_SENSE"),
        passive("R14", "27k 1%", "FB100:R_C_0603_1608Metric", "USB_VBUS_SENSE", "GND"),
        passive("C1", "100nF 16V X7R", "FB100:R_C_0603_1608Metric", "USB_VBUS_SENSE", "GND"),
        passive("R15", "1M 1%", "FB100:R_C_0603_1608Metric", "USB_SHIELD", "GND"),
        passive("C2", "1nF 1kV C0G", "FB100:R_C_0603_1608Metric", "USB_SHIELD", "GND"),
        passive("C3", "1uF 6.3V X7R", "FB100:R_C_0603_1608Metric", "FB_3V3_OR_IO", "GND"),
        passive("C4", "1uF 6.3V X7R", "FB100:R_C_0603_1608Metric", "RGB_CP", "RGB_CM"),
        passive("C5", "1uF 6.3V X7R", "FB100:R_C_0603_1608Metric", "RGB_LED_ANODE", "GND"),
        passive("R16", "35.7k 1%", "FB100:R_C_0603_1608Metric", "RGB_ISETG", "GND"),
        passive("R17", "10k 1%", "FB100:R_C_0603_1608Metric", "FB_3V3_OR_IO", "SERVICE_BTN"),
        passive("C6", "100nF 6.3V X7R", "FB100:R_C_0603_1608Metric", "SERVICE_BTN", "GND"),
        passive("R18", "10k 1%", "FB100:R_C_0603_1608Metric", "FB_3V3_OR_IO", "RESET_BTN"),
        passive("C7", "100nF 6.3V X7R", "FB100:R_C_0603_1608Metric", "RESET_BTN", "GND"),
        passive("R19", "100k 1%", "FB100:R_C_0603_1608Metric", "OLED_RST_OR_INT_DNP", "GND"),
    ]
    for item in extra:
        sch.add(item)
    return sch


def board_outputs(schematic: Schematic) -> tuple[tuple[Path, str], tuple[Path, str]]:
    board_dir = ROOT / ("hardware/logic-board/LB-100" if schematic.board == "LB-100" else "hardware/front-board/FB-100")
    kicad_dir = board_dir / "kicad"
    return (
        (kicad_dir / f"{schematic.board}.kicad_sch", schematic.render()),
        (kicad_dir / "lib" / f"{schematic.prefix}.kicad_sym", schematic.render_library()),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed generated files are stale")
    args = parser.parse_args()
    stale: list[Path] = []
    for schematic in (build_lb(), build_fb()):
        for path, content in board_outputs(schematic):
            if args.check:
                if not path.is_file() or path.read_text(encoding="utf-8") != content:
                    stale.append(path)
            else:
                path.write_text(content, encoding="utf-8")
    if stale:
        for path in stale:
            print(f"stale generated file: {path.relative_to(ROOT)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
