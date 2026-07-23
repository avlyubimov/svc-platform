from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PRIMARY_SCREENS = {
    "dashboard",
    "channels",
    "canTelemetry",
    "navigation",
    "diagnostics",
}


@dataclass(frozen=True)
class StartupTimeline:
    duration_ms: int
    critical_duration_ms: int
    phase_ends_ms: tuple[int, ...]

    @property
    def frames_at_60_fps(self) -> int:
        return round(self.duration_ms / 1000 * 60)


def load_startup_timeline(path: Path) -> StartupTimeline:
    value = json.loads(path.read_text())
    phases = value["phases"]
    ends = (
        phases["screenOnEndMs"],
        phases["logoEndMs"],
        phases["identityEndMs"],
        phases["taglineEndMs"],
        phases["dashboardEndMs"],
    )
    if value["schemaVersion"] != 1:
        raise ValueError("unsupported startup timeline")
    if value["durationMs"] != 2100 or value["criticalDurationMs"] != 500:
        raise ValueError("startup timing differs from the mobile contract")
    if ends != tuple(sorted(ends)) or ends[-1] != value["durationMs"]:
        raise ValueError("startup phases are not monotonic")
    return StartupTimeline(value["durationMs"], value["criticalDurationMs"], ends)


def selected_brand_pack(
    requested_profile: str,
    local_assets: set[str],
) -> str:
    required = {"bmw-roundel.svg", "bmw-motorrad-wordmark.svg"}
    if requested_profile == "bmw-r1200gs-k25-personal" and required <= local_assets:
        return requested_profile
    return "generic-automotive"


def restore_primary_screen(stored: str | None) -> str:
    return stored if stored in PRIMARY_SCREENS else "dashboard"


def startup_duration_ms(
    *,
    animation_enabled: bool,
    reduce_motion: bool,
    critical: bool,
) -> int:
    if not animation_enabled:
        return 0
    if reduce_motion or critical:
        return 500
    return 2100
