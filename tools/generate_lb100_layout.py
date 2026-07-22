#!/usr/bin/env python3
"""Generate the controlled LB-100 KiCad board-import milestone."""

from __future__ import annotations

import argparse
import csv
import re
import uuid
from pathlib import Path

from generate_fb100_layout import (
    Placement,
    escape,
    expression_end,
    flipped_layers,
    hide_reference,
    insert_footprint_child,
    pad_blocks,
    rotate_pad,
)
from generate_lb_fb_schematics import Component, build_lb, uid


ROOT = Path(__file__).resolve().parents[1]
LB_DIR = ROOT / "hardware" / "logic-board" / "LB-100"
KICAD_DIR = LB_DIR / "kicad"
FOOTPRINT_DIR = KICAD_DIR / "lib" / "LB100.pretty"
BOARD_PATH = KICAD_DIR / "LB-100.kicad_pcb"
RULES_PATH = KICAD_DIR / "LB-100.kicad_dru"
ROUTING_PATH = KICAD_DIR / "LB-100-routing.csv"
LAYOUT_UUID_NS = uuid.UUID("cbd021d0-d8ce-4de8-a290-5a8fcaa1db00")


PLACEMENTS = {
    "JPB1": Placement(50.0, 35.0, 0, "B"),
    "JFB1": Placement(6.0, 35.0, 90),
    "JSD1": Placement(90.5, 27.0, 90),
    "JDBG1": Placement(66.0, 5.5, 90),
    "JBT1": Placement(76.0, 5.5, 90),
    "U1": Placement(45.0, 35.0),
    "U2": Placement(18.0, 35.0, 90),
    "U3": Placement(60.0, 48.0, 90),
    "U4": Placement(28.0, 10.0, 90),
    "U5": Placement(42.0, 10.0, 90),
    "U6": Placement(56.0, 10.0, 90),
    "U7": Placement(70.5, 62.0, 90),
    "U8": Placement(68.0, 27.0, 90),
    "U9": Placement(69.0, 42.0, 90),
    "U10": Placement(65.0, 35.0, 90),
    "U11": Placement(60.0, 58.0),
    "U12": Placement(82.0, 30.0, 90),
    "U13": Placement(78.0, 47.0, 90),
    "U14": Placement(14.0, 21.0, 90),
    "U15": Placement(72.0, 49.0, 90),
    "U16": Placement(88.0, 43.0, 90),
    "U17": Placement(78.0, 39.0, 90),
    "U18": Placement(33.0, 58.0, 90),
    "U19": Placement(30.0, 65.0, 90),
    "D19": Placement(23.0, 58.0, 90),
    "D20": Placement(20.0, 65.0, 90),
    "Q18": Placement(28.0, 58.0, 90),
    "Q19": Placement(25.0, 65.0, 90),
    "Y1": Placement(34.0, 35.0, 90),
    "Y2": Placement(55.5, 42.0, 90),
    "C1": Placement(13.0, 31.0, 90),
    "C2": Placement(13.0, 34.5, 90),
    "C3": Placement(13.0, 38.0, 90),
    "R1": Placement(13.0, 41.5, 90),
    "R2": Placement(17.0, 43.0),
    "R3": Placement(20.0, 43.0),
    "FB1": Placement(23.0, 43.0),
    "C4": Placement(26.0, 43.0),
    "C5": Placement(29.0, 43.0),
    "C6": Placement(38.0, 49.0),
    "C7": Placement(41.0, 49.0),
    "R4": Placement(38.0, 20.0),
    "C8": Placement(41.0, 20.0),
    "R5": Placement(44.0, 20.0),
    "R6": Placement(56.0, 54.0),
    "R7": Placement(59.0, 54.0),
    "R8": Placement(62.0, 54.0),
    "R9": Placement(80.0, 52.0),
    "R10": Placement(78.0, 14.0),
    "R11": Placement(78.0, 17.0),
    "R12": Placement(78.0, 20.0),
    "R13": Placement(14.0, 46.0),
    "R14": Placement(17.0, 46.0),
    "R15": Placement(20.0, 46.0),
    "C9": Placement(31.0, 32.0, 90),
    "C10": Placement(31.0, 38.0, 90),
    "C11": Placement(56.0, 38.0, 90),
    "C12": Placement(59.0, 38.0, 90),
    "C13": Placement(78.0, 35.0, 90),
    "C14": Placement(82.0, 47.0, 90),
    "R16": Placement(26.0, 46.0),
    "R17": Placement(29.0, 46.0),
    "C28": Placement(25.0, 49.0),
    "C29": Placement(28.0, 49.0),
    "C30": Placement(62.0, 31.0, 90),
    "C31": Placement(68.0, 35.0, 90),
    "R18": Placement(88.0, 49.0),
    "R19": Placement(92.0, 49.0),
    "R20": Placement(68.0, 49.0, 90),
    "R21": Placement(68.0, 52.0, 90),
    "R22": Placement(50.0, 55.0, 90),
    "C32": Placement(76.0, 52.0),
    "C33": Placement(96.0, 53.0),
    "C34": Placement(88.0, 62.0),
    "R23": Placement(44.0, 58.0),
    "R24": Placement(47.0, 58.0),
    "R25": Placement(50.0, 58.0),
    "R26": Placement(53.0, 58.0),
    "R27": Placement(41.0, 65.0),
    "R28": Placement(44.0, 65.0),
    "R29": Placement(47.0, 65.0),
    "R30": Placement(50.0, 65.0),
    "C35": Placement(38.0, 58.0),
    "C36": Placement(35.0, 65.0),
    "C37": Placement(41.0, 58.0),
    "C38": Placement(38.0, 65.0),
    "C15": Placement(35.0, 24.0, 90),
    "C16": Placement(35.0, 27.0, 90),
    "C17": Placement(35.0, 30.0, 90),
    "C18": Placement(35.0, 40.0, 90),
    "C19": Placement(35.0, 43.0, 90),
    "C20": Placement(35.0, 46.0, 90),
    "C21": Placement(53.5, 25.0, 90),
    "C22": Placement(96.0, 56.0),
    "C23": Placement(92.0, 56.0),
    "C24": Placement(88.0, 59.0),
    "C25": Placement(92.0, 59.0),
    "C26": Placement(82.0, 23.0),
    "C27": Placement(82.0, 26.0),
}


