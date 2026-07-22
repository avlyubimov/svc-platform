from __future__ import annotations

from collections.abc import Iterable, Mapping


LEGACY_RELEASE_STATES = (
    "BLOCKED",
    "LAYOUT-ONLY",
    "PROTO-ONLY",
    "PRODUCTION-READY",
)
PB_RELEASE_STATES = (
    "BLOCKED",
    "EVT-LAYOUT-AUTHORIZED",
    "EVT-FAB-AUTHORIZED",
    "BENCH-VALIDATION",
    "MOTORCYCLE-VALIDATION",
    "PRODUCTION-RELEASE",
)
RELEASE_STATES = tuple(dict.fromkeys((*LEGACY_RELEASE_STATES, *PB_RELEASE_STATES)))
STAGES = (
    "EVT layout authorization",
    "EVT pre-fabrication review",
    "EVT build and inspection",
    "Bench validation",
    "Motorcycle validation",
)
AUTHORIZATION_AFTER_CLOSE = dict(zip(STAGES, PB_RELEASE_STATES[1:], strict=True))
STATE_RANK = {
    "BLOCKED": 0,
    "LAYOUT-ONLY": 1,
    "EVT-LAYOUT-AUTHORIZED": 1,
    "PROTO-ONLY": 2,
    "EVT-FAB-AUTHORIZED": 2,
    "BENCH-VALIDATION": 3,
    "MOTORCYCLE-VALIDATION": 4,
    "PRODUCTION-READY": 5,
    "PRODUCTION-RELEASE": 5,
}


def allowed_release_states(board: str) -> tuple[str, ...]:
    return PB_RELEASE_STATES if board == "PB-100" else LEGACY_RELEASE_STATES


def is_layout_authorized(state: str) -> bool:
    return state in STATE_RANK and STATE_RANK[state] >= 1


def is_fabrication_authorized(state: str) -> bool:
    return state in STATE_RANK and STATE_RANK[state] >= 2


def is_production_authorized(state: str) -> bool:
    return state in {"PRODUCTION-READY", "PRODUCTION-RELEASE"}


def derive_blocker_authorization(rows: Iterable[Mapping[str, str]]) -> str:
    rows_by_stage = {row["Stage"].strip(): row for row in rows}
    if set(rows_by_stage) != set(STAGES):
        raise ValueError("staged blocker must contain each release stage exactly once")

    closed_count = 0
    found_open = False
    for stage in STAGES:
        status = rows_by_stage[stage]["Stage status"].strip()
        if status not in {"Closed", "Conditional", "Blocked"}:
            raise ValueError(f"invalid stage status {status!r}")
        if status == "Closed":
            if found_open:
                raise ValueError("release stages must close in order")
            closed_count += 1
        else:
            found_open = True
    return PB_RELEASE_STATES[closed_count]


def least_authorized(states: Iterable[str]) -> str:
    states = tuple(states)
    if not states:
        raise ValueError("at least one release state is required")
    unknown = set(states) - set(PB_RELEASE_STATES)
    if unknown:
        raise ValueError(f"unknown release state(s): {', '.join(sorted(unknown))}")
    return min(states, key=STATE_RANK.__getitem__)


def derive_pb_release_state(
    stage_rows: Iterable[Mapping[str, str]],
    post_prototype_rows: Iterable[Mapping[str, str]],
) -> str:
    rows_by_blocker: dict[str, list[Mapping[str, str]]] = {}
    for row in stage_rows:
        rows_by_blocker.setdefault(row["Blocker ID"].strip(), []).append(row)
    state = least_authorized(
        derive_blocker_authorization(rows) for rows in rows_by_blocker.values()
    )
    if state == "PRODUCTION-RELEASE" and any(
        row.get("Status", "").strip() != "Closed" for row in post_prototype_rows
    ):
        return "BENCH-VALIDATION"
    return state
