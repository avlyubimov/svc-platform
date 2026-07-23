import XCTest
@testable import SVCMobile

final class BrandingTests: XCTestCase {
    func testMissingBMWAssetsUseSVCFallback() {
        let pack = BrandPack.resolved(
            profileId: "bmw-r1200gs-k25-personal",
            bundle: Bundle(for: Self.self)
        )
        XCTAssertEqual(pack.id, "generic-automotive")
        XCTAssertEqual(pack.brandTagline, "ENGINEERED FOR THE RIDE")
    }

    func testLastScreenRestorationAndSafeFallback() throws {
        let suite = try XCTUnwrap(
            UserDefaults(suiteName: "BrandingTests-\(UUID().uuidString)")
        )
        let store = AppearanceStore(defaults: suite)
        XCTAssertEqual(store.restoredScreen(), .dashboard)
        store.select(.channels)
        XCTAssertEqual(store.restoredScreen(), .channels)
        suite.set("removed-screen", forKey: "lastSelectedScreen")
        XCTAssertEqual(store.restoredScreen(), .dashboard)
    }

    func testMotionAndCriticalDurations() {
        XCTAssertEqual(
            StartupTiming.durationSeconds(
                animationEnabled: true,
                reduceMotion: false,
                critical: false
            ),
            2.1
        )
        XCTAssertEqual(
            StartupTiming.durationSeconds(
                animationEnabled: true,
                reduceMotion: true,
                critical: false
            ),
            0.5
        )
        XCTAssertEqual(
            StartupTiming.durationSeconds(
                animationEnabled: true,
                reduceMotion: false,
                critical: true
            ),
            0.5
        )
        XCTAssertEqual(
            StartupTiming.durationSeconds(
                animationEnabled: false,
                reduceMotion: false,
                critical: false
            ),
            0
        )
    }
}
