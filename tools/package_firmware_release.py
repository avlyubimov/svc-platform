#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from mobile_protocol_validation.ota_release import (
    SIGNATURE_ALGORITHM,
    validate_release_inputs,
)


def package_release(
    release_version: str,
    channel: str,
    minimum_mobile_version: str,
    stm32_artifact: Path,
    e73_artifact: Path,
    output_directory: Path,
    signature_directory: Path,
    key_id: str,
) -> Path:
    inputs = validate_release_inputs(release_version, "1", channel)
    if not key_id or not key_id.replace("-", "").replace("_", "").isalnum():
        raise ValueError("key_id must contain letters, digits, hyphens, or underscores")

    output_directory.mkdir(parents=True, exist_ok=True)
    components = []
    checksum_entries: list[tuple[str, str]] = []
    artifacts = (
        ("stm32-main", stm32_artifact),
        ("e73-radio", e73_artifact),
    )
    for target, source in artifacts:
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.name.endswith(".signed.bin"):
            raise ValueError(
                f"{source}: review input must not claim a native firmware signature"
            )

        filename = f"svc-{target}-{release_version}.review.bin"
        destination = output_directory / filename
        shutil.copyfile(source, destination)
        data = destination.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        checksum_entries.append((digest, filename))

        source_signature = signature_directory / f"{target}.release.sig"
        if not source_signature.is_file():
            raise FileNotFoundError(source_signature)
        signature = source_signature.read_bytes()
        if not signature:
            raise ValueError(f"{source_signature}: detached signature is empty")
        signature_filename = f"{filename}.release.sig"
        signature_destination = output_directory / signature_filename
        signature_destination.write_bytes(signature)
        signature_digest = hashlib.sha256(signature).hexdigest()
        checksum_entries.append((signature_digest, signature_filename))

        components.append(
            {
                "target": target,
                "version": release_version,
                "hardware": ["LB-100-REV1"],
                "protocolVersion": 1,
                "file": filename,
                "size": len(data),
                "sha256": digest,
                "imageFormat": "review-raw",
                "installable": False,
                "releaseSignature": {
                    "algorithm": SIGNATURE_ALGORITHM,
                    "file": signature_filename,
                    "size": len(signature),
                    "sha256": signature_digest,
                    "keyId": key_id,
                },
                "minimumBootloader": "0.1.0",
            }
        )

    manifest_path = output_directory / "firmware-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "releaseVersion": release_version,
                "releaseTag": inputs.release_tag,
                "channel": channel,
                "minimumMobileVersion": minimum_mobile_version,
                "components": components,
            },
            indent=2,
        )
        + "\n"
    )
    checksum_entries.append(
        (
            hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            manifest_path.name,
        )
    )
    checksums = output_directory / "SHA256SUMS"
    checksums.write_text(
        "".join(f"{digest}  {filename}\n" for digest, filename in checksum_entries)
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-version", required=True)
    parser.add_argument("--channel", choices=("dev", "beta", "stable"), required=True)
    parser.add_argument("--minimum-mobile-version", default="0.1.0")
    parser.add_argument("--stm32", type=Path, required=True)
    parser.add_argument("--e73", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--signature-directory", type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    args = parser.parse_args()

    manifest = package_release(
        release_version=args.release_version,
        channel=args.channel,
        minimum_mobile_version=args.minimum_mobile_version,
        stm32_artifact=args.stm32,
        e73_artifact=args.e73,
        output_directory=args.output,
        signature_directory=args.signature_directory,
        key_id=args.key_id,
    )
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
