#!/usr/bin/env python3
"""Generate the Q2-C100 empirical-qualification coupon KiCad design.

Q2-C100 is a dedicated laboratory coupon.  It is not PB-100 and it does not
authorize PB-100 board import or manufacturing output.  The generated board
captures the critical high-current and gate-drive geometry while the remaining
low-energy routing stays visibly open until the test-fixture review closes.
"""

from __future__ import annotations

import argparse
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from generate_lb_fb_schematics import Component, Pin, Schematic, c, uid


ROOT = Path(__file__).resolve().parents[1]
COUPON_DIR = ROOT / "hardware" / "power-board" / "PB-100" / "qualification" / "Q2-C100"
KICAD_DIR = COUPON_DIR / "kicad"
LOCAL_FP_DIR = KICAD_DIR / "lib" / "Q2C100.pretty"
PB_FP_DIR = ROOT / "hardware" / "power-board" / "PB-100" / "kicad" / "lib" / "PB100.pretty"
BOARD_PATH = KICAD_DIR / "Q2-C100.kicad_pcb"
RULES_PATH = KICAD_DIR / "Q2-C100.kicad_dru"
SCHEMATIC_PATH = KICAD_DIR / "Q2-C100.kicad_sch"
SYMBOL_PATH = KICAD_DIR / "lib" / "Q2C100.kicad_sym"
LAYOUT_UUID_NS = uuid.UUID("648e5644-404a-4f2f-9d6c-caf61b3069b6")

TI_DS = "https://www.ti.com/lit/ds/symlink/lm74930-q1.pdf"
INFINEON_Q2_DS = "https://www.infineon.com/assets/row/public/documents/10/49/infineon-iautn15s6n025-datasheet-en.pdf"
INFINEON_Q1_DS = "https://www.infineon.com/assets/row/public/documents/10/49/infineon-iaut300n08s5n012-datasheet-en.pdf"
WURTH_TERMINAL_DS = "https://www.we-online.com/components/products/datasheet/786202073.pdf"
NEXPERIA_ZENER_DS = "https://assets.nexperia.com/documents/data-sheet/BZT52H-Q_SER.pdf"
TDK_CVS_PAGE = "https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA6N3X7R2A225M230AE"


@dataclass(frozen=True)
class Placement:
    x_mm: float
    y_mm: float
    rotation: float = 0.0


PLACEMENTS = {
    "JRAW": Placement(40.0, 12.0),
    "QDUT": Placement(40.0, 35.0),
    "JCOMMON": Placement(70.0, 50.0),
    "QREV": Placement(40.0, 65.0, 180.0),
    "JOUT": Placement(40.0, 90.0),
    "UCTRL": Placement(18.0, 45.0),
    "RVS": Placement(20.0, 20.0, 90.0),
    "DZVS": Placement(12.0, 29.0, 90.0),
    "CVS1": Placement(18.0, 29.0),
    "CVS2": Placement(24.0, 29.0),
    "CCAP": Placement(25.0, 43.0),
    "ROV1": Placement(57.0, 18.0, 90.0),
    "ROV2": Placement(57.0, 24.0, 90.0),
    "ROV3": Placement(57.0, 30.0, 90.0),
    "JDRIVE": Placement(8.0, 48.0, 90.0),
    "JHEAT": Placement(69.0, 75.0),
    "JTEMP": Placement(69.0, 82.0),
    "TPD": Placement(48.0, 34.0),
    "TPG": Placement(30.0, 35.0),
    "TPS": Placement(48.0, 42.0),
    "TPHG": Placement(27.0, 35.0),
    "TPOUT": Placement(48.0, 69.0),
    "TPOV": Placement(61.0, 34.0),
    "TPVS": Placement(12.0, 35.0),
    "TPFLT": Placement(18.0, 68.0),
    "TPGND": Placement(10.0, 70.0),
}


