package com.avlyubimov.svc.core.ble

import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.DiscoveredDevice
import kotlinx.coroutines.flow.StateFlow

interface BleTransport {
    val connectionState: StateFlow<ConnectionState>
    val devices: StateFlow<List<DiscoveredDevice>>
    fun startScan()
    fun stopScan()
    fun connect(deviceId: String)
    fun write(characteristicUuid: String, data: ByteArray)
}
