#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from mobile_protocol_validation import (
    load_brand_catalog,
    load_firmware_manifest,
    load_telemetry,
    load_vehicle_brand_catalog,
    load_vehicle_performance_catalog,
    validate_all_action_pins,
    validate_release_workflow,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "software" / "mobile" / "protocol"
BRANDING = ROOT / "software" / "mobile" / "branding"
VEHICLE_PROFILES = ROOT / "software" / "mobile" / "vehicle-profiles"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--release",
        action="store_true",
        help="reject fixture placeholders in firmware manifests",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROTOCOL / "examples" / "firmware-manifest.dev.json",
    )
    args = parser.parse_args()

    schemas = {}
    for schema_path in sorted(PROTOCOL.glob("*.schema.json")):
        schema = json.loads(schema_path.read_text())
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise SystemExit(f"{schema_path}: expected JSON Schema draft 2020-12")
        if not schema.get("$id"):
            raise SystemExit(f"{schema_path}: missing $id")
        schemas[schema_path.name] = schema

    telemetry_path = ROOT / "software" / "mobile" / "mock-data" / "device-v1.json"
    command_path = PROTOCOL / "examples" / "command-install-denied.json"
    load_telemetry(telemetry_path)
    load_firmware_manifest(args.manifest, release_mode=args.release)
    validate_release_workflow(
        ROOT / ".github" / "workflows" / "firmware-release.yml"
    )
    validate_all_action_pins(ROOT / ".github" / "workflows")

    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        Draft202012Validator = None

    if Draft202012Validator is not None:
        fixtures = (
            ("telemetry-v1.schema.json", telemetry_path),
            ("command-v1.schema.json", command_path),
            ("firmware-manifest-v1.schema.json", args.manifest),
        )
        for schema_name, fixture_path in fixtures:
            schema = schemas[schema_name]
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(
                schema,
                format_checker=FormatChecker(),
            )
            errors = sorted(
                validator.iter_errors(json.loads(fixture_path.read_text())),
                key=lambda error: list(error.absolute_path),
            )
            if errors:
                first = errors[0]
                path = ".".join(str(part) for part in first.absolute_path)
                raise SystemExit(f"{fixture_path}:{path}: {first.message}")

        brand_schema = json.loads(
            (BRANDING / "brand-pack-v1.schema.json").read_text()
        )
        brand_index_schema = json.loads(
            (BRANDING / "brand-pack-index-v1.schema.json").read_text()
        )
        Draft202012Validator.check_schema(brand_schema)
        Draft202012Validator.check_schema(brand_index_schema)
        brand_validator = Draft202012Validator(brand_schema)
        for brand_path in (
            BRANDING / "bmw-r1200gs-k25-personal.json",
            BRANDING / "generic-automotive.json",
        ):
            errors = list(brand_validator.iter_errors(json.loads(brand_path.read_text())))
            if errors:
                raise SystemExit(f"{brand_path}: {errors[0].message}")
        index_path = BRANDING / "brand-pack-index-v1.json"
        index_errors = list(
            Draft202012Validator(brand_index_schema).iter_errors(
                json.loads(index_path.read_text())
            )
        )
        if index_errors:
            raise SystemExit(f"{index_path}: {index_errors[0].message}")

        vehicle_profile_schema = json.loads(
            (VEHICLE_PROFILES / "vehicle-profile-v1.schema.json").read_text()
        )
        vehicle_profile_index_schema = json.loads(
            (
                VEHICLE_PROFILES / "vehicle-profile-index-v1.schema.json"
            ).read_text()
        )
        Draft202012Validator.check_schema(vehicle_profile_schema)
        Draft202012Validator.check_schema(vehicle_profile_index_schema)
        vehicle_profile_validator = Draft202012Validator(vehicle_profile_schema)
        for profile_path in (
            VEHICLE_PROFILES / "bmw-r1200gs-k25-2007.json",
            VEHICLE_PROFILES / "generic-motorcycle.json",
        ):
            errors = list(
                vehicle_profile_validator.iter_errors(
                    json.loads(profile_path.read_text())
                )
            )
            if errors:
                raise SystemExit(f"{profile_path}: {errors[0].message}")
        profile_index_path = (
            VEHICLE_PROFILES / "vehicle-profile-index-v1.json"
        )
        profile_index_errors = list(
            Draft202012Validator(vehicle_profile_index_schema).iter_errors(
                json.loads(profile_index_path.read_text())
            )
        )
        if profile_index_errors:
            raise SystemExit(
                f"{profile_index_path}: {profile_index_errors[0].message}"
            )

    from mobile_protocol_validation import load_startup_timeline

    load_vehicle_brand_catalog(BRANDING)
    load_brand_catalog(BRANDING)
    load_startup_timeline(BRANDING / "startup-animation-v1.json")
    load_vehicle_performance_catalog(VEHICLE_PROFILES, repo_root=ROOT)

    print("mobile protocol validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
