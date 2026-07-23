import Combine
import Foundation

@MainActor
final class AppViewModel: ObservableObject {
    @Published private(set) var device: DeviceSnapshot
    @Published private(set) var discoveredDevices: [DiscoveredDevice] = []
    @Published private(set) var firmwareStatus = "Not checked"

    private let repository: DeviceRepository
    private let releaseRepository: FirmwareReleaseRepository

    init(
        repository: DeviceRepository,
        releaseRepository: FirmwareReleaseRepository = MockFirmwareReleaseRepository()
    ) {
        self.repository = repository
        self.releaseRepository = releaseRepository
        self.device = repository.currentSnapshot()
    }

    func discover() {
        discoveredDevices = repository.discover()
    }

    func connect(to device: DiscoveredDevice) {
        repository.connect(to: device.id)
        self.device = repository.currentSnapshot()
    }

    func refresh() {
        device = repository.currentSnapshot()
    }

    func checkFirmware() {
        Task {
            do {
                let manifest = try await releaseRepository.fetchManifest(channel: .stable)
                firmwareStatus = "\(manifest.channel) release \(manifest.releaseVersion) available"
            } catch {
                firmwareStatus = "Release check failed: \(error.localizedDescription)"
            }
        }
    }

    func installFirmware() {
        let denials = OTAPolicy.denialReasons(for: device.telemetry)
        firmwareStatus = denials.isEmpty
            ? "Mock transfer prepared; no real device action performed"
            : "Denied: \(denials.joined(separator: ", "))"
    }
}
