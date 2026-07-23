import CryptoKit
import Foundation
import XCTest
@testable import SVCMobile

final class GitHubFirmwareReleaseRepositoryTests: XCTestCase {
    override func tearDown() {
        MockReleaseURLProtocol.handler = nil
        super.tearDown()
    }

    func testStableUsesLatestAndVerifiesAssetsWithoutAuthorization() async throws {
        let fixture = makeFixture(
            version: "0.1.0",
            channel: "stable",
            prerelease: false
        )
        var requests: [URLRequest] = []
        MockReleaseURLProtocol.handler = { request in
            requests.append(request)
            return try fixture.response(for: request.url!)
        }
        let repository = makeRepository(verifierResult: true)

        let manifest = try await repository.fetchManifest(channel: .stable)

        XCTAssertEqual(manifest.releaseTag, "svc-v0.1.0")
        XCTAssertTrue(requests[0].url!.path.hasSuffix("/releases/latest"))
        XCTAssertTrue(requests.allSatisfy {
            $0.value(forHTTPHeaderField: "Authorization") == nil
        })
        XCTAssertEqual(requests.count, 4)
    }

    func testBetaAndTestSelectMatchingPrereleases() async throws {
        let beta = makeFixture(
            version: "0.2.0-beta.1",
            channel: "beta",
            prerelease: true
        )
        let test = makeFixture(
            version: "0.2.0-test.1",
            channel: "dev",
            prerelease: true
        )
        let listData = Data("[\(beta.releaseJSON),\(test.releaseJSON)]".utf8)
        MockReleaseURLProtocol.handler = { request in
            if request.url!.path.hasSuffix("/releases") {
                return (listData, 200)
            }
            if let response = beta.responses[request.url!] {
                return response
            }
            return try test.response(for: request.url!)
        }

        let betaManifest = try await makeRepository(
            verifierResult: true
        ).fetchManifest(channel: .beta)
        let testManifest = try await makeRepository(
            verifierResult: true
        ).fetchManifest(channel: .test)

        XCTAssertEqual(betaManifest.releaseTag, "svc-v0.2.0-beta.1")
        XCTAssertEqual(testManifest.releaseTag, "svc-v0.2.0-test.1")
    }

    func testInvalidDetachedSignatureFailsClosed() async {
        let fixture = makeFixture(
            version: "0.1.0",
            channel: "stable",
            prerelease: false
        )
        MockReleaseURLProtocol.handler = { request in
            try fixture.response(for: request.url!)
        }
        do {
            _ = try await makeRepository(
                verifierResult: false
            ).fetchManifest(channel: .stable)
            XCTFail("invalid signature was accepted")
        } catch {
            XCTAssertEqual(error as? FirmwareReleaseError, .invalidSignature)
        }
    }

    private func makeRepository(
        verifierResult: Bool
    ) -> GitHubFirmwareReleaseRepository {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockReleaseURLProtocol.self]
        return GitHubFirmwareReleaseRepository(
            owner: "avlyubimov",
            repository: "svc-platform",
            signatureVerifier: TestReleaseSignatureVerifier(
                result: verifierResult
            ),
            session: URLSession(configuration: configuration)
        )
    }

    private func makeFixture(
        version: String,
        channel: String,
        prerelease: Bool
    ) -> ReleaseFixture {
        let tag = "svc-v\(version)"
        let image = Data("review-\(version)".utf8)
        let signature = Data("signature-\(version)".utf8)
        let imageName = "svc-e73-radio-\(version).review.bin"
        let signatureName = "\(imageName).release.sig"
        let manifest = Data(
            """
            {
              "schemaVersion": 1,
              "releaseVersion": "\(version)",
              "releaseTag": "\(tag)",
              "channel": "\(channel)",
              "minimumMobileVersion": "0.1.0",
              "components": [{
                "target": "e73-radio",
                "version": "\(version)",
                "hardware": ["LB-100-REV1"],
                "protocolVersion": 1,
                "file": "\(imageName)",
                "size": \(image.count),
                "sha256": "\(sha256(image))",
                "imageFormat": "review-raw",
                "installable": false,
                "releaseSignature": {
                  "algorithm": "rsa-pss-sha256",
                  "file": "\(signatureName)",
                  "size": \(signature.count),
                  "sha256": "\(sha256(signature))",
                  "keyId": "TEST_KEY_NOT_FOR_PRODUCTION"
                },
                "minimumBootloader": "0.1.0"
              }]
            }
            """.utf8
        )
        let manifestURL = URL(
            string: "https://github.com/assets/\(tag)-firmware-manifest.json"
        )!
        let imageURL = URL(string: "https://github.com/assets/\(imageName)")!
        let signatureURL = URL(
            string: "https://github.com/assets/\(signatureName)"
        )!
        let releaseJSON = """
            {
              "tag_name": "\(tag)",
              "draft": false,
              "prerelease": \(prerelease),
              "assets": [
                {
                  "name": "firmware-manifest.json",
                  "size": \(manifest.count),
                  "browser_download_url": "\(manifestURL.absoluteString)",
                  "digest": "sha256:\(sha256(manifest))"
                },
                {
                  "name": "\(imageName)",
                  "size": \(image.count),
                  "browser_download_url": "\(imageURL.absoluteString)",
                  "digest": "sha256:\(sha256(image))"
                },
                {
                  "name": "\(signatureName)",
                  "size": \(signature.count),
                  "browser_download_url": "\(signatureURL.absoluteString)",
                  "digest": "sha256:\(sha256(signature))"
                }
              ]
            }
        """
        let latestURL = URL(
            string: "https://api.github.com/repos/avlyubimov/svc-platform/releases/latest"
        )!
        return ReleaseFixture(
            releaseJSON: releaseJSON,
            responses: [
                latestURL: (Data(releaseJSON.utf8), 200),
                manifestURL: (manifest, 200),
                imageURL: (image, 200),
                signatureURL: (signature, 200),
            ]
        )
    }

    private func sha256(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
}

private struct TestReleaseSignatureVerifier: FirmwareReleaseSignatureVerifying {
    let result: Bool

    func verify(
        data: Data,
        signature: Data,
        keyId: String,
        algorithm: String
    ) -> Bool {
        result
    }
}

private struct ReleaseFixture {
    let releaseJSON: String
    let responses: [URL: (Data, Int)]

    func response(for url: URL) throws -> (Data, Int) {
        try XCTUnwrap(responses[url])
    }
}

private final class MockReleaseURLProtocol: URLProtocol {
    static var handler: ((URLRequest) throws -> (Data, Int))?

    override class func canInit(with request: URLRequest) -> Bool {
        true
    }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest {
        request
    }

    override func startLoading() {
        do {
            let handler = try XCTUnwrap(Self.handler)
            let (data, statusCode) = try handler(request)
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: statusCode,
                httpVersion: nil,
                headerFields: nil
            )!
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}
