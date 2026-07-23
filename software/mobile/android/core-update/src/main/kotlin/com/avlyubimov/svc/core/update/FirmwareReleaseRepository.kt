package com.avlyubimov.svc.core.update

import com.avlyubimov.svc.core.protocol.FirmwareManifest
import com.avlyubimov.svc.core.protocol.FirmwareManifestParser
import java.net.URI
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

interface FirmwareReleaseRepository {
    suspend fun fetchManifest(): FirmwareManifest
}

class MockFirmwareReleaseRepository : FirmwareReleaseRepository {
    override suspend fun fetchManifest(): FirmwareManifest = FirmwareManifest(
        schemaVersion = 1,
        releaseVersion = "0.1.0",
        channel = "dev",
        minimumMobileVersion = "0.1.0",
        components = emptyList(),
    )
}

class GitHubFirmwareReleaseRepository(
    manifestUrl: String,
    private val parser: FirmwareManifestParser = FirmwareManifestParser(),
) : FirmwareReleaseRepository {
    private val uri = URI(manifestUrl).also {
        require(it.scheme == "https") { "firmware manifest requires HTTPS" }
    }

    override suspend fun fetchManifest(): FirmwareManifest = withContext(Dispatchers.IO) {
        val connection = uri.toURL().openConnection()
        connection.connectTimeout = 10_000
        connection.readTimeout = 20_000
        connection.getInputStream().bufferedReader().use {
            parser.parse(it.readText())
        }
    }
}
