from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree

PRIMARY_SCREENS = {
    "dashboard",
    "channels",
    "canTelemetry",
    "navigation",
    "diagnostics",
}
REQUIRED_VEHICLE_BRAND_FILES = {
    "brand.json",
    "logo-source.svg",
    "logo-on-dark.svg",
    "logo-on-light.svg",
    "logo-accent.svg",
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
class VehicleBrand:
    identifier: str
    name: str
    accent_color: str
    source: str
    preferred_asset: str | None


@dataclass(frozen=True)
class VehicleBrandCatalog:
    simple_icons_version: str
    brands: dict[str, VehicleBrand]


@dataclass(frozen=True)
class BrandPack:
    identifier: str
    configuration: str
    brand_id: str
    model: str
    generation: str
    year: int
    logo: str | None
    wordmark: str | None


@dataclass(frozen=True)
class BrandCatalog:
    default_profile_id: str
    fallback_profile_id: str
    profiles: dict[str, BrandPack]
    vehicle_brands: VehicleBrandCatalog

    def logo_path(self, profile: BrandPack) -> str | None:
        if profile.brand_id == "svc":
            return profile.logo
        brand = self.vehicle_brands.brands[profile.brand_id]
        file_name = brand.preferred_asset or "logo-on-dark.svg"
        return f"vehicle-brands/brands/{brand.identifier}/{file_name}"

    def select(
        self,
        requested_profile: str,
        asset_exists: Callable[[str], bool],
    ) -> BrandPack:
        requested = self.profiles.get(requested_profile)
        fallback = self.profiles[self.fallback_profile_id]
        if requested is None:
            return fallback
        logo = self.logo_path(requested)
        if logo is None or not asset_exists(logo):
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


def load_vehicle_brand_catalog(directory: Path) -> VehicleBrandCatalog:
    root = directory / "vehicle-brands"
    catalog_path = root / "vehicle-brands-v1.json"
    value = json.loads(catalog_path.read_text())
    if value["schemaVersion"] != 1:
        raise ValueError("unsupported vehicle-brand catalog")

    required_notices = (
        root / "THIRD_PARTY_NOTICES.md",
        root / "third-party" / "simple-icons" / "LICENSE.md",
        root / "third-party" / "simple-icons" / "DISCLAIMER.md",
    )
    for notice in required_notices:
        if not notice.is_file():
            raise ValueError(f"{notice}: required notice is missing")

    brands: dict[str, VehicleBrand] = {}
    for entry in value["brands"]:
        identifier = entry["id"]
        if identifier in brands:
            raise ValueError(f"{catalog_path}: duplicate brand id {identifier}")
        brand_directory = root / "brands" / identifier
        available = {path.name for path in brand_directory.iterdir()}
        missing = REQUIRED_VEHICLE_BRAND_FILES - available
        if missing:
            raise ValueError(
                f"{brand_directory}: missing required files {sorted(missing)}"
            )
        brand_value = json.loads((brand_directory / "brand.json").read_text())
        if brand_value.get("id") != identifier:
            raise ValueError(f"{brand_directory}: brand id mismatch")
        source = brand_value.get("source")
        if not isinstance(source, str) or not source.startswith("https://"):
            raise ValueError(f"{brand_directory}: source URL is missing")
        for field in ("name", "accentColor", "source", "preferredAsset"):
            if brand_value.get(field) != entry.get(field):
                raise ValueError(f"{brand_directory}: catalog {field} mismatch")
        preferred_asset = entry.get("preferredAsset")
        if preferred_asset and not (brand_directory / preferred_asset).is_file():
            raise ValueError(f"{brand_directory}: preferred asset is missing")
        brands[identifier] = VehicleBrand(
            identifier=identifier,
            name=entry["name"],
            accent_color=entry["accentColor"],
            source=source,
            preferred_asset=preferred_asset,
        )

    directories = {
        path.name for path in (root / "brands").iterdir() if path.is_dir()
    }
    if directories != set(brands):
        raise ValueError("vehicle-brand catalog and directories differ")
    for svg_path in root.rglob("*.svg"):
        try:
            ElementTree.parse(svg_path)
        except ElementTree.ParseError as error:
            raise ValueError(f"{svg_path}: invalid SVG XML") from error
    return VehicleBrandCatalog(value["simpleIconsVersion"], brands)


def load_brand_catalog(directory: Path) -> BrandCatalog:
    index = json.loads((directory / "brand-pack-index-v1.json").read_text())
    if index["schemaVersion"] != 1:
        raise ValueError("unsupported BrandPack index")
    vehicle_brands = load_vehicle_brand_catalog(directory)

    profiles: dict[str, BrandPack] = {}
    for entry in index["profiles"]:
        configuration = directory / entry["configuration"]
        value = json.loads(configuration.read_text())
        if value["schemaVersion"] != 1 or value["id"] != entry["id"]:
            raise ValueError(f"{configuration}: BrandPack identity mismatch")
        identifier = value["id"]
        if identifier in profiles:
            raise ValueError(f"{configuration}: duplicate BrandPack id")
        brand_id = value["brandId"]
        if brand_id != "svc" and brand_id not in vehicle_brands.brands:
            raise ValueError(f"{configuration}: unknown brandId {brand_id}")
        assets = value.get("assets", {})
        profiles[identifier] = BrandPack(
            identifier=identifier,
            configuration=entry["configuration"],
            brand_id=brand_id,
            model=value["model"],
            generation=value["generation"],
            year=value["year"],
            logo=assets.get("logo"),
            wordmark=assets.get("wordmark"),
        )

    default_profile_id = index["defaultProfileId"]
    fallback_profile_id = index["fallbackProfileId"]
    if default_profile_id not in profiles:
        raise ValueError("default BrandPack is not listed")
    if fallback_profile_id not in profiles:
        raise ValueError("fallback BrandPack is not listed")
    fallback = profiles[fallback_profile_id]
    if fallback.brand_id != "svc" or not fallback.logo:
        raise ValueError("fallback BrandPack must use committed SVC artwork")
    if fallback.logo.startswith("local/"):
        raise ValueError("fallback BrandPack logo must be committed")
    return BrandCatalog(
        default_profile_id,
        fallback_profile_id,
        profiles,
        vehicle_brands,
    )


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
