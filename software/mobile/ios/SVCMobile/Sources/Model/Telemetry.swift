import Foundation

enum MeasurementSource: String, Codable {
    case adc
    case can1
    case imu
    case sensor
    case outputManager = "output-manager"
    case storage
    case firmware
    case derived
}

enum MeasurementQuality: String, Codable {
    case good
    case degraded
    case invalid
    case unavailable
}

struct Measurement<Value: Codable & Equatable>: Codable, Equatable {
    let value: Value?
    let unit: String
    let timestamp: String
    let valid: Bool
    let stale: Bool
    let source: MeasurementSource
    let quality: MeasurementQuality

    var isUsable: Bool {
        valid && !stale && quality != .invalid && quality != .unavailable
    }
}

struct IdentifiedNumberMeasurement: Codable, Equatable {
    let id: String
    let value: Double?
    let unit: String
    let timestamp: String
    let valid: Bool
    let stale: Bool
    let source: MeasurementSource
    let quality: MeasurementQuality
}

struct ChannelTelemetry: Codable, Equatable, Identifiable {
    let id: String
    let current: Measurement<Double>
    let state: Measurement<String>
    let fault: Measurement<String>
}

struct VectorTelemetry: Codable, Equatable {
    let x: Measurement<Double>
    let y: Measurement<Double>
    let z: Measurement<Double>
}

struct VehicleTelemetry: Codable, Equatable {
    let speed: Measurement<Double>
    let engineRpm: Measurement<Double>
    let engineTemperature: Measurement<Double>
    let instantFuelConsumption: Measurement<Double>
    let averageFuelConsumption: Measurement<Double>
    let fuelLevel: Measurement<Double>
    let ambientTemperature: Measurement<Double>
}

struct CANStatus: Codable, Equatable {
    let state: Measurement<String>
    let rxFrames: Measurement<Double>
    let droppedFrames: Measurement<Double>
    let lastFrameTimestamp: Measurement<String>
}

struct StorageStatus: Codable, Equatable {
    let sdCardState: Measurement<String>
    let canLoggerState: Measurement<String>
    let freeBytes: Measurement<Double>
}

struct FirmwareVersions: Codable, Equatable {
    let stm32: Measurement<String>
    let e73: Measurement<String>
    let protocol: Measurement<String>
}

struct DeviceWarning: Codable, Equatable, Identifiable {
    let code: String
    let severity: String
    let message: String
    let timestamp: String
    let active: Bool

    var id: String { code }
}

struct TelemetrySnapshot: Codable, Equatable {
    let schemaVersion: Int
    let protocolVersion: Int
    let deviceId: String
    let sequence: Int
    let timestamp: String
    let batteryVoltage: Measurement<Double>
    let totalCurrent: Measurement<Double>
    let channels: [ChannelTelemetry]
    let powerZoneTemperatures: [IdentifiedNumberMeasurement]
    let ambientLight: Measurement<Double>
    let accelerometer: VectorTelemetry
    let gyroscope: VectorTelemetry
    let leanAngle: Measurement<Double>
    let vehicle: VehicleTelemetry
    let can1: CANStatus
    let storage: StorageStatus
    let versions: FirmwareVersions
    let warnings: [DeviceWarning]
}
