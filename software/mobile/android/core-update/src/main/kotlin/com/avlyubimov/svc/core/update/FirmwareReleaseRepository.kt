package com.avlyubimov.svc.core.update

import com.avlyubimov.svc.core.protocol.FirmwareComponent
import com.avlyubimov.svc.core.protocol.FirmwareManifest
import com.avlyubimov.svc.core.protocol.FirmwareManifestParser
import com.avlyubimov.svc.core.protocol.SignatureVerifier
import com.avlyubimov.svc.core.protocol.validateArtifact
import java.net.HttpURLConnection
import java.net.URI
import java.security.KeyFactory
import java.security.MessageDigest
import java.security.Signature
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import java.security.spec.X509EncodedKeySpec
import java.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

enum class FirmwareReleaseChannel(val manifestChannel: String) {
    STABLE("stable"),
    BETA("beta"),
    TEST("dev"),
}

interface FirmwareReleaseRepository {
    suspend fun fetchManifest(
        channel: FirmwareReleaseChannel = FirmwareReleaseChannel.STABLE,
    ): FirmwareManifest
}

class MockFirmwareReleaseRepository : FirmwareReleaseRepository {
    override suspend fun fetchManifest(channel: FirmwareReleaseChannel): FirmwareManifest =
        FirmwareManifest(
            schemaVersion = 1,
            releaseVersion = "0.1.0-test.1",
            releaseTag = "svc-v0.1.0-test.1",
            channel = "dev",
            minimumMobileVersion = "0.1.0",
            components = emptyList(),
        )
}

data class ReleaseHttpResponse(
    val statusCode: Int,
    val body: ByteArray,
)

fun interface ReleaseHttpClient {
    fun get(uri: URI, accept: String): ReleaseHttpResponse
}

class UrlConnectionReleaseHttpClient : ReleaseHttpClient {
    override fun get(uri: URI, accept: String): ReleaseHttpResponse {
        require(uri.scheme == "https") { "firmware release API requires HTTPS" }
        val connection = uri.toURL().openConnection() as HttpURLConnection
        connection.connectTimeout = 10_000
        connection.readTimeout = 30_000
        connection.instanceFollowRedirects = true
        connection.setRequestProperty("Accept", accept)
        connection.setRequestProperty("X-GitHub-Api-Version", "2022-11-28")
        val status = connection.responseCode
        val stream = if (status in 200..299) connection.inputStream else connection.errorStream
        return ReleaseHttpResponse(status, stream?.use { it.readBytes() } ?: byteArrayOf())
    }
}

class RsaPssReleaseSignatureVerifier(
    subjectPublicKeyInfoPem: String,
    private val allowedKeyId: String,
) : SignatureVerifier {
    private val publicKey = KeyFactory.getInstance("RSA").generatePublic(
        X509EncodedKeySpec(
            Base64.getDecoder().decode(
                subjectPublicKeyInfoPem
                    .replace("-----BEGIN PUBLIC KEY-----", "")
                    .replace("-----END PUBLIC KEY-----", "")
                    .filterNot(Char::isWhitespace),
            ),
        ),
    )

    override fun verify(keyId: String, bytes: ByteArray, signature: ByteArray): Boolean {
        if (keyId != allowedKeyId) {
            return false
        }
        val verifier = Signature.getInstance("RSASSA-PSS")
        verifier.initVerify(publicKey)
        verifier.setParameter(
            PSSParameterSpec(
                "SHA-256",
                "MGF1",
                MGF1ParameterSpec.SHA256,
                32,
                1,
            ),
        )
        verifier.update(bytes)
        return verifier.verify(signature)
    }
}

