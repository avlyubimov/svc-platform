#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import os
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
EXPECTED_UNCONNECTED_ITEMS = 0
EXPECTED_SEGMENTS = 457
EXPECTED_VIAS = 48
EXPECTED_ZONES = 4
EXPECTED_LOCAL_OVERRIDES = {"J1", "JFB1"}
EXPECTED_BOARD_ONLY_FOOTPRINTS = {"H1", "H2", "H3", "H4"}
MAX_USB_DATA_SKEW_MM = 0.10
USB_TRACE_WIDTH_MM = 0.154
USB_TRACE_GAP_MM = 0.2032
USB_REFERENCE_HEIGHT_MM = 0.0994
USB_OUTER_COPPER_MM = 0.035
USB_PREPREG_ER = 4.1


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
        '(layer "dielectric 1" (type "prepreg") (thickness 0.0994) (material "3313 RC57%") (epsilon_r 4.1)',
        '(layer "dielectric 2" (type "core") (thickness 1.265) (material "FR4") (epsilon_r 4.6)',
        '(copper_finish "ENIG")',
    )
    for token in required_tokens:
        if token not in board_text:
            fail(f"FB-100 controlled layout is missing {token}")
    if board_text.count("\n\t(footprint ") != 48:
        fail("FB-100 placement milestone must contain 44 schematic footprints and four mounting holes")
    if board_text.count("\n\t(segment ") != EXPECTED_SEGMENTS:
        fail(f"FB-100 routing milestone must contain {EXPECTED_SEGMENTS} segments")
    if board_text.count("\n\t(via ") != EXPECTED_VIAS:
        fail(f"FB-100 routing milestone must contain {EXPECTED_VIAS} vias")
    if board_text.count("\n\t(zone\n") != EXPECTED_ZONES:
        fail(f"FB-100 layout must contain {EXPECTED_ZONES} GND zones")
    zone_layers = set(
        re.findall(
            r'\(zone\s+\(net \d+\)\s+\(net_name "GND"\)\s+\(layer "([^"]+)"\)',
            board_text,
        )
    )
    if zone_layers != {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"}:
        fail(f"unexpected FB-100 GND zone layers: {sorted(zone_layers)}")

    project = json.loads((KICAD_DIR / "FB-100.kicad_pro").read_text(encoding="utf-8"))
    mismatch_severity = (
        project.get("board", {})
        .get("design_settings", {})
        .get("rule_severities", {})
        .get("lib_footprint_mismatch")
    )
    if mismatch_severity != "ignore":
        fail("FB-100 generated connector transforms must be audited by CI, not UI warnings")


def validate_usb_geometry() -> None:
    lengths: dict[str, float] = {}
    controlled_segments: dict[str, dict[str, str]] = {}
    ground_vias: list[tuple[float, float]] = []
    with (KICAD_DIR / "FB-100-routing.csv").open(
        newline="", encoding="utf-8"
    ) as routing_file:
        for row in csv.DictReader(routing_file):
            if row["kind"] == "via" and row["net"] == "GND":
                ground_vias.append(
                    (float(row["start_x_mm"]), float(row["start_y_mm"]))
                )
            if row["kind"] != "segment":
                continue
            start_x = float(row["start_x_mm"])
            start_y = float(row["start_y_mm"])
            end_x = float(row["end_x_mm"])
            end_y = float(row["end_y_mm"])
            length = math.hypot(end_x - start_x, end_y - start_y)
            lengths[row["net"]] = lengths.get(row["net"], 0.0) + length
            if (
                row["net"] in {"USB_D_P", "USB_D_N"}
                and row["layer"] == "B.Cu"
                and length > 50.0
            ):
                controlled_segments[row["net"]] = row

    if set(controlled_segments) != {"USB_D_P", "USB_D_N"}:
        fail("FB-100 must have one long controlled B.Cu segment per USB polarity")
    for net_name, row in controlled_segments.items():
        if not math.isclose(
            float(row["width_mm"]), USB_TRACE_WIDTH_MM, abs_tol=0.0005
        ):
            fail(f"{net_name} controlled segment is not 0.154 mm wide")
        if not math.isclose(
            float(row["start_y_mm"]), float(row["end_y_mm"]), abs_tol=1e-9
        ):
            fail(f"{net_name} controlled segment must remain horizontal")
    center_spacing = abs(
        float(controlled_segments["USB_D_P"]["start_y_mm"])
        - float(controlled_segments["USB_D_N"]["start_y_mm"])
    )
    edge_gap = center_spacing - USB_TRACE_WIDTH_MM
    if not math.isclose(edge_gap, USB_TRACE_GAP_MM, abs_tol=0.0005):
        fail(f"FB-100 USB controlled edge gap changed to {edge_gap:.4f} mm")
    skew = abs(lengths["USB_D_P"] - lengths["USB_D_N"])
    if skew > MAX_USB_DATA_SKEW_MM:
        fail(f"FB-100 USB routed skew {skew:.4f} mm exceeds {MAX_USB_DATA_SKEW_MM:.2f} mm")

    # IPC-style edge-coupled microstrip estimate used only as a regression
    # guard. Supplier field-solver confirmation remains an EVT fab-review gate.
    z0 = 87.0 / math.sqrt(USB_PREPREG_ER + 1.41) * math.log(
        5.98 * USB_REFERENCE_HEIGHT_MM
        / (0.8 * USB_TRACE_WIDTH_MM + USB_OUTER_COPPER_MM)
    )
    estimated_differential_ohms = 2.0 * z0 * (
        1.0
        - 0.48
        * math.exp(-0.96 * USB_TRACE_GAP_MM / USB_REFERENCE_HEIGHT_MM)
    )
    if not 85.0 <= estimated_differential_ohms <= 100.0:
        fail(
            "FB-100 analytical USB impedance precheck changed to "
            f"{estimated_differential_ohms:.1f} ohm"
        )

    transition_centres = (
        (3.5, 17.75),
        (13.5, 3.5),
        (69.0, 3.0),
        (73.0, 12.875),
    )
    for centre in transition_centres:
        nearest_ground_via = min(
            math.hypot(centre[0] - via[0], centre[1] - via[1])
            for via in ground_vias
        )
        if nearest_ground_via > 4.0:
            fail(
                "FB-100 USB reference transition lacks a GND via within 4 mm "
                f"at {centre}"
            )


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
            details = "\n".join(
                part for part in (result.stdout.strip(), result.stderr.strip()) if part
            )
            fail(f"KiCad could not validate FB-100 layout: {details}")
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as error:
            fail(f"invalid FB-100 DRC report: {error}")

    violations = report.get("violations", [])
    if violations:
        fail(
            "FB-100 default DRC must be clean after zone refill: "
            f"{dict(Counter(finding.get('type') for finding in violations))}"
        )

    unconnected_items = report.get("unconnected_items", [])
    if len(unconnected_items) != EXPECTED_UNCONNECTED_ITEMS:
        fail(
            "FB-100 placement milestone unconnected count changed: "
            f"expected {EXPECTED_UNCONNECTED_ITEMS}, found {len(unconnected_items)}"
        )
    if unconnected_items and {
        finding.get("type") for finding in unconnected_items
    } != {"unconnected_items"}:
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

    with tempfile.TemporaryDirectory(prefix="svc-fb100-library-audit-") as audit_dir:
        audit_path = Path(audit_dir)
        shutil.copy2(BOARD_PATH, audit_path / BOARD_PATH.name)
        shutil.copy2(KICAD_DIR / "FB-100.kicad_dru", audit_path / "FB-100.kicad_dru")
        shutil.copy2(KICAD_DIR / "fp-lib-table", audit_path / "fp-lib-table")
        os.symlink(KICAD_DIR / "lib", audit_path / "lib", target_is_directory=True)
        audit_report_path = audit_path / "FB-100-library-audit.json"
        audit_result = subprocess.run(
            [
                kicad_cli,
                "pcb",
                "drc",
                "--format",
                "json",
                "--refill-zones",
                "--severity-all",
                "--output",
                str(audit_report_path),
                str(audit_path / BOARD_PATH.name),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if audit_result.returncode:
            fail(f"KiCad could not audit FB-100 connector transforms: {audit_result.stderr.strip()}")
        audit_report = json.loads(audit_report_path.read_text(encoding="utf-8"))
    audit_violations = audit_report.get("violations", [])
    if Counter(finding.get("type") for finding in audit_violations) != Counter(
        {"lib_footprint_mismatch": len(EXPECTED_LOCAL_OVERRIDES)}
    ):
        fail("FB-100 raw library audit contains unexpected findings")
    local_overrides = set().union(
        *(
            item_references(finding, EXPECTED_LOCAL_OVERRIDES)
            for finding in audit_violations
        )
    )
    if local_overrides != EXPECTED_LOCAL_OVERRIDES:
        fail(f"unexpected generated connector transforms: {sorted(local_overrides)}")


def main() -> int:
    validate_generated_files()
    validate_board_milestone()
    validate_usb_geometry()
    validate_drc()
    print(
        "FB-100 controlled routing validation passed "
        f"(44 schematic footprints, 4 mounting holes, {EXPECTED_SEGMENTS} segments, "
        f"{EXPECTED_VIAS} vias, {EXPECTED_ZONES} GND zones, zero DRC and unconnected; "
        "fab review remains open)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
