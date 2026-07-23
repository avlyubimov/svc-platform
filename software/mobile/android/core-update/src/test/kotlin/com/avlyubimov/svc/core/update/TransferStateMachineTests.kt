package com.avlyubimov.svc.core.update

import com.avlyubimov.svc.core.protocol.BleChunk
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class TransferStateMachineTests {
    @Test
    fun interruptionResumeAndRepeatedBlockAreSafe() {
        val stateMachine = TransferStateMachine()
        val first = BleChunk(7, 0, 0, byteArrayOf(1, 2, 3))
        stateMachine.begin(7)
        assertTrue(stateMachine.accept(first))
        assertTrue(stateMachine.accept(first))
        assertEquals(3, stateMachine.progress.committedOffset)

        stateMachine.interrupt()
        val resume = stateMachine.resume(7)
        assertEquals(1, resume.nextSequence)
        assertTrue(stateMachine.accept(BleChunk(7, 3, 1, byteArrayOf(4, 5))))
        stateMachine.verify(fileComplete = true, hashValid = true, signatureValid = true)
        assertEquals(TransferState.VERIFIED, stateMachine.progress.state)
    }

    @Test
    fun rejectsOutOfOrderBlock() {
        val stateMachine = TransferStateMachine()
        stateMachine.begin(9)
        assertFalse(stateMachine.accept(BleChunk(9, 12, 4, byteArrayOf(1))))
        assertEquals(0, stateMachine.progress.committedOffset)
    }
}
