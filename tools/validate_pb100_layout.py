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
KICAD_DIR = ROOT / "hardware" / "power-board" / "PB-100" / "kicad"
BOARD_PATH = KICAD_DIR / "PB-100.kicad_pcb"
REQUIRED_KICAD_VERSION = "10.0.4"
EXPECTED_UNCONNECTED_ITEMS = 0
EXPECTED_FOOTPRINTS = 422
EXPECTED_SEGMENTS = 5677
EXPECTED_VIAS = 949
EXPECTED_ZONES = 38
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
        'VALUE-BEARING EVT LAYOUT - FAB REVIEW REQUIRED',
        'C36_BIDIRECTIONAL: OFF-BOARD FUSED VBAT_RAW BRANCH',
        '(property "Reference" "JPB1"',
        '(property "Reference" "Q1"',
        '(property "Reference" "Q110"',
        '(property "Reference" "U_CAN1_PHY"',
        '(4 "In1.Cu" signal)',
        '(6 "In2.Cu" power)',
        '(12 "In5.Cu" power)',
        '(14 "In6.Cu" signal)',
    ):
        if token not in board_text:
            fail(f"PB-100 controlled layout is missing {token}")
    if board_text.count("\n\t(footprint ") != EXPECTED_FOOTPRINTS:
        fail(
            "PB-100 import must contain 414 footprint-bound schematic parts "
            "and eight mounting holes"
        )
    if board_text.count("\n\t(segment ") != EXPECTED_SEGMENTS:
        fail(f"PB-100 routing baseline must contain {EXPECTED_SEGMENTS} segments")
    if board_text.count("\n\t(via ") != EXPECTED_VIAS:
        fail(f"PB-100 routing baseline must contain {EXPECTED_VIAS} vias")
    if board_text.count("\n\t(zone\n") != EXPECTED_ZONES:
        fail(f"PB-100 power topology must contain {EXPECTED_ZONES} zones")


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
        checked_dir = Path(temp_dir)
        checked_board_path = checked_dir / "PB-100.kicad_pcb"
        shutil.copy2(BOARD_PATH, checked_board_path)
        # Keep the disposable refilled board in the same project context as
        # the tracked board.  Copying only the PCB makes KiCad report every
        # footprint as an unresolved-library issue and hides real mismatch
        # findings behind an artificial warning baseline.
        for project_file in (
            "PB-100.kicad_pro",
            "PB-100.kicad_dru",
            "fp-lib-table",
        ):
            shutil.copy2(KICAD_DIR / project_file, checked_dir / project_file)
        shutil.copytree(KICAD_DIR / "lib", checked_dir / "lib")
        report_path = Path(temp_dir) / "PB-100-drc.json"
        result = subprocess.run(
            [
                kicad_cli,
                "pcb",
                "drc",
                "--format",
                "json",
                "--severity-all",
                "--refill-zones",
                "--save-board",
                "--output",
                str(report_path),
                str(checked_board_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            fail(result.stdout.strip() or result.stderr.strip() or "KiCad could not check PB-100")
        report = json.loads(report_path.read_text(encoding="utf-8"))

    violation_types = Counter(finding.get("type") for finding in report.get("violations", []))
    expected_violations = Counter(
        {
            "lib_footprint_mismatch": 27,
            "lib_footprint_issues": 8,
            "silk_over_copper": 136,
            "silk_overlap": 17,
        }
    )
    if violation_types != expected_violations:
        fail(f"unexpected PB-100 refilled DRC findings: {dict(violation_types)}")
    if len(report.get("unconnected_items", [])) != EXPECTED_UNCONNECTED_ITEMS:
        fail("PB-100 routed-baseline unconnected count changed")

    with tempfile.TemporaryDirectory(prefix="svc-pb100-layout-parity-") as temp_dir:
        parity_report_path = Path(temp_dir) / "PB-100-parity.json"
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
                str(parity_report_path),
                str(BOARD_PATH),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            fail(result.stdout.strip() or result.stderr.strip() or "KiCad parity check failed")
        parity_report = json.loads(parity_report_path.read_text(encoding="utf-8"))

    parity = parity_report.get("schematic_parity", [])
    parity_types = Counter(finding.get("type") for finding in parity)
    expected_parity = Counter({"extra_footprint": 8})
    if parity_types != expected_parity:
        fail(f"PB-100 schematic parity changed: {dict(parity_types)}")
    board_only_refs = set().union(*(item_references(finding, BOARD_ONLY_FOOTPRINTS) for finding in parity))
    if board_only_refs != BOARD_ONLY_FOOTPRINTS:
        fail(f"unexpected PB-100 board-only footprints: {sorted(board_only_refs)}")


def main() -> int:
    validate_generated_files()
    validate_board_milestone()
    validate_drc()
    print(
        "PB-100 controlled EVT routing baseline validation passed "
        f"({EXPECTED_FOOTPRINTS} footprints, {EXPECTED_SEGMENTS} segments, "
        f"{EXPECTED_VIAS} vias, {EXPECTED_ZONES} zones, "
        f"{EXPECTED_UNCONNECTED_ITEMS} remaining connectivity blockers; "
        "fabrication remains blocked pending EVT-FAB-REVIEW)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