def layout_uid(*parts: object) -> str:
    return str(uuid.uuid5(LAYOUT_UUID_NS, ":".join(str(part) for part in parts)))


def replace_uuids(text: str, ref: str) -> str:
    counter = 0

    def replacement(_: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        return f'(uuid "{layout_uid("footprint", ref, counter)}")'

    return re.sub(r'\(uuid\s+"[^"]+"\)', replacement, text)


def render_footprint(component: Component, placement: Placement, net_codes: dict[str, int]) -> str:
    footprint_name = component.footprint.split(":", 1)[1]
    path = FOOTPRINT_DIR / f"{footprint_name}.kicad_mod"
    text = replace_uuids(path.read_text(encoding="utf-8"), component.ref)
    if placement.side == "B":
        text = flipped_layers(text)
    text = re.sub(
        r'^\(footprint\s+"[^"]+"',
        f'(footprint "LB100:{escape(footprint_name)}"',
        text,
        count=1,
    )
    text = re.sub(
        r'(\(layer\s+"[FB]\.Cu"\))',
        lambda match: (
            f'{match.group(1)}\n'
            f'\t(uuid "{layout_uid("footprint", component.ref, "root")}")\n'
            f'\t(at {placement.x_mm:.2f} {placement.y_mm:.2f} {placement.rotation:g})\n'
            f'\t(path "/{uid("LB-100", component.ref, "symbol")}")'
        ),
        text,
        count=1,
    )
    for property_name, value in (
        ("Reference", component.ref),
        ("Value", component.value),
        ("Datasheet", component.datasheet),
        ("Description", ""),
    ):
        text = re.sub(
            rf'(property\s+"{property_name}"\s+)"[^"]*"',
            rf'\1"{escape(value)}"',
            text,
            count=1,
        )
    text = hide_reference(text)
    if '(property "Datasheet"' not in text:
        text = insert_footprint_child(
            text,
            f'\t(property "Datasheet" "{escape(component.datasheet)}" '
            f'(at 0 0 0) (layer "{placement.side}.Fab") (hide yes) '
            f'(uuid "{layout_uid("footprint", component.ref, "datasheet")}") '
            '(effects (font (size 1.27 1.27))))\n',
        )
    if component.dnp:
        if re.search(r'\(attr\s+', text):
            text = re.sub(
                r'\(attr\s+([^\)]*)\)',
                lambda match: f'(attr {match.group(1).strip()} dnp)',
                text,
                count=1,
            )
        else:
            text = insert_footprint_child(text, "\t(attr through_hole dnp)\n")

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
            f'\t\t(pinfunction "{escape(pin.name)}")',
            f'\t\t(pintype "{escape(pin.electrical_type)}")',
        ]
        if pin.net is not None:
            additions.insert(0, f'\t\t(net {net_codes[pin.net]} "{escape(pin.net)}")')
        block = rotate_pad(text[start:end], placement.rotation)
        block = block[:-1] + "\n" + "\n".join(additions) + "\n\t)"
        text = text[:start] + block + text[end:]
    return "\n".join((f"\t{line}" if line else line).rstrip() for line in text.splitlines())


