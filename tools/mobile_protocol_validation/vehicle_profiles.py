from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VehiclePerformanceProfile:
    identifier: str
    manufacturer: str
    model: str
    generation: str | None
    year_from: int | None
    year_to: int | None
    engine_name: str | None
    engine_displacement_cc: float | None
    maximum_torque_nm: float | None
    nominal_power_kw: float | None
    gearbox_gears: int | None
    fuel_capacity_liters: float | None
    fuel_reserve_liters: float | None
    ice_warning_temperature_celsius: float | None
    idle_rpm: int | None
    idle_tolerance_rpm: int | None
    torque_peak_rpm: int | None
    power_peak_rpm: int | None
    tachometer_scale_min_rpm: int
    tachometer_scale_max_rpm: int | None
    warning_start_rpm: int | None
    red_zone_start_rpm: int | None
    rev_limiter_rpm: int | None
    source: str
    reference: str
    confidence: str

    def tachometer_zone(self, rpm: int) -> str:
        if self.tachometer_scale_max_rpm is None:
            return "unavailable"
        clamped = max(self.tachometer_scale_min_rpm, rpm)
        if self.red_zone_start_rpm is not None and clamped >= self.red_zone_start_rpm:
            return "red"
        if self.warning_start_rpm is not None and clamped >= self.warning_start_rpm:
            return "warning"
        return "normal"


@dataclass(frozen=True)
class VehiclePerformanceCatalog:
    default_profile_id: str
    fallback_profile_id: str
    profiles: dict[str, VehiclePerformanceProfile]


def _optional_number(value: object) -> float | None:
    return None if value is None else float(value)


def _profile_from_json(value: dict[str, object]) -> VehiclePerformanceProfile:
    return VehiclePerformanceProfile(
        identifier=str(value["id"]),
        manufacturer=str(value["manufacturer"]),
        model=str(value["model"]),
        generation=None if value["generation"] is None else str(value["generation"]),
        year_from=None if value["yearFrom"] is None else int(value["yearFrom"]),
        year_to=None if value["yearTo"] is None else int(value["yearTo"]),
        engine_name=(
            None if value["engineName"] is None else str(value["engineName"])
        ),
        engine_displacement_cc=_optional_number(value["engineDisplacementCc"]),
        maximum_torque_nm=_optional_number(value["maximumTorqueNm"]),
        nominal_power_kw=_optional_number(value["nominalPowerKw"]),
        gearbox_gears=(
            None if value["gearboxGears"] is None else int(value["gearboxGears"])
        ),
        fuel_capacity_liters=_optional_number(value["fuelCapacityLiters"]),
        fuel_reserve_liters=_optional_number(value["fuelReserveLiters"]),
        ice_warning_temperature_celsius=_optional_number(
            value["iceWarningTemperatureCelsius"]
        ),
        idle_rpm=None if value["idleRpm"] is None else int(value["idleRpm"]),
        idle_tolerance_rpm=(
            None
            if value["idleToleranceRpm"] is None
            else int(value["idleToleranceRpm"])
        ),
        torque_peak_rpm=(
            None if value["torquePeakRpm"] is None else int(value["torquePeakRpm"])
        ),
        power_peak_rpm=(
            None if value["powerPeakRpm"] is None else int(value["powerPeakRpm"])
        ),
        tachometer_scale_min_rpm=int(value["tachometerScaleMinRpm"]),
        tachometer_scale_max_rpm=(
            None
            if value["tachometerScaleMaxRpm"] is None
            else int(value["tachometerScaleMaxRpm"])
        ),
        warning_start_rpm=(
            None if value["warningStartRpm"] is None else int(value["warningStartRpm"])
        ),
        red_zone_start_rpm=(
            None if value["redZoneStartRpm"] is None else int(value["redZoneStartRpm"])
        ),
        rev_limiter_rpm=(
            None if value["revLimiterRpm"] is None else int(value["revLimiterRpm"])
        ),
        source=str(value["source"]),
        reference=str(value["reference"]),
        confidence=str(value["confidence"]),
    )


def _validate_profile(profile: VehiclePerformanceProfile, repo_root: Path) -> None:
    if profile.year_from is not None and profile.year_to is not None:
        if profile.year_from > profile.year_to:
            raise ValueError(f"{profile.identifier}: year range is reversed")
    if (
        profile.fuel_capacity_liters is not None
        and profile.fuel_reserve_liters is not None
        and profile.fuel_reserve_liters > profile.fuel_capacity_liters
    ):
        raise ValueError(f"{profile.identifier}: reserve exceeds fuel capacity")

    scale_max = profile.tachometer_scale_max_rpm
    rpm_values = (
        profile.idle_rpm,
        profile.torque_peak_rpm,
        profile.power_peak_rpm,
        profile.warning_start_rpm,
        profile.red_zone_start_rpm,
        profile.rev_limiter_rpm,
    )
    if scale_max is None:
        if any(value is not None for value in rpm_values):
            raise ValueError(
                f"{profile.identifier}: RPM values require a tachometer scale"
            )
    else:
        if profile.tachometer_scale_min_rpm >= scale_max:
            raise ValueError(f"{profile.identifier}: invalid tachometer scale")
        if any(value is not None and value > scale_max for value in rpm_values):
            raise ValueError(
                f"{profile.identifier}: RPM value exceeds tachometer scale"
            )
        if (
            profile.warning_start_rpm is not None
            and profile.red_zone_start_rpm is not None
            and profile.warning_start_rpm >= profile.red_zone_start_rpm
        ):
            raise ValueError(
                f"{profile.identifier}: warning zone must start before red zone"
            )

    if not (repo_root / profile.reference).is_file():
        raise ValueError(f"{profile.identifier}: reference document is missing")


def load_vehicle_performance_catalog(
    directory: Path,
    *,
    repo_root: Path,
) -> VehiclePerformanceCatalog:
    index_path = directory / "vehicle-profile-index-v1.json"
    index = json.loads(index_path.read_text())
    if index["schemaVersion"] != 1:
        raise ValueError("unsupported vehicle performance profile index")

    profiles: dict[str, VehiclePerformanceProfile] = {}
    for entry in index["profiles"]:
        configuration = directory / entry["configuration"]
        value = json.loads(configuration.read_text())
        if value["schemaVersion"] != 1 or value["id"] != entry["id"]:
            raise ValueError(f"{configuration}: vehicle profile identity mismatch")
        profile = _profile_from_json(value)
        if profile.identifier in profiles:
            raise ValueError(f"{configuration}: duplicate vehicle profile id")
        _validate_profile(profile, repo_root)
        profiles[profile.identifier] = profile

    default_profile_id = index["defaultProfileId"]
    fallback_profile_id = index["fallbackProfileId"]
    if default_profile_id not in profiles:
        raise ValueError("default vehicle profile is not listed")
    if fallback_profile_id not in profiles:
        raise ValueError("fallback vehicle profile is not listed")

    fallback = profiles[fallback_profile_id]
    if (
        fallback.warning_start_rpm is not None
        or fallback.red_zone_start_rpm is not None
        or fallback.rev_limiter_rpm is not None
    ):
        raise ValueError("fallback vehicle profile must not assume RPM limits")

    return VehiclePerformanceCatalog(
        default_profile_id=default_profile_id,
        fallback_profile_id=fallback_profile_id,
        profiles=profiles,
    )
