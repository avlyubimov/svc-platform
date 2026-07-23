#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "hardware" / "logic-board" / "LB-100" / "kicad" / "LB-100.kicad_pcb"
REQUIRED_KICAD_VERSION = "10.0.4"
EXPECTED_UNCONNECTED_ITEMS = 0
EXPECTED_SEGMENTS = 2274
EXPECTED_VIAS = 409
EXPECTED_GND_ZONES = 4
EXPECTED_ANTENNA_KEEPOUTS = 1
EXPECTED_SCHEMATIC_FOOTPRINTS = 104
BOARD_ONLY_FOOTPRINTS = {f"H{index}" for index in range(1, 9)}
ALLOWED_VIOLATIONS = Counter(
    {
        "silk_over_copper": 10,
        "lib_footprint_issues": 8,
        "silk_edge_clearance": 6,
        "lib_footprint_mismatch": 3,
    }
)
MAX_USB_DATA_SKEW_MM = 1.20
USB_TRACE_WIDTH_MM = 0.20
USB_REFERENCE_HEIGHT_MM = 0.1088
USB_INNER_COPPER_MM = 0.0152
USB_PREPREG_ER = 4.16


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def item_references(finding: dict[str, object], candidates: set[str]) -> set[str]:
    references = set()
    for item in finding.get("items", []):
        if not isinstance(item, dict):
            continue
        description = str(item.get("description", ""))
        for candidate in candidates:
            if re.search(rf"(?<![A-Za-z0-9_]){re.escape(candidate)}(?![A-Za-z0-9_])", description):
                references.add(candidate)
    return references


def validate_generated_files() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_lb100_layout.py"), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        fail(result.stdout.strip() or result.stderr.strip() or "LB-100 generated layout is stale")


def csv_row(path: Path, key_column: str, key: str) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            if row.get(key_column) == key:
                return row
    fail(f"{path.relative_to(ROOT)} is missing {key}")


def validate_documented_decisions() -> None:
    lb_dir = BOARD_PATH.parents[1]
    sourcing = csv_row(
        lb_dir / "LB-100-component-sourcing-precheck.csv",
        "Symbol key",
        "LB_LUX",
    )
    if "Rev.1 EVT placement is accepted and non-blocking" not in sourcing.get(
        "Open blocker", ""
    ):
        fail("VEML7700 Rev.1 EVT placement decision is stale in component sourcing")
    inventory = csv_row(
        lb_dir / "LB-100-footprint-binding-inventory.csv",
        "Footprint item",
        "Ambient light sensor",
    )
    if "production/Rev.2" not in inventory.get("Next action", ""):
        fail("VEML7700 external-sensor Rev.2 decision is stale in footprint inventory")
    rail_budget = csv_row(
        lb_dir / "LB-100-rail-budget-closeout-precheck.csv",
        "Budget item",
        "IMU and lux sensors",
    )
    if "production/Rev.2" not in rail_budget.get("Blocked action", ""):
        fail("VEML7700 Rev.1/Rev.2 decision is stale in the rail budget")

    keepout_doc = (lb_dir / "LB-100-e73-antenna-keepout.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "E73-2G4M08S1C",
        "project-derived Rev.1 rule",
        "65.35..78.65 mm",
        "66.61 mm",
        "F.Cu`, `In1.Cu`, `In2.Cu`, `In3.Cu`, `In4.Cu`, and `B.Cu",
    ):
        if token not in keepout_doc:
            fail(f"LB-100 E73 keepout evidence is missing {token}")