def mounting_hole(ref: str, x_mm: float, y_mm: float, shared: bool) -> str:
    label = "STACK M2.5 NPTH" if shared else "LOCAL M2.5 NPTH"
    return f'''\t(footprint "LB100:MountingHole_2.7mm_M2.5"
\t\t(layer "F.Cu")
\t\t(uuid "{layout_uid(ref, "root")}")
\t\t(at {x_mm:.2f} {y_mm:.2f})
\t\t(property "Reference" "{ref}" (at 0 -4 0) (layer "F.SilkS") (hide yes) (uuid "{layout_uid(ref, "reference")}") (effects (font (size 1 1) (thickness 0.15))))
\t\t(property "Value" "{label}" (at 0 4 0) (layer "F.Fab") (uuid "{layout_uid(ref, "value")}") (effects (font (size 1 1) (thickness 0.15))))
\t\t(attr exclude_from_pos_files exclude_from_bom)
\t\t(fp_circle (center 0 0) (end 3.5 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{layout_uid(ref, "courtyard")}"))
\t\t(fp_circle (center 0 0) (end 2 0) (stroke (width 0.25) (type solid)) (fill no) (layer "F.SilkS") (uuid "{layout_uid(ref, "silk")}"))
\t\t(pad "" np_thru_hole circle (at 0 0) (size 2.7 2.7) (drill 2.7) (layers "*.Cu" "*.Mask") (uuid "{layout_uid(ref, "pad")}"))
\t)'''


