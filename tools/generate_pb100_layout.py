#!/usr/bin/env python3
"""Generate the controlled partial PB-100 EVT board-import milestone."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from generate_fb100_layout import (
    Placement,
    escape,
    expression_end,
    hide_reference,
    insert_footprint_child,
    pad_blocks,
    rotate_pad,
)
from generate_lb_fb_schematics import Component, Pin


ROOT = Path(__file__).resolve().parents[1]
PB_DIR = ROOT / "hardware" / "power-board" / "PB-100"
KICAD_DIR = PB_DIR / "kicad"
SCHEMATIC_PATH = KICAD_DIR / "PB-100.kicad_sch"
FOOTPRINT_DIR = KICAD_DIR / "lib" / "PB100.pretty"
BOARD_PATH = KICAD_DIR / "PB-100.kicad_pcb"
RULES_PATH = KICAD_DIR / "PB-100.kicad_dru"
ROUTING_PATH = KICAD_DIR / "PB-100-can-routing.csv"
LAYOUT_UUID_NS = uuid.UUID("da7a3cb6-cb16-4a92-9c70-18496b0ccff1")


PLACEMENTS = {
    "D1": Placement(12.0, 48.0, 90),
    "Q1": Placement(25.0, 42.0, 90),
    "Q2": Placement(25.0, 57.0, 90),
    "U1": Placement(35.0, 50.0, 90),
    "JPB1": Placement(75.0, 45.0),
    "Q101": Placement(50.0, 20.0, 90),
    "Q102": Placement(100.0, 20.0, 90),
    "Q103": Placement(17.0, 70.0, 90),
    "Q104": Placement(30.0, 70.0, 90),
    "Q105": Placement(50.0, 70.0, 90),
    "Q106": Placement(65.0, 70.0, 90),
    "Q107": Placement(80.0, 70.0, 90),
    "Q108": Placement(95.0, 70.0, 90),
    "Q109": Placement(120.0, 70.0, 90),
    "Q110": Placement(132.0, 70.0, 90),
    "U_CAN1_PHY": Placement(137.0, 45.0, 90),
    "D_CAN1": Placement(145.0, 45.0, 90),
    "U_CAN1": Placement(130.0, 42.0, 90),
    "JP_CAN1": Placement(127.0, 38.0),
    "JP_CAN1_NORMAL": Placement(133.0, 38.0),
    "R_CAN1_OE": Placement(127.0, 48.0),
    "R_CAN1_TX_BIAS": Placement(127.0, 51.0),
    "R_CAN1_STATUS_SER": Placement(130.0, 51.0),
    "R_CAN1_STATUS_PULL": Placement(133.0, 51.0),
    "R_CAN1_SILENT": Placement(136.0, 51.0),
    "R_CAN1_TERM": Placement(142.0, 39.0, 90),
    "C_CAN1_VCC": Placement(140.0, 49.0, 90),
    "C_CAN1_VIO": Placement(143.0, 49.0, 90),
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


def load_footprint_bound_components() -> tuple[list[Component], dict[str, str]]:
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli is None:
        raise RuntimeError("kicad-cli is required to import the PB-100 schematic")
    with tempfile.TemporaryDirectory(prefix="svc-pb100-layout-") as temp_dir:
        netlist_path = Path(temp_dir) / "PB-100.xml"
        result = subprocess.run(
            [
                kicad_cli,
                "sch",
                "export",
                "netlist",
                "--format",
                "kicadxml",
                "--output",
                str(netlist_path),
                str(SCHEMATIC_PATH),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            details = "\n".join(
                part for part in (result.stdout.strip(), result.stderr.strip()) if part
            )
            raise RuntimeError(f"KiCad XML export failed: {details}")
        root = ET.parse(netlist_path).getroot()

    libparts: dict[tuple[str, str], dict[str, tuple[str, str]]] = {}
    for libpart in root.findall("./libparts/libpart"):
        key = (libpart.get("lib", ""), libpart.get("part", ""))
        libparts[key] = {
            pin.get("num", ""): (pin.get("name", ""), pin.get("type", "passive"))
            for pin in libpart.findall("./pins/pin")
        }
    node_nets = {
        (node.get("ref", ""), node.get("pin", "")): net.get("name", "")
        for net in root.findall("./nets/net")
        for node in net.findall("node")
    }
    components = []
    schematic_paths = {}
    for element in root.findall("./components/comp"):
        footprint = element.findtext("footprint", default="").strip()
        if not footprint:
            continue
        reference = element.get("ref", "")
        libsource = element.find("libsource")
        if libsource is None:
            raise RuntimeError(f"{reference} has no libsource in XML netlist")
        pin_contract = libparts[(libsource.get("lib", ""), libsource.get("part", ""))]
        pins = tuple(
            Pin(number, name, node_nets.get((reference, number)), electrical_type)
            for number, (name, electrical_type) in pin_contract.items()
        )
        components.append(
            Component(
                ref=reference,
                value=element.findtext("value", default=""),
                footprint=footprint,
                datasheet=element.findtext("datasheet", default=""),
                pins=pins,
                dnp=element.find("./property[@name='dnp']") is not None,
            )
        )
        sheetpath = element.find("sheetpath")
        sheet_tstamp = sheetpath.get("tstamps", "/") if sheetpath is not None else "/"
        schematic_paths[reference] = f'{sheet_tstamp}{element.findtext("tstamps", default="")}'
    return components, schematic_paths


def render_footprint(
    component: Component,
    schematic_path: str,
    placement: Placement,
    net_codes: dict[str, int],
) -> str:
    footprint_name = component.footprint.split(":", 1)[1]
    path = FOOTPRINT_DIR / f"{footprint_name}.kicad_mod"
    text = replace_uuids(path.read_text(encoding="utf-8"), component.ref)
    text = re.sub(
        r'^\(footprint\s+"[^"]+"',
        f'(footprint "PB100:{escape(footprint_name)}"',
        text,
        count=1,
    )
    text = re.sub(
        r'(\(layer\s+"F\.Cu"\))',
        lambda match: (
            f'{match.group(1)}\n'
            f'\t(uuid "{layout_uid("footprint", component.ref, "root")}")\n'
            f'\t(at {placement.x_mm:.2f} {placement.y_mm:.2f} {placement.rotation:g})\n'
            f'\t(path "{schematic_path}")'
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
            f'(at 0 0 0) (layer "F.Fab") (hide yes) '
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
            text = insert_footprint_child(text, "\t(attr smd dnp)\n")

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
        if pin.net:
            additions.insert(0, f'\t\t(net {net_codes[pin.net]} "{escape(pin.net)}")')
        block = rotate_pad(text[start:end], placement.rotation)
        block = block[:-1] + "\n" + "\n".join(additions) + "\n\t)"
        text = text[:start] + block + text[end:]
    return "\n".join((f"\t{line}" if line else line).rstrip() for line in text.splitlines())


def mounting_hole(ref: str, x_mm: float, y_mm: float, diameter_mm: float, radius_mm: float, label: str) -> str:
    return f'''\t(footprint "PB100:MountingHole_{diameter_mm:g}mm"
\t\t(layer "F.Cu")
\t\t(uuid "{layout_uid(ref, "root")}")
\t\t(at {x_mm:.2f} {y_mm:.2f})
\t\t(property "Reference" "{ref}" (at 0 {-radius_mm - 1:.1f} 0) (layer "F.SilkS") (hide yes) (uuid "{layout_uid(ref, "reference")}") (effects (font (size 1 1) (thickness 0.15))))
\t\t(property "Value" "{label}" (at 0 {radius_mm + 1:.1f} 0) (layer "F.Fab") (uuid "{layout_uid(ref, "value")}") (effects (font (size 1 1) (thickness 0.15))))
\t\t(attr exclude_from_pos_files exclude_from_bom)
\t\t(fp_circle (center 0 0) (end {radius_mm:.1f} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{layout_uid(ref, "courtyard")}"))
\t\t(fp_circle (center 0 0) (end {diameter_mm / 2 + 0.7:.2f} 0) (stroke (width 0.25) (type solid)) (fill no) (layer "F.SilkS") (uuid "{layout_uid(ref, "silk")}"))
\t\t(pad "" np_thru_hole circle (at 0 0) (size {diameter_mm:.1f} {diameter_mm:.1f}) (drill {diameter_mm:.1f}) (layers "*.Cu" "*.Mask") (uuid "{layout_uid(ref, "pad")}"))
\t)'''


def board_graphics() -> list[str]:
    rectangles = (
        ("outline", 0, 0, 150, 90, "Edge.Cuts", "default"),
        ("input-zone", 8, 15, 45, 75, "Cmts.User", "dash"),
        ("out12-zone", 35, 8, 115, 35, "Cmts.User", "dash"),
        ("out310-zone", 20, 52, 130, 78, "Cmts.User", "dash"),
        ("battery-entry", 0, 30, 25, 60, "Cmts.User", "dash"),
        ("can-service", 125, 35, 150, 55, "Cmts.User", "dash"),
        ("fuse-service", 25, 72, 125, 90, "Cmts.User", "dash"),
        ("out1-exit", 35, 0, 65, 8, "Cmts.User", "dash"),
        ("out2-exit", 85, 0, 115, 8, "Cmts.User", "dash"),
    )
    graphics = [
        f'\t(gr_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.1) (type {style})) (fill none) (layer "{layer}") (uuid "{layout_uid(name)}"))'
        for name, x1, y1, x2, y2, layer, style in rectangles
    ]
    graphics.extend(
        [
            f'\t(gr_text "PB-100 REV.1 EVT - NOT FOR PRODUCTION" (at 75 87 0) (layer "F.SilkS") (uuid "{layout_uid("board-label")}") (effects (font (size 1.2 1.2) (thickness 0.18))))',
            f'\t(gr_text "PARTIAL SCHEMATIC IMPORT - FAB REVIEW BLOCKED" (at 75 3 0) (layer "Cmts.User") (uuid "{layout_uid("partial-label")}") (effects (font (size 1 1) (thickness 0.16))))',
            f'\t(gr_text "VBAT ENTRY / STRAIN RELIEF" (at 12.5 28 90) (layer "Cmts.User") (uuid "{layout_uid("vbat-label")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            f'\t(gr_text "CAN1 SERVICE" (at 137.5 57 0) (layer "F.SilkS") (uuid "{layout_uid("can-label")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            f'\t(gr_text "C36_BIDIRECTIONAL: OFF-BOARD FUSED VBAT_RAW BRANCH" (at 75 82 0) (layer "Cmts.User") (uuid "{layout_uid("c36-label")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
        ]
    )
    return graphics


def routed_can_copper(net_codes: dict[str, int]) -> list[str]:
    copper = []
    with ROUTING_PATH.open(newline="", encoding="utf-8") as routing_file:
        for index, row in enumerate(csv.DictReader(routing_file), 1):
            net_name = row["net"]
            if not net_name.startswith("CAN1_"):
                raise ValueError(f"PB partial routing may contain only CAN1 nets: {net_name}")
            if net_name not in net_codes:
                raise ValueError(f"routing manifest references unknown net {net_name}")
            route_uuid = layout_uid(
                "can-route",
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
    components, schematic_paths = load_footprint_bound_components()
    component_refs = {component.ref for component in components}
    if component_refs != set(PLACEMENTS):
        missing = sorted(component_refs - set(PLACEMENTS))
        extra = sorted(set(PLACEMENTS) - component_refs)
        raise ValueError(f"placement map mismatch; missing={missing}, extra={extra}")
    net_names = sorted({pin.net for component in components for pin in component.pins if pin.net})
    net_codes = {name: index for index, name in enumerate(net_names, 1)}
    lines = [
        "(kicad_pcb",
        "\t(version 20260206)",
        '\t(generator "svc-pb100-layout-generator")',
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
    for component in components:
        lines.append(
            render_footprint(
                component,
                schematic_paths[component.ref],
                PLACEMENTS[component.ref],
                net_codes,
            )
        )
    for reference, x_mm, y_mm, diameter_mm, radius_mm, label in (
        ("H1", 6.0, 6.0, 3.2, 5.0, "LOCAL M3 NPTH"),
        ("H2", 144.0, 6.0, 3.2, 5.0, "LOCAL M3 NPTH"),
        ("H3", 6.0, 84.0, 3.2, 5.0, "LOCAL M3 NPTH"),
        ("H4", 144.0, 84.0, 3.2, 5.0, "LOCAL M3 NPTH"),
        ("H5", 40.0, 25.0, 2.7, 3.5, "STACK M2.5 NPTH"),
        ("H6", 110.0, 25.0, 2.7, 3.5, "STACK M2.5 NPTH"),
        ("H7", 40.0, 65.0, 2.7, 3.5, "STACK M2.5 NPTH"),
        ("H8", 110.0, 65.0, 2.7, 3.5, "STACK M2.5 NPTH"),
    ):
        lines.append(mounting_hole(reference, x_mm, y_mm, diameter_mm, radius_mm, label))
    lines.extend(routed_can_copper(net_codes))
    lines.extend(board_graphics())
    lines.append(")")
    return "\n".join(lines) + "\n"


def render_rules() -> str:
    return """(version 1)

(rule "PB-100 preliminary signal clearance"
    (constraint clearance (min 0.20mm)))

(rule "PB-100 preliminary signal width"
    (constraint track_width (min 0.20mm)))

(rule "PB-100 CAN preliminary differential width"
    (condition "A.NetName == 'CAN1_HARNESS_H' || A.NetName == 'CAN1_HARNESS_L'")
    (constraint track_width (min 0.20mm) (opt 0.30mm)))

(rule "PB-100 CAN preliminary differential gap"
    (condition "A.NetName == 'CAN1_HARNESS_H' || A.NetName == 'CAN1_HARNESS_L'")
    (constraint diff_pair_gap (min 0.20mm) (opt 0.25mm)))
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