def validate_board_milestone() -> None:
    try:
        board_text = BOARD_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing controlled layout: {BOARD_PATH.relative_to(ROOT)}")
    for token in (
        '(gr_rect (start 0 0) (end 100 70)',
        'LB-100 REV.1 EVT - NOT FOR PRODUCTION',
        'E73 ANTENNA - ALL-COPPER KEEPOUT',
        'STACKUP JLC06161H-3313 / 6L / 1.6 mm',
        'FOG A/B INPUT PROTECTION',
        '(property "Reference" "JPB1"',
        '(property "Reference" "U1"',
        '(property "Reference" "U7"',
        '(property "Reference" "TP1"',
        '(property "Reference" "TP2"',
        '(property "Reference" "TP3"',
        '(property "Reference" "TP4"',
        '(property "Reference" "TP5"',
        '(net 25 "E73_SWDCLK")',
        '(net 26 "E73_SWDIO")',
        '(property "Reference" "H8"',
        '(4 "In1.Cu" signal)',
        '(6 "In2.Cu" power)',
        '(8 "In3.Cu" signal)',
        '(10 "In4.Cu" power)',
        '(13 "F.Paste" user)',
        '(15 "B.Paste" user)',
        '(1 "F.Mask" user)',
        '(3 "B.Mask" user)',
        '(layer "dielectric 1" (type "prepreg") (thickness 0.0994)',
        '(layer "dielectric 2" (type "core") (thickness 0.55)',
        '(layer "dielectric 3" (type "prepreg") (thickness 0.1088)',
    ):
        if token not in board_text:
            fail(f"LB-100 controlled layout is missing {token}")
    if board_text.count("\n\t(footprint ") != EXPECTED_SCHEMATIC_FOOTPRINTS + 8:
        fail(
            "LB-100 placement must contain "
            f"{EXPECTED_SCHEMATIC_FOOTPRINTS} schematic footprints and eight mounting holes"
        )
    if board_text.count('(attr smd exclude_from_pos_files exclude_from_bom)') != 5:
        fail("LB-100 must expose exactly five non-assembly E73 recovery test pads")
    if board_text.count("\n\t(segment ") != EXPECTED_SEGMENTS:
        fail(f"LB-100 routing milestone must contain {EXPECTED_SEGMENTS} segments")
    if board_text.count("\n\t(via ") != EXPECTED_VIAS:
        fail(f"LB-100 routing milestone must contain {EXPECTED_VIAS} vias")
    if board_text.count("\n\t(zone\n") != EXPECTED_GND_ZONES + EXPECTED_ANTENNA_KEEPOUTS:
        fail("LB-100 must contain four GND zones and one E73 antenna keepout")
    gnd_zone_layers = set(
        re.findall(
            r'\(zone\s+\(net \d+\)\s+\(net_name "GND"\)\s+\(layer "([^"]+)"\)',
            board_text,
        )
    )
    if gnd_zone_layers != {"F.Cu", "In2.Cu", "In4.Cu", "B.Cu"}:
        fail(f"unexpected LB-100 GND zone layers: {sorted(gnd_zone_layers)}")
    for token in (
        '(layers "F.Cu" "In1.Cu" "In2.Cu" "In3.Cu" "In4.Cu" "B.Cu")',
        '(keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) '
        '(copperpour not_allowed) (footprints allowed))',
        '(xy 65.35 66.61)',
        '(xy 78.65 70.00)',
    ):
        if token not in board_text:
            fail(f"LB-100 E73 antenna keepout is missing {token}")


