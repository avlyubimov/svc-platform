package com.avlyubimov.svc.core.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.zip.CRC32

data class BleChunk(
    val transferId: Long,
    val offset: Long,
    val sequence: Long,
    val payload: ByteArray,
)

object BleChunkCodec {
    const val HEADER_SIZE = 18

    fun encode(chunk: BleChunk): ByteArray {
        require(chunk.transferId in 0..UInt.MAX_VALUE.toLong())
        require(chunk.offset in 0..UInt.MAX_VALUE.toLong())
        require(chunk.sequence in 0..UInt.MAX_VALUE.toLong())
        require(chunk.payload.size <= UShort.MAX_VALUE.toInt())
        val crc = CRC32().apply { update(chunk.payload) }.value
        return ByteBuffer.allocate(HEADER_SIZE + chunk.payload.size)
            .order(ByteOrder.LITTLE_ENDIAN)
            .putInt(chunk.transferId.toInt())
            .putInt(chunk.offset.toInt())
            .putInt(chunk.sequence.toInt())
            .putShort(chunk.payload.size.toShort())
            .putInt(crc.toInt())
            .put(chunk.payload)
            .array()
    }

    fun decode(bytes: ByteArray): BleChunk {
        require(bytes.size >= HEADER_SIZE) { "truncated header" }
        val buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        val transferId = buffer.int.toUInt().toLong()
        val offset = buffer.int.toUInt().toLong()
        val sequence = buffer.int.toUInt().toLong()
        val payloadLength = buffer.short.toUShort().toInt()
        val expectedCrc = buffer.int.toUInt().toLong()
        require(bytes.size == HEADER_SIZE + payloadLength) { "length mismatch" }
        val payload = ByteArray(payloadLength)
        buffer.get(payload)
        val actualCrc = CRC32().apply { update(payload) }.value
        require(actualCrc == expectedCrc) { "CRC mismatch" }
        return BleChunk(transferId, offset, sequence, payload)
    }
}
