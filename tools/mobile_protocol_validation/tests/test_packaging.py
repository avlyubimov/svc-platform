import json
import tempfile
import unittest
from pathlib import Path

from mobile_protocol_validation import load_firmware_manifest
from package_firmware_release import package_release


class PackagingTests(unittest.TestCase):
    def test_packages_non_installable_review_images_and_detached_signatures(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            stm32 = temporary / "stm32-main.bin"
            e73 = temporary / "e73-radio.bin"
            stm32.write_bytes(b"stm32 review payload")
            e73.write_bytes(b"e73 review payload")
            signatures = temporary / "signatures"
            signatures.mkdir()
            (signatures / "stm32-main.release.sig").write_bytes(b"stm32 signature")
            (signatures / "e73-radio.release.sig").write_bytes(b"e73 signature")
            output = temporary / "out"
            manifest_path = package_release(
                release_version="0.1.0-test.1",
                channel="dev",
                minimum_mobile_version="0.1.0",
                stm32_artifact=stm32,
                e73_artifact=e73,
                output_directory=output,
                signature_directory=signatures,
                key_id="TEST_KEY_NOT_FOR_PRODUCTION",
            )

            manifest = load_firmware_manifest(manifest_path, release_mode=True)
            self.assertEqual(manifest.release_tag, "svc-v0.1.0-test.1")
            self.assertEqual(len(manifest.components), 2)
            self.assertTrue((output / "SHA256SUMS").is_file())
            raw = json.loads(manifest_path.read_text())
            for component in raw["components"]:
                self.assertFalse(component["installable"])
                self.assertEqual(component["imageFormat"], "review-raw")
                self.assertTrue(component["file"].endswith(".review.bin"))
                self.assertFalse(component["file"].endswith(".signed.bin"))
                self.assertTrue(
                    component["releaseSignature"]["file"].endswith(".release.sig")
                )

    def test_rejects_input_that_claims_native_signature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            stm32 = temporary / "stm32-main.signed.bin"
            e73 = temporary / "e73-radio.bin"
            stm32.write_bytes(b"not OEMiRoT")
            e73.write_bytes(b"not MCUboot")
            signatures = temporary / "signatures"
            signatures.mkdir()
            (signatures / "stm32-main.release.sig").write_bytes(b"signature")
            (signatures / "e73-radio.release.sig").write_bytes(b"signature")
            with self.assertRaisesRegex(ValueError, "must not claim"):
                package_release(
                    release_version="0.1.0-test.1",
                    channel="dev",
                    minimum_mobile_version="0.1.0",
                    stm32_artifact=stm32,
                    e73_artifact=e73,
                    output_directory=temporary / "out",
                    signature_directory=signatures,
                    key_id="TEST_KEY_NOT_FOR_PRODUCTION",
                )
