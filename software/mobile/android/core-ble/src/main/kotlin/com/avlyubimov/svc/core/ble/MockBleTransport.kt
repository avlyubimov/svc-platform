package com.avlyubimov.svc.core.ble

import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.DiscoveredDevice
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class MockBleTransport : BleTransport {
    private val mockDevice = DiscoveredDevice(
        id = "D78F3100-2AE5-4B2B-9294-0F299E60AA01",
        name = "SVC-MOCK-001",
        signalStrength = -44,
    )
    private val mutableState = MutableStateFlow(ConnectionState.DISCONNECTED)
    private val mutableDevices = MutableStateFlow<List<DiscoveredDevice>>(emptyList())
    val writes = mutableListOf<Pair<String, ByteArray>>()

    override val connectionState: StateFlow<ConnectionState> = mutableState.asStateFlow()
    override val devices: StateFlow<List<DiscoveredDevice>> = mutableDevices.asStateFlow()

    override fun startScan() {
        mutableState.value = ConnectionState.SCANNING
        mutableDevices.value = listOf(mockDevice)
    }

    override fun stopScan() = Unit

    override fun connect(deviceId: String) {
        mutableState.value = if (deviceId == mockDevice.id) {
            ConnectionState.CONNECTED
        } else {
            ConnectionState.DISCONNECTED
        }
    }

    override fun write(characteristicUuid: String, data: ByteArray) {
        writes += characteristicUuid to data.copyOf()
    }
}
