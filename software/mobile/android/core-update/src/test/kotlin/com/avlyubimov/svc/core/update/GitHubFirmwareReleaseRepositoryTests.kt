package com.avlyubimov.svc.core.update

import com.avlyubimov.svc.core.protocol.SignatureVerifier
import java.net.URI
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.Signature
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import java.util.Base64
import kotlinx.coroutines.runBlocking
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class GitHubFirmwareReleaseRepositoryTests {
    @Test
    fun stableUsesLatestAndVerifiesEveryAsset() = runBlocking {
        val fixture = releaseFixture("0.1.0", "stable", prerelease = false)
        val client = FakeReleaseHttpClient(fixture.responses)
        val repository = repository(client, SignatureVerifier { _, _, _ -> true })

        val manifest = repository.fetchManifest(FirmwareReleaseChannel.STABLE)

        assertEquals("svc-v0.1.0", manifest.releaseTag)
        assertTrue(
            client.requested.first().endsWith(
                "/repos/avlyubimov/svc-platform/releases/latest",
            ),
        )
        assertEquals(4, client.requested.size)
    }

    @Test
    fun betaAndTestSelectMatchingPrereleases() = runBlocking {
        val beta = releaseFixture("0.2.0-beta.1", "beta", prerelease = true)
        val test = releaseFixture("0.2.0-test.1", "dev", prerelease = true)
        val listUrl =
            "https://api.github.com/repos/avlyubimov/svc-platform/releases?per_page=100"
        val releaseList = "[${beta.releaseJson},${test.releaseJson}]".encodeToByteArray()
        val sharedResponses = beta.responses + test.responses + mapOf(
            listUrl to ReleaseHttpResponse(200, releaseList),
        )

        val betaManifest = repository(
            FakeReleaseHttpClient(sharedResponses),
            SignatureVerifier { _, _, _ -> true },
        ).fetchManifest(FirmwareReleaseChannel.BETA)
        val testManifest = repository(
            FakeReleaseHttpClient(sharedResponses),
            SignatureVerifier { _, _, _ -> true },
        ).fetchManifest(FirmwareReleaseChannel.TEST)

        assertEquals("svc-v0.2.0-beta.1", betaManifest.releaseTag)
        assertEquals("svc-v0.2.0-test.1", testManifest.releaseTag)
    }

    @Test
    fun invalidDetachedSignatureFailsClosed() = runBlocking {
        val fixture = releaseFixture("0.1.0", "stable", prerelease = false)
        val repository = repository(
            FakeReleaseHttpClient(fixture.responses),
            SignatureVerifier { _, _, _ -> false },
        )

        assertFailsWith<IllegalArgumentException> {
            repository.fetchManifest(FirmwareReleaseChannel.STABLE)
        }
    }

    @Test
    fun rsaPssVerifierRejectsTamperedPayload() {
        val keyPair = KeyPairGenerator.getInstance("RSA").apply {
            initialize(2048)
        }.generateKeyPair()
        val payload = "review payload".encodeToByteArray()
        val signer = Signature.getInstance("RSASSA-PSS").apply {
            initSign(keyPair.private)
            setParameter(rsaPssParameters())
            update(payload)
        }
        val signature = signer.sign()
        val publicKeyPem = Base64.getEncoder().encodeToString(keyPair.public.encoded)
        val verifier = RsaPssReleaseSignatureVerifier(
            subjectPublicKeyInfoPem = """
                -----BEGIN PUBLIC KEY-----
                $publicKeyPem
                -----END PUBLIC KEY-----
            """.trimIndent(),
            allowedKeyId = "TEST_KEY_NOT_FOR_PRODUCTION",
        )

        assertTrue(
            verifier.verify(
                "TEST_KEY_NOT_FOR_PRODUCTION",
                payload,
                signature,
            ),
        )
        assertTrue(
            !verifier.verify(
                "TEST_KEY_NOT_FOR_PRODUCTION",
                payload + byteArrayOf(0),
                signature,
            ),
        )
    }

    private fun repository(
        client: ReleaseHttpClient,
        verifier: SignatureVerifier,
    ) = GitHubFirmwareReleaseRepository(
        owner = "avlyubimov",
        repository = "svc-platform",
        signatureVerifier = verifier,
        httpClient = client,
    )

    private fun releaseFixture(
        version: String,
        channel: String,
        prerelease: Boolean,
    ): ReleaseFixture {
        val tag = "svc-v$version"
        val image = "review-$version".encodeToByteArray()
        val signature = "signature-$version".encodeToByteArray()
        val imageName = "svc-e73-radio-$version.review.bin"
        val signatureName = "$imageName.release.sig"
        val imageUrl = "https://github.com/assets/$imageName"
        val signatureUrl = "https://github.com/assets/$signatureName"
        val manifest = """
            {
              "schemaVersion": 1,
              "releaseVersion": "$version",
              "releaseTag": "$tag",
              "channel": "$channel",
              "minimumMobileVersion": "0.1.0",
              "components": [{
                "target": "e73-radio",
                "version": "$version",
                "hardware": ["LB-100-REV1"],
                "protocolVersion": 1,
                "file": "$imageName",
                "size": ${image.size},
                "sha256": "${sha256(image)}",
                "imageFormat": "review-raw",
                "installable": false,
                "releaseSignature": {
                  "algorithm": "rsa-pss-sha256",
                  "file": "$signatureName",
                  "size": ${signature.size},
                  "sha256": "${sha256(signature)}",
                  "keyId": "TEST_KEY_NOT_FOR_PRODUCTION"
                },
                "minimumBootloader": "0.1.0"
              }]
            }
        """.trimIndent().encodeToByteArray()
        val manifestUrl = "https://github.com/assets/$tag-firmware-manifest.json"
        val releaseJson = """
            {
              "tag_name": "$tag",
              "draft": false,
              "prerelease": $prerelease,
              "assets": [
                {
                  "name": "firmware-manifest.json",
                  "size": ${manifest.size},
                  "browser_download_url": "$manifestUrl",
                  "digest": "sha256:${sha256(manifest)}"
                },
                {
                  "name": "$imageName",
                  "size": ${image.size},
                  "browser_download_url": "$imageUrl",
                  "digest": "sha256:${sha256(image)}"
                },
                {
                  "name": "$signatureName",
                  "size": ${signature.size},
                  "browser_download_url": "$signatureUrl",
                  "digest": "sha256:${sha256(signature)}"
                }
              ]
            }
        """.trimIndent()
        val latestUrl =
            "https://api.github.com/repos/avlyubimov/svc-platform/releases/latest"
        return ReleaseFixture(
            releaseJson = releaseJson,
            responses = mapOf(
                latestUrl to ReleaseHttpResponse(200, releaseJson.encodeToByteArray()),
                manifestUrl to ReleaseHttpResponse(200, manifest),
                imageUrl to ReleaseHttpResponse(200, image),
                signatureUrl to ReleaseHttpResponse(200, signature),
            ),
        )
    }

    private fun sha256(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256")
            .digest(bytes)
            .joinToString("") { "%02x".format(it) }

    private fun rsaPssParameters() = PSSParameterSpec(
        "SHA-256",
        "MGF1",
        MGF1ParameterSpec.SHA256,
        32,
        1,
    )
}

private data class ReleaseFixture(
    val releaseJson: String,
    val responses: Map<String, ReleaseHttpResponse>,
)

private class FakeReleaseHttpClient(
    private val responses: Map<String, ReleaseHttpResponse>,
) : ReleaseHttpClient {
    val requested = mutableListOf<String>()

    override fun get(uri: URI, accept: String): ReleaseHttpResponse {
        requested += uri.toString()
        return responses.getValue(uri.toString())
    }
}
