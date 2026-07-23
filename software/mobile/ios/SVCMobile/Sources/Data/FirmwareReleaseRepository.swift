import Foundation

protocol FirmwareReleaseRepository {
    func fetchManifest() async throws -> FirmwareManifest
}

struct MockFirmwareReleaseRepository: FirmwareReleaseRepository {
    func fetchManifest() async throws -> FirmwareManifest {
        FirmwareManifest(
            schemaVersion: 1,
            releaseVersion: "0.1.0",
            channel: "dev",
            minimumMobileVersion: "0.1.0",
            components: []
        )
    }
}

struct GitHubFirmwareReleaseRepository: FirmwareReleaseRepository {
    let manifestURL: URL
    var session: URLSession = .shared

    func fetchManifest() async throws -> FirmwareManifest {
        guard manifestURL.scheme == "https" else {
            throw FirmwareReleaseError.httpsRequired
        }
        let (data, response) = try await session.data(from: manifestURL)
        guard
            let httpResponse = response as? HTTPURLResponse,
            (200..<300).contains(httpResponse.statusCode)
        else {
            throw FirmwareReleaseError.invalidResponse
        }
        return try JSONDecoder().decode(FirmwareManifest.self, from: data)
    }
}

enum FirmwareReleaseError: Error {
    case httpsRequired
    case invalidResponse
}
