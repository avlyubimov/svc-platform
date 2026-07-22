#!/usr/bin/env python3
from __future__ import annotations

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
EXPECTED_UNCONNECTED_ITEMS = 55
EXPECTED_SEGMENTS = 1860
EXPECTED_VIAS = 172
BOARD_ONLY_FOOTPRINTS = {f"H{index}" for index in range(1, 9)}
ALLOWED_VIOLATIONS = Counter(
    {
        "lib_footprint_issues": 8,
        "lib_footprint_mismatch": 3,
        "annular_width": 2,
        "padstack": 2,
        "silk_edge_clearance": 2,
        "silk_overlap": 10,
        "silk_over_copper": 25,
        "nonmirrored_text_on_back_layer": 1,
        "diff_pair_uncoupled_length_too_long": 1,
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


def validate_board_milestone() -> None:
    try:
        board_text = BOARD_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing controlled layout: {BOARD_PATH.relative_to(ROOT)}")
    for token in (
        '(gr_rect (start 0 0) (end 100 70)',
        'LB-100 REV.1 EVT - NOT FOR PRODUCTION',
        'BLE ANTENNA - COPPER KEEPOUT REVIEW',
        'FOG A/B INPUT PROTECTION',
        '(property "Reference" "JPB1"',
        '(property "Reference" "U1"',
        '(property "Reference" "U7"',
        '(property "Reference" "H8"',
        '(2 "In1.Cu" power)',
        '(4 "In2.Cu" power)',
    ):
        if token not in board_text:
            fail(f"LB-100 controlled layout is missing {token}")
    if board_text.count("\n\t(footprint ") != 108:
        fail("LB-100 placement must contain 100 schematic footprints and eight mounting holes")
    if board_text.count("\n\t(segment ") != EXPECTED_SEGMENTS:
        fail(f"LB-100 routing milestone must contain {EXPECTED_SEGMENTS} segments")
    if board_text.count("\n\t(via ") != EXPECTED_VIAS:
        fail(f"LB-100 routing milestone must contain {EXPECTED_VIAS} vias")
    if "\n\t(zone " in board_text:
        fail("LB-100 EVT routing milestone must not claim copper-pour completion")


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
    validate_board_milestone()
    validate_drc()
    print(
        "LB-100 controlled routing validation passed "
        f"(100 schematic footprints, 8 mounting holes, {EXPECTED_SEGMENTS} segments, "
        f"{EXPECTED_VIAS} vias, {EXPECTED_UNCONNECTED_ITEMS} connections open; "
        "no shorts, crossings, or copper-clearance violations)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