def layout_uid(*parts: object) -> str:
    return str(uuid.uuid5(LAYOUT_UUID_NS, ":".join(str(part) for part in parts)))


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_coupon() -> Schematic:
    schematic = Schematic(
        "Q2-C100",
        "Q2-C100 Q2 empirical-qualification coupon",
        "\n".join(
            (
                "QUALIFICATION-COUPON-ONLY / NOT FOR VEHICLE INSTALLATION.",
                "QDUT is the exact IAUTN15S6N025ATMA1 selected by ADR-0018.",
                "Correlation build: populate UCTRL and QREV; HGATE is direct to QDUT gate.",
                "Forced build: do not populate UCTRL/QREV; drive QDUT at JDRIVE pins 1/2.",
                "No populated Rg or CdV/dt exists in either accepted build.",
                "RAW_101V may reach 101 V; LM74930 protected pins remain on <=65 V nets.",
                "Power-loop geometry is routed; low-energy fixture routing remains open.",
            )
        ),
        paper="A2",
    )

    terminal_fp = "Q2C100:REDCUBE_786202073_3x3_P2.54"
    terminal_pin = [("1", "POWER", "RAW_101V")]
    schematic.add(c("JRAW", "786202073 REDCUBE M3 130A RAW", terminal_fp, WURTH_TERMINAL_DS, terminal_pin))
    schematic.add(c("JCOMMON", "786202073 REDCUBE M3 130A COMMON", terminal_fp, WURTH_TERMINAL_DS, [("1", "POWER", "COMMON_SOURCE")]))
    schematic.add(c("JOUT", "786202073 REDCUBE M3 130A OUT", terminal_fp, WURTH_TERMINAL_DS, [("1", "POWER", "SYSTEM_OUT")]))

    toll_fp = "PB100:PG-HSOF-8-1_TOLL_Infineon"
    schematic.add(
        c(
            "QDUT",
            "IAUTN15S6N025ATMA1",
            toll_fp,
            INFINEON_Q2_DS,
            [("1", "G", "Q2_HGATE", "input")]
            + [(str(number), "S", "COMMON_SOURCE", "passive") for number in range(2, 9)]
            + [("Tab", "D", "RAW_101V", "passive")],
        )
    )
    schematic.add(
        c(
            "QREV",
            "IAUT300N08S5N012ATMA2",
            toll_fp,
            INFINEON_Q1_DS,
            [("1", "G", "QREV_DGATE", "input")]
            + [(str(number), "S", "COMMON_SOURCE", "passive") for number in range(2, 9)]
            + [("Tab", "D", "SYSTEM_OUT", "passive")],
        )
    )

    controller_pins = (
        Pin("1", "DGATE", "QREV_DGATE", "output"),
        Pin("2", "A", "COMMON_SOURCE", "input"),
        Pin("3", "SW", None, "no_connect"),
        Pin("4", "UVLO", "CTRL_VS", "input"),
        Pin("5", "OV", "CTRL_OV", "input"),
        Pin("6", "EN", "CTRL_VS", "input"),
        Pin("7", "MODE", "CTRL_VS", "input"),
        Pin("8", "N.C.", None, "no_connect"),
        Pin("9", "TMR", "GND", "input"),
        Pin("10", "IMON", None, "no_connect"),
        Pin("11", "ILIM", "GND", "input"),
        Pin("12", "FLT", "CTRL_FLT_N", "open_collector"),
        Pin("13", "GND", "GND", "power_in"),
        Pin("14", "HGATE", "Q2_HGATE", "output"),
        Pin("15", "OUT", "COMMON_SOURCE", "input"),
        Pin("16", "OVCLAMP", "GND", "input"),
        Pin("17", "N.C.", None, "no_connect"),
        Pin("18", "ISCP", "SYSTEM_OUT", "input"),
        Pin("19", "CS-", "SYSTEM_OUT", "input"),
        Pin("20", "CS+", "SYSTEM_OUT", "input"),
        Pin("21", "N.C.", None, "no_connect"),
        Pin("22", "VS", "CTRL_VS", "power_in"),
        Pin("23", "CAP", "CTRL_CAP", "output"),
        Pin("24", "C", "SYSTEM_OUT", "input"),
        Pin("25", "RTN", None, "no_connect"),
    )
    schematic.add(
        Component(
            "UCTRL",
            "LM74930QRGERQ1",
            "PB100:VQFN-24_RGE_4x4mm_P0.5mm_EP2.4mm",
            TI_DS,
            controller_pins,
        )
    )

    passive_0603 = "Q2C100:R_C_0603_1608Metric"
    schematic.add(c("ROV1", "42.2k 1% AEC-Q200", passive_0603, TI_DS, [("1", "1", "RAW_101V"), ("2", "2", "OV_MID")]))
    schematic.add(c("ROV2", "42.2k 1% AEC-Q200", passive_0603, TI_DS, [("1", "1", "OV_MID"), ("2", "2", "CTRL_OV")]))
    schematic.add(c("ROV3", "1.00k 1% AEC-Q200", passive_0603, TI_DS, [("1", "1", "CTRL_OV"), ("2", "2", "GND")]))
    schematic.add(c("RVS", "10.0k 1% 1206 AEC-Q200", "Q2C100:R_1206_3216Metric", TI_DS, [("1", "1", "RAW_101V"), ("2", "2", "CTRL_VS")]))
    schematic.add(c("DZVS", "BZT52H-B56-Q 56V", "Q2C100:SOD123F", NEXPERIA_ZENER_DS, [("1", "K", "CTRL_VS"), ("2", "A", "GND")]))
    for ref in ("CVS1", "CVS2"):
        schematic.add(c(ref, "CGA6N3X7R2A225M230AE 2.2uF 100V X7R", "Q2C100:C_1210_3225Metric", TDK_CVS_PAGE, [("1", "1", "CTRL_VS"), ("2", "2", "GND")]))
    schematic.add(c("CCAP", "100nF 25V X7R AEC-Q200", passive_0603, TI_DS, [("1", "1", "CTRL_CAP"), ("2", "2", "CTRL_VS")]))

    schematic.add(c("JDRIVE", "FORCED_DRIVER_KELVIN", "Q2C100:PinHeader_1x04_P2.54", "PB-100-q2-empirical-qualification-plan.md", [("1", "GATE", "Q2_HGATE"), ("2", "SOURCE_K", "COMMON_SOURCE"), ("3", "TRIGGER", "EXT_TRIGGER"), ("4", "INTERLOCK", "EXT_INTERLOCK")]))
    schematic.add(c("JHEAT", "ISOLATED_CASE_HEATER", "Q2C100:PinHeader_1x02_P2.54", "PB-100-q2-empirical-qualification-plan.md", [("1", "HEAT+", "HEATER_POS"), ("2", "HEAT-", "HEATER_NEG")]))
    schematic.add(c("JTEMP", "ISOLATED_TSEP_INPUT", "Q2C100:PinHeader_1x02_P2.54", "PB-100-q2-empirical-qualification-plan.md", [("1", "T+", "TSEP_POS"), ("2", "T-", "TSEP_NEG")]))

    testpoints = {
        "TPD": ("QDUT_DRAIN_KELVIN", "RAW_101V"),
        "TPG": ("QDUT_GATE_KELVIN", "Q2_HGATE"),
        "TPS": ("QDUT_SOURCE_KELVIN", "COMMON_SOURCE"),
        "TPHG": ("UCTRL_HGATE_PROBE", "Q2_HGATE"),
        "TPOUT": ("SYSTEM_OUT_PROBE", "SYSTEM_OUT"),
        "TPOV": ("OV_TRIGGER_PROBE", "CTRL_OV"),
        "TPVS": ("CTRL_VS_PROBE", "CTRL_VS"),
        "TPFLT": ("FAULT_PROBE", "CTRL_FLT_N"),
        "TPGND": ("PROBE_GND", "GND"),
    }
    for ref, (value, net) in testpoints.items():
        schematic.add(c(ref, value, "Q2C100:TestPoint_Loop_1.0mm", "PB-100-q2-empirical-qualification-plan.md", [("1", "TP", net, "passive")]))

    # Explicit off-board fixture endpoints keep ERC meaningful without placing
    # fictitious hardware on the coupon.
    for ref, net in (
        ("XEXT1", "EXT_TRIGGER"),
        ("XEXT2", "EXT_INTERLOCK"),
        ("XEXT3", "HEATER_POS"),
        ("XEXT4", "HEATER_NEG"),
        ("XEXT5", "TSEP_POS"),
        ("XEXT6", "TSEP_NEG"),
    ):
        schematic.add(c(ref, "EXTERNAL_FIXTURE_ENDPOINT", "", "PB-100-q2-empirical-qualification-plan.md", [("1", "EXT", net, "passive")], in_bom=False, on_board=False))
    schematic.add(c("XPWR1", "EXTERNAL_GND_SOURCE", "", "PB-100-q2-empirical-qualification-plan.md", [("1", "PWR", "GND", "power_out")], in_bom=False, on_board=False))
    schematic.add(c("XPWR2", "RVS_DERIVED_VS_SOURCE", "", TI_DS, [("1", "PWR", "CTRL_VS", "power_out")], in_bom=False, on_board=False))

    return schematic


