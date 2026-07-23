package com.avlyubimov.svc.mobile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.avlyubimov.svc.core.model.ChannelTelemetry
import com.avlyubimov.svc.core.model.DeviceRepository
import com.avlyubimov.svc.core.model.DiscoveredDevice
import com.avlyubimov.svc.core.model.Measurement
import com.avlyubimov.svc.core.model.TelemetrySnapshot
import com.avlyubimov.svc.core.update.OtaPolicy
import kotlinx.coroutines.launch

private enum class Screen(val title: String) {
    PAIRING("Search and pairing"),
    DASHBOARD("Dashboard"),
    CHANNELS("Power channels"),
    DIAGNOSTICS("Diagnostics"),
    CAN("CAN telemetry"),
    EVENTS("Event log"),
    DEVICE("Device information"),
    FIRMWARE("Firmware update"),
    SETTINGS("Settings and calibration"),
}

@Composable
@OptIn(ExperimentalMaterial3Api::class)
fun SVCMobileApp(repository: DeviceRepository) {
    val device by repository.snapshot.collectAsStateWithLifecycle()
    var selectedScreen by remember { mutableStateOf<Screen?>(null) }
    var confirmInstall by remember { mutableStateOf(false) }
    var discoveredDevices by remember { mutableStateOf<List<DiscoveredDevice>>(emptyList()) }
    val coroutineScope = rememberCoroutineScope()

    MaterialTheme {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = {
                        Text(selectedScreen?.title ?: "SVC Mobile")
                    },
                    navigationIcon = {
                        if (selectedScreen != null) {
                            TextButton(onClick = { selectedScreen = null }) {
                                Text("Back")
                            }
                        }
                    },
                )
            },
        ) { padding ->
            if (selectedScreen == null) {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    items(Screen.entries) { screen ->
                        Button(
                            onClick = { selectedScreen = screen },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text(screen.title)
                        }
                    }
                }
            } else {
                val modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp)
                when (selectedScreen) {
                    Screen.PAIRING -> PairingScreen(
                        state = device.connectionState.name,
                        devices = discoveredDevices,
                        modifier = modifier,
                        onScan = {
                            coroutineScope.launch {
                                discoveredDevices = repository.discover()
                            }
                        },
                        onConnect = { selected ->
                            coroutineScope.launch {
                                repository.connect(selected.id)
                            }
                        },
                    )
                    Screen.DASHBOARD -> DashboardScreen(device.telemetry, modifier)
                    Screen.CHANNELS -> ChannelsScreen(device.telemetry.channels, modifier)
                    Screen.DIAGNOSTICS -> DiagnosticsScreen(device.telemetry, modifier)
                    Screen.CAN -> CanScreen(device.telemetry, modifier)
                    Screen.EVENTS -> StringListScreen(device.events, modifier)
                    Screen.DEVICE -> DeviceScreen(device.telemetry, modifier)
                    Screen.FIRMWARE -> FirmwareScreen(
                        telemetry = device.telemetry,
                        modifier = modifier,
                        onInstall = { confirmInstall = true },
                    )
                    Screen.SETTINGS -> SettingsScreen(modifier)
                    null -> Unit
                }
            }
        }

        if (confirmInstall) {
            AlertDialog(
                onDismissRequest = { confirmInstall = false },
                title = { Text("Confirm firmware installation") },
                text = {
                    Text("The mock scaffold performs no real device action.")
                },
                confirmButton = {
                    TextButton(onClick = { confirmInstall = false }) {
                        Text("Install")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { confirmInstall = false }) {
                        Text("Cancel")
                    }
                },
            )
        }
    }
}

@Composable
private fun PairingScreen(
    state: String,
    devices: List<DiscoveredDevice>,
    modifier: Modifier,
    onScan: () -> Unit,
    onConnect: (DiscoveredDevice) -> Unit,
) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Connection: $state")
        Button(onClick = onScan) {
            Text("Search mock SVC")
        }
        devices.forEach { device ->
            Button(
                onClick = { onConnect(device) },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("${device.name} (${device.signalStrength} dBm)")
            }
        }
        Text("BLE callbacks remain isolated in core-ble.")
    }
}

