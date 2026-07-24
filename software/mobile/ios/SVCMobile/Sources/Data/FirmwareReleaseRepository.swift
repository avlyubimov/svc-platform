import CryptoKit
import Foundation

enum FirmwareReleaseChannel: String {
    case stable
    case beta
    case test

    var manifestChannel: String {
        self == .test ? "dev" : rawValue
    }
}

protocol FirmwareReleaseRepository {
    func fetchManifest(channel: FirmwareReleaseChannel) async throws -> FirmwareManifest
}

struct MockFirmwareReleaseRepository: FirmwareReleaseRepository {
    func fetchManifest(channel: FirmwareReleaseChannel) async throws -> FirmwareManifest {
        FirmwareManifest(
            schemaVersion: 1,
            releaseVersion: "0.1.0-test.1",
            releaseTag: "svc-v0.1.0-test.1",
            channel: "dev",
            minimumMobileVersion: "0.1.0",
            components: []
        )
    }
}

protocol FirmwareReleaseSignatureVerifying {
    func verify(
        data: Data,
        signature: Data,
        keyId: String,
        algorithm: String
    ) -> Bool
}

struct GitHubFirmwareReleaseRepository: FirmwareReleaseRepository {
    let owner: String
    let repository: String
    let signatureVerifier: FirmwareReleaseSignatureVerifying
    var session: URLSession = .shared
    var apiBaseURL = URL(string: "https://api.github.com")!

    func fetchManifest(channel: FirmwareReleaseChannel) async throws -> FirmwareManifest {
        let release = try await fetchRelease(channel: channel)
        let manifestAsset = try asset(named: "firmware-manifest.json", in: release)
        let manifestData = try await download(manifestAsset)
        let manifest = try JSONDecoder().decode(FirmwareManifest.self, from: manifestData)
        try validate(
            manifest: manifest,
            releaseTag: release.tagName,
            requestedChannel: channel
        )

        for component in manifest.components {
            let imageAsset = try asset(named: component.file, in: release)
            let signatureAsset = try asset(
                named: component.releaseSignature.file,
                in: release
            )
            let image = try await download(imageAsset)
            let signature = try await download(signatureAsset)
            try validate(
                component: component,
                image: image,
                signature: signature
            )
        }
        return manifest
    }

    private func fetchRelease(channel: FirmwareReleaseChannel) async throws -> GitHubRelease {
        switch channel {
        case .stable:
            let url = apiBaseURL
                .appending(path: "repos")
                .appending(path: owner)
                .appending(path: repository)
                .appending(path: "releases")
                .appending(path: "latest")
            let release = try await request(url: url, as: GitHubRelease.self)
            guard !release.draft, !release.prerelease else {
                throw FirmwareReleaseError.releaseIdentityMismatch
            }
            return release
        case .beta, .test:
            var components = URLComponents(
                url: apiBaseURL
                    .appending(path: "repos")
                    .appending(path: owner)
                    .appending(path: repository)
                    .appending(path: "releases"),
                resolvingAgainstBaseURL: false
            )
            components?.queryItems = [URLQueryItem(name: "per_page", value: "100")]
            guard let url = components?.url else {
                throw FirmwareReleaseError.invalidResponse
            }
            let releases = try await request(url: url, as: [GitHubRelease].self)
            guard let release = releases.first(where: {
                !$0.draft &&
                    $0.prerelease &&
                    releaseTag($0.tagName, matches: channel)
            }) else {
                throw FirmwareReleaseError.releaseUnavailable
            }
            return release
        }
    }

    private func request<Value: Decodable>(
        url: URL,
        as type: Value.Type
    ) async throws -> Value {
        var request = URLRequest(url: url)
        request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        request.setValue("2022-11-28", forHTTPHeaderField: "X-GitHub-Api-Version")
        let (data, response) = try await session.data(for: request)
        try requireSuccess(response)
        return try JSONDecoder().decode(type, from: data)
    }

    private func download(_ asset: GitHubReleaseAsset) async throws -> Data {
        guard
            asset.browserDownloadURL.scheme == "https",
            asset.browserDownloadURL.host == "github.com"
        else {
            throw FirmwareReleaseError.untrustedAssetURL
        }
        var request = URLRequest(url: asset.browserDownloadURL)
        request.setValue("application/octet-stream", forHTTPHeaderField: "Accept")
        let (data, response) = try await session.data(for: request)
        try requireSuccess(response)
        guard data.count == asset.size else {
            throw FirmwareReleaseError.sizeMismatch
        }
        guard asset.digest == "sha256:\(sha256(data))" else {
            throw FirmwareReleaseError.sha256Mismatch
        }
        return data
    }

