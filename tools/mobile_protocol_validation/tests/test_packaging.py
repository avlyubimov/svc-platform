import json
import tempfile
import unittest
from pathlib import Path

from package_firmware_release import package_release
from mobile_protocol_validation import ManifestError, load_firmware_manifest


class PackagingTests(unittest.TestCase):
    def test_packages_hashes_and_rejects_unsigned_release_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            stm32 = temporary / "stm32.bin"
            e73 = temporary / "e73.bin"
            stm32.write_bytes(b"stm32")
            e73.write_bytes(b"e73")
            output = temporary / "out"
            manifest_path = package_release(
                release_version="0.1.0",
                channel="dev",
                minimum_mobile_version="0.1.0",
                stm32_artifact=stm32,
                e73_artifact=e73,
                output_directory=output,
            )

            manifest = load_firmware_manifest(manifest_path)
            self.assertEqual(len(manifest.components), 2)
            self.assertTrue((output / "SHA256SUMS").is_file())
            self.assertNotEqual(
                json.loads(manifest_path.read_text())["components"][0]["sha256"],
                "placeholder",
            )
            with self.assertRaisesRegex(ManifestError, "test placeholder"):
                load_firmware_manifest(manifest_path, release_mode=True)
