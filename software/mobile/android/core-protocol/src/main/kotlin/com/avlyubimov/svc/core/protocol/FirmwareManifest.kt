package com.avlyubimov.svc.core.protocol

import java.security.MessageDigest
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class FirmwareManifest(
    val schemaVersion: Int,
    val releaseVersion: String,
    val channel: String,
    val minimumMobileVersion: String,
    val components: List<FirmwareComponent>,
) {
    fun compatibleComponent(
        target: String,
        hardwareRevision: String,
        protocolVersion: Int,
        bootloaderVersion: String,
    ): FirmwareComponent {
        require(schemaVersion == 1) { "unsupported schema" }
        val component = components.singleOrNull { it.target == target }
            ?: throw ManifestCompatibilityException("target unavailable")
        if (hardwareRevision !in component.hardware) {
            throw ManifestCompatibilityException("hardware mismatch")
        }
        if (protocolVersion != component.protocolVersion) {
            throw ManifestCompatibilityException("protocol mismatch")
        }
        if (compareSemanticVersions(bootloaderVersion, component.minimumBootloader) < 0) {
            throw ManifestCompatibilityException("bootloader too old")
        }
        return component
    }
}

@Serializable
data class FirmwareComponent(
    val target: String,
    val version: String,
    val hardware: List<String>,
    val protocolVersion: Int,
    val file: String,
    val size: Long,
    val sha256: String,
    val signature: String,
    val minimumBootloader: String,
)

fun interface SignatureVerifier {
    fun verify(component: FirmwareComponent, bytes: ByteArray): Boolean
}

class FirmwareManifestParser(
    private val json: Json = Json { ignoreUnknownKeys = false },
) {
    fun parse(value: String): FirmwareManifest {
        val manifest = json.decodeFromString<FirmwareManifest>(value)
        require(manifest.schemaVersion == 1) { "unsupported schema" }
        require(manifest.components.isNotEmpty()) { "components are empty" }
        require(manifest.components.map { it.target }.distinct().size == manifest.components.size) {
            "duplicate target"
        }
        manifest.components.forEach {
            require(it.target == "stm32-main" || it.target == "e73-radio") {
                "unsupported target"
            }
            require(it.file.matches(Regex("^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"))) {
                "file must be a basename"
            }
            require(it.size >= 0) { "negative size" }
        }
        return manifest
    }
}

fun validateArtifact(
    component: FirmwareComponent,
    bytes: ByteArray,
    signatureVerifier: SignatureVerifier,
) {
    require(component.size == bytes.size.toLong()) { "size mismatch" }
    val digest = MessageDigest.getInstance("SHA-256")
        .digest(bytes)
        .joinToString("") { "%02x".format(it) }
    require(component.sha256 == digest) { "SHA-256 mismatch" }
    require(signatureVerifier.verify(component, bytes)) { "signature invalid" }
}

class ManifestCompatibilityException(message: String) : IllegalArgumentException(message)

private fun compareSemanticVersions(left: String, right: String): Int {
    val leftParts = left.substringBefore("-").split(".").map(String::toInt)
    val rightParts = right.substringBefore("-").split(".").map(String::toInt)
    require(leftParts.size == 3 && rightParts.size == 3) { "invalid semantic version" }
    return leftParts.zip(rightParts)
        .firstOrNull { (leftPart, rightPart) -> leftPart != rightPart }
        ?.let { (leftPart, rightPart) -> leftPart.compareTo(rightPart) }
        ?: 0
}
