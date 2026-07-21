#!/usr/bin/env python3
"""Generate the controlled FB-100 KiCad board-import and layout rules."""

from __future__ import annotations

import argparse
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from generate_lb_fb_schematics import Component, build_fb, uid


ROOT = Path(__file__).resolve().parents[1]
FB_DIR = ROOT / "hardware" / "front-board" / "FB-100"
KICAD_DIR = FB_DIR / "kicad"
FOOTPRINT_DIR = KICAD_DIR / "lib" / "FB100.pretty"
BOARD_PATH = KICAD_DIR / "FB-100.kicad_pcb"
RULES_PATH = KICAD_DIR / "FB-100.kicad_dru"
LAYOUT_UUID_NS = uuid.UUID("69d2789f-f372-48ba-b4ad-9142061f7a18")


@dataclass(frozen=True)
class Placement:
    x_mm: float
    y_mm: float
    rotation: float = 0.0
    side: str = "F"


PLACEMENTS = {
    "J1": Placement(2.37, 17.50, -90),
    "D1": Placement(7.50, 17.50, 90),
    "R11": Placement(10.00, 11.50, 90),
    "R12": Placement(13.00, 11.50, 90),
    "R13": Placement(10.50, 15.00),
    "R14": Placement(13.50, 15.00),
    "C1": Placement(13.50, 18.00),
    "R15": Placement(3.00, 24.50),
    "C2": Placement(6.00, 24.50),
    "D2": Placement(12.00, 26.00),
    "U1": Placement(12.00, 21.50),
    "C3": Placement(15.50, 20.50, 90),
    "C4": Placement(7.00, 20.50, 90),
    "C5": Placement(15.50, 23.50, 90),
    "R16": Placement(9.00, 23.00, 90),
    "J2": Placement(18.50, 9.00),
    "R19": Placement(22.00, 9.00),
    "SW1": Placement(55.00, 9.00),
    "R17": Placement(52.00, 13.50),
    "C6": Placement(56.00, 13.50),
    "SW2": Placement(67.00, 9.00),
    "R18": Placement(64.00, 13.50),
    "C7": Placement(68.00, 13.50),
    "JFB1": Placement(75.20, 17.50, -90, "B"),
    **{
        f"D{index + 2}": Placement(15.00 + index * 5.00, 26.00)
        for index in range(1, 11)
    },
    **{
        f"R{index}": Placement(15.00 + index * 5.00, 31.50)
        for index in range(1, 11)
    },
}


def layout_uid(*parts: object) -> str:
    return str(uuid.uuid5(LAYOUT_UUID_NS, ":".join(str(part) for part in parts)))


def escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


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
    blocks = []
    for match in re.finditer(r'\(pad\s+"([^"]*)"', text):
        blocks.append((match.start(), expression_end(text, match.start()), match.group(1)))
    return blocks


def rotate_pad(block: str, rotation: float) -> str:
    pattern = re.compile(r'\(at\s+(-?[0-9.]+)\s+(-?[0-9.]+)(?:\s+(-?[0-9.]+))?\)')
    match = pattern.search(block)
    if match is None:
        raise ValueError("pad is missing an at expression")
    angle = (float(match.group(3) or 0.0) + rotation) % 360
    angle_text = f"{angle:g}" if angle else "0"
    replacement = f"(at {match.group(1)} {match.group(2)} {angle_text})"
    return block[:match.start()] + replacement + block[match.end():]


