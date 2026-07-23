package com.avlyubimov.svc.core.ble

import com.avlyubimov.svc.core.model.ConnectionState
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals

class MockBleTransportTests {
    @Test
    fun scansConnectsAndRecordsWrites() {
        val transport = MockBleTransport()
        transport.startScan()
        assertEquals(ConnectionState.SCANNING, transport.connectionState.value)
        val device = transport.devices.value.single()
        transport.connect(device.id)
        assertEquals(ConnectionState.CONNECTED, transport.connectionState.value)
        transport.write("9f9e7101-7b7a-4f4f-a001-535643000001", byteArrayOf(1, 2))
        assertEquals(1, transport.writes.size)
        assertContentEquals(byteArrayOf(1, 2), transport.writes.single().second)
    }
}
