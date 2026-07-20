#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PB100_DIR = REPO_ROOT / "hardware" / "power-board" / "PB-100"
CHECKLIST = PB100_DIR / "PB-100-schematic-freeze-checklist.md"
BLOCKERS = PB100_DIR / "PB-100-board-release-blocker-register.csv"
CLOSURE_MATRIX = PB100_DIR / "PB-100-board-print-closure-matrix.csv"
POST_PROTOTYPE_GATE = PB100_DIR / "PB-100-post-prototype-validation-gate.csv"
LAYOUT_START_CHECKLIST = PB100_DIR / "PB-100-pcb-layout-start-checklist.csv"
FOOTPRINT_BINDING_STATUS = (
    REPO_ROOT / "production" / "board-order" / "three_board_footprint_binding_status.csv"
)
MECHANICAL_ENVELOPE_STATUS = (
    REPO_ROOT / "production" / "board-order" / "three_board_mechanical_envelope_status.csv"
)
KICAD_DIR = PB100_DIR / "kicad"

MANUFACTURING_SUFFIXES = {
    ".drl",
    ".gbr",
    ".gbl",
    ".gbo",
    ".gbs",
    ".gko",
    ".gm1",
    ".gtl",
    ".gto",
    ".gts",
    ".kicad_pos",
    ".pos",
    ".xln",
}
MANUFACTURING_NAME_FRAGMENTS = (
    "gerber",
    "drill",
    "pick-place",
    "pick_and_place",
    "pickplace",
    "placement",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report whether PB-100 is ready for PCB layout or board printing."
    )
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="return a non-zero exit code when PB-100 is not board-print ready",
    )
    return parser.parse_args()


def checklist_status() -> str:
    text = CHECKLIST.read_text(encoding="utf-8")
    match = re.search(r"^Status:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    if not match:
        return "Unknown"
    return match.group(1)


def checklist_gates() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in CHECKLIST.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 4:
            continue
        if cells[0] in {"Gate", "---"}:
            continue
        rows.append(
            {
                "Gate": cells[0].strip("`"),
                "Status": cells[1].strip("`"),
                "Evidence": cells[2],
                "Close condition": cells[3],
            }
        )
    return rows


def release_blockers() -> list[dict[str, str]]:
    with BLOCKERS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def board_print_closure_rows() -> list[dict[str, str]]:
    if not CLOSURE_MATRIX.exists():
        return []
    with CLOSURE_MATRIX.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def post_prototype_gate_rows() -> list[dict[str, str]]:
    if not POST_PROTOTYPE_GATE.exists():
        return []
    with POST_PROTOTYPE_GATE.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def layout_start_rows() -> list[dict[str, str]]:
    if not LAYOUT_START_CHECKLIST.exists():
        return []
    with LAYOUT_START_CHECKLIST.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def open_footprint_items() -> str:
    if not FOOTPRINT_BINDING_STATUS.exists():
        return "Missing"
    with FOOTPRINT_BINDING_STATUS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["Board"] == "PB-100":
                return row["Open footprint items"]
    return "Missing"


def open_mechanical_items() -> str:
    if not MECHANICAL_ENVELOPE_STATUS.exists():
        return "Missing"
    with MECHANICAL_ENVELOPE_STATUS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["Board"] == "PB-100":
                return row["Open mechanical items"]
    return "Missing"


def layout_files() -> list[Path]:
    return sorted(KICAD_DIR.rglob("*.kicad_pcb"))


def manufacturing_files() -> list[Path]:
    files: list[Path] = []
    for path in PB100_DIR.rglob("*"):
        if not path.is_file():
            continue
        lowered_name = path.name.lower()
        if path.suffix.lower() in MANUFACTURING_SUFFIXES:
            files.append(path)
            continue
        if path.suffix.lower() == ".zip" and any(
            fragment in lowered_name for fragment in MANUFACTURING_NAME_FRAGMENTS
        ):
            files.append(path)
    return sorted(files)


def relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def main() -> int:
    args = parse_args()

    status = checklist_status()
    gates = checklist_gates()
    blockers = release_blockers()
    closure_rows = board_print_closure_rows()
    post_prototype_rows = post_prototype_gate_rows()
    layout_rows = layout_start_rows()
    active_gates = [row for row in gates if row["Status"] != "Closed"]
    active_blockers = [row for row in blockers if row["Status"] != "Closed"]
    active_closure_rows = [row for row in closure_rows if row["Current proof state"] != "Closed"]
    deferred_post_prototype = [
        row for row in post_prototype_rows if row.get("Status", "").strip() != "Closed"
    ]
    pcbs = layout_files()
    manufacturing = manufacturing_files()
    open_layout_start_rows = [row for row in layout_rows if row.get("Status", "").strip() == "Open"]
    board_import_blockers = [
        row for row in open_layout_start_rows if row.get("Gate", "").strip() in {"Footprint binding", "Mechanical envelope"}
    ]

    board_print_ready = (
        status == "Closed"
        and not active_gates
        and not active_blockers
        and bool(pcbs)
        and bool(manufacturing)
    )
    layout_ready = status == "Closed" and not active_gates and not active_blockers
    board_import_ready = layout_ready and not board_import_blockers

    print("PB-100 release status")
    print(f"  Schematic freeze checklist: {status}")
    print(f"  Layout planning authorization: {'READY' if layout_ready else 'BLOCKED'}")
    print(f"  KiCad board import: {'READY' if board_import_ready else 'BLOCKED'}")
    print(f"  Board-print package: {'READY' if board_print_ready else 'NO-GO'}")
    print(f"  Active freeze gates: {len(active_gates)}")
    print(f"  Active release blockers: {len(active_blockers)}")
    print(f"  Open layout-start gates: {len(open_layout_start_rows)}")
    print(f"  Open footprint items: {open_footprint_items()}")
    print(f"  Open mechanical items: {open_mechanical_items()}")
    print(f"  Board-print closure rows: {len(active_closure_rows)}")
    print(f"  Deferred post-prototype validation gates: {len(deferred_post_prototype)}")
    print(f"  KiCad PCB files: {len(pcbs)}")
    print(f"  Manufacturing output files: {len(manufacturing)}")

    if active_blockers:
        print("")
        print("Active release blockers:")
        for row in active_blockers:
            gate = row["Gate"]
            blocker_id = row["Blocker ID"]
            action = row["Next engineering action"]
            print(f"  - {blocker_id}: {gate} - {action}")

    if board_import_blockers:
        print("")
        print("KiCad board-import blockers:")
        for row in board_import_blockers:
            print(f"  - {row['Gate']}: {row['Blocked action']}")

    if pcbs:
        print("")
        print("KiCad PCB files:")
        for path in pcbs:
            print(f"  - {relative(path)}")

    if manufacturing:
        print("")
        print("Manufacturing output files:")
        for path in manufacturing:
            print(f"  - {relative(path)}")

    if args.fail_on_blocked and not board_print_ready:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