@Composable
private fun DashboardScreen(telemetry: TelemetrySnapshot, modifier: Modifier) {
    StringListScreen(
        listOf(
            "Battery: ${telemetry.batteryVoltage.display()}",
            "Total current: ${telemetry.totalCurrent.display()}",
            "Speed: ${telemetry.vehicle.speed.display()}",
            "Engine RPM: ${telemetry.vehicle.engineRpm.display()}",
            "Lean: ${telemetry.leanAngle.display()}",
        ),
        modifier,
    )
}

@Composable
private fun ChannelsScreen(channels: List<ChannelTelemetry>, modifier: Modifier) {
    LazyColumn(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items(channels) { channel ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp)) {
                    Text(channel.id, style = MaterialTheme.typography.titleMedium)
                    Text("State: ${channel.state.display()}")
                    Text("Current: ${channel.current.display()}")
                    Text("Fault: ${channel.fault.display()}")
                }
            }
        }
    }
}

@Composable
private fun DiagnosticsScreen(telemetry: TelemetrySnapshot, modifier: Modifier) {
    StringListScreen(
        telemetry.warnings.map { "${it.severity}: ${it.message}" } +
            telemetry.powerZoneTemperatures.map {
                "${it.id}: ${if (it.valid && !it.stale) "${it.value} ${it.unit}" else "Unavailable"}"
            },
        modifier,
    )
}

@Composable
private fun CanScreen(telemetry: TelemetrySnapshot, modifier: Modifier) {
    StringListScreen(
        listOf(
            "CAN1: ${telemetry.can1.state.display()}",
            "Speed: ${telemetry.vehicle.speed.display()}",
            "RPM: ${telemetry.vehicle.engineRpm.display()}",
            "Engine temperature: ${telemetry.vehicle.engineTemperature.display()}",
            "Instant fuel: ${telemetry.vehicle.instantFuelConsumption.display()}",
            "Average fuel: ${telemetry.vehicle.averageFuelConsumption.display()}",
            "Fuel level: ${telemetry.vehicle.fuelLevel.display()}",
        ),
        modifier,
    )
}

@Composable
private fun DeviceScreen(telemetry: TelemetrySnapshot, modifier: Modifier) {
    StringListScreen(
        listOf(
            "Device: ${telemetry.deviceId}",
            "STM32: ${telemetry.versions.stm32.display()}",
            "E73: ${telemetry.versions.e73.display()}",
            "Protocol: ${telemetry.versions.protocol.display()}",
            "SD card: ${telemetry.storage.sdCardState.display()}",
            "CAN logger: ${telemetry.storage.canLoggerState.display()}",
        ),
        modifier,
    )
}

@Composable
private fun FirmwareScreen(
    telemetry: TelemetrySnapshot,
    modifier: Modifier,
    onInstall: () -> Unit,
) {
    val denials = OtaPolicy.denials(telemetry)
    Column(modifier, verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Button(onClick = {}) {
            Text("Check GitHub release")
        }
        Text("Mock dev release 0.1.0")
        if (denials.isEmpty()) {
            Text("Device mock is eligible")
        } else {
            denials.forEach { Text("Denied: ${it.name.lowercase()}") }
        }
        Button(onClick = onInstall, enabled = denials.isEmpty()) {
            Text("Install with confirmation")
        }
        Text("Updates are never started automatically or from Android Auto.")
    }
}

@Composable
private fun SettingsScreen(modifier: Modifier) {
    StringListScreen(
        listOf(
            "Telemetry rate: mock",
            "Calibration: staged only",
            "No hardware value is changed",
        ),
        modifier,
    )
}

@Composable
private fun StringListScreen(values: List<String>, modifier: Modifier) {
    LazyColumn(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items(values) { value ->
            Row(Modifier.fillMaxWidth()) {
                Text(value)
            }
        }
    }
}

private fun <T> Measurement<T>.display(): String =
    if (isUsable && value != null) {
        "$value ${if (unit in setOf("state", "fault")) "" else unit}".trim()
    } else {
        "Unavailable"
    }
