import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from mobile_protocol_validation import (
    ArtifactValidationError,
    CompatibilityError,
    ManifestError,
    load_firmware_manifest,
    load_telemetry,
    validate_artifact,
)

ROOT = Path(__file__).resolve().parents[3]
MOCK = ROOT / "software" / "mobile" / "mock-data" / "device-v1.json"
MANIFEST = (
    ROOT
    / "software"
    / "mobile"
    / "protocol"
    / "examples"
    / "firmware-manifest.dev.json"
)


class ValidationTests(unittest.TestCase):
    def write_json(self, value: dict) -> Path:
        temporary = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(value, temporary)
        temporary.close()
        self.addCleanup(Path(temporary.name).unlink)
        return Path(temporary.name)

    def test_parses_complete_mock_telemetry(self) -> None:
        telemetry = load_telemetry(MOCK)
        self.assertEqual(telemetry["schemaVersion"], 1)
        self.assertEqual(len(telemetry["channels"]), 10)

    def test_undecoded_can_is_unavailable_not_fabricated(self) -> None:
        telemetry = load_telemetry(MOCK)
        engine_temperature = telemetry["vehicle"]["engineTemperature"]
        self.assertIsNone(engine_temperature["value"])
        self.assertFalse(engine_temperature["valid"])
        self.assertEqual(engine_temperature["quality"], "unavailable")

    def test_stale_can_value_remains_explicit(self) -> None:
        raw = json.loads(MOCK.read_text())
        raw["vehicle"]["speed"]["stale"] = True
        parsed = load_telemetry(self.write_json(raw))
        self.assertTrue(parsed["vehicle"]["speed"]["stale"])

    def test_missing_sd_card_is_a_capability_state(self) -> None:
        telemetry = load_telemetry(MOCK)
        self.assertEqual(telemetry["storage"]["sdCardState"]["value"], "missing")
        self.assertEqual(
            telemetry["storage"]["canLoggerState"]["value"], "unavailable"
        )

    def test_rejects_unavailable_value_with_fabricated_number(self) -> None:
        raw = json.loads(MOCK.read_text())
        raw["vehicle"]["fuelLevel"]["value"] = 50
        with self.assertRaisesRegex(ValueError, "unavailable"):
            load_telemetry(self.write_json(raw))

    def test_rejects_incompatible_protocol(self) -> None:
        manifest = load_firmware_manifest(MANIFEST)
        with self.assertRaisesRegex(CompatibilityError, "protocol mismatch"):
            manifest.component_for("stm32-main", "LB-100-REV1", 2, "0.1.0")

    def test_rejects_wrong_hardware_revision(self) -> None:
        manifest = load_firmware_manifest(MANIFEST)
        with self.assertRaisesRegex(CompatibilityError, "hardware mismatch"):
            manifest.component_for("stm32-main", "LB-100-REV2", 1, "0.1.0")

    def test_rejects_non_installable_review_component(self) -> None:
        manifest = load_firmware_manifest(MANIFEST)
        with self.assertRaisesRegex(CompatibilityError, "not installable"):
            manifest.component_for("stm32-main", "LB-100-REV1", 1, "0.1.0")

    def test_rejects_duplicate_component_target(self) -> None:
        raw = json.loads(MANIFEST.read_text())
        raw["components"][1]["target"] = "stm32-main"
        with self.assertRaisesRegex(ManifestError, "duplicate target"):
            load_firmware_manifest(self.write_json(raw))

    def test_release_mode_rejects_test_key_fixture(self) -> None:
        with self.assertRaisesRegex(ManifestError, "test placeholder"):
            load_firmware_manifest(MANIFEST, release_mode=True)

    def test_rejects_wrong_sha256(self) -> None:
        raw = json.loads(MANIFEST.read_text())
        data = b"signed candidate"
        raw["components"][0]["size"] = len(data)
        raw["components"][0]["sha256"] = "0" * 64
        signature = b"test signature"
        raw["components"][0]["releaseSignature"]["size"] = len(signature)
        raw["components"][0]["releaseSignature"]["sha256"] = hashlib.sha256(
            signature
        ).hexdigest()
        manifest = load_firmware_manifest(self.write_json(raw))
        component = manifest.components[0]
        with self.assertRaisesRegex(ArtifactValidationError, "SHA-256 mismatch"):
            validate_artifact(
                component,
                data,
                signature,
                lambda _component, _data, _signature: True,
            )

    def test_rejects_invalid_signature(self) -> None:
        raw = json.loads(MANIFEST.read_text())
        data = b"signed candidate"
        raw["components"][0]["size"] = len(data)
        raw["components"][0]["sha256"] = hashlib.sha256(data).hexdigest()
        signature = b"test signature"
        raw["components"][0]["releaseSignature"]["size"] = len(signature)
        raw["components"][0]["releaseSignature"]["sha256"] = hashlib.sha256(
            signature
        ).hexdigest()
        manifest = load_firmware_manifest(self.write_json(raw))
        component = manifest.components[0]
        with self.assertRaisesRegex(ArtifactValidationError, "signature invalid"):
            validate_artifact(
                component,
                data,
                signature,
                lambda _component, _data, _signature: False,
            )

    def test_accepts_valid_artifact_with_injected_verifier(self) -> None:
        raw = copy.deepcopy(json.loads(MANIFEST.read_text()))
        data = b"signed candidate"
        raw["components"][0]["size"] = len(data)
        raw["components"][0]["sha256"] = hashlib.sha256(data).hexdigest()
        signature = b"test signature"
        raw["components"][0]["releaseSignature"]["size"] = len(signature)
        raw["components"][0]["releaseSignature"]["sha256"] = hashlib.sha256(
            signature
        ).hexdigest()
        manifest = load_firmware_manifest(self.write_json(raw))
        validate_artifact(
            manifest.components[0],
            data,
            signature,
            lambda component, candidate, detached_signature: (
                component.release_signature.key_id == "TEST_KEY_NOT_FOR_PRODUCTION"
                and candidate == data
                and detached_signature == signature
            ),
        )


if __name__ == "__main__":
    unittest.main()