def validate_routing_geometry() -> None:
    lengths: dict[str, float] = {}
    controlled_segments: dict[str, dict[str, str]] = {}
    ground_vias: list[tuple[float, float]] = []
    segment_count = 0
    via_count = 0
    with (BOARD_PATH.parent / "LB-100-routing.csv").open(
        newline="", encoding="utf-8"
    ) as routing_file:
        for row in csv.DictReader(routing_file):
            if row["kind"] == "via":
                via_count += 1
                if row["start_layer"] != "F.Cu" or row["end_layer"] != "B.Cu":
                    fail("LB-100 EVT routing must use standard through vias only")
                if not math.isclose(float(row["diameter_mm"]), 0.50, abs_tol=1e-9):
                    fail("LB-100 via diameter changed from 0.50 mm")
                if not math.isclose(float(row["drill_mm"]), 0.30, abs_tol=1e-9):
                    fail("LB-100 via drill changed from 0.30 mm")
                if row["net"] == "GND":
                    ground_vias.append(
                        (float(row["start_x_mm"]), float(row["start_y_mm"]))
                    )
                continue
            if row["kind"] != "segment":
                fail(f"unsupported LB-100 routing item {row['kind']!r}")
            segment_count += 1
            if row["layer"] in {"In2.Cu", "In4.Cu"}:
                fail(f"signal routing is not allowed on reference plane {row['layer']}")
            start_x = float(row["start_x_mm"])
            start_y = float(row["start_y_mm"])
            end_x = float(row["end_x_mm"])
            end_y = float(row["end_y_mm"])
            length = math.hypot(end_x - start_x, end_y - start_y)
            lengths[row["net"]] = lengths.get(row["net"], 0.0) + length
            if (
                row["net"] in {"USB_D_P", "USB_D_N"}
                and row["layer"] == "In3.Cu"
                and length > 20.0
            ):
                controlled_segments[row["net"]] = row

    if segment_count != EXPECTED_SEGMENTS or via_count != EXPECTED_VIAS:
        fail("LB-100 routing-manifest counts do not match the controlled board")
    if set(controlled_segments) != {"USB_D_P", "USB_D_N"}:
        fail("LB-100 must have one long controlled In3.Cu segment per USB polarity")
    for net_name, row in controlled_segments.items():
        if not math.isclose(float(row["width_mm"]), USB_TRACE_WIDTH_MM, abs_tol=1e-9):
            fail(f"{net_name} controlled segment is not 0.20 mm wide")

    p = controlled_segments["USB_D_P"]
    n = controlled_segments["USB_D_N"]
    p_vector = (
        float(p["end_x_mm"]) - float(p["start_x_mm"]),
        float(p["end_y_mm"]) - float(p["start_y_mm"]),
    )
    n_vector = (
        float(n["end_x_mm"]) - float(n["start_x_mm"]),
        float(n["end_y_mm"]) - float(n["start_y_mm"]),
    )
    if any(not math.isclose(a, b, abs_tol=1e-9) for a, b in zip(p_vector, n_vector)):
        fail("LB-100 USB controlled segments are no longer parallel and length matched")
    offset = (
        float(n["start_x_mm"]) - float(p["start_x_mm"]),
        float(n["start_y_mm"]) - float(p["start_y_mm"]),
    )
    vector_length = math.hypot(*p_vector)
    centre_spacing = abs(p_vector[0] * offset[1] - p_vector[1] * offset[0]) / vector_length
    edge_gap = centre_spacing - USB_TRACE_WIDTH_MM
    if not 0.15 <= edge_gap <= 0.17:
        fail(f"LB-100 USB controlled edge gap changed to {edge_gap:.4f} mm")
    skew = abs(lengths["USB_D_P"] - lengths["USB_D_N"])
    if skew > MAX_USB_DATA_SKEW_MM:
        fail(f"LB-100 USB routed skew {skew:.4f} mm exceeds {MAX_USB_DATA_SKEW_MM:.2f} mm")

    # IPC-style edge-coupled estimate is a regression guard, not supplier
    # impedance evidence. The JLCPCB field solver remains an upload-time gate.
    z0 = 87.0 / math.sqrt(USB_PREPREG_ER + 1.41) * math.log(
        5.98 * USB_REFERENCE_HEIGHT_MM
        / (0.8 * USB_TRACE_WIDTH_MM + USB_INNER_COPPER_MM)
    )
    estimated_differential_ohms = 2.0 * z0 * (
        1.0 - 0.48 * math.exp(-0.96 * edge_gap / USB_REFERENCE_HEIGHT_MM)
    )
    if not 83.0 <= estimated_differential_ohms <= 95.0:
        fail(
            "LB-100 analytical USB impedance precheck changed to "
            f"{estimated_differential_ohms:.1f} ohm"
        )

    for centre in ((8.0, 39.0), (41.25, 43.15)):
        nearest_ground_via = min(
            math.hypot(centre[0] - via[0], centre[1] - via[1])
            for via in ground_vias
        )
        if nearest_ground_via > 4.0:
            fail(
                "LB-100 USB reference transition lacks a GND via within 4 mm "
                f"at {centre}"
            )


