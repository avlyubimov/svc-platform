from __future__ import annotations

import csv
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PB100_DIR = REPO_ROOT / "hardware" / "power-board" / "PB-100"
LB100_DIR = REPO_ROOT / "hardware" / "logic-board" / "LB-100"
FB100_DIR = REPO_ROOT / "hardware" / "front-board" / "FB-100"

BLOCKER_REGISTERS = {
    "PB-100": PB100_DIR / "PB-100-board-release-blocker-register.csv",
    "LB-100": LB100_DIR / "LB-100-board-release-blocker-register.csv",
    "FB-100": FB100_DIR / "FB-100-board-release-blocker-register.csv",
}
AGGREGATE_READINESS = (
    REPO_ROOT / "production" / "board-order" / "three_board_jlcpcb_order_readiness.csv",
    REPO_ROOT / "production" / "board-order" / "three_board_layout_start_readiness.csv",
)
FINAL_READINESS = REPO_ROOT / "docs" / "product" / "final-readiness.md"
ADR_0015 = REPO_ROOT / "docs" / "adr" / "ADR-0015-can1-physical-layer-board-ownership.md"
FOOTPRINT_STATUS = (
    REPO_ROOT / "production" / "board-order" / "three_board_footprint_binding_status.csv"
)
LAYOUT_CHECKLISTS = {
    "PB-100": PB100_DIR / "PB-100-pcb-layout-start-checklist.csv",
    "LB-100": LB100_DIR / "LB-100-pcb-layout-start-checklist.csv",
    "FB-100": FB100_DIR / "FB-100-pcb-layout-start-checklist.csv",
}

ACTIVE_DOCUMENTS = (
    PB100_DIR / "PB-100-schematic-freeze-checklist.md",
    PB100_DIR / "PB-100-schematic-readiness-dashboard.csv",
    PB100_DIR / "PB-100-board-print-closure-matrix.csv",
    PB100_DIR / "PB-100-footprint-binding-progress.csv",
    PB100_DIR / "PB-100-footprint-binding-progress.md",
    PB100_DIR / "PB-100-mechanical-layout-input-closeout.md",
    PB100_DIR / "PB-100-board-release-local-evidence-closeout.csv",
    PB100_DIR / "PB-100-current-telemetry-closeout-precheck.csv",
    PB100_DIR / "PB-100-pcb-layout-start-checklist.csv",
    LB100_DIR / "LB-100-schematic-freeze-checklist.md",
    LB100_DIR / "LB-100-schematic-review-closeout.md",
    LB100_DIR / "LB-100-footprint-binding-progress.csv",
    LB100_DIR / "LB-100-footprint-binding-progress.md",
    LB100_DIR / "LB-100-mechanical-layout-input-closeout.md",
    LB100_DIR / "LB-100-pcb-layout-start-checklist.csv",
    *AGGREGATE_READINESS,
    FOOTPRINT_STATUS,
    FINAL_READINESS,
)

REQUIRED_FACTS = {
    PB100_DIR / "PB-100-schematic-freeze-checklist.md": (
        "ADR-0015 Accepted",
        "six official plated lands",
        "four GND MF circuits",
    ),
    PB100_DIR / "PB-100-schematic-readiness-dashboard.csv": (
        "ADR-0015 Accepted",
        "BUK7S1R2-80M 80 V LFPAK88",
        "six official plated lands",
        "four GND MF circuits",
    ),
    PB100_DIR / "PB-100-board-print-closure-matrix.csv": (
        "ADR-0015 Accepted",
        "six official plated lands",
        "four GND MF circuits",
    ),
    PB100_DIR / "PB-100-footprint-binding-progress.csv": (
        "BUK7S1R2-80M 80 V baseline",
        "six official plated lands",
        "four GND MF circuits",
        "zero Open rows",
    ),
    PB100_DIR / "PB-100-mechanical-layout-input-closeout.md": (
        "six official plated lands",
        "four GND MF circuits",
        "20 mm stack tolerance",
    ),
    PB100_DIR / "PB-100-pcb-layout-start-checklist.csv": (
        "zero Open rows",
        "six official plated lands",
        "four GND MF circuits",
    ),
    LB100_DIR / "LB-100-schematic-freeze-checklist.md": (
        "ADR-0015 Accepted",
        "six official plated",
        "four GND MF circuits",
        "`LBREL-003`",
        "`LBREL-007`",
    ),
    LB100_DIR / "LB-100-schematic-review-closeout.md": (
        "ADR-0015 Accepted",
        "six official plated lands",
        "four GND MF circuits",
    ),
    LB100_DIR / "LB-100-footprint-binding-progress.csv": (
        "ADR-0015 Accepted",
        "six official plated lands",
        "four GND MF circuits",
    ),
    LB100_DIR / "LB-100-mechanical-layout-input-closeout.md": (
        "six official plated lands",
        "four GND MF circuits",
        "20 mm stack tolerance",
    ),
    LB100_DIR / "LB-100-pcb-layout-start-checklist.csv": (
        "ADR-0015 Accepted",
        "six official plated lands",
        "four GND MF circuits",
    ),
}

STALE_CLAIMS = (
    "proposed adr-0015",
    "adr-0015 is proposed",
    "ownership is unapproved",
    "ownership unresolved",
    "board owner unresolved",
    "ownership remains open",
    "currently lb-owned transceiver",
    "omit six th",
    "missing mf contact",
    "lacks approved mf",
    "mf circuits and six th lands are unresolved",
    "mf/th footprint mechanics remain open",
    "60/80 v evidence",
    "60 v overshoot acceptance or 80 v",
    "60 v overshoot or 80 v migration",
    "final q1 voltage class remains open",
)


