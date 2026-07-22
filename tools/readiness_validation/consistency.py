from __future__ import annotations

import csv
import re
from pathlib import Path

from .stages import (
    AUTHORIZATION_AFTER_CLOSE,
    STAGES,
    allowed_release_states,
    derive_blocker_authorization,
    derive_pb_release_state,
)


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
ADR_0017 = REPO_ROOT / "docs" / "adr" / "ADR-0017-pb-100-staged-release-authorization.md"
ADR_0019 = REPO_ROOT / "docs" / "adr" / "ADR-0019-pb-100-evt-development-release.md"
ADR_0020 = REPO_ROOT / "docs" / "adr" / "ADR-0020-platform-evt-development-and-reference-loads.md"
PB_STAGED_READINESS = PB100_DIR / "PB-100-staged-release-readiness.csv"
PB_POST_PROTOTYPE = PB100_DIR / "PB-100-post-prototype-validation-gate.csv"
EVT_FAB_READINESS = REPO_ROOT / "production" / "board-order" / "three_board_evt_fab_readiness.csv"
PRODUCTION_BLOCKERS = REPO_ROOT / "production" / "board-order" / "three_board_production_blockers.csv"
EVT_FAB_CHECKLISTS = {
    "PB-100": PB100_DIR / "PB-100-evt-fab-review-checklist.csv",
    "LB-100": LB100_DIR / "LB-100-evt-fab-review-checklist.csv",
    "FB-100": FB100_DIR / "FB-100-evt-fab-review-checklist.csv",
}
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
    PB_STAGED_READINESS,
    ADR_0020,
    EVT_FAB_READINESS,
    PRODUCTION_BLOCKERS,
    *EVT_FAB_CHECKLISTS.values(),
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
        "IAUT300N08S5N012ATMA2 80 V TOLL",
        "six official plated lands",
        "four GND MF circuits",
    ),
    PB100_DIR / "PB-100-board-print-closure-matrix.csv": (
        "ADR-0015 Accepted",
        "six official plated lands",
        "four GND MF circuits",
    ),
    PB100_DIR / "PB-100-footprint-binding-progress.csv": (
        "IAUT300N08S5N012ATMA2 80 V baseline",
        "six official plated lands",
        "four GND MF circuits",
        "zero Open rows",
    ),
    PB100_DIR / "PB-100-mechanical-layout-input-closeout.md": (
        "six official plated lands",
        "four GND MF circuits",
        "20 mm stack",
        "20.3 +/-0.127 mm",
    ),
    PB100_DIR / "PB-100-pcb-layout-start-checklist.csv": (
        "zero Open rows",
        "six official plated lands",
        "four GND MF circuits",
    ),
    PB_STAGED_READINESS: (
        "PBREL-006",
        "PBREL-007",
        "EVT-LAYOUT-AUTHORIZED",
        "EVT-FAB-REVIEW",
        "EVT-FAB-AUTHORIZED",
        "BENCH-VALIDATION",
        "MOTORCYCLE-VALIDATION",
        "PRODUCTION-BLOCKED",
        "PRODUCTION-RELEASE",
        "PB-BENCH-004",
        "PB-BENCH-010",
    ),
    LB100_DIR / "LB-100-schematic-freeze-checklist.md": (
        "ADR-0015 Accepted",
        "six official plated",
        "four GND MF circuits",
        "zero active LBREL blockers",
        "83 components",
        "191 electrical nets",
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
        "20 mm stack",
        "20.3 +/-0.127 mm",
    ),
    LB100_DIR / "LB-100-pcb-layout-start-checklist.csv": (
        "ADR-0015 Accepted",
        "six official plated lands",
        "four GND MF circuits",
        "20.3 +/-0.127 mm",
    ),
    FB100_DIR / "FB-100-schematic-freeze-checklist.md": (
        "zero active FBREL blockers",
        "44 components",
        "46 nets",
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
            if row["Status"].strip() in {"Open", "Conditional", "Blocked"}
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


def validate_adr_0017() -> None:
    text = read_text(ADR_0017)
    if "superseded by ADR-0019 and ADR-0020" not in text:
        raise ValidationError(f"{relative(ADR_0017)} must record ADR-0019/ADR-0020 supersession")
    for token in (
        "BLOCKED",
        "LAYOUT-ONLY",
        "PROTO-ONLY",
        "PRODUCTION-READY",
        "PB-BENCH-004",
        "PB-BENCH-010",
        "No second-developer review is required",
    ):
        if token not in text:
            raise ValidationError(f"{relative(ADR_0017)} must include {token!r}")


def validate_adr_0019() -> None:
    text = read_text(ADR_0019)
    for token in (
        "release-state model superseded by ADR-0020",
        "EVT-LAYOUT-AUTHORIZED",
        "EVT-FAB-AUTHORIZED",
        "BENCH-VALIDATION",
        "MOTORCYCLE-VALIDATION",
        "PRODUCTION-RELEASE",
        "PB-100 REV.1 EVT — NOT FOR PRODUCTION",
        "exactly five",
        "Q2-C100",
        "paused",
        "Rev.2",
        "CAN1 TX",
    ):
        if token not in text:
            raise ValidationError(f"{relative(ADR_0019)} must include {token!r}")


def validate_adr_0020() -> None:
    text = read_text(ADR_0020)
    for token in (
        "Accepted — final Product Owner direction on 2026-07-22",
        "EVT-LAYOUT-AUTHORIZED",
        "EVT-FAB-REVIEW",
        "EVT-FAB-AUTHORIZED",
        "BENCH-VALIDATION",
        "MOTORCYCLE-VALIDATION",
        "PRODUCTION-BLOCKED",
        "PRODUCTION-RELEASE",
        "PBREL-007 is a production-release blocker only",
        "Q2-C100 remains a paused diagnostic coupon",
        "FOG_SW_IN",
        "C36_BIDIRECTIONAL",
        "A second human developer is not required",
    ):
        if token not in text:
            raise ValidationError(f"{relative(ADR_0020)} must include {token!r}")


def validate_staged_release_readiness() -> None:
    rows = read_csv(PB_STAGED_READINESS)
    required_columns = {
        "Blocker ID",
        "Stage",
        "Stage status",
        "Required evidence",
        "Current evidence",
        "Authorization after close",
        "Current blocker authorization",
        "Blocked scope",
    }
    missing_columns = required_columns - set(rows[0])
    if missing_columns:
        raise ValidationError(
            f"{relative(PB_STAGED_READINESS)} is missing columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    rows_by_blocker: dict[str, list[dict[str, str]]] = {}
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        blocker_id = row["Blocker ID"].strip()
        stage = row["Stage"].strip()
        key = blocker_id, stage
        if key in seen_keys:
            raise ValidationError(f"{relative(PB_STAGED_READINESS)} has duplicate {key}")
        seen_keys.add(key)
        rows_by_blocker.setdefault(blocker_id, []).append(row)
        if stage not in STAGES:
            raise ValidationError(f"{relative(PB_STAGED_READINESS)} has unknown stage {stage!r}")
        expected_after_close = AUTHORIZATION_AFTER_CLOSE[stage]
        if row["Authorization after close"].strip() != expected_after_close:
            raise ValidationError(
                f"{relative(PB_STAGED_READINESS)}:{blocker_id}/{stage} must advance to "
                f"{expected_after_close}"
            )
        if "production" not in row["Blocked scope"].lower() or "field" not in row["Blocked scope"].lower():
            raise ValidationError(
                f"{relative(PB_STAGED_READINESS)}:{blocker_id}/{stage} must preserve production/field restrictions"
            )

    if set(rows_by_blocker) != {"PBREL-006", "PBREL-007"}:
        raise ValidationError(f"{relative(PB_STAGED_READINESS)} must stage PBREL-006 and PBREL-007 exactly")
    for blocker_id, blocker_rows in rows_by_blocker.items():
        try:
            authorization = derive_blocker_authorization(blocker_rows)
        except ValueError as exc:
            raise ValidationError(
                f"{relative(PB_STAGED_READINESS)}:{blocker_id}: {exc}"
            ) from exc
        reported = {row["Current blocker authorization"].strip() for row in blocker_rows}
        if reported != {authorization}:
            raise ValidationError(
                f"{relative(PB_STAGED_READINESS)}:{blocker_id} must report current authorization {authorization}"
            )

    required_tokens = {
        "PBREL-006": (
            "IAUT300N08S5N012ATMA2",
            "4.032 W",
            "150 C",
            "6.20 K/W",
            "PB-BENCH-010",
        ),
        "PBREL-007": (
            "LM74930QRGERQ1",
            "IAUTN15S6N025ATMA1",
            "79-101 V",
            "0.5-4 ohm",
            "40-400 ms",
            "48.99-54.89 V",
            "25/125/150 C",
            "5-10 ms",
            "0.72 us",
            "59.52 V",
            "2.08x",
            "7.200 W",
            "PB-BENCH-004",
        ),
    }
    for blocker_id, tokens in required_tokens.items():
        text = " ".join(" ".join(row.values()) for row in rows_by_blocker[blocker_id])
        for token in tokens:
            if token not in text:
                raise ValidationError(
                    f"{relative(PB_STAGED_READINESS)}:{blocker_id} must include {token!r}"
                )

    try:
        pb_release_state = derive_pb_release_state(rows, read_csv(PB_POST_PROTOTYPE))
    except ValueError as exc:
        raise ValidationError(f"{relative(PB_STAGED_READINESS)}: {exc}") from exc

    readiness_states: dict[Path, dict[str, str]] = {}
    for path in AGGREGATE_READINESS:
        board_states = {
            row["Board"].strip(): row.get("Release state", "").strip()
            for row in read_csv(path)
        }
        for board, state in board_states.items():
            if state not in allowed_release_states(board):
                raise ValidationError(
                    f"{relative(path)}:{board} has invalid Release state {state!r}"
                )
        if board_states.get("PB-100") != pb_release_state:
            raise ValidationError(
                f"{relative(path)}:PB-100 must report derived release state {pb_release_state}"
            )
        readiness_states[path] = board_states
    if len({tuple(states.items()) for states in readiness_states.values()}) != 1:
        raise ValidationError("aggregate readiness CSV files must report identical release states")

    final_text = read_text(FINAL_READINESS)
    if f"aggregate authorization remains `{pb_release_state}`" not in final_text:
        raise ValidationError(
            f"{relative(FINAL_READINESS)} must report aggregate PB-100 authorization {pb_release_state}"
        )


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


def validate_evt_fab_and_production_boundaries() -> None:
    aggregate_states = {
        row["Board"].strip(): row["Release state"].strip()
        for row in read_csv(AGGREGATE_READINESS[1])
    }
    fab_rows = {row["Board"].strip(): row for row in read_csv(EVT_FAB_READINESS)}
    if set(fab_rows) != set(aggregate_states):
        raise ValidationError(f"{relative(EVT_FAB_READINESS)} must contain all three boards exactly")
    for board, state in aggregate_states.items():
        row = fab_rows[board]
        if row["Current state"].strip() != state:
            raise ValidationError(f"{relative(EVT_FAB_READINESS)}:{board} must report {state}")
        if row["EVT batch size"].strip() != "5":
            raise ValidationError(f"{relative(EVT_FAB_READINESS)}:{board} EVT batch must be five")
        marking = row["EVT marking"].strip()
        if board not in marking or "NOT FOR PRODUCTION" not in marking:
            raise ValidationError(f"{relative(EVT_FAB_READINESS)}:{board} needs EVT marking")
    if "PBREL-007" in fab_rows["PB-100"]["EVT-FAB blockers"]:
        raise ValidationError("PBREL-007 must not appear as a PB-100 EVT-FAB blocker")

    for board, path in EVT_FAB_CHECKLISTS.items():
        rows = read_csv(path)
        if any(row.get("Status", "").strip() != "Open" for row in rows):
            raise ValidationError(f"{relative(path)} must remain open before routed fab review")
        text = " ".join(" ".join(row.values()) for row in rows)
        for token in ("DRC", "EVT-FAB-AUTHORIZED", "Product Owner", "no second developer required"):
            if token not in text:
                raise ValidationError(f"{relative(path)} must include {token!r}")
        if board == "PB-100" and "PBREL-007" in text:
            raise ValidationError(f"{relative(path)} must not make PBREL-007 an EVT-FAB gate")

    production_rows = read_csv(PRODUCTION_BLOCKERS)
    if any(row.get("Status", "").strip() != "Blocked" for row in production_rows):
        raise ValidationError(f"{relative(PRODUCTION_BLOCKERS)} must keep production blockers Blocked")
    production_text = " ".join(" ".join(row.values()) for row in production_rows)
    for token in ("PBREL-007", "Rev.2", "Product Owner", "PB-100", "LB-100", "FB-100"):
        if token not in production_text:
            raise ValidationError(f"{relative(PRODUCTION_BLOCKERS)} must include {token!r}")


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


def validate_pb100_local_closeout() -> None:
    register_rows = {
        row["Blocker ID"].strip(): row
        for row in read_csv(BLOCKER_REGISTERS["PB-100"])
    }
    closeout_path = PB100_DIR / "PB-100-board-release-local-evidence-closeout.csv"
    closeout_rows = {
        row["Blocker ID"].strip(): row
        for row in read_csv(closeout_path)
    }
    if set(closeout_rows) != set(register_rows):
        raise ValidationError(
            f"{relative(closeout_path)} blocker IDs must match the PB-100 blocker register"
        )

    for blocker_id, register_row in register_rows.items():
        register_status = register_row["Status"].strip()
        impact = closeout_rows[blocker_id]["Status impact"].strip()
        if register_status == "Closed" and not impact.startswith("Closed for pre-layout"):
            raise ValidationError(
                f"{relative(closeout_path)}:{blocker_id} contradicts Closed register status"
            )
        if register_status in {"Open", "Conditional"} and register_status.lower() not in impact.lower():
            raise ValidationError(
                f"{relative(closeout_path)}:{blocker_id} must report {register_status} impact"
            )

    manifest_path = PB100_DIR / "PB-100-review-release-manifest.csv"
    manifest_rows = {
        row["Artifact"].strip(): row
        for row in read_csv(manifest_path)
    }
    artifact = "hardware/power-board/PB-100/PB-100-board-release-local-evidence-closeout.csv"
    expected_manifest_status = (
        "Closed"
        if all(row["Status"].strip() == "Closed" for row in register_rows.values())
        else "Conditional"
    )
    actual_manifest_status = manifest_rows.get(artifact, {}).get("Status", "").strip()
    if actual_manifest_status != expected_manifest_status:
        raise ValidationError(
            f"{relative(manifest_path)} local closeout row must be "
            f"{expected_manifest_status}, got {actual_manifest_status or 'missing'}"
        )


def validate_no_stale_claims() -> None:
    for path in ACTIVE_DOCUMENTS:
        text = read_text(path).lower()
        for claim in STALE_CLAIMS:
            if claim in text:
                raise ValidationError(f"{relative(path)} contains stale claim {claim!r}")


def validate() -> None:
    expected = active_blockers()
    validate_adr_0015()
    validate_adr_0017()
    validate_adr_0019()
    validate_adr_0020()
    validate_staged_release_readiness()
    validate_aggregate_counts(expected)
    validate_evt_fab_and_production_boundaries()
    validate_final_readiness(expected)
    validate_footprint_gate_status()
    validate_required_facts()
    validate_pb100_local_closeout()
    validate_no_stale_claims()