    private func validate(
        manifest: FirmwareManifest,
        releaseTag: String,
        requestedChannel: FirmwareReleaseChannel
    ) throws {
        guard manifest.schemaVersion == 1 else {
            throw FirmwareReleaseError.unsupportedManifest
        }
        guard
            manifest.releaseTag == releaseTag,
            manifest.releaseTag == "svc-v\(manifest.releaseVersion)",
            manifest.channel == requestedChannel.manifestChannel,
            self.releaseTag(releaseTag, matches: requestedChannel),
            !manifest.components.isEmpty,
            Set(manifest.components.map(\.target)).count == manifest.components.count,
            manifest.components.allSatisfy({ $0.version == manifest.releaseVersion })
        else {
            throw FirmwareReleaseError.releaseIdentityMismatch
        }
        for component in manifest.components {
            guard
                ["stm32-main", "e73-radio"].contains(component.target),
                component.size >= 0,
                component.releaseSignature.size > 0,
                isAssetBasename(component.file),
                isAssetBasename(component.releaseSignature.file),
                component.file != component.releaseSignature.file,
                component.releaseSignature.algorithm == "rsa-pss-sha256"
            else {
                throw FirmwareReleaseError.unsupportedManifest
            }
            let expectedFormat = component.target == "e73-radio"
                ? "mcuboot-signed"
                : "oemirot-signed"
            guard
                !(component.imageFormat == "review-raw" && component.installable),
                !component.installable || component.imageFormat == expectedFormat
            else {
                throw FirmwareReleaseError.unsupportedManifest
            }
        }
    }

    private func validate(
        component: FirmwareComponent,
        image: Data,
        signature: Data
    ) throws {
        guard image.count == component.size else {
            throw FirmwareReleaseError.sizeMismatch
        }
        guard sha256(image) == component.sha256 else {
            throw FirmwareReleaseError.sha256Mismatch
        }
        guard signature.count == component.releaseSignature.size else {
            throw FirmwareReleaseError.signatureSizeMismatch
        }
        guard sha256(signature) == component.releaseSignature.sha256 else {
            throw FirmwareReleaseError.signatureSha256Mismatch
        }
        guard signatureVerifier.verify(
            data: image,
            signature: signature,
            keyId: component.releaseSignature.keyId,
            algorithm: component.releaseSignature.algorithm
        ) else {
            throw FirmwareReleaseError.invalidSignature
        }
    }

    private func asset(
        named name: String,
        in release: GitHubRelease
    ) throws -> GitHubReleaseAsset {
        guard let asset = release.assets.first(where: { $0.name == name }) else {
            throw FirmwareReleaseError.assetMissing
        }
        return asset
    }

    private func requireSuccess(_ response: URLResponse) throws {
        guard
            let response = response as? HTTPURLResponse,
            (200..<300).contains(response.statusCode)
        else {
            throw FirmwareReleaseError.invalidResponse
        }
    }

    private func releaseTag(
        _ tag: String,
        matches channel: FirmwareReleaseChannel
    ) -> Bool {
        let core = #"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"#
        let pattern: String
        switch channel {
        case .stable:
            pattern = #"^svc-v\#(core)$"#
        case .beta:
            pattern = #"^svc-v\#(core)-beta\.(?:0|[1-9][0-9]*)$"#
        case .test:
            pattern = #"^svc-v\#(core)-test\.(?:0|[1-9][0-9]*)$"#
        }
        return tag.range(of: pattern, options: .regularExpression) != nil
    }

    private func isAssetBasename(_ value: String) -> Bool {
        value.range(
            of: #"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"#,
            options: .regularExpression
        ) != nil
    }

    private func sha256(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
}

private struct GitHubRelease: Decodable {
    let tagName: String
    let draft: Bool
    let prerelease: Bool
    let assets: [GitHubReleaseAsset]

    enum CodingKeys: String, CodingKey {
        case tagName = "tag_name"
        case draft
        case prerelease
        case assets
    }
}

private struct GitHubReleaseAsset: Decodable {
    let name: String
    let size: Int
    let browserDownloadURL: URL
    let digest: String

    enum CodingKeys: String, CodingKey {
        case name
        case size
        case browserDownloadURL = "browser_download_url"
        case digest
    }
}

enum FirmwareReleaseError: Error, Equatable {
    case httpsRequired
    case invalidResponse
    case releaseUnavailable
    case assetMissing
    case untrustedAssetURL
    case unsupportedManifest
    case releaseIdentityMismatch
    case sizeMismatch
    case sha256Mismatch
    case signatureSizeMismatch
    case signatureSha256Mismatch
    case invalidSignature
}