class ValidationError(RuntimeError):
    pass


def relative(path: Path) -> Path:
    return path.relative_to(REPO_ROOT)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"missing readiness artifact: {relative(path)}") from exc


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing readiness artifact: {relative(path)}") from exc
    if not rows:
        raise ValidationError(f"empty readiness artifact: {relative(path)}")
    return rows


def active_blockers() -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for board, path in BLOCKER_REGISTERS.items():
        rows = read_csv(path)
        active = tuple(
            row["Blocker ID"].strip()
            for row in rows
            if row["Status"].strip() in {"Open", "Conditional"}
        )
        result[board] = active
    return result


def validate_adr_0015() -> None:
    text = read_text(ADR_0015)
    if re.search(r"^## Status\s*\nAccepted\b", text, flags=re.MULTILINE) is None:
        raise ValidationError(f"{relative(ADR_0015)} must remain Accepted")
    for token in (
        "Candidate A is approved",
        "PB-100 owns the CAN1 transceiver",
        "LB-100 owns STM32 FDCAN",
        "CAN1_TXD_SAFE -> PB-100 CAN1 transceiver TXD",
    ):
        if token not in text:
            raise ValidationError(f"{relative(ADR_0015)} must include {token!r}")


def validate_aggregate_counts(expected: dict[str, tuple[str, ...]]) -> None:
    for path in AGGREGATE_READINESS:
        rows = read_csv(path)
        rows_by_board = {row["Board"].strip(): row for row in rows}
        if set(rows_by_board) != set(expected):
            raise ValidationError(f"{relative(path)} must contain exactly PB-100 LB-100 and FB-100")
        for board, blocker_ids in expected.items():
            row = rows_by_board[board]
            try:
                count = int(row["Active blocker count"].strip())
            except (KeyError, ValueError) as exc:
                raise ValidationError(
                    f"{relative(path)}:{board} needs an integer Active blocker count"
                ) from exc
            reported_ids = tuple(filter(None, row.get("Active blocker IDs", "").split(";")))
            if count != len(blocker_ids) or reported_ids != blocker_ids:
                raise ValidationError(
                    f"{relative(path)}:{board} reports {count} {reported_ids} but "
                    f"the blocker register reports {len(blocker_ids)} {blocker_ids}"
                )


def validate_final_readiness(expected: dict[str, tuple[str, ...]]) -> None:
    text = read_text(FINAL_READINESS)
    for board, blocker_ids in expected.items():
        noun = "blocker" if len(blocker_ids) == 1 else "blockers"
        marker = f"{len(blocker_ids)} active {noun}"
        if blocker_ids:
            marker += ": " + ", ".join(f"`{blocker_id}`" for blocker_id in blocker_ids)
        if marker not in text:
            raise ValidationError(
                f"{relative(FINAL_READINESS)}:{board} must include the current marker {marker!r}"
            )


def validate_footprint_gate_status() -> None:
    status_rows = {row["Board"].strip(): row for row in read_csv(FOOTPRINT_STATUS)}
    aggregate_rows = {
        row["Board"].strip(): row for row in read_csv(AGGREGATE_READINESS[1])
    }
    expected_boards = set(LAYOUT_CHECKLISTS)
    if set(status_rows) != expected_boards or set(aggregate_rows) != expected_boards:
        raise ValidationError("footprint status inputs must contain exactly PB-100 LB-100 and FB-100")
    for board, checklist_path in LAYOUT_CHECKLISTS.items():
        try:
            open_items = int(status_rows[board]["Open footprint items"].strip())
        except (KeyError, ValueError) as exc:
            raise ValidationError(
                f"{relative(FOOTPRINT_STATUS)}:{board} needs an integer Open footprint items"
            ) from exc
        expected = "Closed" if open_items == 0 else "Open"
        checklist_rows = {
            row["Gate"].strip(): row for row in read_csv(checklist_path)
        }
        actual = checklist_rows.get("Footprint binding", {}).get("Status", "").strip()
        if actual != expected:
            raise ValidationError(
                f"{relative(checklist_path)} footprint gate is {actual!r} but "
                f"{relative(FOOTPRINT_STATUS)} requires {expected!r}"
            )
        aggregate_state = aggregate_rows[board]["Footprint binding state"].strip()
        if not aggregate_state.startswith(expected.upper()):
            raise ValidationError(
                f"{relative(AGGREGATE_READINESS[1])}:{board} footprint state must start "
                f"with {expected.upper()}"
            )


def validate_required_facts() -> None:
    for path, tokens in REQUIRED_FACTS.items():
        text = read_text(path)
        for token in tokens:
            if token not in text:
                raise ValidationError(f"{relative(path)} must include current fact {token!r}")


def validate_no_stale_claims() -> None:
    for path in ACTIVE_DOCUMENTS:
        text = read_text(path).lower()
        for claim in STALE_CLAIMS:
            if claim in text:
                raise ValidationError(f"{relative(path)} contains stale claim {claim!r}")


def validate() -> None:
    expected = active_blockers()
    validate_adr_0015()
    validate_aggregate_counts(expected)
    validate_final_readiness(expected)
    validate_footprint_gate_status()
    validate_required_facts()
    validate_no_stale_claims()
