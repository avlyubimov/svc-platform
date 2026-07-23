from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
HARDWARE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,31}$")
FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CHANNEL_IDS = tuple(f"OUT{index}" for index in range(1, 11))
TARGETS = {"stm32-main", "e73-radio"}
SOURCES = {
    "adc",
    "can1",
    "imu",
    "sensor",
    "output-manager",
    "storage",
    "firmware",
    "derived",
}
QUALITIES = {"good", "degraded", "invalid", "unavailable"}


class ManifestError(ValueError):
    pass


class TelemetryError(ValueError):
    pass


class CompatibilityError(ValueError):
    pass


class ArtifactValidationError(ValueError):
    pass


@dataclass(frozen=True)
class FirmwareComponent:
    target: str
    version: str
    hardware: tuple[str, ...]
    protocol_version: int
    file: str
    size: int
    sha256: str
    signature: str
    minimum_bootloader: str


@dataclass(frozen=True)
class FirmwareManifest:
    schema_version: int
    release_version: str
    channel: str
    minimum_mobile_version: str
    components: tuple[FirmwareComponent, ...]

    def component_for(
        self,
        target: str,
        hardware_revision: str,
        protocol_version: int,
        bootloader_version: str,
    ) -> FirmwareComponent:
        component = next(
            (candidate for candidate in self.components if candidate.target == target),
            None,
        )
        if component is None:
            raise CompatibilityError(f"target unavailable: {target}")
        if hardware_revision not in component.hardware:
            raise CompatibilityError(
                f"hardware mismatch: {hardware_revision} is not supported by {target}"
            )
        if component.protocol_version != protocol_version:
            raise CompatibilityError(
                f"protocol mismatch: device={protocol_version}, manifest={component.protocol_version}"
            )
        if _version_tuple(bootloader_version) < _version_tuple(
            component.minimum_bootloader
        ):
            raise CompatibilityError(
                f"bootloader too old: {bootloader_version} < {component.minimum_bootloader}"
            )
        return component


def _version_tuple(version: str) -> tuple[int, int, int]:
    if not SEMVER_PATTERN.fullmatch(version):
        raise CompatibilityError(f"invalid semantic version: {version}")
    core = version.split("-", maxsplit=1)[0]
    return tuple(int(part) for part in core.split("."))  # type: ignore[return-value]


