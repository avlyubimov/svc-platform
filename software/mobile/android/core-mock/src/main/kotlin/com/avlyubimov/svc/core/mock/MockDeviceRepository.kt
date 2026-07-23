package com.avlyubimov.svc.core.mock

import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.DeviceRepository
import com.avlyubimov.svc.core.model.DeviceSnapshot
import com.avlyubimov.svc.core.model.DiscoveredDevice
import com.avlyubimov.svc.core.model.TelemetrySnapshot
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.Json

class MockDeviceRepository(
    json: Json = Json { ignoreUnknownKeys = false },
) : DeviceRepository {
    private val telemetry = javaClass.classLoader
        .getResourceAsStream("device-v1.json")
        ?.bufferedReader()
        ?.use { json.decodeFromString<TelemetrySnapshot>(it.readText()) }
        ?: error("device-v1.json is missing")

    private val mutableSnapshot = MutableStateFlow(
        DeviceSnapshot(
            connectionState = ConnectionState.DISCONNECTED,
            telemetry = telemetry,
            events = listOf(
                "Mock repository active",
                "CAN1 is listen-only",
                "SD card is unavailable",
            ),
        ),
    )

    override val snapshot: StateFlow<DeviceSnapshot> = mutableSnapshot.asStateFlow()

    override suspend fun discover(): List<DiscoveredDevice> = listOf(
        DiscoveredDevice(
            id = "D78F3100-2AE5-4B2B-9294-0F299E60AA01",
            name = telemetry.deviceId,
            signalStrength = -46,
        ),
    )

    override suspend fun connect(id: String) {
        mutableSnapshot.value = mutableSnapshot.value.copy(
            connectionState = ConnectionState.CONNECTED,
        )
    }

    override suspend fun refresh() {
        mutableSnapshot.value = mutableSnapshot.value.copy(telemetry = telemetry)
    }
}
