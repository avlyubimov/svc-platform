import XCTest
@testable import SVCMobile

final class FirmwareManifestTests: XCTestCase {
    func testRejectsIncompatibleProtocolAndHardware() throws {
        let url = try XCTUnwrap(
            Bundle(for: Self.self).url(
                forResource: "firmware-manifest.dev",
                withExtension: "json"
            )
        )
        let manifest = try JSONDecoder().decode(
            FirmwareManifest.self,
            from: Data(contentsOf: url)
        )

        XCTAssertThrowsError(
            try manifest.component(
                target: "stm32-main",
                hardwareRevision: "LB-100-REV2",
                protocolVersion: 1
            )
        )
        XCTAssertThrowsError(
            try manifest.component(
                target: "stm32-main",
                hardwareRevision: "LB-100-REV1",
                protocolVersion: 2
            )
        )
        XCTAssertThrowsError(
            try manifest.component(
                target: "stm32-main",
                hardwareRevision: "LB-100-REV1",
                protocolVersion: 1
            )
        ) { error in
            XCTAssertEqual(
                error as? FirmwareManifestError,
                .nonInstallableReviewImage
            )
        }
    }
}