def board_graphics() -> list[str]:
    rectangles = (
        ("outline", 0, 0, 100, 70, "Edge.Cuts", "default"),
        ("mcu-zone", 28, 18, 58, 48, "Cmts.User", "dash"),
        ("power-zone", 10, 22, 30, 48, "Cmts.User", "dash"),
        ("microsd-zone", 82, 8, 100, 28, "Cmts.User", "dash"),
        ("ble-zone", 72, 48, 100, 70, "Cmts.User", "dash"),
        ("imu-zone", 58, 28, 72, 42, "Cmts.User", "dash"),
        ("lux-zone", 60, 55, 74, 65, "Cmts.User", "dash"),
        ("service-zone", 20, 0, 80, 12, "Cmts.User", "dash"),
    )
    graphics = [
        f'\t(gr_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.1) (type {style})) (fill none) (layer "{layer}") (uuid "{layout_uid(name)}"))'
        for name, x1, y1, x2, y2, layer, style in rectangles
    ]
    graphics.extend(
        [
            f'\t(gr_text "LB-100 REV.1 EVT - NOT FOR PRODUCTION" (at 30 68 0) (layer "F.SilkS") (uuid "{layout_uid("board-label")}") (effects (font (size 1 1) (thickness 0.16))))',
            f'\t(gr_text "BLE ANTENNA - COPPER KEEPOUT REVIEW" (at 86 66 0) (layer "Cmts.User") (uuid "{layout_uid("ble-label")}") (effects (font (size 0.7 0.7) (thickness 0.12))))',
            f'\t(gr_text "MICROSD ACCESS" (at 91 7 0) (layer "Cmts.User") (uuid "{layout_uid("sd-label")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            f'\t(gr_text "SERVICE / EXPANSION" (at 50 2 0) (layer "Cmts.User") (uuid "{layout_uid("service-label")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            f'\t(gr_text "FOG A/B INPUT PROTECTION" (at 74 67 0) (layer "F.SilkS") (uuid "{layout_uid("fog-label")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
        ]
    )
    return graphics


def routed_copper(net_codes: dict[str, int]) -> list[str]:
    copper = []
    with ROUTING_PATH.open(newline="", encoding="utf-8") as routing_file:
        for index, row in enumerate(csv.DictReader(routing_file), 1):
            net_name = row["net"]
            if net_name not in net_codes:
                raise ValueError(f"routing manifest references unknown net {net_name}")
            route_uuid = layout_uid(
                "route",
                index,
                *(row[column] for column in row),
            )
            if row["kind"] == "segment":
                copper.append(
                    f'\t(segment (start {row["start_x_mm"]} {row["start_y_mm"]}) '
                    f'(end {row["end_x_mm"]} {row["end_y_mm"]}) '
                    f'(width {row["width_mm"]}) (layer "{row["layer"]}") '
                    f'(net {net_codes[net_name]}) (uuid "{route_uuid}"))'
                )
            elif row["kind"] == "via":
                copper.append(
                    f'\t(via (at {row["start_x_mm"]} {row["start_y_mm"]}) '
                    f'(size {row["diameter_mm"]}) (drill {row["drill_mm"]}) '
                    f'(layers "{row["start_layer"]}" "{row["end_layer"]}") '
                    f'(net {net_codes[net_name]}) (uuid "{route_uuid}"))'
                )
            else:
                raise ValueError(f'unknown routing manifest kind {row["kind"]}')
    return copper


def render_board() -> str:
    schematic = build_lb()
    components = {component.ref: component for component in schematic.components}
    if set(components) != set(PLACEMENTS):
        missing = sorted(set(components) - set(PLACEMENTS))
        extra = sorted(set(PLACEMENTS) - set(components))
        raise ValueError(f"placement map mismatch; missing={missing}, extra={extra}")
    net_names = sorted(
        {pin.net for component in schematic.components for pin in component.pins if pin.net}
    )
    net_codes = {name: index for index, name in enumerate(net_names, 1)}
    lines = [
        "(kicad_pcb",
        "\t(version 20260206)",
        '\t(generator "svc-lb100-layout-generator")',
        '\t(generator_version "1.0")',
        "\t(general (thickness 1.6) (legacy_teardrops no))",
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
        '\t\t(29 "B.CrtYd" user "B.Courtyard")',
        "\t)",
        "\t(setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))",
        "\t(embedded_fonts no)",
        '\t(net 0 "")',
        *[f'\t(net {code} "{escape(name)}")' for name, code in net_codes.items()],
    ]
    for component in schematic.components:
        lines.append(render_footprint(component, PLACEMENTS[component.ref], net_codes))
    for reference, x_mm, y_mm, shared in (
        ("H1", 5.0, 5.0, False),
        ("H2", 95.0, 5.0, False),
        ("H3", 5.0, 65.0, False),
        ("H4", 95.0, 65.0, False),
        ("H5", 15.0, 15.0, True),
        ("H6", 85.0, 15.0, True),
        ("H7", 15.0, 55.0, True),
        ("H8", 85.0, 55.0, True),
    ):
        lines.append(mounting_hole(reference, x_mm, y_mm, shared))
    lines.extend(routed_copper(net_codes))
    lines.extend(board_graphics())
    lines.append(")")
    return "\n".join(lines) + "\n"


def render_rules() -> str:
    return """(version 1)

(rule "LB-100 minimum copper clearance"
    (constraint clearance (min 0.15mm)))

(rule "LB-100 minimum routed width"
    (constraint track_width (min 0.15mm)))

(rule "LB-100 USB preliminary width boundary"
    (condition "A.NetName == 'USB_D_P' || A.NetName == 'USB_D_N'")
    (constraint track_width (min 0.15mm) (opt 0.20mm) (max 0.30mm)))

(rule "LB-100 USB preliminary differential gap"
    (condition "A.NetName == 'USB_D_P' || A.NetName == 'USB_D_N'")
    (constraint diff_pair_gap (min 0.15mm) (opt 0.20mm) (max 0.30mm))
    (constraint diff_pair_uncoupled (max 1.00mm)))
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = {BOARD_PATH: render_board(), RULES_PATH: render_rules()}
    stale = []
    for path, content in outputs.items():
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
