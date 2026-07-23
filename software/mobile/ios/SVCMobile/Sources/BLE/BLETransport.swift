import Foundation

protocol BLETransport: AnyObject {
    var onDevicesChanged: (([DiscoveredDevice]) -> Void)? { get set }
    var onConnectionChanged: ((ConnectionState) -> Void)? { get set }
    func startScan()
    func stopScan()
    func connect(to id: UUID)
    func write(_ data: Data, characteristic: UUID)
}
