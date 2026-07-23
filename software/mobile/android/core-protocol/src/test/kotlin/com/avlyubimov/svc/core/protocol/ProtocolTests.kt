package com.avlyubimov.svc.core.protocol

import java.security.MessageDigest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class ProtocolTests {
    private val manifestJson = """
        {
          "schemaVersion": 1,
          "releaseVersion": "0.1.0",
          "channel": "dev",
          "minimumMobileVersion": "0.1.0",
          "components": [{
            "target": "stm32-main",
            "version": "0.1.0",
            "hardware": ["LB-100-REV1"],
            "protocolVersion": 1,
            "file": "candidate.bin",
            "size": 3,
            "sha256": "placeholder",
            "signature": "TEST-SIGNATURE-NOT-FOR-PRODUCTION",
            "minimumBootloader": "0.1.0"
          }]
        }
    """.trimIndent()

    @Test
    fun rejectsIncompatibleProtocolAndHardware() {
        val manifest = FirmwareManifestParser().parse(manifestJson)
        assertFailsWith<ManifestCompatibilityException> {
            manifest.compatibleComponent("stm32-main", "LB-100-REV2", 1, "0.1.0")
        }
        assertFailsWith<ManifestCompatibilityException> {
            manifest.compatibleComponent("stm32-main", "LB-100-REV1", 2, "0.1.0")
        }
    }

    @Test
    fun rejectsWrongHashAndSignature() {
        val bytes = byteArrayOf(1, 2, 3)
        val component = FirmwareManifestParser().parse(manifestJson).components.single()
        assertFailsWith<IllegalArgumentException> {
            validateArtifact(component, bytes, SignatureVerifier { _, _ -> true })
        }
        val digest = MessageDigest.getInstance("SHA-256")
            .digest(bytes)
            .joinToString("") { "%02x".format(it) }
        val withDigest = component.copy(sha256 = digest)
        assertFailsWith<IllegalArgumentException> {
            validateArtifact(withDigest, bytes, SignatureVerifier { _, _ -> false })
        }
    }

    @Test
    fun chunkRoundTripAndCorruptionDetection() {
        val chunk = BleChunk(9, 512, 3, byteArrayOf(4, 5, 6, 7))
        val encoded = BleChunkCodec.encode(chunk)
        val decoded = BleChunkCodec.decode(encoded)
        assertEquals(chunk.transferId, decoded.transferId)
        assertEquals(chunk.offset, decoded.offset)
        assertEquals(chunk.sequence, decoded.sequence)
        assertContentEquals(chunk.payload, decoded.payload)

        encoded[encoded.lastIndex] = (encoded.last() + 1).toByte()
        assertFailsWith<IllegalArgumentException> {
            BleChunkCodec.decode(encoded)
        }
    }
}
