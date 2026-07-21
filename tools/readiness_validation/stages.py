from __future__ import annotations

from collections.abc import Iterable, Mapping


RELEASE_STATES = (
    "BLOCKED",
    "LAYOUT-ONLY",
    "PROTO-ONLY",
    "PRODUCTION-READY",
)
STAGES = (
    "Pre-layout design",
    "Post-layout verification",
    "Prototype qualification",
)
AUTHORIZATION_AFTER_CLOSE = dict(zip(STAGES, RELEASE_STATES[1:], strict=True))
STATE_RANK = {state: rank for rank, state in enumerate(RELEASE_STATES)}


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
    return RELEASE_STATES[closed_count]


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
    if state == "PRODUCTION-READY" and any(
        row.get("Status", "").strip() != "Closed" for row in post_prototype_rows
    ):
        return "PROTO-ONLY"
    return state
