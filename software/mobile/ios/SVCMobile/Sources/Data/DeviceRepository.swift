import Foundation

enum ConnectionState: String {
    case disconnected
    case scanning
    case connected
}

struct DiscoveredDevice: Identifiable, Equatable {
    let id: UUID
    let name: String
    let signalStrength: Int
}

struct DeviceSnapshot {
    let connectionState: ConnectionState
    let telemetry: TelemetrySnapshot
    let events: [String]
}

protocol DeviceRepository {
    func discover() -> [DiscoveredDevice]
    func connect(to id: UUID)
    func currentSnapshot() -> DeviceSnapshot
}
