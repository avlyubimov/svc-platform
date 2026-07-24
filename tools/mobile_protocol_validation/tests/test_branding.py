import hashlib
import unittest
from pathlib import Path

from mobile_protocol_validation.branding import (
    load_brand_catalog,
    load_startup_timeline,
    load_vehicle_brand_catalog,
    restore_primary_screen,
    startup_duration_ms,
)

ROOT = Path(__file__).resolve().parents[3]
BRANDING = ROOT / "software" / "mobile" / "branding"


class BrandingTests(unittest.TestCase):
    def test_bmw_assets_and_fallback(self) -> None:
        catalog = load_brand_catalog(BRANDING)
        bmw_profile = catalog.profiles["bmw-r1200gs-k25-personal"]
        expected_logo = (
            "vehicle-brands/brands/bmw/bmw-roundel-1997-2020.svg"
        )
        self.assertEqual(bmw_profile.brand_id, "bmw")
        self.assertEqual(bmw_profile.model, "R1200GS")
        self.assertEqual(bmw_profile.generation, "K25")
        self.assertEqual(bmw_profile.year, 2007)
        self.assertEqual(catalog.logo_path(bmw_profile), expected_logo)
        self.assertEqual(
            catalog.select(
                "bmw-r1200gs-k25-personal",
                lambda asset: (BRANDING / asset).is_file(),
            ).identifier,
            "bmw-r1200gs-k25-personal",
        )
        self.assertEqual(
            catalog.select(
                "bmw-r1200gs-k25-personal",
                lambda asset: asset.startswith("svc/"),
            ).identifier,
            "generic-automotive",
        )
        self.assertEqual(catalog.default_profile_id, "bmw-r1200gs-k25-personal")
        self.assertEqual(catalog.fallback_profile_id, "generic-automotive")

    def test_vehicle_brand_catalog_assets_and_svg_xml(self) -> None:
        catalog = load_vehicle_brand_catalog(BRANDING)
        self.assertEqual(catalog.simple_icons_version, "16.27.0")
        self.assertEqual(len(catalog.brands), 29)
        self.assertEqual(catalog.brands["bmw"].name, "BMW")
        self.assertEqual(
            catalog.brands["bmw"].preferred_asset,
            "bmw-roundel-1997-2020.svg",
        )

    def test_motion_critical_and_disabled_timings(self) -> None:
        timeline = load_startup_timeline(BRANDING / "startup-animation-v1.json")
        self.assertEqual(
            startup_duration_ms(
                animation_enabled=True,
                reduce_motion=False,
                critical=False,
                timeline=timeline,
            ),
            2100,
        )
        self.assertEqual(
            startup_duration_ms(
                animation_enabled=True,
                reduce_motion=True,
                critical=False,
                timeline=timeline,
            ),
            500,
        )
        self.assertEqual(
            startup_duration_ms(
                animation_enabled=True,
                reduce_motion=False,
                critical=True,
                timeline=timeline,
            ),
            500,
        )
        self.assertEqual(
            startup_duration_ms(
                animation_enabled=False,
                reduce_motion=False,
                critical=False,
                timeline=timeline,
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

    def test_mobile_sources_do_not_duplicate_brand_copy_or_timeline(self) -> None:
        mobile_sources = "\n".join(
            path.read_text()
            for root in (
                ROOT / "software/mobile/android/app-mobile/src/main/kotlin",
                ROOT / "software/mobile/ios/SVCMobile/Sources",
            )
            for path in root.rglob("*")
            if path.suffix in {".kt", ".swift"}
        )
        for configured_value in (
            "BMW MOTORRAD",
            "MAKE LIFE A RIDE",
            "ENGINEERED FOR THE RIDE",
            "bmw-r1200gs-k25-personal",
        ):
            self.assertNotIn(configured_value, mobile_sources)
        self.assertNotIn("else -> 2100", mobile_sources)
        self.assertNotIn("critical || reduceMotion -> 500", mobile_sources)

    def test_public_app_identity_uses_committed_svc_assets(self) -> None:
        svc_assets = BRANDING / "svc"
        for name in (
            "svg/svc-app-icon.svg",
            "svg/svc-emblem-color.svg",
            "svg/svc-wordmark-horizontal-light.svg",
            "platform/ios/AppIcon-1024.png",
            "platform/android/play-store/icon-512.png",
        ):
            self.assertTrue((svc_assets / name).is_file())

        android_manifest = (
            ROOT / "software/mobile/android/app-mobile/src/main/AndroidManifest.xml"
        ).read_text()
        ios_project = (
            ROOT / "software/mobile/ios/SVCMobile/project.yml"
        ).read_text()
        self.assertIn('android:icon="@mipmap/ic_launcher"', android_manifest)
        self.assertIn("ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon", ios_project)
        self.assertNotIn("bmw", android_manifest.lower())
        app_icon_setting = next(
            line
            for line in ios_project.splitlines()
            if "ASSETCATALOG_COMPILER_APPICON_NAME" in line
        )
        self.assertNotIn("bmw", app_icon_setting.lower())
        self.assertEqual(
            (
                ROOT
                / "software/mobile/ios/SVCMobile/Sources/Resources/Assets.xcassets/AppIcon.appiconset/svc-app-icon-1024.png"
            ).read_bytes(),
            (svc_assets / "platform/ios/AppIcon-1024.png").read_bytes(),
        )
        for density in ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"):
            self.assertEqual(
                (
                    ROOT
                    / f"software/mobile/android/app-mobile/src/main/res/mipmap-{density}/ic_launcher.png"
                ).read_bytes(),
                (
                    svc_assets
                    / f"platform/android/mipmap-{density}/ic_launcher.png"
                ).read_bytes(),
            )

    def test_svc_pack_checksums(self) -> None:
        svc_assets = BRANDING / "svc"
        checksum_file = svc_assets / "SHA256SUMS"
        checked_paths: set[str] = set()
        for line in checksum_file.read_text().splitlines():
            if not line:
                continue
            expected_digest, relative_path = line.split(maxsplit=1)
            relative_path = relative_path.removeprefix("*").removeprefix("./")
            asset_path = svc_assets / relative_path
            self.assertTrue(asset_path.is_file(), relative_path)
            self.assertEqual(
                hashlib.sha256(asset_path.read_bytes()).hexdigest(),
                expected_digest,
                relative_path,
            )
            checked_paths.add(relative_path)

        expected_paths = {
            str(path.relative_to(svc_assets))
            for path in svc_assets.rglob("*")
            if path.is_file() and path != checksum_file
        }
        self.assertEqual(checked_paths, expected_paths)


if __name__ == "__main__":
    unittest.main()
