#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ORDER_READINESS = REPO_ROOT / "production" / "board-order" / "three_board_jlcpcb_order_readiness.csv"
LAYOUT_START_READINESS = (
    REPO_ROOT / "production" / "board-order" / "three_board_layout_start_readiness.csv"
)
FOOTPRINT_BINDING_STATUS = (
    REPO_ROOT / "production" / "board-order" / "three_board_footprint_binding_status.csv"
)
PB100_FREEZE = REPO_ROOT / "hardware" / "power-board" / "PB-100" / "PB-100-schematic-freeze-checklist.md"
PB100_BLOCKERS = REPO_ROOT / "hardware" / "power-board" / "PB-100" / "PB-100-board-release-blocker-register.csv"
BOARD_BLOCKERS = {
    "PB-100": PB100_BLOCKERS,
    "LB-100": REPO_ROOT / "hardware" / "logic-board" / "LB-100" / "LB-100-board-release-blocker-register.csv",
    "FB-100": REPO_ROOT / "hardware" / "front-board" / "FB-100" / "FB-100-board-release-blocker-register.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report SVC three-board JLCPCB order readiness.")
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="return a non-zero exit code while any board is not order-ready",
    )
    return parser.parse_args()


def checklist_status(path: Path) -> str:
    if not path.exists():
        return "Missing"
    match = re.search(r"^Status:\s*(.+?)\s*$", path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    if match is None:
        return "Unknown"
    return match.group(1)


def active_pb100_blockers() -> int:
    return active_blockers(PB100_BLOCKERS)


def active_blockers(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for row in csv.DictReader(handle) if row["Status"].strip() != "Closed")


def load_order_rows() -> list[dict[str, str]]:
    with ORDER_READINESS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_layout_rows() -> dict[str, dict[str, str]]:
    if not LAYOUT_START_READINESS.exists():
        return {}
    with LAYOUT_START_READINESS.open(newline="", encoding="utf-8") as handle:
        return {row["Board"]: row for row in csv.DictReader(handle)}


def load_footprint_rows() -> dict[str, dict[str, str]]:
    if not FOOTPRINT_BINDING_STATUS.exists():
        return {}
    with FOOTPRINT_BINDING_STATUS.open(newline="", encoding="utf-8") as handle:
        return {row["Board"]: row for row in csv.DictReader(handle)}


def main() -> int:
    args = parse_args()
    rows = load_order_rows()
    layout_rows = load_layout_rows()
    footprint_rows = load_footprint_rows()
    blocked_rows = [row for row in rows if row["Order state"].strip() != "READY"]
    layout_ready_rows = [
        row for row in layout_rows.values() if row["Layout planning state"].strip() == "READY"
    ]
    layout_import_blocked_rows = [
        row for row in layout_rows.values() if row["KiCad board import state"].strip() == "BLOCKED"
    ]

    print("SVC three-board order status")
    print(f"  Overall JLCPCB/PCBWay order: {'READY' if not blocked_rows else 'NO-GO'}")
    print(f"  PB-100 schematic freeze: {checklist_status(PB100_FREEZE)}")
    print(f"  PB-100 active release blockers: {active_pb100_blockers()}")
    print(f"  Boards tracked: {len(rows)}")
    print(f"  Boards not order-ready: {len(blocked_rows)}")
    print(f"  Boards layout-planning ready: {len(layout_ready_rows)}")
    print(f"  Boards KiCad board-import blocked: {len(layout_import_blocked_rows)}")
    print("")
    print("Board states:")
    for row in rows:
        board = row["Board"]
        blocker_path = BOARD_BLOCKERS.get(board)
        active_count = active_blockers(blocker_path) if blocker_path is not None else 0
        layout_row = layout_rows.get(board, {})
        footprint_row = footprint_rows.get(board, {})
        layout_state = layout_row.get("Layout planning state", "Missing")
        import_state = layout_row.get("KiCad board import state", "Missing")
        open_footprints = footprint_row.get("Open footprint items", "Missing")
        print(
            f"  - {board}: {row['Order state']} | "
            f"freeze={row['Schematic freeze state']} | "
            f"active_blockers={active_count} | "
            f"layout_planning={layout_state} | "
            f"board_import={import_state} | "
            f"open_footprints={open_footprints} | "
            f"kicad={row['KiCad schematic state']} | "
            f"next={row['Next action']}"
        )

    if args.fail_on_blocked and blocked_rows:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
