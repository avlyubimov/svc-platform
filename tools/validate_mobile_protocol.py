#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from mobile_protocol_validation import load_firmware_manifest, load_telemetry

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "software" / "mobile" / "protocol"


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

    print("mobile protocol validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
