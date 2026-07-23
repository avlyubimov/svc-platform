import json
import tempfile
import unittest
from pathlib import Path

from mobile_protocol_validation.vehicle_profiles import (
    load_vehicle_performance_catalog,
)

ROOT = Path(__file__).resolve().parents[3]
PROFILES = ROOT / "software" / "mobile" / "vehicle-profiles"


class VehiclePerformanceProfileTests(unittest.TestCase):
    def test_bmw_reference_values_and_zones(self) -> None:
        catalog = load_vehicle_performance_catalog(PROFILES, repo_root=ROOT)
        profile = catalog.profiles["bmw-r1200gs-k25-2007"]

        self.assertEqual(profile.engine_displacement_cc, 1170)
        self.assertEqual(profile.maximum_torque_nm, 115)
        self.assertEqual(profile.nominal_power_kw, 74)
        self.assertEqual(profile.gearbox_gears, 6)
        self.assertEqual(profile.fuel_capacity_liters, 20)
        self.assertEqual(profile.fuel_reserve_liters, 4)
        self.assertEqual(profile.ice_warning_temperature_celsius, 3)
        self.assertEqual(profile.idle_rpm, 1150)
        self.assertEqual(profile.idle_tolerance_rpm, 50)
        self.assertEqual(profile.torque_peak_rpm, 5500)
        self.assertEqual(profile.power_peak_rpm, 7000)
        self.assertEqual(profile.tachometer_scale_max_rpm, 9000)
        self.assertIsNone(profile.rev_limiter_rpm)

        expected_zones = {
            0: "normal",
            6999: "normal",
            7000: "warning",
            7799: "warning",
            7800: "red",
            9000: "red",
        }
        for rpm, expected in expected_zones.items():
            self.assertEqual(profile.tachometer_zone(rpm), expected)

    def test_generic_profile_has_no_assumed_limits(self) -> None:
        catalog = load_vehicle_performance_catalog(PROFILES, repo_root=ROOT)
        profile = catalog.profiles["generic-motorcycle"]

        self.assertIsNone(profile.gearbox_gears)
        self.assertIsNone(profile.tachometer_scale_max_rpm)
        self.assertIsNone(profile.warning_start_rpm)
        self.assertIsNone(profile.red_zone_start_rpm)
        self.assertIsNone(profile.rev_limiter_rpm)
        self.assertEqual(profile.tachometer_zone(0), "unavailable")

    def test_invalid_zone_order_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            profile = json.loads(
                (PROFILES / "bmw-r1200gs-k25-2007.json").read_text()
            )
            profile["warningStartRpm"] = 7800
            profile["redZoneStartRpm"] = 7000
            (directory / "invalid.json").write_text(json.dumps(profile))
            (directory / "vehicle-profile-index-v1.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "defaultProfileId": profile["id"],
                        "fallbackProfileId": profile["id"],
                        "profiles": [
                            {
                                "id": profile["id"],
                                "configuration": "invalid.json",
                            }
                        ],
                    }
                )
            )
            with self.assertRaisesRegex(ValueError, "warning zone"):
                load_vehicle_performance_catalog(directory, repo_root=ROOT)


if __name__ == "__main__":
    unittest.main()
