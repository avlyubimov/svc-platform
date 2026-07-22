from __future__ import annotations

from collections.abc import Iterable, Mapping


RELEASE_STATES = (
    "EVT-LAYOUT-AUTHORIZED",
    "EVT-FAB-REVIEW",
    "EVT-FAB-AUTHORIZED",
    "BENCH-VALIDATION",
    "MOTORCYCLE-VALIDATION",
    "PRODUCTION-BLOCKED",
    "PRODUCTION-RELEASE",
)
STAGES = (
    "EVT layout authorization",
    "EVT layout complete",
    "EVT pre-fabrication review",
    "EVT build and inspection",
    "Bench validation",
    "Motorcycle validation",
    "Production qualification",
)
AUTHORIZATION_AFTER_CLOSE = dict(zip(STAGES, RELEASE_STATES, strict=True))
STATE_RANK = {state: rank for rank, state in enumerate(RELEASE_STATES)}


def allowed_release_states(board: str) -> tuple[str, ...]:
    del board
    return RELEASE_STATES


def is_layout_authorized(state: str) -> bool:
    return state in STATE_RANK


def is_fabrication_review(state: str) -> bool:
    return state in STATE_RANK and STATE_RANK[state] >= STATE_RANK["EVT-FAB-REVIEW"]


def is_fabrication_authorized(state: str) -> bool:
    return state in STATE_RANK and STATE_RANK[state] >= STATE_RANK["EVT-FAB-AUTHORIZED"]


def is_production_authorized(state: str) -> bool:
    return state == "PRODUCTION-RELEASE"


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
    if closed_count == 0:
        raise ValueError("EVT layout authorization must close before a release state can be derived")
    return RELEASE_STATES[closed_count - 1]


def least_authorized(states: Iterable[str]) -> str:
    states = tuple(states)
    if not states:
        raise ValueError("at least one release state is required")
    unknown = set(states) - set(RELEASE_STATES)
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
        return "PRODUCTION-BLOCKED"
    return state
