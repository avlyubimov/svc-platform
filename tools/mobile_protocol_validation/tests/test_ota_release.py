import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from mobile_protocol_validation import (
    OTAReleaseError,
    load_private_key_from_environment,
    public_key_fingerprint,
    sign_detached,
    validate_all_action_pins,
    validate_candidate_run_metadata,
    validate_release_inputs,
    validate_release_workflow,
    validate_tag_version_channel,
    verify_detached,
)
from sign_firmware_review import sign_and_package_review

ROOT = Path(__file__).resolve().parents[3]
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "firmware-release.yml"


class OTAReleaseTests(unittest.TestCase):
    def valid_run(self) -> dict:
        return {
            "id": 123456,
            "status": "completed",
            "conclusion": "success",
            "path": ".github/workflows/firmware-candidates.yml",
            "head_sha": "a" * 40,
            "repository": {
                "full_name": "avlyubimov/svc-platform",
            },
            "head_repository": {
                "full_name": "avlyubimov/svc-platform",
                "fork": False,
            },
        }

    def test_rejects_shell_injection_inputs(self) -> None:
        invalid = (
            ("0.1.0; touch /tmp/pwned", "123", "stable"),
            ("0.1.0", "123$(id)", "stable"),
            ("0.1.0\nmalicious=true", "123", "stable"),
            ("0.1.0", "123", "stable; echo"),
        )
        for release_version, run_id, channel in invalid:
            with self.subTest(
                release_version=release_version,
                run_id=run_id,
                channel=channel,
            ):
                with self.assertRaises(OTAReleaseError):
                    validate_release_inputs(release_version, run_id, channel)

    def test_accepts_canonical_channel_tags(self) -> None:
        cases = (
            ("0.1.0", "stable", "svc-v0.1.0"),
            ("0.1.0-beta.1", "beta", "svc-v0.1.0-beta.1"),
            ("0.1.0-test.1", "dev", "svc-v0.1.0-test.1"),
        )
        for version, channel, tag in cases:
            with self.subTest(version=version):
                self.assertEqual(
                    validate_release_inputs(version, "123", channel).release_tag,
                    tag,
                )

    def test_rejects_release_tag_version_channel_mismatch(self) -> None:
        mismatches = (
            ("svc-v0.1.0-beta.1", "0.1.0", "stable"),
            ("svc-v0.1.0", "0.1.0-beta.1", "beta"),
            ("svc-v0.1.0-test.1", "0.1.0-test.1", "stable"),
        )
        for tag, version, channel in mismatches:
            with self.subTest(tag=tag):
                with self.assertRaises(OTAReleaseError):
                    validate_tag_version_channel(tag, version, channel)

    def test_rejects_unsuitable_artifact_run(self) -> None:
        mutations = (
            ("conclusion", "failure"),
            ("path", ".github/workflows/firmware-e73.yml"),
        )
        for key, value in mutations:
            metadata = self.valid_run()
            metadata[key] = value
            with self.subTest(key=key):
                with self.assertRaises(OTAReleaseError):
                    validate_candidate_run_metadata(
                        metadata,
                        "123456",
                        "avlyubimov/svc-platform",
                    )

        fork = self.valid_run()
        fork["head_repository"] = {
            "full_name": "attacker/svc-platform",
            "fork": True,
        }
        with self.assertRaisesRegex(OTAReleaseError, "fork"):
            validate_candidate_run_metadata(
                fork,
                "123456",
                "avlyubimov/svc-platform",
            )

    def test_real_signature_verification_rejects_tampering(self) -> None:
        test_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        data = b"TEST firmware review payload"
        signature = sign_detached(data, test_key)
        self.assertTrue(verify_detached(data, signature, test_key.public_key()))
        self.assertFalse(
            verify_detached(data + b"tampered", signature, test_key.public_key())
        )

    def test_missing_production_key_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            OTAReleaseError,
            "OTA_PROD_SIGNING_KEY_B64",
        ):
            load_private_key_from_environment({})
        with self.assertRaisesRegex(
            OTAReleaseError,
            "OTA_PROD_SIGNING_KEY_PASSWORD",
        ):
            load_private_key_from_environment(
                {"OTA_PROD_SIGNING_KEY_B64": "dGVzdA=="}
            )

    def test_loads_encrypted_ephemeral_test_key(self) -> None:
        password = b"TEST-PASSWORD-NOT-FOR-PRODUCTION"
        test_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        pem = test_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(password),
        )
        loaded = load_private_key_from_environment(
            {
                "OTA_PROD_SIGNING_KEY_B64": base64.b64encode(pem).decode("ascii"),
                "OTA_PROD_SIGNING_KEY_PASSWORD": password.decode("ascii"),
            }
        )
        self.assertEqual(
            public_key_fingerprint(loaded.public_key()),
            public_key_fingerprint(test_key.public_key()),
        )

    def test_signing_pipeline_verifies_and_packages_detached_signatures(self) -> None:
        password = b"TEST-PASSWORD-NOT-FOR-PRODUCTION"
        test_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        encrypted_pem = test_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(password),
        )
        environment = {
            "OTA_PROD_SIGNING_KEY_B64": base64.b64encode(encrypted_pem).decode(
                "ascii"
            ),
            "OTA_PROD_SIGNING_KEY_PASSWORD": password.decode("ascii"),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stm32 = root / "stm32-main.bin"
            e73 = root / "e73-radio.bin"
            stm32.write_bytes(b"STM32 TEST REVIEW PAYLOAD")
            e73.write_bytes(b"E73 TEST REVIEW PAYLOAD")
            output = root / "dist"
            with patch.dict("os.environ", environment, clear=True):
                manifest_path = sign_and_package_review(
                    release_version="0.1.0-test.1",
                    channel="dev",
                    minimum_mobile_version="0.1.0",
                    stm32_artifact=stm32,
                    e73_artifact=e73,
                    output_directory=output,
                    expected_public_key_sha256=public_key_fingerprint(
                        test_key.public_key()
                    ),
                )

            manifest = json.loads(manifest_path.read_text())
            for component in manifest["components"]:
                image = (output / component["file"]).read_bytes()
                signature = (
                    output / component["releaseSignature"]["file"]
                ).read_bytes()
                self.assertTrue(
                    verify_detached(
                        image,
                        signature,
                        test_key.public_key(),
                    )
                )
                self.assertFalse(
                    verify_detached(
                        image + b"tampered",
                        signature,
                        test_key.public_key(),
                    )
                )

    def test_release_workflow_requires_environment_and_scoped_secrets(self) -> None:
        validate_release_workflow(RELEASE_WORKFLOW)
        validate_all_action_pins(ROOT / ".github" / "workflows")

        without_environment = RELEASE_WORKFLOW.read_text().replace(
            "    environment: firmware-production\n",
            "",
        )
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yml",
            delete=False,
        ) as temporary:
            temporary.write(without_environment)
            temporary_path = Path(temporary.name)
        self.addCleanup(temporary_path.unlink)
        with self.assertRaisesRegex(OTAReleaseError, "environment"):
            validate_release_workflow(temporary_path)

    def test_release_workflow_rejects_broad_permissions(self) -> None:
        broad_permissions = RELEASE_WORKFLOW.read_text().replace(
            "permissions: {}\n",
            "permissions:\n  contents: write\n",
            1,
        )
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yml",
            delete=False,
        ) as temporary:
            temporary.write(broad_permissions)
            temporary_path = Path(temporary.name)
        self.addCleanup(temporary_path.unlink)
        with self.assertRaisesRegex(OTAReleaseError, "top-level permissions"):
            validate_release_workflow(temporary_path)

    def test_release_workflow_requires_master_signing_guard(self) -> None:
        without_master_guard = RELEASE_WORKFLOW.read_text().replace(
            "    if: github.ref == 'refs/heads/master'\n",
            "",
        )
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yml",
            delete=False,
        ) as temporary:
            temporary.write(without_master_guard)
            temporary_path = Path(temporary.name)
        self.addCleanup(temporary_path.unlink)
        with self.assertRaisesRegex(OTAReleaseError, "restricted to master"):
            validate_release_workflow(temporary_path)

    def test_no_private_key_is_committed(self) -> None:
        private_key_marker = "BEGIN " + "PRIVATE KEY"
        for path in ROOT.rglob("*"):
            if (
                not path.is_file()
                or ".git" in path.parts
                or "__pycache__" in path.parts
                or path.suffix == ".pyc"
            ):
                continue
            if path.stat().st_size > 1_000_000:
                continue
            self.assertNotIn(
                private_key_marker,
                path.read_text(errors="ignore"),
                str(path),
            )