def validate_drc() -> None:
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli is None:
        fail("kicad-cli is required for LB-100 layout validation")
    version = subprocess.run([kicad_cli, "--version"], text=True, capture_output=True, check=False)
    if version.returncode or version.stdout.strip() != REQUIRED_KICAD_VERSION:
        fail(
            f"kicad-cli {REQUIRED_KICAD_VERSION} is required; "
            f"found {version.stdout.strip() or 'unavailable'}"
        )
    with tempfile.TemporaryDirectory(prefix="svc-lb100-layout-") as temp_dir:
        report_path = Path(temp_dir) / "LB-100-drc.json"
        result = subprocess.run(
            [
                kicad_cli,
                "pcb",
                "drc",
                "--format",
                "json",
                "--schematic-parity",
                "--severity-all",
                "--refill-zones",
                "--output",
                str(report_path),
                str(BOARD_PATH),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            fail(result.stdout.strip() or result.stderr.strip() or "KiCad could not check LB-100")
        report = json.loads(report_path.read_text(encoding="utf-8"))

    violations = report.get("violations", [])
    violation_types = Counter(finding.get("type") for finding in violations)
    if violation_types != ALLOWED_VIOLATIONS:
        fail(f"unexpected LB-100 placement DRC findings: {dict(violation_types)}")
    forbidden_types = {
        "shorting_items",
        "clearance",
        "hole_clearance",
        "courtyards_overlap",
        "npth_inside_courtyard",
        "pth_inside_courtyard",
        "copper_edge_clearance",
        "tracks_crossing",
        "items_not_allowed",
    }
    if forbidden_types & set(violation_types):
        fail(f"LB-100 placement contains unsafe geometry: {sorted(forbidden_types & set(violation_types))}")

    local_overrides = set().union(
        *(item_references(finding, {"JPB1", "JSD1", "JBT1"}) for finding in violations if finding.get("type") == "lib_footprint_mismatch")
    )
    if local_overrides != {"JPB1", "JSD1", "JBT1"}:
        fail(f"unexpected LB-100 local footprint overrides: {sorted(local_overrides)}")

    if len(report.get("unconnected_items", [])) != EXPECTED_UNCONNECTED_ITEMS:
        fail("LB-100 unconnected count changed during routing review")
    parity = report.get("schematic_parity", [])
    if Counter(finding.get("type") for finding in parity) != Counter({"extra_footprint": 8}):
        fail("LB-100 parity must contain only eight board mounting holes")
    parity_refs = set().union(*(item_references(finding, BOARD_ONLY_FOOTPRINTS) for finding in parity))
    if parity_refs != BOARD_ONLY_FOOTPRINTS:
        fail(f"unexpected LB-100 board-only footprints: {sorted(parity_refs)}")


def main() -> int:
    validate_generated_files()
    validate_documented_decisions()
    validate_board_milestone()
    validate_routing_geometry()
    validate_drc()
    print(
        "LB-100 controlled routing validation passed "
        f"({EXPECTED_SCHEMATIC_FOOTPRINTS} schematic footprints, 8 mounting holes, {EXPECTED_SEGMENTS} segments, "
        f"{EXPECTED_VIAS} standard through vias, zero unconnected; "
        f"{EXPECTED_GND_ZONES} GND zones and one six-layer E73 keepout; "
        "zero DRC errors with reviewed fabrication warnings after refill)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
