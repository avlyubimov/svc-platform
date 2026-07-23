import Foundation

final class MockBLETransport: BLETransport {
    var onDevicesChanged: (([DiscoveredDevice]) -> Void)?
    var onConnectionChanged: ((ConnectionState) -> Void)?
    private(set) var writes: [(Data, UUID)] = []

    let device = DiscoveredDevice(
        id: UUID(uuidString: "D78F3100-2AE5-4B2B-9294-0F299E60AA01")!,
        name: "SVC-MOCK-001",
        signalStrength: -42
    )

    func startScan() {
        onConnectionChanged?(.scanning)
        onDevicesChanged?([device])
    }

    func stopScan() {}

    func connect(to id: UUID) {
        onConnectionChanged?(id == device.id ? .connected : .disconnected)
    }

    func write(_ data: Data, characteristic: UUID) {
        writes.append((data, characteristic))
    }
}
