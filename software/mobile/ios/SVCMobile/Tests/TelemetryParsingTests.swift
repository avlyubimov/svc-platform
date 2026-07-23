import XCTest
@testable import SVCMobile

final class TelemetryParsingTests: XCTestCase {
    func testParsesMockTelemetryAndUnavailableCAN() throws {
        let url = try XCTUnwrap(
            Bundle(for: Self.self).url(forResource: "device-v1", withExtension: "json")
        )
        let telemetry = try JSONDecoder().decode(
            TelemetrySnapshot.self,
            from: Data(contentsOf: url)
        )

        XCTAssertEqual(telemetry.channels.count, 10)
        XCTAssertNil(telemetry.vehicle.engineTemperature.value)
        XCTAssertEqual(telemetry.vehicle.engineTemperature.quality, .unavailable)
        XCTAssertEqual(telemetry.storage.sdCardState.value, "missing")
    }

    func testStaleCANPreventsUpdate() throws {
        let unavailable = Measurement<Double>(
            value: 0,
            unit: "km/h",
            timestamp: "2026-07-23T10:00:00Z",
            valid: true,
            stale: true,
            source: .can1,
            quality: .degraded
        )
        let repository = MockDeviceRepository(bundle: Bundle(for: Self.self))
        let snapshot = repository.currentSnapshot().telemetry
        let vehicle = VehicleTelemetry(
            speed: unavailable,
            engineRpm: snapshot.vehicle.engineRpm,
            engineTemperature: snapshot.vehicle.engineTemperature,
            instantFuelConsumption: snapshot.vehicle.instantFuelConsumption,
            averageFuelConsumption: snapshot.vehicle.averageFuelConsumption,
            fuelLevel: snapshot.vehicle.fuelLevel,
            ambientTemperature: snapshot.vehicle.ambientTemperature
        )
        let modified = TelemetrySnapshot(
            schemaVersion: snapshot.schemaVersion,
            protocolVersion: snapshot.protocolVersion,
            deviceId: snapshot.deviceId,
            sequence: snapshot.sequence,
            timestamp: snapshot.timestamp,
            batteryVoltage: snapshot.batteryVoltage,
            totalCurrent: snapshot.totalCurrent,
            channels: snapshot.channels,
            powerZoneTemperatures: snapshot.powerZoneTemperatures,
            ambientLight: snapshot.ambientLight,
            accelerometer: snapshot.accelerometer,
            gyroscope: snapshot.gyroscope,
            leanAngle: snapshot.leanAngle,
            vehicle: vehicle,
            can1: snapshot.can1,
            storage: snapshot.storage,
            versions: snapshot.versions,
            warnings: snapshot.warnings
        )

        XCTAssertTrue(OTAPolicy.denialReasons(for: modified).contains("vehicle_moving"))
    }
}