class GitHubFirmwareReleaseRepository(
    private val owner: String,
    private val repository: String,
    private val signatureVerifier: SignatureVerifier,
    private val httpClient: ReleaseHttpClient = UrlConnectionReleaseHttpClient(),
    private val parser: FirmwareManifestParser = FirmwareManifestParser(),
    private val json: Json = Json { ignoreUnknownKeys = true },
    private val apiBaseUri: URI = URI("https://api.github.com"),
) : FirmwareReleaseRepository {
    override suspend fun fetchManifest(
        channel: FirmwareReleaseChannel,
    ): FirmwareManifest = withContext(Dispatchers.IO) {
        val release = fetchRelease(channel)
        val manifestAsset = release.asset("firmware-manifest.json")
        val manifestBytes = download(manifestAsset)
        val manifest = parser.parse(manifestBytes.decodeToString())
        validateReleaseIdentity(manifest, release.tagName, channel)
        manifest.components.forEach { component ->
            val image = download(release.asset(component.file))
            val signature = download(release.asset(component.releaseSignature.file))
            validateArtifact(component, image, signature, signatureVerifier)
        }
        manifest
    }

    private fun fetchRelease(channel: FirmwareReleaseChannel): GitHubRelease {
        if (channel == FirmwareReleaseChannel.STABLE) {
            val uri = apiBaseUri.resolve("/repos/$owner/$repository/releases/latest")
            return json.decodeFromString<GitHubRelease>(
                requestJson(uri).decodeToString(),
            ).also {
                require(!it.draft && !it.prerelease) {
                    "stable release metadata is invalid"
                }
            }
        }
        val uri = apiBaseUri.resolve("/repos/$owner/$repository/releases?per_page=100")
        return json.decodeFromString<List<GitHubRelease>>(requestJson(uri).decodeToString())
            .firstOrNull {
                !it.draft &&
                    it.prerelease &&
                    releaseTagMatches(it.tagName, channel)
            }
            ?: throw FirmwareReleaseException("release unavailable")
    }

    private fun requestJson(uri: URI): ByteArray {
        val response = httpClient.get(uri, "application/vnd.github+json")
        require(response.statusCode in 200..299) { "GitHub API request failed" }
        return response.body
    }

    private fun download(asset: GitHubReleaseAsset): ByteArray {
        val uri = URI(asset.browserDownloadUrl)
        require(uri.scheme == "https" && uri.host == "github.com") {
            "untrusted release asset URL"
        }
        val response = httpClient.get(uri, "application/octet-stream")
        require(response.statusCode in 200..299) { "asset download failed" }
        require(response.body.size.toLong() == asset.size) { "asset size mismatch" }
        require(asset.digest == "sha256:${sha256(response.body)}") {
            "asset SHA-256 mismatch"
        }
        return response.body
    }

    private fun validateReleaseIdentity(
        manifest: FirmwareManifest,
        releaseTag: String,
        requestedChannel: FirmwareReleaseChannel,
    ) {
        require(manifest.releaseTag == releaseTag) { "release tag mismatch" }
        require(manifest.releaseTag == "svc-v${manifest.releaseVersion}") {
            "release tag/version mismatch"
        }
        require(manifest.channel == requestedChannel.manifestChannel) {
            "release channel mismatch"
        }
        require(releaseTagMatches(releaseTag, requestedChannel)) {
            "release tag/channel mismatch"
        }
        require(manifest.components.all { it.version == manifest.releaseVersion }) {
            "component version mismatch"
        }
    }

    private fun releaseTagMatches(tag: String, channel: FirmwareReleaseChannel): Boolean {
        val core = "(?:0|[1-9][0-9]*)\\.(?:0|[1-9][0-9]*)\\.(?:0|[1-9][0-9]*)"
        val pattern = when (channel) {
            FirmwareReleaseChannel.STABLE -> "^svc-v$core$"
            FirmwareReleaseChannel.BETA -> "^svc-v$core-beta\\.(?:0|[1-9][0-9]*)$"
            FirmwareReleaseChannel.TEST -> "^svc-v$core-test\\.(?:0|[1-9][0-9]*)$"
        }
        return Regex(pattern).matches(tag)
    }

    private fun sha256(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256")
            .digest(bytes)
            .joinToString("") { "%02x".format(it) }
}

@Serializable
private data class GitHubRelease(
    @SerialName("tag_name")
    val tagName: String,
    val draft: Boolean,
    val prerelease: Boolean,
    val assets: List<GitHubReleaseAsset>,
) {
    fun asset(name: String): GitHubReleaseAsset =
        assets.singleOrNull { it.name == name }
            ?: throw FirmwareReleaseException("release asset missing: $name")
}

@Serializable
private data class GitHubReleaseAsset(
    val name: String,
    val size: Long,
    @SerialName("browser_download_url")
    val browserDownloadUrl: String,
    val digest: String,
)

class FirmwareReleaseException(message: String) : IllegalArgumentException(message)
