import CoreBluetooth
import Foundation

final class CoreBluetoothTransport: NSObject, BLETransport {
    var onDevicesChanged: (([DiscoveredDevice]) -> Void)?
    var onConnectionChanged: ((ConnectionState) -> Void)?

    private lazy var central = CBCentralManager(delegate: self, queue: nil)
    private var peripherals: [UUID: CBPeripheral] = [:]

    func startScan() {
        guard central.state == .poweredOn else {
            onConnectionChanged?(.disconnected)
            return
        }
        onConnectionChanged?(.scanning)
        central.scanForPeripherals(withServices: nil)
    }

    func stopScan() {
        central.stopScan()
    }

    func connect(to id: UUID) {
        guard let peripheral = peripherals[id] else {
            onConnectionChanged?(.disconnected)
            return
        }
        central.connect(peripheral)
    }

    func write(_ data: Data, characteristic: UUID) {
        guard
            let peripheral = peripherals.values.first(where: { $0.state == .connected }),
            let service = peripheral.services?.first(where: {
                $0.characteristics?.contains(where: { $0.uuid.uuidString == characteristic.uuidString }) == true
            }),
            let target = service.characteristics?.first(where: {
                $0.uuid.uuidString == characteristic.uuidString
            })
        else {
            return
        }
        peripheral.writeValue(data, for: target, type: .withoutResponse)
    }
}

extension CoreBluetoothTransport: CBCentralManagerDelegate {
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state != .poweredOn {
            onConnectionChanged?(.disconnected)
        }
    }

    func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String: Any],
        rssi RSSI: NSNumber
    ) {
        peripherals[peripheral.identifier] = peripheral
        let devices = peripherals.values.map {
            DiscoveredDevice(
                id: $0.identifier,
                name: $0.name ?? "SVC",
                signalStrength: RSSI.intValue
            )
        }
        onDevicesChanged?(devices)
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        peripheral.delegate = self
        onConnectionChanged?(.connected)
    }

    func centralManager(
        _ central: CBCentralManager,
        didFailToConnect peripheral: CBPeripheral,
        error: Error?
    ) {
        onConnectionChanged?(.disconnected)
    }
}

extension CoreBluetoothTransport: CBPeripheralDelegate {}
