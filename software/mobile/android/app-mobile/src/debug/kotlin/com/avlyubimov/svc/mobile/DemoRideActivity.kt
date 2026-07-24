package com.avlyubimov.svc.mobile

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.RideDashboardState
import com.avlyubimov.svc.core.model.RideThemeMode
import com.avlyubimov.svc.core.model.RideThemeThresholds
import kotlinx.coroutines.isActive

class DemoRideActivity : ComponentActivity() {
    private lateinit var windowController: RideModeWindowController
    private val repository = DemoRideRepository()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        windowController = RideModeWindowController(this)
        setContent {
            DemoRideApp(
                repository = repository,
                windowController = windowController,
                onExit = ::finish,
            )
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        if (intent.getBooleanExtra("restartDemoRide", false)) {
            repository.restart()
        }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus && ::windowController.isInitialized) {
            windowController.reassertImmersiveMode()
        }
    }

    override fun onDestroy() {
        if (::windowController.isInitialized) {
            windowController.exit()
        }
        super.onDestroy()
    }
}

@Composable
private fun DemoRideApp(
    repository: DemoRideRepository,
    windowController: RideModeWindowController,
    onExit: () -> Unit,
) {
    val frame by repository.frame.collectAsStateWithLifecycle()
    val restartGeneration by repository.restartGeneration.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val brandCatalog = remember { MobileBrandCatalog.load(context) }
    val brandPack = remember {
        brandCatalog.resolve(brandCatalog.fallbackProfileId)
    }
    val startupTimeline = remember { MobileStartupTimeline.load(context) }
    val profile = remember {
        val catalog = MobileVehiclePerformanceCatalog.load(context)
        catalog.resolve(catalog.defaultProfileId)
    }
    var startupVisible by remember { mutableStateOf(true) }
    var rideGeneration by remember { mutableStateOf<Int?>(null) }
    val dashboardData = remember(frame, profile) {
        val telemetry = frame.snapshot.telemetry
        val dashboard = RideDashboardState.build(
            telemetry = telemetry,
            connectionState = ConnectionState.CONNECTED,
            isConnecting = false,
            profile = profile,
            leanCalibrated = true,
        )
        TftDashboardData.resolve(
            dashboard = dashboard,
            telemetry = telemetry,
            demoMode = false,
        ).copy(
            gear = frame.sample.gear.displayValue,
            tripDistanceKm = 227.8,
            rangeKm = 214.0,
            frontPressureBar = 2.3,
            rearPressureBar = 2.6,
            currentTime = "10:42",
        )
    }

    LaunchedEffect(restartGeneration) {
        rideGeneration = null
        startupVisible = true
    }
    LaunchedEffect(rideGeneration) {
        val activeGeneration = rideGeneration ?: return@LaunchedEffect
        val startedAt = withFrameNanos { it }
        while (isActive) {
            withFrameNanos { frameTime ->
                repository.seek(
                    (frameTime - startedAt).coerceAtLeast(0L) / 1_000_000_000.0,
                    activeGeneration,
                )
            }
        }
    }
    DisposableEffect(windowController) {
        windowController.enter()
        onDispose(windowController::exit)
    }

    MaterialTheme(
        colorScheme = androidx.compose.material3.darkColorScheme(
            background = MobileColors.Background,
            surface = MobileColors.Surface,
            primary = MobileColors.ActiveRed,
            onBackground = MobileColors.PrimaryText,
            onSurface = MobileColors.PrimaryText,
            error = MobileColors.Critical,
        ),
    ) {
        Box(
            Modifier
                .fillMaxSize()
                .background(MobileColors.Background),
        ) {
            RideModeScreen(
                telemetry = frame.snapshot.telemetry,
                connectionState = ConnectionState.CONNECTED,
                isConnecting = false,
                profile = profile,
                themeMode = RideThemeMode.NIGHT,
                themeThresholds = RideThemeThresholds.DEFAULT,
                reduceMotion = false,
                pageIndicatorEnabled = false,
                demoMode = false,
                dashboardDataOverride = dashboardData,
                initialPage = 0,
                windowController = windowController,
                onPageChanged = {},
                onThemeModeChanged = {},
                onExit = onExit,
                onOpenSettings = {},
            )
            if (startupVisible) {
                StartupAnimation(
                    brandPack = brandPack,
                    timeline = startupTimeline,
                    enabled = true,
                    reduceMotion = false,
                    critical = false,
                    replayKey = restartGeneration,
                    onComplete = {
                        startupVisible = false
                        rideGeneration = restartGeneration
                    },
                )
            }
        }
    }
}
