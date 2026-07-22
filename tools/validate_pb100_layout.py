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
BOARD_PATH = ROOT / "hardware" / "power-board" / "PB-100" / "kicad" / "PB-100.kicad_pcb"
REQUIRED_KICAD_VERSION = "10.0.4"
EXPECTED_UNCONNECTED_ITEMS = 127
EXPECTED_SEGMENTS = 110
EXPECTED_VIAS = 14
BOARD_ONLY_FOOTPRINTS = {f"H{index}" for index in range(1, 9)}


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
        [sys.executable, str(ROOT / "tools" / "generate_pb100_layout.py"), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        fail(result.stdout.strip() or result.stderr.strip() or "PB-100 generated layout is stale")


def validate_board_milestone() -> None:
    try:
        board_text = BOARD_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing controlled layout: {BOARD_PATH.relative_to(ROOT)}")
    for token in (
        '(gr_rect (start 0 0) (end 150 90)',
        'PB-100 REV.1 EVT - NOT FOR PRODUCTION',
        'PARTIAL SCHEMATIC IMPORT - FAB REVIEW BLOCKED',
        'C36_BIDIRECTIONAL: OFF-BOARD FUSED VBAT_RAW BRANCH',
        '(property "Reference" "JPB1"',
        '(property "Reference" "Q1"',
        '(property "Reference" "Q110"',
        '(property "Reference" "U_CAN1_PHY"',
        '(2 "In1.Cu" power)',
        '(4 "In2.Cu" power)',
    ):
        if token not in board_text:
            fail(f"PB-100 controlled layout is missing {token}")
    if board_text.count("\n\t(footprint ") != 41:
        fail("PB-100 import must contain 33 footprint-bound schematic parts and eight mounting holes")
    if board_text.count("\n\t(segment ") != EXPECTED_SEGMENTS:
        fail(f"PB-100 CAN1 and FOG-entry routing milestone must contain {EXPECTED_SEGMENTS} segments")
    if board_text.count("\n\t(via ") != EXPECTED_VIAS:
        fail(f"PB-100 CAN1 routing milestone must contain {EXPECTED_VIAS} vias")
    if "\n\t(zone " in board_text:
        fail("PB-100 partial import must not claim copper-pour completion")


def validate_drc() -> None:
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli is None:
        fail("kicad-cli is required for PB-100 layout validation")
    version = subprocess.run([kicad_cli, "--version"], text=True, capture_output=True, check=False)
    if version.returncode or version.stdout.strip() != REQUIRED_KICAD_VERSION:
        fail(
            f"kicad-cli {REQUIRED_KICAD_VERSION} is required; "
            f"found {version.stdout.strip() or 'unavailable'}"
        )
    with tempfile.TemporaryDirectory(prefix="svc-pb100-layout-drc-") as temp_dir:
        report_path = Path(temp_dir) / "PB-100-drc.json"
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
            fail(result.stdout.strip() or result.stderr.strip() or "KiCad could not check PB-100")
        report = json.loads(report_path.read_text(encoding="utf-8"))

    violation_types = Counter(finding.get("type") for finding in report.get("violations", []))
    if violation_types != Counter({"silk_over_copper": 14, "lib_footprint_issues": 8}):
        fail(f"unexpected PB-100 placement DRC findings: {dict(violation_types)}")
    if len(report.get("unconnected_items", [])) != EXPECTED_UNCONNECTED_ITEMS:
        fail("PB-100 unconnected count changed before complete schematic import and power routing")

    parity = report.get("schematic_parity", [])
    parity_types = Counter(finding.get("type") for finding in parity)
    expected_parity = Counter({"missing_footprint": 46, "extra_footprint": 8, "net_conflict": 6})
    if parity_types != expected_parity:
        fail(f"PB-100 partial-import parity changed: {dict(parity_types)}")
    board_only_refs = set().union(*(item_references(finding, BOARD_ONLY_FOOTPRINTS) for finding in parity))
    if board_only_refs != BOARD_ONLY_FOOTPRINTS:
        fail(f"unexpected PB-100 board-only footprints: {sorted(board_only_refs)}")
    net_conflict_refs = set().union(*(item_references(finding, {"U1"}) for finding in parity if finding.get("type") == "net_conflict"))
    if net_conflict_refs != {"U1"}:
        fail(f"unexpected PB-100 partial-import net conflicts: {sorted(net_conflict_refs)}")


def main() -> int:
    validate_generated_files()
    validate_board_milestone()
    validate_drc()
    print(
        "PB-100 controlled partial import validation passed "
        f"(33 footprint-bound parts, 8 mounting holes, CAN1 safety island and protected FOG entry routed with "
        f"{EXPECTED_SEGMENTS} segments and {EXPECTED_VIAS} vias; 46 missing footprints "
        "and all power routing remain fab blockers)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
