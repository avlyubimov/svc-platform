package com.avlyubimov.svc.core.update

import com.avlyubimov.svc.core.protocol.BleChunk
import java.util.zip.CRC32

enum class TransferState {
    IDLE,
    RECEIVING,
    INTERRUPTED,
    VERIFIED,
    FAILED,
}

data class TransferProgress(
    val state: TransferState = TransferState.IDLE,
    val transferId: Long = 0,
    val committedOffset: Long = 0,
    val nextSequence: Long = 0,
    val lastPayloadCrc: Long? = null,
)

class TransferStateMachine {
    var progress = TransferProgress()
        private set

    fun begin(transferId: Long) {
        require(progress.state == TransferState.IDLE || progress.state == TransferState.FAILED)
        progress = TransferProgress(
            state = TransferState.RECEIVING,
            transferId = transferId,
        )
    }

    fun accept(chunk: BleChunk): Boolean {
        require(progress.state == TransferState.RECEIVING)
        require(chunk.transferId == progress.transferId)
        val crc = CRC32().apply { update(chunk.payload) }.value
        if (
            chunk.sequence + 1 == progress.nextSequence &&
            chunk.offset + chunk.payload.size == progress.committedOffset &&
            crc == progress.lastPayloadCrc
        ) {
            return true
        }
        if (
            chunk.sequence != progress.nextSequence ||
            chunk.offset != progress.committedOffset
        ) {
            return false
        }
        progress = progress.copy(
            committedOffset = progress.committedOffset + chunk.payload.size,
            nextSequence = progress.nextSequence + 1,
            lastPayloadCrc = crc,
        )
        return true
    }

    fun interrupt() {
        require(progress.state == TransferState.RECEIVING)
        progress = progress.copy(state = TransferState.INTERRUPTED)
    }

    fun resume(transferId: Long): TransferProgress {
        require(progress.state == TransferState.INTERRUPTED)
        require(progress.transferId == transferId)
        progress = progress.copy(state = TransferState.RECEIVING)
        return progress
    }

    fun verify(fileComplete: Boolean, hashValid: Boolean, signatureValid: Boolean) {
        require(progress.state == TransferState.RECEIVING)
        progress = progress.copy(
            state = if (fileComplete && hashValid && signatureValid) {
                TransferState.VERIFIED
            } else {
                TransferState.FAILED
            },
        )
    }
}
