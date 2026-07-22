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


REPO_ROOT = Path(__file__).resolve().parents[1]
FB100_DIR = REPO_ROOT / "hardware" / "front-board" / "FB-100"
KICAD_DIR = FB100_DIR / "kicad"
BOARD_PATH = KICAD_DIR / "FB-100.kicad_pcb"
REQUIRED_KICAD_VERSION = "10.0.4"
EXPECTED_UNCONNECTED_ITEMS = 93
EXPECTED_LOCAL_OVERRIDES = {"J1", "J2", "JFB1"}
EXPECTED_BOARD_ONLY_FOOTPRINTS = {"H1", "H2", "H3", "H4"}
EXPECTED_EDGE_ITEM_UUIDS = {
    "fb0719a1-1843-5594-91c9-801588abb5dc": "BOARD_OUTLINE",
    "2130a68b-ae92-520a-b8f3-3a1de6853de5": "J1_PAD_3_USB_SHIELD",
    "0b390b2f-9137-5ce3-8b57-77e787288b2e": "J1_PAD_4_USB_SHIELD",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def item_descriptions(finding: dict[str, object]) -> set[str]:
    items = finding.get("items", [])
    return {
        str(item.get("description", ""))
        for item in items
        if isinstance(item, dict)
    }


def item_references(finding: dict[str, object], candidates: set[str]) -> set[str]:
    references = set()
    for description in item_descriptions(finding):
        for candidate in candidates:
            reference_pattern = (
                rf"(?<![A-Za-z0-9_]){re.escape(candidate)}(?![A-Za-z0-9_])"
            )
            if re.search(reference_pattern, description):
                references.add(candidate)
    return references


def validate_generated_files() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "generate_fb100_layout.py"), "--check"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        details = "\n".join(
            part for part in (result.stdout.strip(), result.stderr.strip()) if part
        )
        fail(details or "FB-100 generated layout files are stale")


def validate_board_milestone() -> None:
    try:
        board_text = BOARD_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing controlled layout: {BOARD_PATH.relative_to(REPO_ROOT)}")

    required_tokens = (
        '(gr_rect (start 0 0) (end 80 35)',
        'FB-100 REV.1 EVT - NOT FOR PRODUCTION',
        'USB PANEL KEEPOUT',
        'FFC BEND KEEPOUT',
        'OLED DNP WINDOW',
        '(property "Reference" "J1"',
        '(property "Reference" "JFB1"',
        '(property "Reference" "H1"',
        '(property "Reference" "H4"',
    )
    for token in required_tokens:
        if token not in board_text:
            fail(f"FB-100 controlled layout is missing {token}")
    if board_text.count("\n\t(footprint ") != 48:
        fail("FB-100 placement milestone must contain 44 schematic footprints and four mounting holes")
    if board_text.count("\n\t(segment ") != 10:
        fail("FB-100 routing milestone must contain ten local LED series routes")
    for forbidden_token in ("\n\t(via ", "\n\t(zone "):
        if forbidden_token in board_text:
            fail("FB-100 routing milestone must not claim via or copper-pour completion")


def validate_drc() -> None:
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli is None:
        fail("kicad-cli is required for FB-100 layout validation")
    version = subprocess.run(
        [kicad_cli, "--version"],
        text=True,
        capture_output=True,
        check=False,
    )
    if version.returncode or version.stdout.strip() != REQUIRED_KICAD_VERSION:
        fail(
            f"kicad-cli {REQUIRED_KICAD_VERSION} is required; "
            f"found {version.stdout.strip() or 'unavailable'}"
        )

    with tempfile.TemporaryDirectory(prefix="svc-fb100-layout-") as temp_dir:
        report_path = Path(temp_dir) / "FB-100-drc.json"
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
            details = "\n".join(
                part for part in (result.stdout.strip(), result.stderr.strip()) if part
            )
            fail(f"KiCad could not validate FB-100 layout: {details}")
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as error:
            fail(f"invalid FB-100 DRC report: {error}")

    violations = report.get("violations", [])
    violation_types = Counter(finding.get("type") for finding in violations)
    if violation_types != Counter({"copper_edge_clearance": 2, "lib_footprint_mismatch": 3}):
        fail(f"unexpected FB-100 placement DRC findings: {dict(violation_types)}")

    edge_pads = set()
    local_overrides = set()
    for finding in violations:
        finding_type = finding.get("type")
        if finding_type == "copper_edge_clearance":
            item_uuids = {
                str(item.get("uuid", ""))
                for item in finding.get("items", [])
                if isinstance(item, dict)
            }
            labels = {
                EXPECTED_EDGE_ITEM_UUIDS.get(item_uuid) for item_uuid in item_uuids
            }
            if None in labels or "BOARD_OUTLINE" not in labels or len(labels) != 2:
                fail(
                    "unexpected objects in USB-C edge-entry exception: "
                    f"{sorted(item_uuids)}"
                )
            edge_pads.update(label for label in labels if label != "BOARD_OUTLINE")
        elif finding_type == "lib_footprint_mismatch":
            local_overrides.update(item_references(finding, EXPECTED_LOCAL_OVERRIDES))
    if edge_pads != {
        "J1_PAD_3_USB_SHIELD",
        "J1_PAD_4_USB_SHIELD",
    }:
        fail(f"unexpected USB-C edge-entry findings: {sorted(edge_pads)}")
    if local_overrides != EXPECTED_LOCAL_OVERRIDES:
        fail(f"unexpected generated connector overrides: {sorted(local_overrides)}")

    unconnected_items = report.get("unconnected_items", [])
    if len(unconnected_items) != EXPECTED_UNCONNECTED_ITEMS:
        fail(
            "FB-100 placement milestone unconnected count changed: "
            f"expected {EXPECTED_UNCONNECTED_ITEMS}, found {len(unconnected_items)}"
        )
    if {finding.get("type") for finding in unconnected_items} != {"unconnected_items"}:
        fail("FB-100 unconnected section contains an unexpected finding type")

    parity_findings = report.get("schematic_parity", [])
    if Counter(finding.get("type") for finding in parity_findings) != Counter(
        {"extra_footprint": 4}
    ):
        fail("FB-100 schematic parity must contain only the four board mounting holes")
    parity_footprints = set().union(
        *(
            item_references(finding, EXPECTED_BOARD_ONLY_FOOTPRINTS)
            for finding in parity_findings
        )
    )
    if parity_footprints != EXPECTED_BOARD_ONLY_FOOTPRINTS:
        fail(f"unexpected FB-100 board-only footprints: {sorted(parity_footprints)}")


def main() -> int:
    validate_generated_files()
    validate_board_milestone()
    validate_drc()
    print(
        "FB-100 controlled routing validation passed "
        "(44 schematic footprints, 4 mounting holes, 10 local indicator series routes)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
