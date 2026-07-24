import Foundation

struct FirmwareManifest: Codable, Equatable {
    let schemaVersion: Int
    let releaseVersion: String
    let releaseTag: String
    let channel: String
    let minimumMobileVersion: String
    let components: [FirmwareComponent]

    func component(
        target: String,
        hardwareRevision: String,
        protocolVersion: Int
    ) throws -> FirmwareComponent {
        guard schemaVersion == 1 else {
            throw FirmwareManifestError.unsupportedSchema
        }
        guard let component = components.first(where: { $0.target == target }) else {
            throw FirmwareManifestError.targetUnavailable
        }
        guard component.hardware.contains(hardwareRevision) else {
            throw FirmwareManifestError.hardwareMismatch
        }
        guard component.protocolVersion == protocolVersion else {
            throw FirmwareManifestError.protocolMismatch
        }
        let expectedFormat = target == "e73-radio"
            ? "mcuboot-signed"
            : "oemirot-signed"
        guard component.installable, component.imageFormat == expectedFormat else {
            throw FirmwareManifestError.nonInstallableReviewImage
        }
        return component
    }
}

struct FirmwareReleaseSignature: Codable, Equatable {
    let algorithm: String
    let file: String
    let size: Int
    let sha256: String
    let keyId: String
}

struct FirmwareComponent: Codable, Equatable {
    let target: String
    let version: String
    let hardware: [String]
    let protocolVersion: Int
    let file: String
    let size: Int
    let sha256: String
    let imageFormat: String
    let installable: Bool
    let releaseSignature: FirmwareReleaseSignature
    let minimumBootloader: String
}

enum FirmwareManifestError: Error, Equatable {
    case unsupportedSchema
    case targetUnavailable
    case hardwareMismatch
    case protocolMismatch
    case nonInstallableReviewImage
}
