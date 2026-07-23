import XCTest
@testable import SVCMobile

final class BrandingTests: XCTestCase {
    func testMissingBMWAssetsUseSVCFallback() {
        let bundle = Bundle(for: Self.self)
        let catalog = BrandCatalog.load(bundle: bundle)
        let pack = catalog.resolve(profileId: catalog.defaultProfileId)
        XCTAssertEqual(catalog.profiles.count, 2)
        XCTAssertEqual(pack.id, "generic-automotive")
        XCTAssertTrue(pack.usesFallback)
        XCTAssertNotNil(pack.logoResource)
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
        let timeline = StartupTimeline.load(bundle: Bundle(for: Self.self))
        XCTAssertEqual(
            timeline.durationSeconds(
                animationEnabled: true,
                reduceMotion: false,
                critical: false
            ),
            2.1
        )
        XCTAssertEqual(
            timeline.durationSeconds(
                animationEnabled: true,
                reduceMotion: true,
                critical: false
            ),
            0.5
        )
        XCTAssertEqual(
            timeline.durationSeconds(
                animationEnabled: true,
                reduceMotion: false,
                critical: true
            ),
            0.5
        )
        XCTAssertEqual(
            timeline.durationSeconds(
                animationEnabled: false,
                reduceMotion: false,
                critical: false
            ),
            0
        )
    }
}
