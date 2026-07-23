package com.avlyubimov.svc.core.model

import kotlinx.coroutines.flow.StateFlow

enum class ConnectionState {
    DISCONNECTED,
    SCANNING,
    CONNECTED,
}

data class DiscoveredDevice(
    val id: String,
    val name: String,
    val signalStrength: Int,
)

data class DeviceSnapshot(
    val connectionState: ConnectionState,
    val telemetry: TelemetrySnapshot,
    val events: List<String>,
)

interface DeviceRepository {
    val snapshot: StateFlow<DeviceSnapshot>
    suspend fun discover(): List<DiscoveredDevice>
    suspend fun connect(id: String)
    suspend fun refresh()
}