def expression_end(text: str, start: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("unterminated KiCad expression")


def pad_blocks(text: str) -> list[tuple[int, int, str]]:
    return [
        (match.start(), expression_end(text, match.start()), match.group(1))
        for match in re.finditer(r'\(pad\s+"([^"]*)"', text)
    ]


def replace_uuids(text: str, ref: str) -> str:
    counter = 0

    def replacement(_: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        return f'(uuid "{layout_uid("footprint", ref, counter)}")'

    return re.sub(r'\(uuid\s+"[^"]+"\)', replacement, text)


def rotate_pad(block: str, rotation: float) -> str:
    pattern = re.compile(r'\(at\s+(-?[0-9.]+)\s+(-?[0-9.]+)(?:\s+(-?[0-9.]+))?\)')
    match = pattern.search(block)
    if match is None:
        raise ValueError("pad is missing an at expression")
    angle = (float(match.group(3) or 0.0) + rotation) % 360
    replacement = f"(at {match.group(1)} {match.group(2)} {angle:g})"
    return block[: match.start()] + replacement + block[match.end() :]


def insert_child(text: str, child: str) -> str:
    markers = ("\n\t(fp_", "\n\t(pad ", "\n\t(zone ", "\n\t(model ")
    positions = [position for marker in markers if (position := text.find(marker)) >= 0]
    insert_at = min(positions) + 1 if positions else text.rfind("\n)") + 1
    return text[:insert_at] + child + text[insert_at:]


def render_footprint(component: Component, placement: Placement, net_codes: dict[str, int]) -> str:
    library, footprint_name = component.footprint.split(":", 1)
    source_dir = PB_FP_DIR if library == "PB100" else LOCAL_FP_DIR
    source_path = source_dir / f"{footprint_name}.kicad_mod"
    if source_path.is_file():
        source_text = source_path.read_text(encoding="utf-8")
    else:
        source_text = custom_footprints()[source_path]
    text = replace_uuids(source_text, component.ref)
    text = re.sub(r'^\(footprint\s+"[^"]+"', f'(footprint "{library}:{esc(footprint_name)}"', text, count=1)
    text = re.sub(
        r'(\(layer\s+"F\.Cu"\))',
        lambda match: (
            f'{match.group(1)}\n\t(uuid "{layout_uid("footprint", component.ref, "root")}")\n'
            f'\t(at {placement.x_mm:.2f} {placement.y_mm:.2f} {placement.rotation:g})\n'
            f'\t(path "/{uid("Q2-C100", component.ref, "symbol")}")'
        ),
        text,
        count=1,
    )
    text = re.sub(r'(property\s+"Reference"\s+)"[^"]*"', rf'\1"{esc(component.ref)}"', text, count=1)
    text = re.sub(r'(property\s+"Value"\s+)"[^"]*"', rf'\1"{esc(component.value)}"', text, count=1)
    text = re.sub(r'(property\s+"Datasheet"\s+)"[^"]*"', rf'\1"{esc(component.datasheet)}"', text, count=1)
    text = re.sub(r'(property\s+"Description"\s+)"[^"]*"', r'\1""', text, count=1)
    if '(property "Datasheet"' not in text:
        text = insert_child(
            text,
            f'\t(property "Datasheet" "{esc(component.datasheet)}" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{layout_uid("footprint", component.ref, "datasheet")}") (effects (font (size 1.27 1.27))))\n',
        )
    if component.dnp:
        text = insert_child(text, "\t(attr dnp)\n")

    pins = {pin.number: pin for pin in component.pins}
    footprint_pad_numbers = {number for _, _, number in pad_blocks(text) if number}
    if footprint_pad_numbers != set(pins):
        raise ValueError(
            f"{component.ref} footprint pad set {sorted(footprint_pad_numbers)} "
            f"does not match schematic pin set {sorted(pins)}"
        )
    for start, end, number in reversed(pad_blocks(text)):
        if not number:
            continue
        pin = pins[number]
        additions = [
            f'\t\t(pinfunction "{esc(pin.name)}")',
            f'\t\t(pintype "{esc(pin.electrical_type)}")',
        ]
        if pin.net is not None:
            additions.insert(0, f'\t\t(net {net_codes[pin.net]} "{esc(pin.net)}")')
        block = rotate_pad(text[start:end], placement.rotation).rstrip()
        block = block[:-1].rstrip() + "\n" + "\n".join(additions) + "\n\t)"
        text = text[:start] + block + text[end:]
    return "\n".join(f"\t{line}" if line else line for line in text.splitlines())


def simple_footprint(name: str, pads: list[str], *, body_x: float, body_y: float, attr: str = "smd") -> str:
    lines = [
        f'(footprint "{name}"',
        '\t(version 20260206)',
        '\t(generator "svc-q2-coupon-generator")',
        '\t(layer "F.Cu")',
        f'\t(property "Reference" "REF**" (at 0 {-body_y / 2 - 1.5:.2f} 0) (layer "F.SilkS") (uuid "{layout_uid(name, "ref")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
        f'\t(property "Value" "{name}" (at 0 {body_y / 2 + 1.5:.2f} 0) (layer "F.Fab") (uuid "{layout_uid(name, "value")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
        f'\t(attr {attr})',
        f'\t(fp_rect (start {-body_x / 2:.2f} {-body_y / 2:.2f}) (end {body_x / 2:.2f} {body_y / 2:.2f}) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab") (uuid "{layout_uid(name, "fab")}"))',
        *pads,
        ')',
    ]
    return "\n".join(lines) + "\n"


def custom_footprints() -> dict[Path, str]:
    def smd_pad(name: str, x: float, y: float, sx: float, sy: float) -> str:
        return f'\t(pad "{name}" smd roundrect (at {x:g} {y:g}) (size {sx:g} {sy:g}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (uuid "{layout_uid("pad", name, x, y, sx, sy)}"))'

    footprints: dict[str, str] = {}
    footprints["R_C_0603_1608Metric"] = simple_footprint(
        "R_C_0603_1608Metric",
        [smd_pad("1", -0.85, 0, 0.9, 0.95), smd_pad("2", 0.85, 0, 0.9, 0.95)],
        body_x=1.6,
        body_y=0.8,
    )
    footprints["R_1206_3216Metric"] = simple_footprint(
        "R_1206_3216Metric",
        [smd_pad("1", -1.75, 0, 1.4, 1.8), smd_pad("2", 1.75, 0, 1.4, 1.8)],
        body_x=3.2,
        body_y=1.6,
    )
    footprints["C_1210_3225Metric"] = simple_footprint(
        "C_1210_3225Metric",
        [smd_pad("1", -1.8, 0, 1.5, 2.8), smd_pad("2", 1.8, 0, 1.5, 2.8)],
        body_x=3.2,
        body_y=2.5,
    )
    footprints["SOD123F"] = simple_footprint(
        "SOD123F",
        [smd_pad("1", -1.65, 0, 1.4, 1.4), smd_pad("2", 1.65, 0, 1.4, 1.4)],
        body_x=2.6,
        body_y=1.6,
    )

    for count in (2, 4):
        pads = []
        start = -(count - 1) * 1.27
        for index in range(count):
            x = start + index * 2.54
            shape = "rect" if index == 0 else "circle"
            pads.append(f'\t(pad "{index + 1}" thru_hole {shape} (at {x:.2f} 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (uuid "{layout_uid("header", count, index)}"))')
        footprints[f"PinHeader_1x0{count}_P2.54"] = simple_footprint(
            f"PinHeader_1x0{count}_P2.54",
            pads,
            body_x=count * 2.54,
            body_y=2.54,
            attr="through_hole",
        )

    footprints["TestPoint_Loop_1.0mm"] = simple_footprint(
        "TestPoint_Loop_1.0mm",
        [f'\t(pad "1" thru_hole circle (at 0 0) (size 2.4 2.4) (drill 1.0) (layers "*.Cu" "*.Mask") (uuid "{layout_uid("testpoint-pad")}"))'],
        body_x=2.5,
        body_y=2.5,
        attr="through_hole",
    )
    footprints["MountingHole_M3_NPTH"] = simple_footprint(
        "MountingHole_M3_NPTH",
        [f'\t(pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers "*.Cu" "*.Mask") (uuid "{layout_uid("mounting-pad")}"))'],
        body_x=3.2,
        body_y=3.2,
        attr="through_hole exclude_from_pos_files exclude_from_bom",
    )

    terminal_pads = []
    for row, y in enumerate((-2.54, 0.0, 2.54)):
        for column, x in enumerate((-2.54, 0.0, 2.54)):
            terminal_pads.append(
                f'\t(pad "1" thru_hole circle (at {x:g} {y:g}) (size 2.15 2.15) (drill 1.60) (layers "*.Cu" "*.Mask") (uuid "{layout_uid("redcube", row, column)}"))'
            )
    footprints["REDCUBE_786202073_3x3_P2.54"] = simple_footprint(
        "REDCUBE_786202073_3x3_P2.54",
        terminal_pads,
        body_x=7.0,
        body_y=7.0,
        attr="through_hole",
    )
    return {LOCAL_FP_DIR / f"{name}.kicad_mod": content for name, content in footprints.items()}


def segment(net_codes: dict[str, int], net: str, layer: str, width: float, start: tuple[float, float], end: tuple[float, float], token: str) -> str:
    return (
        f'\t(segment (start {start[0]:.3f} {start[1]:.3f}) (end {end[0]:.3f} {end[1]:.3f}) '
        f'(width {width:.3f}) (layer "{layer}") (net {net_codes[net]}) (uuid "{layout_uid("segment", token, layer)}"))'
    )


def via(net_codes: dict[str, int], net: str, x: float, y: float, token: str) -> str:
    return (
        f'\t(via (at {x:.3f} {y:.3f}) (size 1.2) (drill 0.6) (layers "F.Cu" "B.Cu") '
        f'(net {net_codes[net]}) (uuid "{layout_uid("via", token)}"))'
    )


def critical_routing(net_codes: dict[str, int]) -> list[str]:
    routes = []
    for layer in ("F.Cu", "B.Cu"):
        routes.extend(
            [
                segment(net_codes, "RAW_101V", layer, 7.0, (40.0, 12.0), (40.0, 28.0), "raw-main"),
                segment(net_codes, "COMMON_SOURCE", layer, 5.0, (40.0, 43.0), (40.0, 57.0), "common-spine"),
                segment(net_codes, "COMMON_SOURCE", layer, 6.0, (40.0, 50.0), (70.0, 50.0), "common-terminal"),
                segment(net_codes, "SYSTEM_OUT", layer, 7.0, (40.0, 72.0), (40.0, 90.0), "out-main"),
            ]
        )
    routes.extend(
        [
            segment(net_codes, "RAW_101V", "F.Cu", 5.0, (40.0, 28.0), (40.0, 33.45), "raw-neck"),
            segment(net_codes, "COMMON_SOURCE", "F.Cu", 0.8, (37.0, 39.1), (44.2, 39.1), "qdut-source-row"),
            segment(net_codes, "COMMON_SOURCE", "F.Cu", 0.8, (40.0, 39.1), (40.0, 43.0), "qdut-source-neck"),
            segment(net_codes, "COMMON_SOURCE", "F.Cu", 0.8, (35.8, 60.9), (43.0, 60.9), "qrev-source-row"),
            segment(net_codes, "COMMON_SOURCE", "F.Cu", 0.8, (40.0, 57.0), (40.0, 60.9), "qrev-source-neck"),
            segment(net_codes, "SYSTEM_OUT", "F.Cu", 5.0, (40.0, 66.55), (40.0, 72.0), "out-neck"),
            segment(net_codes, "Q2_HGATE", "F.Cu", 0.25, (20.0, 45.75), (22.0, 45.75), "hgate-a"),
            segment(net_codes, "Q2_HGATE", "F.Cu", 0.25, (22.0, 45.75), (22.0, 47.0), "hgate-b"),
            segment(net_codes, "Q2_HGATE", "F.Cu", 0.25, (22.0, 47.0), (28.0, 47.0), "hgate-c"),
            segment(net_codes, "Q2_HGATE", "F.Cu", 0.25, (28.0, 47.0), (35.8, 39.1), "hgate-d"),
        ]
    )
    # DGATE and the two controller source-sense paths cross power copper only
    # on separate internal layers and return through local vias.
    routes.extend(
        [
            segment(net_codes, "QREV_DGATE", "F.Cu", 0.25, (16.0, 43.75), (14.0, 43.75), "dgate-top-a"),
            segment(net_codes, "QREV_DGATE", "F.Cu", 0.25, (14.0, 43.75), (10.5, 42.5), "dgate-top-b"),
            via(net_codes, "QREV_DGATE", 10.5, 42.5, "dgate-left"),
            segment(net_codes, "QREV_DGATE", "In1.Cu", 0.25, (10.5, 42.5), (10.5, 62.5), "dgate-inner-a"),
            segment(net_codes, "QREV_DGATE", "In1.Cu", 0.25, (10.5, 62.5), (46.0, 62.5), "dgate-inner-b"),
            segment(net_codes, "QREV_DGATE", "In1.Cu", 0.25, (46.0, 62.5), (46.0, 60.9), "dgate-inner-c"),
            via(net_codes, "QREV_DGATE", 46.0, 60.9, "dgate-right"),
            segment(net_codes, "QREV_DGATE", "F.Cu", 0.25, (46.0, 60.9), (44.2, 60.9), "dgate-top-c"),
            segment(net_codes, "COMMON_SOURCE", "F.Cu", 0.25, (20.0, 45.25), (22.0, 45.25), "out-kelvin-top-a"),
            segment(net_codes, "COMMON_SOURCE", "F.Cu", 0.25, (22.0, 45.25), (23.0, 44.0), "out-kelvin-top-b"),
            via(net_codes, "COMMON_SOURCE", 23.0, 44.0, "out-kelvin-left"),
            segment(net_codes, "COMMON_SOURCE", "In2.Cu", 0.25, (23.0, 44.0), (37.0, 45.25), "out-kelvin-inner"),
            via(net_codes, "COMMON_SOURCE", 37.0, 45.25, "out-kelvin-right"),
            segment(net_codes, "COMMON_SOURCE", "F.Cu", 0.25, (16.0, 44.25), (14.0, 44.25), "a-kelvin-top-a"),
            segment(net_codes, "COMMON_SOURCE", "F.Cu", 0.25, (14.0, 44.25), (13.0, 47.0), "a-kelvin-top-b"),
            via(net_codes, "COMMON_SOURCE", 13.0, 47.0, "a-kelvin-left"),
            segment(net_codes, "COMMON_SOURCE", "In2.Cu", 0.25, (13.0, 47.0), (13.0, 40.0), "a-kelvin-inner-a"),
            segment(net_codes, "COMMON_SOURCE", "In2.Cu", 0.25, (13.0, 40.0), (37.0, 40.0), "a-kelvin-inner-b"),
            via(net_codes, "COMMON_SOURCE", 37.0, 40.0, "a-kelvin-right"),
        ]
    )
    for net, points in {
        "RAW_101V": ((37.0, 20.0), (43.0, 20.0), (37.0, 28.0), (43.0, 28.0)),
        "COMMON_SOURCE": ((37.0, 43.0), (43.0, 43.0), (37.0, 50.0), (43.0, 50.0), (50.0, 50.0), (60.0, 50.0), (37.0, 57.0), (43.0, 57.0)),
        "SYSTEM_OUT": ((37.0, 72.0), (43.0, 72.0), (37.0, 80.0), (43.0, 80.0)),
    }.items():
        for index, (x, y) in enumerate(points):
            routes.append(via(net_codes, net, x, y, f"{net}-{index}"))
    return routes


def mounting_hole(ref: str, x: float, y: float) -> str:
    component = Component(
        ref,
        "M3 NPTH",
        "Q2C100:MountingHole_M3_NPTH",
        "",
        tuple(),
        in_bom=False,
        on_board=True,
    )
    return render_footprint(component, Placement(x, y), {})


def render_board(schematic: Schematic) -> str:
    components = {component.ref: component for component in schematic.components if component.on_board}
    if set(components) != set(PLACEMENTS):
        raise ValueError(f"placement mismatch: missing={sorted(set(components) - set(PLACEMENTS))}, extra={sorted(set(PLACEMENTS) - set(components))}")
    net_names = sorted({pin.net for component in components.values() for pin in component.pins if pin.net is not None})
    net_codes = {name: index for index, name in enumerate(net_names, 1)}
    lines = [
        "(kicad_pcb",
        "\t(version 20260206)",
        '\t(generator "svc-q2-coupon-generator")',
        '\t(generator_version "1.0")',
        "\t(general (thickness 2.0) (legacy_teardrops no))",
        '\t(paper "A4")',
        "\t(layers",
        '\t\t(0 "F.Cu" signal)',
        '\t\t(2 "In1.Cu" power)',
        '\t\t(4 "In2.Cu" power)',
        '\t\t(6 "B.Cu" signal)',
        '\t\t(5 "F.SilkS" user "f.silkscreen")',
        '\t\t(7 "B.SilkS" user "b.silkscreen")',
        '\t\t(25 "Edge.Cuts" user)',
        '\t\t(27 "Margin" user)',
        '\t\t(31 "F.CrtYd" user "F.Courtyard")',
        "\t)",
        "\t(setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))",
        "\t(embedded_fonts no)",
        '\t(net 0 "")',
        *[f'\t(net {code} "{esc(name)}")' for name, code in net_codes.items()],
    ]
    for component in schematic.components:
        if component.on_board:
            lines.append(render_footprint(component, PLACEMENTS[component.ref], net_codes))
    for ref, x, y in (("H1", 5.0, 5.0), ("H2", 75.0, 5.0), ("H3", 5.0, 95.0), ("H4", 75.0, 95.0)):
        lines.append(mounting_hole(ref, x, y))
    lines.extend(critical_routing(net_codes))
    lines.extend(
        [
            f'\t(gr_rect (start 0 0) (end 80 100) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{layout_uid("outline")}"))',
            f'\t(gr_rect (start 32 5) (end 64 37) (stroke (width 0.2) (type dash)) (fill none) (layer "Cmts.User") (uuid "{layout_uid("hv-boundary")}"))',
            f'\t(gr_text "Q2-C100 Rev.1  QUALIFICATION COUPON ONLY" (at 40 97 0) (layer "F.SilkS") (uuid "{layout_uid("label-main")}") (effects (font (size 1.1 1.1) (thickness 0.18))))',
            f'\t(gr_text "RAW 101V" (at 65 10 0) (layer "F.SilkS") (uuid "{layout_uid("label-raw")}") (effects (font (size 1.2 1.2) (thickness 0.18))))',
            f'\t(gr_text "DANGER - NOT FOR VEHICLE / NOT FOR FAB" (at 40 3 0) (layer "F.SilkS") (uuid "{layout_uid("label-danger")}") (effects (font (size 1 1) (thickness 0.16))))',
            f'\t(gr_text "CRITICAL POWER + GATE LOOP ROUTED; FIXTURE NETS OPEN" (at 40 94.5 0) (layer "Cmts.User") (uuid "{layout_uid("label-state")}") (effects (font (size 0.9 0.9) (thickness 0.14))))',
        ]
    )
    lines.append(")")
    return "\n".join(lines) + "\n"


def render_rules() -> str:
    return """(version 1)

(rule "Q2-C100 default clearance"
    (constraint clearance (min 0.20mm)))

(rule "Q2-C100 RAW 101V clearance"
    (condition "(A.NetName == 'RAW_101V' || B.NetName == 'RAW_101V') && !(A.Reference == 'QDUT' || B.Reference == 'QDUT' || A.Reference == 'ROV1' || B.Reference == 'ROV1' || A.Reference == 'RVS' || B.Reference == 'RVS')")
    (constraint clearance (min 2.00mm)))

(rule "Q2-C100 routed width"
    (condition "A.NetName == 'Q2_HGATE' || A.NetName == 'QREV_DGATE' || A.NetName == 'COMMON_SOURCE' || A.NetName == 'RAW_101V' || A.NetName == 'SYSTEM_OUT'")
    (constraint track_width (min 0.25mm)))
"""


def render_project() -> str:
    return json.dumps(
        {
            "meta": {"filename": "Q2-C100.kicad_pro", "version": 1},
            "project": {
                "name": "Q2-C100",
                "description": "Q2 empirical qualification coupon; not PB-100 and not for vehicle installation",
            },
            "schematic": {"plot_directory": "exports/schematic/"},
            "text_variables": {"BOARD": "Q2-C100", "PROJECT": "SVC", "RELEASE": "QUALIFICATION-COUPON-ONLY"},
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    schematic = build_coupon()
    outputs = {
        SCHEMATIC_PATH: schematic.render(),
        SYMBOL_PATH: schematic.render_library(),
        BOARD_PATH: render_board(schematic),
        RULES_PATH: render_rules(),
        KICAD_DIR / "Q2-C100.kicad_pro": render_project(),
        KICAD_DIR / "sym-lib-table": '(sym_lib_table\n  (version 7)\n  (lib (name "Q2C100") (type "KiCad") (uri "${KIPRJMOD}/lib/Q2C100.kicad_sym") (options "") (descr "Q2-C100 generated symbols"))\n)\n',
        KICAD_DIR / "fp-lib-table": '(fp_lib_table\n  (version 7)\n  (lib (name "Q2C100") (type "KiCad") (uri "${KIPRJMOD}/lib/Q2C100.pretty") (options "") (descr "Q2-C100 generated footprints"))\n  (lib (name "PB100") (type "KiCad") (uri "${KIPRJMOD}/../../../kicad/lib/PB100.pretty") (options "") (descr "Reviewed PB-100 power footprints reused by Q2-C100"))\n)\n',
        **custom_footprints(),
    }
    stale = []
    for path, content in outputs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    for path in stale:
        print(f"stale generated file: {path.relative_to(ROOT)}")
    return 1 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
