import XCTest
@testable import SVCMobile

final class MockBLETransportTests: XCTestCase {
    func testMockScanConnectAndWrite() {
        let transport = MockBLETransport()
        var devices: [DiscoveredDevice] = []
        var state = ConnectionState.disconnected
        transport.onDevicesChanged = { devices = $0 }
        transport.onConnectionChanged = { state = $0 }

        transport.startScan()
        XCTAssertEqual(devices, [transport.device])
        XCTAssertEqual(state, .scanning)

        transport.connect(to: transport.device.id)
        XCTAssertEqual(state, .connected)

        let characteristic = UUID()
        transport.write(Data([1, 2, 3]), characteristic: characteristic)
        XCTAssertEqual(transport.writes.count, 1)
        XCTAssertEqual(transport.writes[0].0, Data([1, 2, 3]))
        XCTAssertEqual(transport.writes[0].1, characteristic)
    }
}
