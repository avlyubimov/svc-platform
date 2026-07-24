#!/usr/bin/env python3
"""Generate the controlled connectivity-complete PB-100 Rev.1 EVT layout."""

from __future__ import annotations

import argparse
import csv
import math
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
    flipped_layers,
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
ROUTING_PATH = KICAD_DIR / "PB-100-routing.csv"

# These GND lands sit in deliberately tight power-stage geometry where a
# two-spoke thermal cannot be formed.  A local solid connection is explicit
# and reviewable; applying it to every GND pad would unnecessarily increase
# tombstoning risk for ordinary small passives.
SOLID_GND_PADS = {
    "U1": {"9", "11", "13", "16"},
    "U2": {"7"},
    "U3": {"1"},
    "U_CAN1_PHY": {"2"},
    "RT1": {"2"},
    "C1705": {"2"},
    "R1703": {"2"},
    "R1705": {"2"},
    "R1707": {"2"},
    "U101": {"6"},
    **{f"U{channel}": {"6"} for channel in range(105, 110)},
    **{f"DCL{channel}": {"1", "3"} for channel in range(101, 111)},
}
LAYOUT_UUID_NS = uuid.UUID("da7a3cb6-cb16-4a92-9c70-18496b0ccff1")


FIXED_PLACEMENTS = {
    "D1": Placement(143.0, 29.0, 90, "B"),
    "JIN1": Placement(6.5, 45.0, 270),
    "Q1": Placement(18.0, 52.0, 180),
    "Q2": Placement(18.0, 39.5),
    "RSH1": Placement(27.0, 60.0, 0, "B"),
    "JISO1": Placement(34.0, 44.0, 90),
    "U1": Placement(18.0, 43.0, 90, "B"),
    "U2": Placement(24.5, 43.0, 90, "B"),
    "U3": Placement(124.0, 14.0, 90),
    "L1": Placement(126.0, 25.0),
    "C30": Placement(114.0, 8.0, 90),
    "C31": Placement(118.0, 8.0, 90),
    "C32": Placement(114.0, 15.5, 90),
    "C33": Placement(119.0, 14.0, 90),
    "C34": Placement(137.0, 22.0, 90),
    "C35": Placement(137.0, 28.0, 90),
    "C36": Placement(137.0, 34.0, 90),
    "R30": Placement(114.0, 3.0, 90),
    "R31": Placement(118.0, 3.0, 90),
    "R32": Placement(122.0, 3.0, 90),
    "R33": Placement(118.0, 34.0, 90),
    "R34": Placement(122.0, 34.0, 90),
    "C38": Placement(144.0, 15.0, 90),
    "R36": Placement(144.0, 19.0, 90),
    "C39": Placement(144.0, 23.0, 90),
    "R37": Placement(128.0, 34.0, 90),
    "C40": Placement(132.0, 34.0, 90),
    "JPB1": Placement(75.0, 45.0),
    "JFOG1": Placement(4.0, 20.0, 270),
    "D_FOG1": Placement(10.0, 25.5, 270),
    "R_FOG_GND": Placement(9.0, 31.0, 90),
    "R_FOG_12V": Placement(13.0, 31.0, 90),
    "F_FOG_12V": Placement(17.0, 29.0),
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


LOWER_OUTPUT_X = {1: 50.0, 2: 100.0}
UPPER_OUTPUT_EXIT_X = {
    3: 19.0,
    4: 35.0,
    5: 51.0,
    6: 67.0,
    7: 83.0,
    8: 99.0,
    9: 115.0,
    10: 131.0,
}
UPPER_OUTPUT_CORE_X = {
    # OUT3 is displaced inboard of its shunt to clear the input hot-swap
    # corridor and the H3 stack fastener without overlapping courtyards.
    3: 9.5,
    4: 30.0,
    5: 51.0,
    6: 67.0,
    7: 83.0,
    8: 99.0,
    9: 120.0,
    10: 131.0,
}
UPPER_OUTPUT_SHUNT_X = {
    # OUT3 clears the input Q1 corridor.  OUT4 is shifted right by 2.4 mm so
    # the independent input-shunt via fields do not intersect its
    # power/Kelvin lands on the opposite side of the board.
    3: 19.0,
    4: 32.4,
    5: 51.0,
    6: 67.0,
    7: 83.0,
    8: 99.0,
    9: 120.0,
    10: 131.0,
}

UPPER_OUTPUT_CLAMP_X = {
    3: 16.0,
    4: 30.0,
    5: 51.0,
    6: 67.0,
    7: 83.0,
    8: 99.0,
    9: 120.0,
    10: 134.0,
}

OUTPUT_POWER_FIELD_COLUMNS = {
    1: (58.0, 59.6, 61.2),
    2: (98.0, 99.6, 101.2),
    3: (12.8, 11.2),
    4: (44.2, 45.2),
    5: (47.8, 46.2),
    6: (63.8, 62.2),
    7: (79.8, 78.2),
    8: (95.8, 94.2),
    9: (111.6, 110.0),
    10: (127.6, 126.0),
}

OUTPUT_BACK_SUPPORT_COUNTS = {
    # JPB1 occupies the centre of these four service slices.  Keep the
    # controller-facing support row on F.Cu and move only the minimum overflow
    # needed to retain every channel inside its own slice.
    5: 3,
    6: 10,
    7: 11,
    8: 4,
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


def load_footprint_bound_components() -> tuple[
    list[Component],
    dict[str, str],
    dict[str, str],
]:
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
    sheet_names = {}
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
            Pin(
                number,
                name,
                (
                    None
                    if electrical_type == "no_connect"
                    or node_nets.get((reference, number), "").startswith("unconnected-(")
                    else node_nets.get((reference, number))
                ),
                electrical_type,
            )
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
        sheet_names[reference] = sheetpath.get("names", "/") if sheetpath is not None else "/"
    return components, schematic_paths, sheet_names


def footprint_bounds(component: Component) -> tuple[float, float, float, float]:
    footprint_name = component.footprint.split(":", 1)[1]
    text = (FOOTPRINT_DIR / f"{footprint_name}.kicad_mod").read_text(encoding="utf-8")
    points: list[tuple[float, float]] = []
    for match in re.finditer(r"\(fp_(?:line|rect|circle|arc|poly)\b", text):
        block = text[match.start():expression_end(text, match.start())]
        if '(layer "F.CrtYd")' not in block:
            continue
        coordinates = [
            (float(x_value), float(y_value))
            for _, x_value, y_value in re.findall(
                r"\((start|end|center|mid)\s+(-?[0-9.]+)\s+(-?[0-9.]+)",
                block,
            )
        ]
        if block.startswith("(fp_circle") and len(coordinates) >= 2:
            center, edge = coordinates[0], coordinates[1]
            radius = math.hypot(edge[0] - center[0], edge[1] - center[1])
            points.extend(
                (
                    (center[0] - radius, center[1] - radius),
                    (center[0] + radius, center[1] + radius),
                )
            )
        else:
            points.extend(coordinates)
    # A courtyard is only useful when it actually encloses every land.  Some
    # of the legacy PB footprints predate the present generator and have
    # undersized courtyards (notably the TPS48110 VSSOP).  Include pad copper
    # in the packing envelope so that deterministic placement cannot create a
    # short even while those source footprints are being corrected.
    for match in re.finditer(r"\(pad\b", text):
        block = text[match.start():expression_end(text, match.start())]
        at_match = re.search(
            r"\(at\s+(-?[0-9.]+)\s+(-?[0-9.]+)(?:\s+(-?[0-9.]+))?",
            block,
        )
        size_match = re.search(r"\(size\s+([0-9.]+)\s+([0-9.]+)", block)
        if at_match is None or size_match is None:
            continue
        pad_x = float(at_match.group(1))
        pad_y = float(at_match.group(2))
        pad_rotation = float(at_match.group(3) or 0.0)
        half_width = float(size_match.group(1)) / 2.0
        half_height = float(size_match.group(2)) / 2.0
        pad_bounds = rotated_bounds(
            (-half_width, -half_height, half_width, half_height),
            pad_rotation,
        )
        points.extend(
            (
                (pad_x + pad_bounds[0], pad_y + pad_bounds[1]),
                (pad_x + pad_bounds[2], pad_y + pad_bounds[3]),
            )
        )
    if not points:
        raise ValueError(f"{footprint_name} has no parseable F.CrtYd geometry")
    return (
        min(point[0] for point in points),
        min(point[1] for point in points),
        max(point[0] for point in points),
        max(point[1] for point in points),
    )


def rotated_bounds(
    bounds: tuple[float, float, float, float],
    rotation: float,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = bounds
    # KiCad's positive board rotation follows the screen-coordinate direction,
    # opposite the conventional mathematical sign used by sin/cos.
    angle = -math.radians(rotation)
    cosine, sine = math.cos(angle), math.sin(angle)
    points = [
        (x * cosine - y * sine, x * sine + y * cosine)
        for x, y in ((x1, y1), (x1, y2), (x2, y1), (x2, y2))
    ]
    return (
        min(point[0] for point in points),
        min(point[1] for point in points),
        max(point[0] for point in points),
        max(point[1] for point in points),
    )


def placement_rectangle(
    component: Component,
    placement: Placement,
) -> tuple[float, float, float, float, str]:
    x1, y1, x2, y2 = rotated_bounds(footprint_bounds(component), placement.rotation)
    return (
        placement.x_mm + x1,
        placement.y_mm + y1,
        placement.x_mm + x2,
        placement.y_mm + y2,
        component.ref,
    )


def through_footprint(component: Component) -> bool:
    footprint_name = component.footprint.split(":", 1)[1]
    text = (FOOTPRINT_DIR / f"{footprint_name}.kicad_mod").read_text(encoding="utf-8")
    return "thru_hole" in text


def rectangles_overlap(
    first: tuple[float, float, float, float, str],
    second: tuple[float, float, float, float, str],
    gap_mm: float,
) -> bool:
    return not (
        first[2] + gap_mm <= second[0]
        or second[2] + gap_mm <= first[0]
        or first[3] + gap_mm <= second[1]
        or second[3] + gap_mm <= first[1]
    )


def shelf_pack(
    placements: dict[str, Placement],
    components: list[Component],
    regions: tuple[tuple[float, float, float, float], ...],
    occupied: list[tuple[float, float, float, float, str]],
    *,
    side: str = "B",
    gap_mm: float = 0.30,
) -> None:
    region_states = [
        {"x": x1, "y": y1, "row_height": 0.0}
        for x1, y1, _, _ in regions
    ]
    ordered = sorted(
        components,
        key=lambda component: (
            -(footprint_bounds(component)[3] - footprint_bounds(component)[1]),
            -(footprint_bounds(component)[2] - footprint_bounds(component)[0]),
            component.ref,
        ),
    )
    for component in ordered:
        local_x1, local_y1, local_x2, local_y2 = footprint_bounds(component)
        width = local_x2 - local_x1
        height = local_y2 - local_y1
        placed = False
        for region_index, (region_x1, region_y1, region_x2, region_y2) in enumerate(regions):
            state = region_states[region_index]
            attempts = 0
            while attempts < 2000:
                attempts += 1
                if state["x"] + width > region_x2:
                    state["x"] = region_x1
                    state["y"] += state["row_height"] + gap_mm
                    state["row_height"] = 0.0
                if state["y"] + height > region_y2:
                    break
                x_mm = state["x"] - local_x1
                y_mm = state["y"] - local_y1
                candidate = (
                    state["x"],
                    state["y"],
                    state["x"] + width,
                    state["y"] + height,
                    component.ref,
                )
                collisions = [
                    rectangle
                    for rectangle in occupied
                    if rectangles_overlap(candidate, rectangle, gap_mm)
                ]
                if collisions:
                    state["x"] = max(rectangle[2] for rectangle in collisions) + gap_mm
                    continue
                placement = Placement(x_mm, y_mm, 0.0, side)
                placements[component.ref] = placement
                occupied.append(candidate)
                state["x"] += width + gap_mm
                state["row_height"] = max(state["row_height"], height)
                placed = True
                break
            if placed:
                break
        if not placed:
            raise ValueError(
                f"cannot pack {component.ref} in regions {regions}; "
                f"{len(components)} components requested"
            )


def output_channel_for_ref(reference: str) -> int | None:
    for prefix in ("RSH", "DCL", "QT", "W", "U", "Q"):
        if reference.startswith(prefix):
            suffix = reference[len(prefix):]
            if suffix.isdigit() and 101 <= int(suffix) <= 110:
                return int(suffix) - 100
    if reference.startswith(("R", "C")) and reference[1:].isdigit():
        number = int(reference[1:])
        if 1101 <= number <= 2013:
            channel = (number - 1000) // 100
            if 1 <= channel <= 10:
                return channel
    if reference.startswith("TP") and reference[2:].isdigit():
        number = int(reference[2:])
        if 22 <= number <= 61:
            return (number - 22) // 4 + 1
    return None


def output_front_side_support(reference: str) -> bool:
    """Put TPS48110 top-row support parts opposite the controller.

    The 0.50 mm controller pins cannot accept an ordinary through via in-pad.
    Keeping their support passives on the same side traps the outward fan-out
    between adjacent lands.  These parts are deliberately placed on F.Cu so
    the B.Cu pin row can escape before changing layer with a conventional via.
    """

    if reference.startswith("QT") and reference[2:].isdigit():
        return 101 <= int(reference[2:]) <= 110
    if reference.startswith(("R", "C")) and reference[1:].isdigit():
        number = int(reference[1:])
        channel = (number - 1000) // 100
        if not 1 <= channel <= 10:
            return False
        offset = number - (1000 + channel * 100)
        if reference.startswith("R"):
            return offset in {1, 2, 3, 5, 7, 8, 9, 12}
        return offset in {1, 5}
    return False


def split_output_support(
    channel: int,
    components: list[Component],
) -> tuple[list[Component], list[Component]]:
    back_count = OUTPUT_BACK_SUPPORT_COUNTS.get(channel, 0)
    ordered = sorted(
        components,
        key=lambda component: (
            output_front_side_support(component.ref),
            component.ref,
        ),
    )
    back_refs = {component.ref for component in ordered[:back_count]}
    return (
        [component for component in components if component.ref not in back_refs],
        [component for component in components if component.ref in back_refs],
    )


def build_placements(
    components: list[Component],
    sheet_names: dict[str, str],
) -> dict[str, Placement]:
    by_ref = {component.ref: component for component in components}
    placements = {
        reference: placement
        for reference, placement in FIXED_PLACEMENTS.items()
        if reference in by_ref
    }

    # Place every large current-path part before packing low-energy networks.
    lower_core = {
        1: {"q": 55.0, "shunt": 55.0, "clamp": 68.0},
        2: {"q": 95.0, "shunt": 95.0, "clamp": 82.0},
    }
    for channel, exit_x in LOWER_OUTPUT_X.items():
        core = lower_core[channel]
        placements[f"W{100 + channel}"] = Placement(exit_x, 4.5)
        placements[f"Q{100 + channel}"] = Placement(core["q"], 16.0, 180)
        placements[f"RSH{100 + channel}"] = Placement(core["shunt"], 28.0, 90)
        placements[f"DCL{100 + channel}"] = Placement(core["clamp"], 16.0, 90)
        placements[f"U{100 + channel}"] = Placement(
            46.3 if channel == 1 else 79.5,
            23.78,
            0,
            "B",
        )

    for channel, exit_x in UPPER_OUTPUT_EXIT_X.items():
        core_x = UPPER_OUTPUT_CORE_X[channel]
        placements[f"W{100 + channel}"] = Placement(exit_x, 85.5)
        q_y = 72.0 if channel == 3 else 74.0
        placements[f"Q{100 + channel}"] = Placement(core_x, q_y)
        placements[f"RSH{100 + channel}"] = Placement(
            UPPER_OUTPUT_SHUNT_X[channel],
            64.0 if channel == 3 else 62.0,
            270,
        )
        placements[f"DCL{100 + channel}"] = Placement(
            UPPER_OUTPUT_CLAMP_X[channel],
            75.0,
            270,
            "B",
        )
        controller_y = 54.0 if channel == 3 else 58.0
        controller_x = 35.5 if channel == 4 else exit_x
        placements[f"U{100 + channel}"] = Placement(
            controller_x,
            controller_y,
            0,
            "B",
        )

    # Seed underside packing with existing B-side and all through-hole
    # courtyards. The four local and four stack mounting-hole clearances block
    # both sides.
    occupied: list[tuple[float, float, float, float, str]] = []
    front_occupied: list[tuple[float, float, float, float, str]] = []
    for reference, placement in placements.items():
        component = by_ref[reference]
        if placement.side == "B" or through_footprint(component):
            occupied.append(placement_rectangle(component, placement))
        if placement.side == "F" or through_footprint(component):
            front_occupied.append(placement_rectangle(component, placement))
    for reference, x_mm, y_mm, radius_mm in (
        ("H1", 6.0, 6.0, 5.0),
        ("H2", 144.0, 6.0, 5.0),
        ("H3", 6.0, 84.0, 5.0),
        ("H4", 144.0, 84.0, 5.0),
        ("H5", 40.0, 25.0, 3.5),
        ("H6", 110.0, 25.0, 3.5),
        ("H7", 40.0, 65.0, 3.5),
        ("H8", 110.0, 65.0, 3.5),
    ):
        keepout = (
            x_mm - radius_mm,
            y_mm - radius_mm,
            x_mm + radius_mm,
            y_mm + radius_mm,
            reference,
        )
        occupied.append(keepout)
        front_occupied.append(keepout)
    # The deterministic power-via fields are emitted after placement, so add
    # their physical envelopes to the underside packer up front.  Without
    # these reservations a locally packed passive or test point can be placed
    # directly over a 1.0/0.5 mm high-current transition even though ordinary
    # footprint-to-footprint courtyard checks still pass.
    power_transition_envelopes = (
        ("VIN_REV_VIAS", 23.4, 61.3, 24.2, 65.55),
        ("VIN_PRELINK_VIAS", 27.9, 61.3, 29.5, 63.85),
        ("OUT1_VBAT_NECK", 55.45, 31.625, 61.6, 32.425),
        ("OUT2_VBAT_NECK", 95.45, 31.625, 101.6, 32.425),
        ("OUT1_VBAT_VIAS", 58.0, 32.2, 61.2, 37.0),
        ("OUT2_VBAT_VIAS", 98.0, 32.2, 101.2, 37.0),
        ("OUT3_VBAT_VIAS", 11.2, 55.2, 12.8, 60.0),
        ("OUT4_VBAT_VIAS", 44.2, 50.4, 45.2, 55.2),
        ("OUT5_VBAT_VIAS", 46.2, 54.6, 47.8, 59.4),
        ("OUT6_VBAT_VIAS", 62.2, 54.6, 63.8, 59.4),
        ("OUT7_VBAT_VIAS", 78.2, 54.6, 79.8, 59.4),
        ("OUT8_VBAT_VIAS", 94.2, 54.6, 95.8, 59.4),
        ("OUT9_VBAT_VIAS", 110.0, 54.6, 111.6, 59.4),
        ("OUT10_VBAT_VIAS", 126.0, 54.6, 127.6, 59.4),
    )
    for identity, x1, y1, x2, y2 in power_transition_envelopes:
        keepout = (x1 - 0.8, y1 - 0.8, x2 + 0.8, y2 + 0.8, identity)
        occupied.append(keepout)
        front_occupied.append(keepout)
    # Reserve every broad F.Cu protected-bus neck, not only its terminal via
    # field.  Several upper channels have deliberately offset via columns, so
    # the 2.4 mm neck crosses much of the service slice.
    for channel in range(3, 11):
        if channel == 4:
            front_occupied.extend(
                (
                    (30.35, 55.5, 31.55, 57.975, "OUT4_VBAT_NECK_VERTICAL"),
                    (30.35, 54.9, 44.2, 56.1, "OUT4_VBAT_NECK_HORIZONTAL"),
                )
            )
            continue
        pad_x = UPPER_OUTPUT_SHUNT_X[channel] - 0.85
        pad_y = 59.975 if channel == 3 else 57.975
        far_x = OUTPUT_POWER_FIELD_COLUMNS[channel][-1]
        front_occupied.append(
            (
                min(pad_x, far_x) - 1.2,
                pad_y - 1.2,
                max(pad_x, far_x) + 1.2,
                pad_y + 1.2,
                f"OUT{channel}_VBAT_NECK",
            )
        )

    # Input low-energy parts occupy the underside of the battery corridor.
    input_components = [
        component
        for component in components
        if component.ref not in placements
        and sheet_names[component.ref] == "/input-protection/"
    ]
    shelf_pack(
        placements,
        input_components,
        ((2.0, 21.0, 37.0, 42.0), (2.0, 51.0, 13.0, 68.0)),
        occupied,
    )

    # OUT1/OUT2 use the reviewed lower-edge DTP corridors.
    for channel, regions in (
        (1, ((42.0, 21.0, 73.0, 42.0),)),
        (2, ((77.0, 21.0, 108.0, 42.0),)),
    ):
        channel_components = [
            component
            for component in components
            if component.ref not in placements
            and output_channel_for_ref(component.ref) == channel
        ]
        front_components, back_components = split_output_support(
            channel,
            channel_components,
        )
        packing_regions = (
            *regions,
            (2.0, 2.0, 148.0, 20.0),
            (2.0, 21.0, 148.0, 38.0),
            (2.0, 51.0, 148.0, 64.0),
        )
        shelf_pack(
            placements,
            front_components,
            packing_regions,
            front_occupied,
            side="F",
        )
        shelf_pack(
            placements,
            back_components,
            packing_regions,
            occupied,
            side="B",
        )

    # Keep each remaining output network in its own vertical service slice.
    # This is slightly less area-efficient than one global shelf but preserves
    # short, reviewable controller/gate/Kelvin paths and prevents the router
    # from crossing unrelated channels merely because equal-size passives were
    # sorted together.
    output_slices = {
        3: (12.0, 26.0),
        4: (27.0, 43.0),
        5: (44.0, 58.0),
        6: (60.0, 74.0),
        7: (76.0, 90.0),
        8: (92.0, 106.0),
        9: (108.0, 123.0),
        10: (125.0, 140.0),
    }
    for channel, (x1, x2) in output_slices.items():
        channel_components = [
            component
            for component in components
            if component.ref not in placements
            and output_channel_for_ref(component.ref) == channel
        ]
        front_components, back_components = split_output_support(
            channel,
            channel_components,
        )
        packing_regions = (
            (x1, 2.0, x2, 20.0),
            (x1, 21.0, x2, 38.0),
            (x1, 38.0, x2, 51.0),
            (x1, 51.0, x2, 64.0),
            (2.0, 2.0, 148.0, 20.0),
            (2.0, 21.0, 148.0, 38.0),
            (2.0, 51.0, 148.0, 64.0),
        )
        shelf_pack(
            placements,
            front_components,
            packing_regions,
            front_occupied,
            side="F",
        )
        shelf_pack(
            placements,
            back_components,
            packing_regions,
            occupied,
            side="B",
        )

    # Telemetry and non-critical logic support parts fit in the low-energy
    # service corner. The LM5164 switch loop itself is fixed on F.Cu above.
    service_components = [
        component
        for component in components
        if component.ref not in placements
        and sheet_names[component.ref] in {"/telemetry/", "/logic-power/"}
    ]
    shelf_pack(
        placements,
        service_components,
        ((120.0, 37.0, 148.0, 71.0),),
        occupied,
    )

    missing = sorted(set(by_ref) - set(placements))
    extra = sorted(set(placements) - set(by_ref))
    if missing or extra:
        raise ValueError(f"placement map mismatch; missing={missing}, extra={extra}")
    return placements


def render_footprint(
    component: Component,
    schematic_path: str,
    placement: Placement,
    net_codes: dict[str, int],
) -> str:
    footprint_name = component.footprint.split(":", 1)[1]
    path = FOOTPRINT_DIR / f"{footprint_name}.kicad_mod"
    text = replace_uuids(path.read_text(encoding="utf-8"), component.ref)
    if placement.side == "B":
        text = flipped_layers(text)
    text = re.sub(
        r'^\(footprint\s+"[^"]+"',
        f'(footprint "PB100:{escape(footprint_name)}"',
        text,
        count=1,
    )
    text = re.sub(
        r'(\(layer\s+"[FB]\.Cu"\))',
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
                lambda match: (
                    f'(attr {match.group(1).strip()})'
                    if "dnp" in match.group(1).split()
                    else f'(attr {match.group(1).strip()} dnp)'
                ),
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
        if pin.net == "GND" and number in SOLID_GND_PADS.get(component.ref, set()):
            additions.insert(0, "\t\t(zone_connect 2)")
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
            f'\t(gr_text "VALUE-BEARING EVT LAYOUT - FAB REVIEW REQUIRED" (at 75 3 0) (layer "Cmts.User") (uuid "{layout_uid("partial-label")}") (effects (font (size 1 1) (thickness 0.16))))',
            f'\t(gr_text "VBAT ENTRY / STRAIN RELIEF" (at 12.5 28 90) (layer "Cmts.User") (uuid "{layout_uid("vbat-label")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            f'\t(gr_text "CAN1 SERVICE" (at 137.5 57 0) (layer "F.SilkS") (uuid "{layout_uid("can-label")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
            f'\t(gr_text "C36_BIDIRECTIONAL: OFF-BOARD FUSED VBAT_RAW BRANCH" (at 75 82 0) (layer "Cmts.User") (uuid "{layout_uid("c36-label")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
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
            route_uuid = layout_uid("route", index, *(row[column] for column in row))
            if row["kind"] == "segment":
                copper.append(
                    f'\t(segment (start {row["start_x_mm"]} {row["start_y_mm"]}) '
                    f'(end {row["end_x_mm"]} {row["end_y_mm"]}) '
                    f'(width {row["width_mm"]}) (layer "{row["layer"]}") '
                    f'(net {net_codes[net_name]}) (uuid "{route_uuid}"))'
                )
            elif row["kind"] == "via":
                via_type = row.get("via_type", "through")
                via_keyword = (
                    "via micro"
                    if via_type == "micro"
                    else "via blind"
                    if via_type == "blind"
                    else "via"
                )
                copper.append(
                    f'\t({via_keyword} (at {row["start_x_mm"]} {row["start_y_mm"]}) '
                    f'(size {row["diameter_mm"]}) (drill {row["drill_mm"]}) '
                    f'(layers "{row["start_layer"]}" "{row["end_layer"]}") '
                    f'(net {net_codes[net_name]}) (uuid "{route_uuid}"))'
                )
            else:
                raise ValueError(f'unknown routing manifest kind {row["kind"]}')
    return copper


def copper_zone(
    net_codes: dict[str, int],
    net_name: str,
    layer: str,
    points: tuple[tuple[float, float], ...],
    identity: str,
    *,
    priority: int = 1,
    solid: bool = False,
) -> str:
    point_lines = "\n".join(
        f"\t\t\t\t(xy {x_mm:.3f} {y_mm:.3f})" for x_mm, y_mm in points
    )
    pad_connection = (
        "(connect_pads yes (clearance 0))"
        if solid
        else "(connect_pads (clearance 0.20))"
    )
    fill = (
        "(fill yes)"
        if solid
        # A 0.25 mm bridge still exceeds the preliminary 0.20 mm signal
        # minimum, while allowing two independent spokes around the dense
        # bottom-side controller and clamp pads.  The previous 0.40 mm bridge
        # starved several thermals down to one spoke.
        else "(fill yes (thermal_gap 0.20) (thermal_bridge_width 0.25))"
    )
    return f'''\t(zone
\t\t(net {net_codes[net_name]})
\t\t(net_name "{escape(net_name)}")
\t\t(layer "{layer}")
\t\t(uuid "{layout_uid("zone", identity, layer, net_name)}")
\t\t(hatch edge 0.5)
\t\t(priority {priority})
\t\t{pad_connection}
\t\t(min_thickness 0.20)
\t\t{fill}
\t\t(polygon
\t\t\t(pts
{point_lines}
\t\t\t)
\t\t)
\t)'''


def power_zones(net_codes: dict[str, int]) -> list[str]:
    """Return the explicit Rev.1 EVT power topology.

    In2 is a continuous GND reference, In5 is the protected battery
    distribution plane, and the outer pours provide return-current continuity.
    In1, In3, In4 and In6 remain signal-capable so the 100-pin JPB1 fan-out
    does not require slots through either reference/power plane.
    High-current input/output islands use solid pad connections and outrank the
    reference pours.  The preliminary 2 oz outer / 1 oz inner construction
    and each island remain subject to supplier stackup and current-density
    review before EVT fabrication release.
    """

    board = ((0.5, 0.5), (149.5, 0.5), (149.5, 89.5), (0.5, 89.5))
    zones = [
        copper_zone(net_codes, "GND", layer, board, "reference", priority=1)
        for layer in ("F.Cu", "In2.Cu", "B.Cu")
    ]
    zones.append(
        copper_zone(
            net_codes,
            "VBAT_PROT",
            "In5.Cu",
            board,
            "protected-distribution",
            priority=1,
            solid=True,
        )
    )

    # Battery entry: JIN1 -> Q2 -> common-source Q1 -> reverse shunt -> JISO1.
    input_islands = (
        (
            "VBAT_RAW",
            "F.Cu",
            ((2.5, 35.0), (22.5, 35.0), (22.5, 40.6), (10.5, 40.6), (10.5, 44.5), (2.5, 44.5)),
            "input-raw",
        ),
        (
            "INPUT_COMMON_SOURCE",
            "F.Cu",
            ((14.4, 42.0), (22.7, 42.0), (22.7, 45.2), (21.4, 45.2), (21.4, 49.4), (13.3, 49.4), (13.3, 46.3), (14.4, 46.3)),
            "input-common-source",
        ),
        (
            "VBAT_REV_PROT",
            "F.Cu",
            (
                (13.5, 50.8),
                (22.4, 50.8),
                (22.4, 57.5),
                (24.7, 57.5),
                (24.7, 66.0),
                (22.9, 66.0),
                (22.9, 58.0),
                (18.5, 58.0),
                (18.5, 56.3),
                (13.5, 56.3),
            ),
            "input-reverse-front",
        ),
        (
            "VBAT_REV_PROT",
            "B.Cu",
            ((19.0, 58.0), (24.7, 58.0), (24.7, 66.0), (19.0, 66.0)),
            "input-reverse-back",
        ),
        (
            "VBAT_PROT_PRELINK",
            "B.Cu",
            ((28.2, 58.0), (32.5, 58.0), (32.5, 66.0), (28.2, 66.0)),
            "input-prelink-back",
        ),
        (
            "VBAT_PROT_PRELINK",
            "F.Cu",
            ((25.0, 47.5), (30.0, 47.5), (30.0, 66.0), (25.0, 66.0)),
            "input-prelink-front",
        ),
    )
    zones.extend(
        copper_zone(net_codes, net_name, layer, points, identity, priority=20, solid=True)
        for net_name, layer, points, identity in input_islands
    )

    # OUT1/2: high-current lower-edge channels.
    for channel, centre_x, clamp_x, exit_x in (
        (1, 55.0, 68.0, 46.7),
        (2, 95.0, 82.0, 96.7),
    ):
        zones.append(
            copper_zone(
                net_codes,
                f"OUT{channel}_FET_DRAIN",
                "F.Cu",
                (
                    (centre_x - 2.00, 14.8),
                    (centre_x + 3.70, 14.8),
                    (centre_x + 3.70, 25.4),
                    (centre_x - 2.00, 25.4),
                ),
                f"out{channel}-drain",
                priority=20,
                solid=True,
            )
        )
        left = min(centre_x - 4.5, clamp_x - 4.8, exit_x - 3.0)
        right = max(centre_x + 4.5, clamp_x + 4.8, exit_x + 3.0)
        zones.append(
            copper_zone(
                net_codes,
                f"OUT{channel}_SWITCHED",
                "F.Cu",
                (
                    (left, 1.5),
                    (right, 1.5),
                    (right, 24.3),
                    (clamp_x - 5.0, 24.3),
                    (clamp_x - 5.0, 13.4),
                    (left, 13.4),
                ),
                f"out{channel}-switched",
                priority=20,
                solid=True,
            )
        )

    # OUT3..10: drain necks on F.Cu, source/connector copper on F.Cu and
    # clamp/connector copper on B.Cu.  The connector PTH lands join both sides.
    for channel in range(3, 11):
        core_x = UPPER_OUTPUT_CORE_X[channel]
        shunt_x = UPPER_OUTPUT_SHUNT_X[channel]
        drain_x = shunt_x - 0.85
        exit_x = UPPER_OUTPUT_EXIT_X[channel]
        clamp_x = UPPER_OUTPUT_CLAMP_X[channel]
        if channel == 3:
            drain_points = (
                (5.1, 66.7),
                (21.0, 66.7),
                (21.0, 69.4),
                (13.9, 75.2),
                (5.1, 75.2),
            )
        elif channel == 4:
            drain_points = (
                (drain_x - 1.25, 64.7),
                (drain_x + 1.25, 64.7),
                (34.35, 69.6),
                (34.35, 75.2),
                (drain_x - 1.25, 75.2),
            )
        else:
            drain_points = (
                (drain_x - 1.25, 64.7),
                (drain_x + 1.25, 64.7),
                (drain_x + 1.25, 75.2),
                (drain_x - 1.25, 75.2),
            )
        zones.append(
            copper_zone(
                net_codes,
                f"OUT{channel}_FET_DRAIN",
                "F.Cu",
                drain_points,
                f"out{channel}-drain",
                priority=20,
                solid=True,
            )
        )
        source_left = core_x - 3.6
        source_right = core_x + 4.6
        connector_left = exit_x - 6.3
        connector_right = exit_x
        zones.append(
            copper_zone(
                net_codes,
                f"OUT{channel}_SWITCHED",
                "F.Cu",
                (
                    (source_left, 76.6),
                    (source_right, 76.6),
                    (source_right, 81.0),
                    (connector_right, 81.0),
                    (connector_right, 89.5),
                    (connector_left, 89.5),
                    (connector_left, 82.0),
                    (source_left, 82.0),
                ),
                f"out{channel}-switched-front",
                priority=20,
                solid=True,
            )
        )
        back_left = min(clamp_x - 4.9, exit_x - 6.3)
        back_right = max(clamp_x + 4.9, exit_x)
        zones.append(
            copper_zone(
                net_codes,
                f"OUT{channel}_SWITCHED",
                "B.Cu",
                (
                    (back_left, 66.7),
                    (back_right, 66.7),
                    (back_right, 89.5),
                    (exit_x - 6.3, 89.5),
                    (exit_x - 6.3, 82.0),
                    (back_left, 82.0),
                ),
                f"out{channel}-switched-back",
                priority=20,
                solid=True,
            )
        )
    return zones


def high_current_transitions(net_codes: dict[str, int]) -> list[str]:
    """Create explicit through-via fields for layer-changing power current."""

    copper: list[str] = []
    index = 0

    def segment(
        net_name: str,
        start: tuple[float, float],
        end: tuple[float, float],
        width_mm: float,
        layer: str,
        identity: str,
    ) -> None:
        nonlocal index
        index += 1
        copper.append(
            f'\t(segment (start {start[0]:.3f} {start[1]:.3f}) '
            f'(end {end[0]:.3f} {end[1]:.3f}) (width {width_mm:.3f}) '
            f'(layer "{layer}") (net {net_codes[net_name]}) '
            f'(uuid "{layout_uid("power-segment", index, identity)}"))'
        )

    def via(net_name: str, point: tuple[float, float], identity: str) -> None:
        nonlocal index
        index += 1
        copper.append(
            f'\t(via (at {point[0]:.3f} {point[1]:.3f}) '
            f'(size 1.000) (drill 0.500) (layers "F.Cu" "B.Cu") '
            f'(net {net_codes[net_name]}) '
            f'(uuid "{layout_uid("power-via", index, identity)}"))'
        )

    # Q1 is on F.Cu while the four-terminal 40 A input shunt is on B.Cu.
    # Twelve plated, filled/capped through vias per side make both high-current
    # layer changes explicit.  These power fields remain conventional through
    # vias; the manifest's HDI microvias are low-energy connectivity
    # attachments and are not credited for current capacity.
    for net_name, columns, rows, identity in (
        (
            "VBAT_REV_PROT",
            (23.4, 24.2),
            (61.3, 62.15, 63.0, 63.85, 64.7, 65.55),
            "input-reverse",
        ),
        (
            "VBAT_PROT_PRELINK",
            (27.9, 28.7, 29.5),
            (61.3, 62.15, 63.0, 63.85),
            "input-prelink",
        ),
    ):
        for column_index, column_x in enumerate(columns, 1):
            for row_index, row_y in enumerate(rows, 1):
                via(
                    net_name,
                    (column_x, row_y),
                    f"{identity}-{column_index}-{row_index}",
                )

    # Every output shunt has a short, broad neck into the protected In4 plane.
    # OUT1/2 receive 12/16 0.5 mm finished-hole transitions; the remaining
    # channels use eight.  The fields are deliberately displaced beyond the
    # bottom-side controller/clamp copper.  Final current density is still a
    # supplier-review and bench-thermal gate, not a production qualification.
    for channel in range(1, 11):
        if channel <= 2:
            pad_x = 55.85 if channel == 1 else 95.85
            pad_y = 32.025
            rows = (32.2, 33.8, 35.4, 37.0)
        else:
            shunt_x = UPPER_OUTPUT_SHUNT_X[channel]
            pad_x = shunt_x - 0.85
            pad_y = 59.975 if channel == 3 else 57.975
            if channel == 4:
                rows = (50.4, 52.0, 53.6, 55.2)
            elif channel == 3:
                rows = (55.2, 56.8, 58.4, 60.0)
            else:
                rows = (54.6, 56.2, 57.8, 59.4)
        columns = OUTPUT_POWER_FIELD_COLUMNS[channel]
        far_x = columns[-1]
        if channel == 4:
            # OUT4 exits to the right of JISO1; this keeps its protected-bus
            # transition independent from both sides of the input shunt.
            segment(
                "VBAT_PROT",
                (pad_x, pad_y),
                (pad_x, 55.5),
                1.2,
                "F.Cu",
                "out4-vbat-neck-up",
            )
            segment(
                "VBAT_PROT",
                (pad_x, 55.5),
                (44.2, 55.5),
                1.2,
                "F.Cu",
                "out4-vbat-neck-right",
            )
        else:
            segment(
                "VBAT_PROT",
                (pad_x, pad_y),
                (far_x, pad_y),
                2.4,
                "F.Cu",
                f"out{channel}-vbat-neck",
            )
        bus_y = 55.5 if channel == 4 else pad_y
        for column_index, column_x in enumerate(columns, 1):
            segment(
                "VBAT_PROT",
                (column_x, min(rows[0], bus_y)),
                (column_x, max(rows[-1], bus_y)),
                1.2,
                "F.Cu",
                f"out{channel}-vbat-column-{column_index}",
            )
            for row_index, row_y in enumerate(rows, 1):
                via(
                    "VBAT_PROT",
                    (column_x, row_y),
                    f"out{channel}-vbat-{column_index}-{row_index}",
                )
    return copper


def render_board() -> str:
    components, schematic_paths, sheet_names = load_footprint_bound_components()
    placements = build_placements(components, sheet_names)
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
        '\t\t(4 "In1.Cu" signal)',
        '\t\t(6 "In2.Cu" power)',
        '\t\t(8 "In3.Cu" signal)',
        '\t\t(10 "In4.Cu" signal)',
        '\t\t(12 "In5.Cu" power)',
        '\t\t(14 "In6.Cu" signal)',
        '\t\t(2 "B.Cu" signal)',
        '\t\t(13 "F.Paste" user)',
        '\t\t(15 "B.Paste" user)',
        '\t\t(5 "F.SilkS" user "f.silkscreen")',
        '\t\t(7 "B.SilkS" user "b.silkscreen")',
        '\t\t(1 "F.Mask" user)',
        '\t\t(3 "B.Mask" user)',
        '\t\t(25 "Edge.Cuts" user)',
        '\t\t(27 "Margin" user)',
        '\t\t(31 "F.CrtYd" user "F.Courtyard")',
        '\t\t(29 "B.CrtYd" user "B.Courtyard")',
        "\t)",
        "\t(setup",
        "\t\t(stackup",
        '\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "White"))',
        '\t\t\t(layer "F.Paste" (type "Top Solder Paste"))',
        '\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.01))',
        '\t\t\t(layer "F.Cu" (type "copper") (thickness 0.070))',
        '\t\t\t(layer "dielectric 1" (type "prepreg") (thickness 0.1000) (material "FR4") (epsilon_r 4.2) (loss_tangent 0.02))',
        '\t\t\t(layer "In1.Cu" (type "copper") (thickness 0.035))',
        '\t\t\t(layer "dielectric 2" (type "core") (thickness 0.1800) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))',
        '\t\t\t(layer "In2.Cu" (type "copper") (thickness 0.035))',
        '\t\t\t(layer "dielectric 3" (type "prepreg") (thickness 0.1000) (material "2116") (epsilon_r 4.16) (loss_tangent 0.02))',
        '\t\t\t(layer "In3.Cu" (type "copper") (thickness 0.035))',
        '\t\t\t(layer "dielectric 4" (type "core") (thickness 0.4700) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))',
        '\t\t\t(layer "In4.Cu" (type "copper") (thickness 0.035))',
        '\t\t\t(layer "dielectric 5" (type "prepreg") (thickness 0.1000) (material "2116") (epsilon_r 4.16) (loss_tangent 0.02))',
        '\t\t\t(layer "In5.Cu" (type "copper") (thickness 0.035))',
        '\t\t\t(layer "dielectric 6" (type "core") (thickness 0.1800) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))',
        '\t\t\t(layer "In6.Cu" (type "copper") (thickness 0.035))',
        '\t\t\t(layer "dielectric 7" (type "prepreg") (thickness 0.1000) (material "FR4") (epsilon_r 4.2) (loss_tangent 0.02))',
        '\t\t\t(layer "B.Cu" (type "copper") (thickness 0.070))',
        '\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.01))',
        '\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))',
        '\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))',
        '\t\t\t(copper_finish "ENIG")',
        "\t\t\t(dielectric_constraints yes)",
        "\t\t)",
        "\t\t(pad_to_mask_clearance 0)",
        "\t\t(allow_soldermask_bridges_in_footprints no)",
        "\t\t(tenting (front yes) (back yes))",
        "\t\t(covering (front no) (back no))",
        "\t\t(plugging (front no) (back no))",
        "\t\t(capping yes)",
        "\t\t(filling yes)",
        "\t)",
        "\t(embedded_fonts no)",
        '\t(net 0 "")',
        *[f'\t(net {code} "{escape(name)}")' for name, code in net_codes.items()],
    ]
    for component in components:
        lines.append(
            render_footprint(
                component,
                schematic_paths[component.ref],
                placements[component.ref],
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
    # Power transitions are added before the signal-routing manifest.
    lines.extend(high_current_transitions(net_codes))
    lines.extend(routed_copper(net_codes))
    lines.extend(power_zones(net_codes))
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
    global BOARD_PATH, ROUTING_PATH

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--board-output",
        type=Path,
        default=BOARD_PATH,
        help="override the generated board path for disposable routing trials",
    )
    parser.add_argument(
        "--routing-path",
        type=Path,
        default=ROUTING_PATH,
        help="override the routing-manifest input path",
    )
    args = parser.parse_args()
    BOARD_PATH = args.board_output
    ROUTING_PATH = args.routing_path
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
