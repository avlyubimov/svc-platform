import Foundation

final class MockDeviceRepository: DeviceRepository {
    private var connectionState = ConnectionState.disconnected
    private let telemetry: TelemetrySnapshot

    init(bundle: Bundle = .main) {
        let url = bundle.url(forResource: "device-v1", withExtension: "json")
        let data = url.flatMap { try? Data(contentsOf: $0) }
        self.telemetry = data
            .flatMap { try? JSONDecoder().decode(TelemetrySnapshot.self, from: $0) }
            ?? Self.fallbackTelemetry()
    }

    func discover() -> [DiscoveredDevice] {
        [
            DiscoveredDevice(
                id: UUID(uuidString: "D78F3100-2AE5-4B2B-9294-0F299E60AA01")!,
                name: "SVC-MOCK-001",
                signalStrength: -48
            )
        ]
    }

    func connect(to id: UUID) {
        connectionState = .connected
    }

    func currentSnapshot() -> DeviceSnapshot {
        DeviceSnapshot(
            connectionState: connectionState,
            telemetry: telemetry,
            events: [
                "Mock repository active",
                "CAN1 is listen-only",
                "SD card is unavailable"
            ]
        )
    }

    private static func fallbackTelemetry() -> TelemetrySnapshot {
        let unavailableNumber = Measurement<Double>(
            value: nil,
            unit: "unavailable",
            timestamp: "1970-01-01T00:00:00Z",
            valid: false,
            stale: false,
            source: .firmware,
            quality: .unavailable
        )
        let unavailableString = Measurement<String>(
            value: nil,
            unit: "unavailable",
            timestamp: "1970-01-01T00:00:00Z",
            valid: false,
            stale: false,
            source: .firmware,
            quality: .unavailable
        )
        let channels = (1...10).map { index in
            ChannelTelemetry(
                id: "OUT\(index)",
                current: unavailableNumber,
                state: unavailableString,
                fault: unavailableString
            )
        }
        return TelemetrySnapshot(
            schemaVersion: 1,
            protocolVersion: 1,
            deviceId: "SVC-MOCK-FALLBACK",
            sequence: 0,
            timestamp: "1970-01-01T00:00:00Z",
            batteryVoltage: unavailableNumber,
            totalCurrent: unavailableNumber,
            channels: channels,
            powerZoneTemperatures: [],
            ambientLight: unavailableNumber,
            accelerometer: VectorTelemetry(
                x: unavailableNumber,
                y: unavailableNumber,
                z: unavailableNumber
            ),
            gyroscope: VectorTelemetry(
                x: unavailableNumber,
                y: unavailableNumber,
                z: unavailableNumber
            ),
            leanAngle: unavailableNumber,
            vehicle: VehicleTelemetry(
                speed: unavailableNumber,
                engineRpm: unavailableNumber,
                engineTemperature: unavailableNumber,
                instantFuelConsumption: unavailableNumber,
                averageFuelConsumption: unavailableNumber,
                fuelLevel: unavailableNumber,
                ambientTemperature: unavailableNumber
            ),
            can1: CANStatus(
                state: unavailableString,
                rxFrames: unavailableNumber,
                droppedFrames: unavailableNumber,
                lastFrameTimestamp: unavailableString
            ),
            storage: StorageStatus(
                sdCardState: unavailableString,
                canLoggerState: unavailableString,
                freeBytes: unavailableNumber
            ),
            versions: FirmwareVersions(
                stm32: unavailableString,
                e73: unavailableString,
                protocolVersion: unavailableString
            ),
            warnings: []
        )
    }
}
