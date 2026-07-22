#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
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
EXPECTED_UNCONNECTED_ITEMS = 53
EXPECTED_SEGMENTS = 1844
EXPECTED_VIAS = 188
EXPECTED_GND_ZONES = 4
EXPECTED_ANTENNA_KEEPOUTS = 1
EXPECTED_SCHEMATIC_FOOTPRINTS = 104
BOARD_ONLY_FOOTPRINTS = {f"H{index}" for index in range(1, 9)}
ALLOWED_VIOLATIONS = Counter(
    {
        "silk_over_copper": 10,
        "track_dangling": 7,
        "lib_footprint_issues": 8,
        "silk_edge_clearance": 6,
        "silk_overlap": 6,
        "starved_thermal": 3,
        "lib_footprint_mismatch": 3,
        "annular_width": 2,
        "padstack": 2,
        "diff_pair_uncoupled_length_too_long": 1,
        "via_dangling": 1,
        "nonmirrored_text_on_back_layer": 1,
    }
)


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
        "F.Cu`, `In1.Cu`, `In2.Cu`, and `B.Cu",
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
        '(2 "In1.Cu" power)',
        '(4 "In2.Cu" power)',
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
    if gnd_zone_layers != {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"}:
        fail(f"unexpected LB-100 GND zone layers: {sorted(gnd_zone_layers)}")
    for token in (
        '(layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu")',
        '(keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) '
        '(copperpour not_allowed) (footprints allowed))',
        '(xy 65.35 66.61)',
        '(xy 78.65 70.00)',
    ):
        if token not in board_text:
            fail(f"LB-100 E73 antenna keepout is missing {token}")


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
    validate_drc()
    print(
        "LB-100 controlled routing validation passed "
        f"({EXPECTED_SCHEMATIC_FOOTPRINTS} schematic footprints, 8 mounting holes, {EXPECTED_SEGMENTS} segments, "
        f"{EXPECTED_VIAS} vias, {EXPECTED_UNCONNECTED_ITEMS} connections open; "
        f"{EXPECTED_GND_ZONES} GND zones and one four-layer E73 keepout; "
        "no shorts, crossings, copper-clearance, or keepout violations after refill)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
