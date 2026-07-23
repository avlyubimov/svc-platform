#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from mobile_protocol_validation import (
    load_firmware_manifest,
    load_private_key_from_environment,
    public_key_fingerprint,
    require_expected_public_key_fingerprint,
    sign_detached,
    verify_detached,
)
from package_firmware_release import package_release


def sign_and_package_review(
    release_version: str,
    channel: str,
    minimum_mobile_version: str,
    stm32_artifact: Path,
    e73_artifact: Path,
    output_directory: Path,
    expected_public_key_sha256: str,
) -> Path:
    private_key = load_private_key_from_environment()
    public_key = private_key.public_key()
    require_expected_public_key_fingerprint(
        public_key,
        expected_public_key_sha256,
    )
    key_id = f"ota-prod-{public_key_fingerprint(public_key)[:16]}"

    artifacts = {
        "stm32-main": stm32_artifact,
        "e73-radio": e73_artifact,
    }
    with tempfile.TemporaryDirectory(prefix="svc-release-signatures-") as temporary:
        signature_directory = Path(temporary)
        for target, artifact in artifacts.items():
            data = artifact.read_bytes()
            signature = sign_detached(data, private_key)
            if not verify_detached(data, signature, public_key):
                raise RuntimeError(f"{target}: post-signature verification failed")
            (signature_directory / f"{target}.release.sig").write_bytes(signature)

        manifest_path = package_release(
            release_version=release_version,
            channel=channel,
            minimum_mobile_version=minimum_mobile_version,
            stm32_artifact=stm32_artifact,
            e73_artifact=e73_artifact,
            output_directory=output_directory,
            signature_directory=signature_directory,
            key_id=key_id,
        )

    manifest = load_firmware_manifest(manifest_path, release_mode=True)
    raw_manifest = json.loads(manifest_path.read_text())
    for component in raw_manifest["components"]:
        image = (output_directory / component["file"]).read_bytes()
        signature = (
            output_directory / component["releaseSignature"]["file"]
        ).read_bytes()
        if not verify_detached(image, signature, public_key):
            raise RuntimeError(
                f"{component['target']}: packaged detached signature is invalid"
            )
    if manifest.release_tag != f"svc-v{release_version}":
        raise RuntimeError("packaged release tag is inconsistent")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-version", required=True)
    parser.add_argument("--channel", choices=("dev", "beta", "stable"), required=True)
    parser.add_argument("--minimum-mobile-version", default="0.1.0")
    parser.add_argument("--stm32", type=Path, required=True)
    parser.add_argument("--e73", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-public-key-sha256", required=True)
    args = parser.parse_args()
    manifest = sign_and_package_review(
        release_version=args.release_version,
        channel=args.channel,
        minimum_mobile_version=args.minimum_mobile_version,
        stm32_artifact=args.stm32,
        e73_artifact=args.e73,
        output_directory=args.output,
        expected_public_key_sha256=args.expected_public_key_sha256,
    )
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
