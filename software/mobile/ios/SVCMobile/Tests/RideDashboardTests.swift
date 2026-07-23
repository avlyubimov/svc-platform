import XCTest
@testable import SVCMobile

final class RideDashboardTests: XCTestCase {
    private var profile: VehiclePerformanceProfile {
        VehiclePerformanceCatalog.load(bundle: Bundle(for: Self.self))
            .resolve(profileId: "bmw-r1200gs-k25-2007")
    }

    func testTachometerBoundariesAreExact() {
        let expected: [(Double, TachometerZone)] = [
            (0, .normal),
            (6_999, .normal),
            (7_000, .warning),
            (7_799, .warning),
            (7_800, .red),
            (9_000, .red)
        ]

        for (rpm, zone) in expected {
            XCTAssertEqual(
                TachometerZoneResolver.zone(rpm: rpm, profile: profile),
                zone
            )
        }
        XCTAssertNil(profile.revLimiterRpm)
    }

    func testTachometerHysteresisAvoidsBoundaryOscillation() {
        XCTAssertEqual(
            TachometerZoneResolver.zoneWithHysteresis(
                rpm: 7_750,
                profile: profile,
                previous: .red
            ),
            .red
        )
        XCTAssertEqual(
            TachometerZoneResolver.zoneWithHysteresis(
                rpm: 6_950,
                profile: profile,
                previous: .warning
            ),
            .warning
        )
    }

    func testAllGearPresentationStatesAreExplicit() {
        XCTAssertEqual(
            RideGear.allCases.map(\.displayValue),
            ["N", "1", "2", "3", "4", "5", "6", "BETWEEN", "—"]
        )
    }

    func testStaleInvalidUnavailableAndDegradedStates() {
        XCTAssertNil(
            RideValue(value: 1_200.0, unit: "rpm", state: .stale).displayValue
        )
        XCTAssertNil(
            RideValue(value: 1_200.0, unit: "rpm", state: .invalid).displayValue
        )
        XCTAssertNil(
            RideValue(value: 1_200.0, unit: "rpm", state: .unavailable).displayValue
        )
        XCTAssertEqual(
            RideValue(value: 1_200.0, unit: "rpm", state: .degraded).displayValue,
            1_200
        )
    }

    func testLeanExtremaTrackBothDirectionsAndResetOnlyAtZero() {
        var extrema = LeanExtrema()
        extrema.observe(-34)
        extrema.observe(42)
        extrema.observe(-12)
        XCTAssertEqual(extrema.maximumLeftDegrees, 34)
        XCTAssertEqual(extrema.maximumRightDegrees, 42)

        XCTAssertFalse(
            extrema.resetIfStationary(
                speed: RideValue(value: 2.0, unit: "km/h", state: .valid)
            )
        )
        XCTAssertEqual(extrema.maximumLeftDegrees, 34)
        XCTAssertTrue(
            extrema.resetIfStationary(
                speed: RideValue(value: 0.0, unit: "km/h", state: .valid)
            )
        )
        XCTAssertEqual(extrema, LeanExtrema())
    }

    func testCalibrationRequiresDemoAndConfirmedStop() {
        let stopped = RideValue(value: 0.0, unit: "km/h", state: .valid)
        let moving = RideValue(value: 1.0, unit: "km/h", state: .valid)
        let unavailable = RideValue<Double>(
            value: nil,
            unit: "km/h",
            state: .unavailable
        )

        XCTAssertTrue(
            MotorcycleCalibrationPolicy.canCalibrate(
                speed: stopped,
                demoMode: true
            )
        )
        XCTAssertFalse(
            MotorcycleCalibrationPolicy.canCalibrate(
                speed: stopped,
                demoMode: false
            )
        )
        XCTAssertFalse(
            MotorcycleCalibrationPolicy.canCalibrate(
                speed: moving,
                demoMode: true
            )
        )
        XCTAssertFalse(
            MotorcycleCalibrationPolicy.canCalibrate(
                speed: unavailable,
                demoMode: true
            )
        )
    }

    func testAutomaticThemeHysteresisAndUnavailableLight() {
        let low = RideValue(value: 200.0, unit: "lux", state: .valid)
        let middle = RideValue(value: 450.0, unit: "lux", state: .valid)
        let high = RideValue(value: 700.0, unit: "lux", state: .valid)
        let unavailable = RideValue<Double>(
            value: nil,
            unit: "lux",
            state: .unavailable
        )

        XCTAssertEqual(
            RideThemeResolver.resolve(
                mode: .automatic,
                ambientLight: low,
                previous: .day
            ),
            .night
        )
        XCTAssertEqual(
            RideThemeResolver.resolve(
                mode: .automatic,
                ambientLight: middle,
                previous: .night
            ),
            .night
        )
        XCTAssertEqual(
            RideThemeResolver.resolve(
                mode: .automatic,
                ambientLight: high,
                previous: .night
            ),
            .day
        )
        XCTAssertEqual(
            RideThemeResolver.resolve(
                mode: .automatic,
                ambientLight: unavailable,
                previous: .day
            ),
            .day
        )
    }

    func testProfileSwitchFallsBackSafely() {
        let catalog = VehiclePerformanceCatalog.load(bundle: Bundle(for: Self.self))
        XCTAssertEqual(
            catalog.resolve(profileId: "bmw-r1200gs-k25-2007").redZoneStartRpm,
            7_800
        )
        XCTAssertNil(
            catalog.resolve(profileId: "generic-motorcycle").redZoneStartRpm
        )
        XCTAssertEqual(
            catalog.resolve(profileId: "missing-profile").id,
            "generic-motorcycle"
        )
    }

    func testMockDashboardDoesNotInventGearAndKeepsWarning() {
        let snapshot = MockDeviceRepository(
            bundle: Bundle(for: Self.self)
        ).currentSnapshot()
        let dashboard = RideDashboardState.build(
            telemetry: snapshot.telemetry,
            connectionState: snapshot.connectionState,
            isConnecting: false,
            profile: profile
        )

        XCTAssertEqual(dashboard.gear, .unavailable)
        XCTAssertEqual(dashboard.leanAngle.state, .degraded)
        XCTAssertTrue(dashboard.alerts.contains { $0.id == "sd_card_missing" })
    }

    func testReduceMotionUsesZeroDuration() {
        XCTAssertEqual(RideMotionPolicy.duration(reduceMotion: true), 0)
        XCTAssertEqual(
            RideMotionPolicy.duration(reduceMotion: false),
            RideDesignTokens.standardAnimation
        )
    }
}
