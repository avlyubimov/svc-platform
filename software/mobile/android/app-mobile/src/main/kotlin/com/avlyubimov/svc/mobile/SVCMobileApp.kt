package com.avlyubimov.svc.mobile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.avlyubimov.svc.core.model.ChannelTelemetry
import com.avlyubimov.svc.core.model.DeviceRepository
import com.avlyubimov.svc.core.model.DiscoveredDevice
import com.avlyubimov.svc.core.model.Measurement
import com.avlyubimov.svc.core.model.RideThemeMode
import com.avlyubimov.svc.core.model.TelemetrySnapshot
import com.avlyubimov.svc.core.model.VehiclePerformanceProfile
import com.avlyubimov.svc.core.update.OtaPolicy
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay

private enum class Screen(val title: String) {
    PAIRING("Search and pairing"),
    DASHBOARD("Dashboard"),
    CHANNELS("Power channels"),
    DIAGNOSTICS("Diagnostics"),
    CAN("CAN telemetry"),
    NAVIGATION("Navigation status"),
    EVENTS("Event log"),
    DEVICE("Device information"),
    FIRMWARE("Firmware update"),
    SETTINGS("Settings and calibration"),
}

@Composable
@OptIn(ExperimentalMaterial3Api::class)
fun SVCMobileApp(repository: DeviceRepository) {
    val context = LocalContext.current
    val brandCatalog = remember { MobileBrandCatalog.load(context) }
    val performanceCatalog = remember {
        MobileVehiclePerformanceCatalog.load(context)
    }
    val startupTimeline = remember { MobileStartupTimeline.load(context) }
    val appearance = remember { AppearancePreferences(context, brandCatalog) }
    val ridePreferences = remember {
        RidePreferences(context, performanceCatalog)
    }
    val device by repository.snapshot.collectAsStateWithLifecycle()
    var selectedScreen by remember {
        mutableStateOf<Screen?>(
            Screen.entries.firstOrNull { it.name == appearance.restoreScreen() }
                ?.takeIf { it.isRestorable }
                ?: Screen.DASHBOARD,
        )
    }
    var confirmInstall by remember { mutableStateOf(false) }
    var discoveredDevices by remember { mutableStateOf<List<DiscoveredDevice>>(emptyList()) }
    var isConnecting by remember { mutableStateOf(device.connectionState.name != "CONNECTED") }
    var showStartup by remember { mutableStateOf(true) }
    var startupReplayKey by remember { mutableStateOf(0) }
    var appearanceRevision by remember { mutableStateOf(0) }
    var rideRevision by remember { mutableStateOf(0) }
    val coroutineScope = rememberCoroutineScope()
    val brandPack = remember(appearanceRevision) { appearance.brandPack() }
    val vehicleProfile = remember(rideRevision) {
        ridePreferences.vehicleProfile()
    }
    val rideThemeMode = remember(rideRevision) { ridePreferences.themeMode }
    val rideThemeThresholds = remember(rideRevision) {
        ridePreferences.themeThresholds()
    }
    val criticalWarning = device.telemetry.warnings.firstOrNull {
        it.active && it.severity.equals("critical", ignoreCase = true)
    }

    androidx.compose.runtime.LaunchedEffect(Unit) {
        launch { appearance.brandPack() }
        launch { appearance.restoreScreen() }
        launch {
            discoveredDevices = repository.discover()
            delay(3_000)
            discoveredDevices.firstOrNull()?.let { repository.connect(it.id) }
            isConnecting = false
        }
    }

    MaterialTheme(
        colorScheme = androidx.compose.material3.darkColorScheme(
            background = MobileColors.Background,
            surface = MobileColors.Surface,
            primary = brandPack.accentColor.toComposeColor(),
            onBackground = MobileColors.PrimaryText,
            onSurface = MobileColors.PrimaryText,
            error = MobileColors.Critical,
        ),
    ) {
        Box(Modifier.fillMaxSize().background(MobileColors.Background)) {
            Scaffold(
                containerColor = MobileColors.Background,
            topBar = {
                TopAppBar(
                    title = {
                        Text(
                            if (selectedScreen == Screen.DASHBOARD) {
                                "SVC Ride"
                            } else {
                                selectedScreen?.title ?: "SVC Mobile"
                            },
                        )
                    },
                    navigationIcon = {
                        if (selectedScreen != null) {
                            TextButton(onClick = { selectedScreen = null }) {
                                Text("Menu")
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
                            onClick = {
                                selectedScreen = screen
                                if (screen.isRestorable) appearance.storeScreen(screen.name)
                            },
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
                    Screen.DASHBOARD -> RideDashboardScreen(
                        telemetry = device.telemetry,
                        connectionState = device.connectionState,
                        isConnecting = isConnecting,
                        profile = vehicleProfile,
                        themeMode = rideThemeMode,
                        themeThresholds = rideThemeThresholds,
                        reduceMotion = appearance.reduceMotionOverride ||
                            systemReduceMotion(context),
                        modifier = modifier,
                    )
                    Screen.CHANNELS -> ChannelsScreen(device.telemetry.channels, modifier)
                    Screen.DIAGNOSTICS -> DiagnosticsScreen(device.telemetry, modifier)
                    Screen.CAN -> CanScreen(device.telemetry, modifier)
                    Screen.NAVIGATION -> StringListScreen(
                        listOf("Navigation provider unavailable"),
                        modifier,
                    )
                    Screen.EVENTS -> StringListScreen(device.events, modifier)
                    Screen.DEVICE -> DeviceScreen(device.telemetry, modifier)
                    Screen.FIRMWARE -> FirmwareScreen(
                        telemetry = device.telemetry,
                        modifier = modifier,
                        onInstall = { confirmInstall = true },
                    )
                    Screen.SETTINGS -> SettingsScreen(
                        preferences = appearance,
                        profiles = brandCatalog.profiles,
                        ridePreferences = ridePreferences,
                        vehicleProfiles = performanceCatalog.profiles,
                        usingFallback = brandPack.id != appearance.profileId,
                        modifier = modifier,
                        onAppearanceChanged = { appearanceRevision += 1 },
                        onRideChanged = { rideRevision += 1 },
                        onPreview = {
                            startupReplayKey += 1
                            showStartup = true
                        },
                    )
                    null -> Unit
                }
            }
            }

            if (!showStartup && criticalWarning != null) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                ) {
                    Text(
                        "Critical: ${criticalWarning.message}",
                        color = Color.White,
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(MobileColors.Critical)
                            .padding(16.dp),
                    )
                }
            }

            if (showStartup) {
                StartupAnimation(
                    brandPack = brandPack,
                    timeline = startupTimeline,
                    enabled = appearance.animationEnabled,
                    reduceMotion = appearance.reduceMotionOverride ||
                        systemReduceMotion(context),
                    critical = criticalWarning != null,
                    replayKey = startupReplayKey,
                    onComplete = { showStartup = false },
                )
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
}

private val Screen.isRestorable: Boolean
    get() = this in setOf(
        Screen.DASHBOARD,
        Screen.CHANNELS,
        Screen.CAN,
        Screen.NAVIGATION,
        Screen.DIAGNOSTICS,
    )

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
private fun SettingsScreen(
    preferences: AppearancePreferences,
    profiles: List<MobileBrandPack>,
    ridePreferences: RidePreferences,
    vehicleProfiles: List<VehiclePerformanceProfile>,
    usingFallback: Boolean,
    modifier: Modifier,
    onAppearanceChanged: () -> Unit,
    onRideChanged: () -> Unit,
    onPreview: () -> Unit,
) {
    var selectedProfile by remember { mutableStateOf(preferences.profileId) }
    var selectedVehicleProfile by remember {
        mutableStateOf(ridePreferences.vehicleProfileId)
    }
    var selectedTheme by remember { mutableStateOf(ridePreferences.themeMode) }
    var nightEnterLux by remember { mutableStateOf(ridePreferences.nightEnterLux) }
    var dayEnterLux by remember { mutableStateOf(ridePreferences.dayEnterLux) }
    var animationEnabled by remember { mutableStateOf(preferences.animationEnabled) }
    var reduceMotion by remember { mutableStateOf(preferences.reduceMotionOverride) }
    Column(
        modifier.verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text("Appearance", style = MaterialTheme.typography.titleLarge)
        profiles.forEach { profile ->
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(profile.displayName)
                RadioButton(
                    selected = selectedProfile == profile.id,
                    onClick = {
                        selectedProfile = profile.id
                        preferences.profileId = profile.id
                        onAppearanceChanged()
                    },
                )
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Startup animation")
            Switch(
                checked = animationEnabled,
                onCheckedChange = {
                    animationEnabled = it
                    preferences.animationEnabled = it
                },
            )
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Reduce Motion preview")
            Switch(
                checked = reduceMotion,
                onCheckedChange = {
                    reduceMotion = it
                    preferences.reduceMotionOverride = it
                },
            )
        }
        Button(onClick = onPreview, modifier = Modifier.fillMaxWidth()) {
            Text("Preview Startup Animation")
        }
        if (usingFallback) {
            Text(
                "Selected manufacturer logo is absent. SVC fallback branding is active.",
                color = MobileColors.SecondaryText,
            )
        }
        Text("Ride dashboard", style = MaterialTheme.typography.titleLarge)
        vehicleProfiles.forEach { profile ->
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(profile.displayName)
                RadioButton(
                    selected = selectedVehicleProfile == profile.id,
                    onClick = {
                        selectedVehicleProfile = profile.id
                        ridePreferences.vehicleProfileId = profile.id
                        onRideChanged()
                    },
                )
            }
        }
        Text("Theme", style = MaterialTheme.typography.titleMedium)
        RideThemeMode.entries.forEach { mode ->
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    when (mode) {
                        RideThemeMode.DAY -> "SVC Day"
                        RideThemeMode.NIGHT -> "SVC Night"
                        RideThemeMode.AUTOMATIC -> "Automatic"
                    },
                )
                RadioButton(
                    selected = selectedTheme == mode,
                    onClick = {
                        selectedTheme = mode
                        ridePreferences.themeMode = mode
                        onRideChanged()
                    },
                )
            }
        }
        Text("Night below ${nightEnterLux.toInt()} lux")
        Slider(
            value = nightEnterLux.toFloat(),
            onValueChange = {
                nightEnterLux = it.toDouble()
                ridePreferences.nightEnterLux = nightEnterLux
                onRideChanged()
            },
            valueRange = 50f..500f,
        )
        Text("Day above ${dayEnterLux.toInt()} lux")
        Slider(
            value = dayEnterLux.toFloat(),
            onValueChange = {
                dayEnterLux = it.toDouble()
                ridePreferences.dayEnterLux = dayEnterLux
                onRideChanged()
            },
            valueRange = 300f..1_200f,
        )
        Text("Motorcycle level calibration", style = MaterialTheme.typography.titleMedium)
        Button(
            onClick = {},
            enabled = false,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Calibrate motorcycle level")
        }
        Text(
            "Calibration requires confirmed 0 km/h and Dashboard Demo Mode. " +
                "No BLE calibration command is available.",
            color = MobileColors.SecondaryText,
        )
    }
}

@Composable
private fun StringListScreen(values: List<String>, modifier: Modifier) {
    LazyColumn(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items(values) { value ->
            Row(Modifier.fillMaxWidth()) {
                Text(value, fontFamily = FontFamily.Monospace)
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