def replace_uuids(text: str, ref: str) -> str:
    counter = 0

    def replacement(_: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        return f'(uuid "{layout_uid("footprint", ref, counter)}")'

    return re.sub(r'\(uuid\s+"[^"]+"\)', replacement, text)


def flipped_layers(text: str) -> str:
    layer_map = {
        "F.Cu": "B.Cu",
        "F.Paste": "B.Paste",
        "F.Mask": "B.Mask",
        "F.SilkS": "B.SilkS",
        "F.Fab": "B.Fab",
        "F.CrtYd": "B.CrtYd",
    }
    return re.sub(
        r'"(F\.(?:Cu|Paste|Mask|SilkS|Fab|CrtYd))"',
        lambda match: f'"{layer_map[match.group(1)]}"',
        text,
    )


def insert_footprint_child(text: str, child: str) -> str:
    markers = ("\n\t(fp_", "\n\t(pad ", "\n\t(zone ", "\n\t(model ")
    positions = [position for marker in markers if (position := text.find(marker)) >= 0]
    insert_at = min(positions) + 1 if positions else text.rfind("\n)") + 1
    return text[:insert_at] + child + text[insert_at:]


def hide_reference(text: str) -> str:
    start = text.find('(property "Reference"')
    if start < 0:
        raise ValueError("footprint is missing its Reference property")
    end = expression_end(text, start)
    block = text[start:end]
    if "(hide yes)" in block:
        return text
    layer = re.search(r'\(layer\s+"[FB]\.SilkS"\)', block)
    if layer is None:
        raise ValueError("footprint Reference is not on a silkscreen layer")
    insert_at = start + layer.end()
    return text[:insert_at] + "\n\t\t(hide yes)" + text[insert_at:]


def render_footprint(component: Component, placement: Placement, net_codes: dict[str, int]) -> str:
    footprint_name = component.footprint.split(":", 1)[1]
    path = FOOTPRINT_DIR / f"{footprint_name}.kicad_mod"
    text = replace_uuids(path.read_text(encoding="utf-8"), component.ref)
    if placement.side == "B":
        text = flipped_layers(text)
    text = re.sub(
        r'^\(footprint\s+"[^"]+"',
        f'(footprint "FB100:{escape(footprint_name)}"',
        text,
        count=1,
    )
    text = re.sub(
        r'(\(layer\s+"[FB]\.Cu"\))',
        lambda match: (
            f'{match.group(1)}\n'
            f'\t(uuid "{layout_uid("footprint", component.ref, "root")}")\n'
            f'\t(at {placement.x_mm:.2f} {placement.y_mm:.2f} {placement.rotation:g})\n'
            f'\t(path "/{uid("FB-100", component.ref, "symbol")}")'
        ),
        text,
        count=1,
    )
    text = re.sub(
        r'(property\s+"Reference"\s+)"[^"]*"',
        rf'\1"{escape(component.ref)}"',
        text,
        count=1,
    )
    text = re.sub(
        r'(property\s+"Value"\s+)"[^"]*"',
        rf'\1"{escape(component.value)}"',
        text,
        count=1,
    )
    text = re.sub(
        r'(property\s+"Datasheet"\s+)"[^"]*"',
        rf'\1"{escape(component.datasheet)}"',
        text,
        count=1,
    )
    text = re.sub(
        r'(property\s+"Description"\s+)"[^"]*"',
        r'\1""',
        text,
        count=1,
    )
    text = hide_reference(text)
    if '(property "Datasheet"' not in text:
        property_text = (
            f'\t(property "Datasheet" "{escape(component.datasheet)}" '
            f'(at 0 0 0) (layer "{placement.side}.Fab") (hide yes) '
            f'(uuid "{layout_uid("footprint", component.ref, "datasheet")}") '
            '(effects (font (size 1.27 1.27))))\n'
        )
        text = insert_footprint_child(text, property_text)
    if component.dnp:
        if re.search(r'\(attr\s+', text):
            text = re.sub(
                r'\(attr\s+([^\)]*)\)',
                lambda match: f'(attr {match.group(1).strip()} dnp)',
                text,
                count=1,
            )
        else:
            text = insert_footprint_child(
                text,
                "\t(attr through_hole dnp)\n",
            )

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
    return "\n".join(
        (f"\t{line}" if line else line).rstrip()
        for line in text.splitlines()
    )


def mounting_hole(ref: str, x_mm: float, y_mm: float) -> str:
    return f'''\t(footprint "FB100:MountingHole_2.7mm_M2.5"
\t\t(layer "F.Cu")
\t\t(uuid "{layout_uid(ref, "root")}")
\t\t(at {x_mm:.2f} {y_mm:.2f})
\t\t(property "Reference" "{ref}" (at 0 -4 0) (layer "F.SilkS") (uuid "{layout_uid(ref, "reference")}") (effects (font (size 1 1) (thickness 0.15))))
\t\t(property "Value" "M2.5 NPTH" (at 0 4 0) (layer "F.Fab") (uuid "{layout_uid(ref, "value")}") (effects (font (size 1 1) (thickness 0.15))))
\t\t(attr exclude_from_pos_files exclude_from_bom)
\t\t(fp_circle (center 0 0) (end 3.5 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{layout_uid(ref, "courtyard")}"))
\t\t(fp_circle (center 0 0) (end 2 0) (stroke (width 0.25) (type solid)) (fill no) (layer "F.SilkS") (uuid "{layout_uid(ref, "silk")}"))
\t\t(pad "" np_thru_hole circle (at 0 0) (size 2.7 2.7) (drill 2.7) (layers "*.Cu" "*.Mask") (uuid "{layout_uid(ref, "pad")}"))
\t)'''


def board_graphics() -> list[str]:
    graphics = [
        f'\t(gr_rect (start 0 0) (end 80 35) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{layout_uid("outline")}"))',
        f'\t(gr_rect (start -12 13.5) (end 0 21.5) (stroke (width 0.15) (type dash)) (fill none) (layer "Cmts.User") (uuid "{layout_uid("usb-panel-keepout")}"))',
        f'\t(gr_rect (start 80 12.5) (end 100 22.5) (stroke (width 0.15) (type dash)) (fill none) (layer "Cmts.User") (uuid "{layout_uid("ffc-cable-keepout")}"))',
        f'\t(gr_rect (start 18 7) (end 46 23) (stroke (width 0.15) (type dash)) (fill none) (layer "Cmts.User") (uuid "{layout_uid("oled-window")}"))',
        f'\t(gr_rect (start 52 6) (end 58 12) (stroke (width 0.15) (type dash)) (fill none) (layer "Cmts.User") (uuid "{layout_uid("service-keepout")}"))',
        f'\t(gr_rect (start 64 6) (end 70 12) (stroke (width 0.15) (type dash)) (fill none) (layer "Cmts.User") (uuid "{layout_uid("reset-keepout")}"))',
        f'\t(gr_text "FB-100 Rev.1  LAYOUT-ONLY" (at 40 33.5 0) (layer "F.SilkS") (uuid "{layout_uid("board-label")}") (effects (font (size 1.2 1.2) (thickness 0.18))))',
        f'\t(gr_text "USB PANEL KEEPOUT" (at -6 12.5 0) (layer "Cmts.User") (uuid "{layout_uid("usb-label")}") (effects (font (size 1 1) (thickness 0.15))))',
        f'\t(gr_text "FFC BEND KEEPOUT" (at 90 11.5 0) (layer "Cmts.User") (uuid "{layout_uid("ffc-label")}") (effects (font (size 1 1) (thickness 0.15))))',
        f'\t(gr_text "OLED DNP WINDOW" (at 32 15 0) (layer "Cmts.User") (uuid "{layout_uid("oled-label")}") (effects (font (size 1 1) (thickness 0.15))))',
        f'\t(gr_text "SERVICE" (at 55 5 0) (layer "F.SilkS") (uuid "{layout_uid("service-label")}") (effects (font (size 0.9 0.9) (thickness 0.15))))',
        f'\t(gr_text "RESET" (at 67 5 0) (layer "F.SilkS") (uuid "{layout_uid("reset-label")}") (effects (font (size 0.9 0.9) (thickness 0.15))))',
        f'\t(gr_text "STATUS" (at 12 30.5 0) (layer "F.SilkS") (uuid "{layout_uid("status-label")}") (effects (font (size 0.9 0.9) (thickness 0.15))))',
    ]
    for index in range(1, 11):
        channel_x_mm = 15.0 + index * 5.0
        graphics.extend(
            [
                f'\t(gr_circle (center {channel_x_mm:.2f} 26) (end {channel_x_mm + 3:.2f} 26) (stroke (width 0.12) (type dash)) (fill none) (layer "Cmts.User") (uuid "{layout_uid("optical", index)}"))',
                f'\t(gr_text "CH{index}" (at {channel_x_mm:.2f} 29.7 0) (layer "F.SilkS") (uuid "{layout_uid("channel-label", index)}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            ]
        )
    graphics.append(
        f'\t(gr_circle (center 12 26) (end 15 26) (stroke (width 0.12) (type dash)) (fill none) (layer "Cmts.User") (uuid "{layout_uid("status-optical")}"))'
    )
    return graphics


def render_board() -> str:
    schematic = build_fb()
    components = {component.ref: component for component in schematic.components}
    if set(components) != set(PLACEMENTS):
        missing = sorted(set(components) - set(PLACEMENTS))
        extra = sorted(set(PLACEMENTS) - set(components))
        raise ValueError(f"placement map mismatch; missing={missing}, extra={extra}")
    net_names = sorted(
        {
            pin.net
            for component in schematic.components
            for pin in component.pins
            if pin.net is not None
        }
    )
    net_codes = {name: index for index, name in enumerate(net_names, 1)}
    lines = [
        "(kicad_pcb",
        "\t(version 20260206)",
        '\t(generator "svc-fb100-layout-generator")',
        '\t(generator_version "1.0")',
        "\t(general",
        "\t\t(thickness 1.6)",
        "\t\t(legacy_teardrops no)",
        "\t)",
        '\t(paper "A4")',
        "\t(layers",
        '\t\t(0 "F.Cu" signal)',
        '\t\t(2 "B.Cu" signal)',
        '\t\t(5 "F.SilkS" user "f.silkscreen")',
        '\t\t(7 "B.SilkS" user "b.silkscreen")',
        '\t\t(25 "Edge.Cuts" user)',
        '\t\t(27 "Margin" user)',
        '\t\t(31 "F.CrtYd" user "F.Courtyard")',
        '\t\t(29 "B.CrtYd" user "B.Courtyard")',
        "\t)",
        "\t(setup",
        "\t\t(pad_to_mask_clearance 0)",
        "\t\t(allow_soldermask_bridges_in_footprints no)",
        "\t\t(tenting (front yes) (back yes))",
        "\t\t(covering (front no) (back no))",
        "\t\t(plugging (front no) (back no))",
        "\t\t(capping no)",
        "\t\t(filling no)",
        "\t)",
        "\t(embedded_fonts no)",
        '\t(net 0 "")',
        *[f'\t(net {code} "{escape(name)}")' for name, code in net_codes.items()],
    ]
    for component in schematic.components:
        lines.append(render_footprint(component, PLACEMENTS[component.ref], net_codes))
    for reference, x_mm, y_mm in (
        ("H1", 5.0, 5.0),
        ("H2", 75.0, 5.0),
        ("H3", 5.0, 30.0),
        ("H4", 75.0, 30.0),
    ):
        lines.append(mounting_hole(reference, x_mm, y_mm))
    lines.extend(board_graphics())
    lines.append(")")
    return "\n".join(lines) + "\n"


def render_rules() -> str:
    return """(version 1)

(rule "FB-100 minimum copper clearance"
    (constraint clearance (min 0.15mm)))

(rule "FB-100 minimum routed width"
    (constraint track_width (min 0.15mm)))

(rule "FB-100 USB data width"
    (condition "A.NetName == 'USB_D_P' || A.NetName == 'USB_D_N' || A.NetName == 'USB_D_P_CONN' || A.NetName == 'USB_D_N_CONN'")
    (constraint track_width (min 0.15mm) (opt 0.20mm) (max 0.30mm)))

(rule "FB-100 USB differential gap"
    (condition "A.NetName == 'USB_D_P' || A.NetName == 'USB_D_N'")
    (constraint diff_pair_gap (min 0.15mm) (opt 0.20mm) (max 0.30mm))
    (constraint diff_pair_uncoupled (max 1.00mm)))

(rule "FB-100 USB-C locator-hole clearance"
    (condition "A.Reference == 'J1' && B.Reference == 'J1'")
    (constraint hole_clearance (min 0.00mm)))
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = {
        BOARD_PATH: render_board(),
        RULES_PATH: render_rules(),
    }
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
