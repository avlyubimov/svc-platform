import unittest
from pathlib import Path

from mobile_protocol_validation.branding import (
    load_startup_timeline,
    restore_primary_screen,
    selected_brand_pack,
    startup_duration_ms,
)

ROOT = Path(__file__).resolve().parents[3]
BRANDING = ROOT / "software" / "mobile" / "branding"


class BrandingTests(unittest.TestCase):
    def test_bmw_assets_and_fallback(self) -> None:
        self.assertEqual(
            selected_brand_pack(
                "bmw-r1200gs-k25-personal",
                {"bmw-roundel.svg", "bmw-motorrad-wordmark.svg"},
            ),
            "bmw-r1200gs-k25-personal",
        )
        self.assertEqual(
            selected_brand_pack(
                "bmw-r1200gs-k25-personal",
                {"bmw-roundel.svg"},
            ),
            "generic-automotive",
        )

    def test_motion_critical_and_disabled_timings(self) -> None:
        self.assertEqual(
            startup_duration_ms(
                animation_enabled=True,
                reduce_motion=False,
                critical=False,
            ),
            2100,
        )
        self.assertEqual(
            startup_duration_ms(
                animation_enabled=True,
                reduce_motion=True,
                critical=False,
            ),
            500,
        )
        self.assertEqual(
            startup_duration_ms(
                animation_enabled=True,
                reduce_motion=False,
                critical=True,
            ),
            500,
        )
        self.assertEqual(
            startup_duration_ms(
                animation_enabled=False,
                reduce_motion=False,
                critical=False,
            ),
            0,
        )

    def test_last_screen_falls_back_safely(self) -> None:
        self.assertEqual(restore_primary_screen("channels"), "channels")
        self.assertEqual(restore_primary_screen("removed-screen"), "dashboard")
        self.assertEqual(restore_primary_screen(None), "dashboard")

    def test_timeline_is_monotonic_and_60_fps_sized(self) -> None:
        timeline = load_startup_timeline(BRANDING / "startup-animation-v1.json")
        self.assertEqual(timeline.phase_ends_ms, (250, 700, 1200, 1600, 2100))
        self.assertEqual(timeline.frames_at_60_fps, 126)

    def test_mock_ble_restore_outlives_normal_animation(self) -> None:
        android_app = (
            ROOT
            / "software/mobile/android/app-mobile/src/main/kotlin/com/avlyubimov/svc/mobile/SVCMobileApp.kt"
        ).read_text()
        ios_model = (
            ROOT
            / "software/mobile/ios/SVCMobile/Sources/App/AppViewModel.swift"
        ).read_text()
        self.assertIn("delay(3_000)", android_app)
        self.assertIn("Task.sleep(for: .seconds(3))", ios_model)

    def test_startup_has_no_post_text_or_white_background(self) -> None:
        startup_sources = (
            ROOT
            / "software/mobile/android/app-mobile/src/main/kotlin/com/avlyubimov/svc/mobile/StartupBranding.kt"
        ).read_text() + (
            ROOT
            / "software/mobile/ios/SVCMobile/Sources/UI/StartupAnimationView.swift"
        ).read_text()
        for forbidden in ("POWER", "SENSORS", "OUTPUTS", "Color.White.background"):
            self.assertNotIn(forbidden, startup_sources)
        android_style = (
            ROOT / "software/mobile/android/app-mobile/src/main/res/values/styles.xml"
        ).read_text()
        ios_launch = (
            ROOT
            / "software/mobile/ios/SVCMobile/Sources/Resources/LaunchScreen.storyboard"
        ).read_text()
        self.assertIn('android:windowBackground">#050505', android_style)
        self.assertIn('android:windowSplashScreenBackground">#050505', android_style)
        self.assertIn('red="0.01960784314"', ios_launch)


if __name__ == "__main__":
    unittest.main()