def _require_object(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object")
    return value


def _require_keys(value: dict, keys: set[str], context: str) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise ValueError(f"{context} missing keys: {', '.join(missing)}")


def _validate_timestamp(value: object, context: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{context} must be a timestamp string")
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"{context} is not an ISO-8601 timestamp") from error


def _validate_measurement(
    value: object,
    context: str,
    expected_type: type | tuple[type, ...],
) -> None:
    measurement = _require_object(value, context)
    _require_keys(
        measurement,
        {"value", "unit", "timestamp", "valid", "stale", "source", "quality"},
        context,
    )
    if measurement["value"] is not None and not isinstance(
        measurement["value"], expected_type
    ):
        raise ValueError(f"{context}.value has the wrong type")
    if not isinstance(measurement["unit"], str) or not measurement["unit"]:
        raise ValueError(f"{context}.unit must be non-empty")
    _validate_timestamp(measurement["timestamp"], f"{context}.timestamp")
    if not isinstance(measurement["valid"], bool):
        raise ValueError(f"{context}.valid must be boolean")
    if not isinstance(measurement["stale"], bool):
        raise ValueError(f"{context}.stale must be boolean")
    if measurement["source"] not in SOURCES:
        raise ValueError(f"{context}.source is unsupported")
    if measurement["quality"] not in QUALITIES:
        raise ValueError(f"{context}.quality is unsupported")
    if measurement["quality"] == "unavailable":
        if measurement["value"] is not None or measurement["valid"]:
            raise ValueError(
                f"{context} unavailable values must use null and valid=false"
            )
    if measurement["value"] is None and measurement["valid"]:
        raise ValueError(f"{context} null values cannot be valid")


def load_telemetry(path: Path) -> dict:
    try:
        telemetry = _require_object(json.loads(path.read_text()), "telemetry")
        required = {
            "schemaVersion",
            "protocolVersion",
            "deviceId",
            "sequence",
            "timestamp",
            "batteryVoltage",
            "totalCurrent",
            "channels",
            "powerZoneTemperatures",
            "ambientLight",
            "accelerometer",
            "gyroscope",
            "leanAngle",
            "vehicle",
            "can1",
            "storage",
            "versions",
            "warnings",
        }
        _require_keys(telemetry, required, "telemetry")
        if telemetry["schemaVersion"] != 1:
            raise ValueError("unsupported telemetry schema version")
        if not isinstance(telemetry["protocolVersion"], int):
            raise ValueError("protocolVersion must be an integer")
        _validate_timestamp(telemetry["timestamp"], "telemetry.timestamp")
        _validate_measurement(
            telemetry["batteryVoltage"], "batteryVoltage", (int, float)
        )
        _validate_measurement(
            telemetry["totalCurrent"], "totalCurrent", (int, float)
        )
        channels = telemetry["channels"]
        if not isinstance(channels, list) or len(channels) != len(CHANNEL_IDS):
            raise ValueError("telemetry must contain exactly ten channels")
        channel_ids = tuple(channel.get("id") for channel in channels)
        if set(channel_ids) != set(CHANNEL_IDS) or len(set(channel_ids)) != 10:
            raise ValueError("channel IDs must contain OUT1 through OUT10 exactly once")
        for channel in channels:
            channel_id = channel["id"]
            _validate_measurement(
                channel.get("current"), f"{channel_id}.current", (int, float)
            )
            _validate_measurement(
                channel.get("state"), f"{channel_id}.state", str
            )
            _validate_measurement(
                channel.get("fault"), f"{channel_id}.fault", str
            )
        temperatures = telemetry["powerZoneTemperatures"]
        if not isinstance(temperatures, list) or not temperatures:
            raise ValueError("at least one power-zone temperature is required")
        for index, temperature in enumerate(temperatures):
            _validate_measurement(
                temperature, f"powerZoneTemperatures[{index}]", (int, float)
            )
            if not isinstance(temperature.get("id"), str):
                raise ValueError("power-zone temperature requires an id")
        _validate_measurement(
            telemetry["ambientLight"], "ambientLight", (int, float)
        )
        _validate_measurement(telemetry["leanAngle"], "leanAngle", (int, float))
        for vector_name in ("accelerometer", "gyroscope"):
            vector = _require_object(telemetry[vector_name], vector_name)
            _require_keys(vector, {"x", "y", "z"}, vector_name)
            for axis in ("x", "y", "z"):
                _validate_measurement(
                    vector[axis], f"{vector_name}.{axis}", (int, float)
                )
        vehicle = _require_object(telemetry["vehicle"], "vehicle")
        for field in (
            "speed",
            "engineRpm",
            "engineTemperature",
            "instantFuelConsumption",
            "averageFuelConsumption",
            "fuelLevel",
            "ambientTemperature",
        ):
            _validate_measurement(vehicle.get(field), f"vehicle.{field}", (int, float))
        can1 = _require_object(telemetry["can1"], "can1")
        _validate_measurement(can1.get("state"), "can1.state", str)
        _validate_measurement(can1.get("rxFrames"), "can1.rxFrames", (int, float))
        _validate_measurement(
            can1.get("droppedFrames"), "can1.droppedFrames", (int, float)
        )
        _validate_measurement(
            can1.get("lastFrameTimestamp"), "can1.lastFrameTimestamp", str
        )
        storage = _require_object(telemetry["storage"], "storage")
        _validate_measurement(storage.get("sdCardState"), "storage.sdCardState", str)
        _validate_measurement(
            storage.get("canLoggerState"), "storage.canLoggerState", str
        )
        _validate_measurement(
            storage.get("freeBytes"), "storage.freeBytes", (int, float)
        )
        versions = _require_object(telemetry["versions"], "versions")
        for field in ("stm32", "e73", "protocol"):
            _validate_measurement(versions.get(field), f"versions.{field}", str)
        return telemetry
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise TelemetryError(f"{path}: {error}") from error


def load_firmware_manifest(path: Path, release_mode: bool = False) -> FirmwareManifest:
    try:
        raw = _require_object(json.loads(path.read_text()), "manifest")
        _require_keys(
            raw,
            {
                "schemaVersion",
                "releaseVersion",
                "channel",
                "minimumMobileVersion",
                "components",
            },
            "manifest",
        )
        if raw["schemaVersion"] != 1:
            raise ValueError("unsupported manifest schema version")
        if not SEMVER_PATTERN.fullmatch(raw["releaseVersion"]):
            raise ValueError("releaseVersion is not semantic version")
        if raw["channel"] not in {"dev", "beta", "stable"}:
            raise ValueError("unsupported release channel")
        if not SEMVER_PATTERN.fullmatch(raw["minimumMobileVersion"]):
            raise ValueError("minimumMobileVersion is not semantic version")
        if not isinstance(raw["components"], list) or not raw["components"]:
            raise ValueError("components must be a non-empty array")

        targets: set[str] = set()
        components: list[FirmwareComponent] = []
        for index, item in enumerate(raw["components"]):
            component = _require_object(item, f"components[{index}]")
            _require_keys(
                component,
                {
                    "target",
                    "version",
                    "hardware",
                    "protocolVersion",
                    "file",
                    "size",
                    "sha256",
                    "signature",
                    "minimumBootloader",
                },
                f"components[{index}]",
            )
            target = component["target"]
            if target not in TARGETS:
                raise ValueError(f"unsupported target: {target}")
            if target in targets:
                raise ValueError(f"duplicate target: {target}")
            targets.add(target)
            if not SEMVER_PATTERN.fullmatch(component["version"]):
                raise ValueError(f"{target} version is invalid")
            hardware = component["hardware"]
            if (
                not isinstance(hardware, list)
                or not hardware
                or len(hardware) != len(set(hardware))
                or not all(
                    isinstance(revision, str)
                    and HARDWARE_PATTERN.fullmatch(revision)
                    for revision in hardware
                )
            ):
                raise ValueError(f"{target} hardware allowlist is invalid")
            protocol_version = component["protocolVersion"]
            if not isinstance(protocol_version, int) or protocol_version < 1:
                raise ValueError(f"{target} protocolVersion is invalid")
            filename = component["file"]
            if not isinstance(filename, str) or not FILENAME_PATTERN.fullmatch(
                filename
            ):
                raise ValueError(f"{target} file must be a basename")
            size = component["size"]
            if not isinstance(size, int) or size < 0:
                raise ValueError(f"{target} size is invalid")
            digest = component["sha256"]
            if digest != "placeholder" and not SHA256_PATTERN.fullmatch(digest):
                raise ValueError(f"{target} sha256 is invalid")
            signature = component["signature"]
            if not isinstance(signature, str) or not signature:
                raise ValueError(f"{target} signature is missing")
            if release_mode and (
                digest == "placeholder"
                or "NOT-FOR-PRODUCTION" in signature
                or "SIGNATURE-DISABLED" in signature
                or "placeholder" in signature.lower()
            ):
                raise ValueError(f"{target} contains a test placeholder")
            if not SEMVER_PATTERN.fullmatch(component["minimumBootloader"]):
                raise ValueError(f"{target} minimumBootloader is invalid")
            components.append(
                FirmwareComponent(
                    target=target,
                    version=component["version"],
                    hardware=tuple(hardware),
                    protocol_version=protocol_version,
                    file=filename,
                    size=size,
                    sha256=digest,
                    signature=signature,
                    minimum_bootloader=component["minimumBootloader"],
                )
            )
        return FirmwareManifest(
            schema_version=raw["schemaVersion"],
            release_version=raw["releaseVersion"],
            channel=raw["channel"],
            minimum_mobile_version=raw["minimumMobileVersion"],
            components=tuple(components),
        )
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as error:
        raise ManifestError(f"{path}: {error}") from error


def validate_artifact(
    component: FirmwareComponent,
    data: bytes,
    verify_signature: Callable[[FirmwareComponent, bytes], bool],
) -> None:
    if component.size != len(data):
        raise ArtifactValidationError(
            f"size mismatch: manifest={component.size}, actual={len(data)}"
        )
    digest = hashlib.sha256(data).hexdigest()
    if component.sha256 != digest:
        raise ArtifactValidationError(
            f"SHA-256 mismatch: manifest={component.sha256}, actual={digest}"
        )
    if not verify_signature(component, data):
        raise ArtifactValidationError("signature invalid")
