#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
from pathlib import Path


def package_release(
    release_version: str,
    channel: str,
    minimum_mobile_version: str,
    stm32_artifact: Path,
    e73_artifact: Path,
    output_directory: Path,
    signature_directory: Path | None = None,
) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    components = []
    inputs = (
        ("stm32-main", stm32_artifact),
        ("e73-radio", e73_artifact),
    )
    for target, source in inputs:
        if not source.is_file():
            raise FileNotFoundError(source)
        filename = f"svc-{target}-{release_version}.signed.bin"
        destination = output_directory / filename
        shutil.copyfile(source, destination)
        data = destination.read_bytes()
        signature = "SIGNATURE-DISABLED-NO-PRODUCTION-SECRET"
        if signature_directory is not None:
            signature_path = signature_directory / f"{target}.sig"
            if not signature_path.is_file():
                raise FileNotFoundError(signature_path)
            signature = "openssl-sha256:" + base64.b64encode(
                signature_path.read_bytes()
            ).decode("ascii")
        components.append(
            {
                "target": target,
                "version": release_version,
                "hardware": ["LB-100-REV1"],
                "protocolVersion": 1,
                "file": filename,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "signature": signature,
                "minimumBootloader": "0.1.0",
            }
        )

    manifest_path = output_directory / "firmware-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "releaseVersion": release_version,
                "channel": channel,
                "minimumMobileVersion": minimum_mobile_version,
                "components": components,
            },
            indent=2,
        )
        + "\n"
    )
    checksums = output_directory / "SHA256SUMS"
    checksum_lines = [
        f"{component['sha256']}  {component['file']}" for component in components
    ]
    checksum_lines.append(
        f"{hashlib.sha256(manifest_path.read_bytes()).hexdigest()}  {manifest_path.name}"
    )
    checksums.write_text("\n".join(checksum_lines) + "\n")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-version", required=True)
    parser.add_argument("--channel", choices=("dev", "beta", "stable"), required=True)
    parser.add_argument("--minimum-mobile-version", default="0.1.0")
    parser.add_argument("--stm32", type=Path, required=True)
    parser.add_argument("--e73", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--signature-directory", type=Path)
    args = parser.parse_args()

    manifest = package_release(
        release_version=args.release_version,
        channel=args.channel,
        minimum_mobile_version=args.minimum_mobile_version,
        stm32_artifact=args.stm32,
        e73_artifact=args.e73,
        output_directory=args.output,
        signature_directory=args.signature_directory,
    )
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
