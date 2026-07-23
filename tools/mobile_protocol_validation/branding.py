from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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

    def duration_for(
        self,
        *,
        animation_enabled: bool,
        reduce_motion: bool,
        critical: bool,
    ) -> int:
        if not animation_enabled:
            return 0
        if reduce_motion or critical:
            return self.critical_duration_ms
        return self.duration_ms


@dataclass(frozen=True)
class BrandPack:
    identifier: str
    configuration: str
    logo: str
    wordmark: str | None


@dataclass(frozen=True)
class BrandCatalog:
    default_profile_id: str
    fallback_profile_id: str
    profiles: dict[str, BrandPack]

    def select(
        self,
        requested_profile: str,
        asset_exists: Callable[[str], bool],
    ) -> BrandPack:
        requested = self.profiles.get(requested_profile)
        fallback = self.profiles[self.fallback_profile_id]
        if requested is None or not asset_exists(requested.logo):
            return fallback
        return requested


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


def load_brand_catalog(directory: Path) -> BrandCatalog:
    index = json.loads((directory / "brand-pack-index-v1.json").read_text())
    if index["schemaVersion"] != 1:
        raise ValueError("unsupported BrandPack index")

    profiles: dict[str, BrandPack] = {}
    for entry in index["profiles"]:
        configuration = directory / entry["configuration"]
        value = json.loads(configuration.read_text())
        if value["schemaVersion"] != 1 or value["id"] != entry["id"]:
            raise ValueError(f"{configuration}: BrandPack identity mismatch")
        assets = value["assets"]
        identifier = value["id"]
        if identifier in profiles:
            raise ValueError(f"{configuration}: duplicate BrandPack id")
        profiles[identifier] = BrandPack(
            identifier=identifier,
            configuration=entry["configuration"],
            logo=assets["logo"],
            wordmark=assets.get("wordmark"),
        )

    default_profile_id = index["defaultProfileId"]
    fallback_profile_id = index["fallbackProfileId"]
    if default_profile_id not in profiles:
        raise ValueError("default BrandPack is not listed")
    if fallback_profile_id not in profiles:
        raise ValueError("fallback BrandPack is not listed")
    fallback = profiles[fallback_profile_id]
    if fallback.logo.startswith("local/"):
        raise ValueError("fallback BrandPack logo must be committed")
    return BrandCatalog(default_profile_id, fallback_profile_id, profiles)


def restore_primary_screen(stored: str | None) -> str:
    return stored if stored in PRIMARY_SCREENS else "dashboard"


def startup_duration_ms(
    *,
    animation_enabled: bool,
    reduce_motion: bool,
    critical: bool,
    timeline: StartupTimeline,
) -> int:
    return timeline.duration_for(
        animation_enabled=animation_enabled,
        reduce_motion=reduce_motion,
        critical=critical,
    )
