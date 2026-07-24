package com.avlyubimov.svc.mobile

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.snapping.SnapPosition
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.displayCutout
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.PagerDefaults
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.avlyubimov.svc.core.model.ChannelTelemetry
import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.LeanExtrema
import com.avlyubimov.svc.core.model.Measurement
import com.avlyubimov.svc.core.model.RideDashboardState
import com.avlyubimov.svc.core.model.RideResolvedTheme
import com.avlyubimov.svc.core.model.RideThemeMode
import com.avlyubimov.svc.core.model.RideThemeResolver
import com.avlyubimov.svc.core.model.RideThemeThresholds
import com.avlyubimov.svc.core.model.TelemetrySnapshot
import com.avlyubimov.svc.core.model.VehiclePerformanceProfile
import kotlinx.coroutines.delay
import java.util.Locale
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sin

internal enum class RideModePage(val title: String) {
    MAIN_DASHBOARD("PURE RIDE"),
    LEAN_IMU("SPORT / CORE"),
    VEHICLE_RDC("VEHICLE"),
    SVC_POWER("SVC POWER"),
    CAN_DIAGNOSTICS("DIAGNOSTICS"),
}

@Composable
@OptIn(ExperimentalFoundationApi::class)
internal fun RideModeScreen(
    telemetry: TelemetrySnapshot,
    connectionState: ConnectionState,
    isConnecting: Boolean,
    profile: VehiclePerformanceProfile,
    themeMode: RideThemeMode,
    themeThresholds: RideThemeThresholds,
    reduceMotion: Boolean,
    pageIndicatorEnabled: Boolean,
    demoMode: Boolean,
    initialPage: Int,
    windowController: RideModeWindowController,
    onPageChanged: (Int) -> Unit,
    onThemeModeChanged: (RideThemeMode) -> Unit,
    onExit: () -> Unit,
    onOpenSettings: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val dashboard = remember(
        telemetry,
        connectionState,
        isConnecting,
        profile,
    ) {
        RideDashboardState.build(
            telemetry = telemetry,
            connectionState = connectionState,
            isConnecting = isConnecting,
            profile = profile,
        )
    }
    val tftData = remember(dashboard, telemetry, demoMode) {
        TftDashboardData.resolve(dashboard, telemetry, demoMode)
    }
    var resolvedTheme by remember { mutableStateOf(RideResolvedTheme.NIGHT) }
    LaunchedEffect(themeMode, dashboard.ambientLight, themeThresholds) {
        resolvedTheme = RideThemeResolver.resolve(
            mode = themeMode,
            ambientLight = dashboard.ambientLight,
            previous = resolvedTheme,
            thresholds = themeThresholds,
        )
    }
    val palette = RidePalette.resolve(resolvedTheme)
    val pagerState = rememberPagerState(
        initialPage = initialPage.coerceIn(0, RideModePage.entries.lastIndex),
    ) {
        RideModePage.entries.size
    }
    var indicatorPulse by remember { mutableIntStateOf(0) }
    var indicatorVisible by remember { mutableStateOf(pageIndicatorEnabled) }
    var controlsPulse by remember { mutableIntStateOf(0) }
    var controlsVisible by remember { mutableStateOf(false) }
    var brightness by remember {
        mutableFloatStateOf(windowController.currentBrightness())
    }
    val layoutDirection = LocalLayoutDirection.current
    val cutoutPadding = WindowInsets.displayCutout.asPaddingValues()
    val leftInset = maxOf(
        cutoutPadding.calculateLeftPadding(layoutDirection),
        RideModeGesturePolicy.systemEdgeWidth,
    )
    val rightInset = maxOf(
        cutoutPadding.calculateRightPadding(layoutDirection),
        RideModeGesturePolicy.systemEdgeWidth,
    )
    val topInset = cutoutPadding.calculateTopPadding()
    val bottomInset = cutoutPadding.calculateBottomPadding()
    val pageFling = PagerDefaults.flingBehavior(
        state = pagerState,
        snapAnimationSpec = tween(RideModeGesturePolicy.transitionMillis),
    )
    val pageInteractionSource = remember { MutableInteractionSource() }

    LaunchedEffect(pagerState) {
        snapshotFlow { pagerState.settledPage }.collect { page ->
            indicatorPulse += 1
            onPageChanged(page)
        }
    }
    LaunchedEffect(pagerState.isScrollInProgress) {
        if (pagerState.isScrollInProgress) indicatorPulse += 1
    }
    LaunchedEffect(indicatorPulse, pageIndicatorEnabled) {
        if (!pageIndicatorEnabled) {
            indicatorVisible = false
            return@LaunchedEffect
        }
        indicatorVisible = true
        delay(RideModeGesturePolicy.overlayTimeoutMillis)
        indicatorVisible = false
    }
    LaunchedEffect(controlsPulse) {
        if (controlsPulse == 0) return@LaunchedEffect
        controlsVisible = true
        delay(RideModeGesturePolicy.overlayTimeoutMillis)
        controlsVisible = false
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(palette.background)
            .testTag("rideModeRoot")
            .semantics {
                stateDescription = RideModePage.entries[pagerState.currentPage].title
            },
    ) {
        HorizontalPager(
            state = pagerState,
            modifier = Modifier
                .fillMaxSize()
                .padding(
                    start = leftInset,
                    top = topInset,
                    end = rightInset,
                    bottom = maxOf(
                        bottomInset,
                        RideModeGesturePolicy.indicatorClearance,
                    ),
                ),
            flingBehavior = pageFling,
            beyondViewportPageCount = 1,
            pageSpacing = 8.dp,
            snapPosition = SnapPosition.Start,
            key = { RideModePage.entries[it].name },
        ) { pageIndex ->
            val page = RideModePage.entries[pageIndex]
            Box(
                Modifier
                    .fillMaxSize()
                    .clickable(
                        interactionSource = pageInteractionSource,
                        indication = null,
                    ) {
                        controlsPulse += 1
                    }
                    .testTag("ridePage_${page.name}")
                    .semantics { contentDescription = page.title },
            ) {
                when (page) {
                    RideModePage.MAIN_DASHBOARD -> RideDashboardScreen(
                        data = tftData,
                        palette = palette,
                        reduceMotion = reduceMotion,
                    )
                    RideModePage.LEAN_IMU -> LeanImuPage(
                        data = tftData,
                        telemetry = telemetry,
                        palette = palette,
                    )
                    RideModePage.VEHICLE_RDC -> VehicleRdcPage(
                        data = tftData,
                        telemetry = telemetry,
                        palette = palette,
                    )
                    RideModePage.SVC_POWER -> SvcPowerPage(
                        telemetry = telemetry,
                        data = tftData,
                        palette = palette,
                    )
                    RideModePage.CAN_DIAGNOSTICS -> CanDiagnosticsPage(
                        telemetry = telemetry,
                        data = tftData,
                        palette = palette,
                    )
                }
            }
        }

        AnimatedVisibility(
            visible = pageIndicatorEnabled && indicatorVisible,
            enter = fadeIn(tween(120)),
            exit = fadeOut(tween(320)),
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = bottomInset + 6.dp),
        ) {
            RidePageIndicator(
                selectedPage = pagerState.currentPage,
                palette = palette,
            )
        }

        AnimatedVisibility(
            visible = controlsVisible,
            enter = fadeIn(tween(120)),
            exit = fadeOut(tween(180)),
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = topInset + 10.dp),
        ) {
            RideControlsOverlay(
                brightness = brightness,
                themeMode = themeMode,
                stationaryControlsEnabled = dashboard.speed.displayValue == 0.0,
                palette = palette,
                onBrightnessChanged = {
                    brightness = it
                    windowController.setBrightness(it)
                    controlsPulse += 1
                },
                onThemeModeChanged = { selectedMode ->
                    onThemeModeChanged(selectedMode)
                    brightness = when (selectedMode) {
                        RideThemeMode.DAY -> max(brightness, 0.85f)
                        RideThemeMode.NIGHT -> min(brightness, 0.35f)
                        RideThemeMode.AUTOMATIC ->
                            windowController.currentBrightness()
                    }
                    windowController.setBrightness(brightness)
                    controlsPulse += 1
                },
                onExit = onExit,
                onOpenSettings = onOpenSettings,
            )
        }
    }
}

private object RideModeGesturePolicy {
    val systemEdgeWidth = 24.dp
    val indicatorClearance = 24.dp
    const val transitionMillis = 250
    const val overlayTimeoutMillis = 3_000L
}

@Composable
private fun RidePageIndicator(
    selectedPage: Int,
    palette: RidePalette,
) {
    Row(
        modifier = Modifier
            .alpha(0.76f)
            .testTag("ridePageIndicator"),
        horizontalArrangement = Arrangement.spacedBy(7.dp),
    ) {
        RideModePage.entries.forEachIndexed { index, _ ->
            Box(
                Modifier
                    .size(if (index == selectedPage) 6.dp else 4.dp)
                    .background(
                        if (index == selectedPage) {
                            palette.primaryText
                        } else {
                            palette.secondaryText.copy(alpha = 0.42f)
                        },
                        CircleShape,
                    ),
            )
        }
    }
}

@Composable
private fun LeanImuPage(
    data: TftDashboardData,
    telemetry: TelemetrySnapshot,
    palette: RidePalette,
) {
    var extrema by remember { mutableStateOf(LeanExtrema()) }
    LaunchedEffect(data.leanDegrees) {
        extrema = extrema.observe(data.leanDegrees)
    }
    BoxWithConstraints(
        Modifier
            .fillMaxSize()
            .background(palette.background)
            .padding(horizontal = 22.dp, vertical = 12.dp),
    ) {
        val compact = maxHeight < 390.dp
        TftPageHeader("SPORT / CORE", data, palette)
        Spacer(
            Modifier
                .align(Alignment.TopStart)
                .padding(top = 28.dp)
                .width(if (compact) 72.dp else 96.dp)
                .height(3.dp)
                .background(palette.accent),
        )
        Row(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = if (compact) 30.dp else 34.dp),
            horizontalArrangement = Arrangement.spacedBy(if (compact) 28.dp else 46.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TftSportMetric(
                "SPEED",
                "${data.speedKmh?.roundToInt() ?: "—"} km/h",
                palette,
                compact,
            )
            TftSportMetric(
                "RPM",
                data.engineRpm?.roundToInt()?.toString() ?: "—",
                palette,
                compact,
            )
            TftSportMetric(
                "GEAR",
                data.gear.ifBlank { "—" },
                palette,
                compact,
                valueColor = if (data.gear == "N") palette.valid else palette.primaryText,
            )
        }
        LeanHorizon(
            leanDegrees = data.leanDegrees,
            palette = palette,
            modifier = Modifier
                .align(Alignment.Center)
                .fillMaxWidth(0.68f)
                .fillMaxHeight(0.58f)
                .padding(top = if (compact) 36.dp else 46.dp),
        )
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier
                .align(Alignment.Center)
                .padding(top = if (compact) 48.dp else 58.dp),
        ) {
            Text(
                text = data.leanDegrees.signedTft("°", 1),
                color = palette.primaryText,
                fontSize = if (compact) 72.sp else 96.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Light,
            )
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    if ((data.leanDegrees ?: 0.0) < 0) "LEFT LEAN" else "RIGHT LEAN",
                    color = palette.secondaryText,
                    fontSize = 10.sp,
                    letterSpacing = 2.sp,
                )
                if (data.leanDegraded) {
                    Text("  ▲", color = palette.degraded, fontSize = 9.sp)
                }
            }
        }
        Row(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .padding(horizontal = 18.dp, vertical = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.Bottom,
        ) {
            TftSideMetric("MAX LEFT", "${extrema.maximumLeftDegrees.oneDecimal()}°", palette)
            TftSideMetric("MAX RIGHT", "${extrema.maximumRightDegrees.oneDecimal()}°", palette)
            TftSideMetric(
                "ACCELERATION",
                data.accelerationG.tftValue("g", 2),
                palette,
            )
            TftSideMetric(
                "BRAKING",
                data.brakingG.tftValue("g", 2),
                palette,
                alignEnd = true,
            )
        }
    }
}

@Composable
private fun LeanHorizon(
    leanDegrees: Double?,
    palette: RidePalette,
    modifier: Modifier,
) {
    Canvas(modifier) {
        val lean = (leanDegrees ?: 0.0).coerceIn(-60.0, 60.0)
        val radians = Math.toRadians(lean)
        val center = Offset(size.width / 2f, size.height * 0.58f)
        val radius = min(size.width, size.height) * 0.43f
        drawArc(
            color = palette.divider,
            startAngle = 205f,
            sweepAngle = 130f,
            useCenter = false,
            topLeft = Offset(center.x - radius, center.y - radius),
            size = androidx.compose.ui.geometry.Size(radius * 2f, radius * 2f),
            style = Stroke(2.dp.toPx(), cap = StrokeCap.Round),
        )
        for (mark in -60..60 step 10) {
            val angle = Math.toRadians((270 + mark).toDouble())
            val outer = Offset(
                center.x + cos(angle).toFloat() * radius,
                center.y + sin(angle).toFloat() * radius,
            )
            val inner = Offset(
                center.x + cos(angle).toFloat() * (radius - 12.dp.toPx()),
                center.y + sin(angle).toFloat() * (radius - 12.dp.toPx()),
            )
            drawLine(
                palette.secondaryText.copy(alpha = 0.72f),
                inner,
                outer,
                1.5.dp.toPx(),
            )
        }
        val length = radius * 0.78f
        val dx = cos(radians).toFloat() * length
        val dy = sin(radians).toFloat() * length
        drawLine(
            color = palette.accent,
            start = Offset(center.x - dx, center.y - dy),
            end = Offset(center.x + dx, center.y + dy),
            strokeWidth = 5.dp.toPx(),
            cap = StrokeCap.Round,
        )
        drawCircle(palette.primaryText, 4.dp.toPx(), center)
    }
}

@Composable
private fun VehicleRdcPage(
    data: TftDashboardData,
    telemetry: TelemetrySnapshot,
    palette: RidePalette,
) {
    BoxWithConstraints(
        Modifier
            .fillMaxSize()
            .background(palette.background)
            .padding(horizontal = 22.dp, vertical = 12.dp),
    ) {
        val compact = maxHeight < 390.dp
        TftPageHeader("VEHICLE", data, palette)
        Row(
            modifier = Modifier
                .align(Alignment.Center)
                .fillMaxWidth()
                .fillMaxHeight(0.72f),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TftLargeZone(
                label = "FUEL",
                value = data.fuelPercent.tftValue("%", 0),
                detail = "RANGE ${data.rangeKm.tftValue("km", 0)}  ·  AVG ${
                    telemetry.vehicle.averageFuelConsumption.tftMeasurement(" L/100", 1)
                }",
                palette = palette,
                compact = compact,
                modifier = Modifier.weight(1f),
            )
            TftVerticalDivider(palette)
            TftLargeZone(
                label = "ENGINE / OIL",
                value = data.engineTemperatureCelsius.tftValue("°C", 0),
                detail = "BAT ${data.batteryVoltage.tftValue("V", 1)}  ·  AIR ${
                    data.ambientTemperatureCelsius.signedTft("°C", 0)
                }",
                palette = palette,
                compact = compact,
                modifier = Modifier.weight(1f),
            )
            TftVerticalDivider(palette)
            Column(
                modifier = Modifier.weight(1.1f),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text(
                    "RDC",
                    color = palette.secondaryText,
                    fontSize = 10.sp,
                    letterSpacing = 2.sp,
                )
                Spacer(Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(32.dp)) {
                    TirePressure("FRONT", data.frontPressureBar, palette, compact)
                    TirePressure("REAR", data.rearPressureBar, palette, compact)
                }
                Spacer(Modifier.height(12.dp))
                Text(
                    text = "DWA  —",
                    color = palette.secondaryText,
                    fontFamily = FontFamily.Monospace,
                    fontSize = if (compact) 11.sp else 13.sp,
                )
            }
        }
    }
}

@Composable
private fun SvcPowerPage(
    telemetry: TelemetrySnapshot,
    data: TftDashboardData,
    palette: RidePalette,
) {
    BoxWithConstraints(
        Modifier
            .fillMaxSize()
            .background(palette.background)
            .padding(horizontal = 22.dp, vertical = 12.dp),
    ) {
        val compact = maxHeight < 390.dp
        Column(Modifier.fillMaxSize()) {
            TftPageHeader("SVC POWER", data, palette)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(if (compact) 60.dp else 76.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                TftInlineMetric(
                    "INPUT",
                    telemetry.batteryVoltage.tftMeasurement("V", 1),
                    palette,
                    Modifier.weight(1f),
                )
                TftInlineMetric(
                    "TOTAL",
                    telemetry.totalCurrent.tftMeasurement("A", 1),
                    palette,
                    Modifier.weight(1f),
                )
                TftInlineMetric(
                    "POWER TEMP",
                    telemetry.powerZoneTemperatures
                        .mapNotNull { value ->
                            value.value?.takeIf { value.valid && !value.stale }
                        }
                        .maxOrNull()
                        .tftValue("°C", 0),
                    palette,
                    Modifier.weight(1f),
                )
                TftCompactOutputStates(
                    palette = palette,
                    modifier = Modifier.weight(1.45f),
                )
                TftInlineMetric(
                    "FAULTS",
                    telemetry.channels.count { channel ->
                        channel.fault.isUsable &&
                            !channel.fault.value.equals("none", ignoreCase = true)
                    }.toString(),
                    palette,
                    Modifier.weight(0.75f),
                )
            }
            Spacer(
                Modifier
                    .fillMaxWidth()
                    .height(1.dp)
                    .background(palette.divider),
            )
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(top = 8.dp),
                verticalArrangement = Arrangement.spacedBy(5.dp),
            ) {
                telemetry.channels.chunked(5).forEach { rowChannels ->
                    Row(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        rowChannels.forEach { channel ->
                            TftChannel(
                                channel = channel,
                                palette = palette,
                                modifier = Modifier
                                    .weight(1f)
                                    .fillMaxHeight(),
                            )
                        }
                        repeat(5 - rowChannels.size) {
                            Spacer(Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun CanDiagnosticsPage(
    telemetry: TelemetrySnapshot,
    data: TftDashboardData,
    palette: RidePalette,
) {
    Box(
        Modifier
            .fillMaxSize()
            .background(palette.background)
            .padding(horizontal = 22.dp, vertical = 12.dp),
    ) {
        TftPageHeader("DIAGNOSTICS", data, palette)
        Row(
            modifier = Modifier
                .align(Alignment.Center)
                .fillMaxWidth()
                .fillMaxHeight(0.76f),
        ) {
            Column(
                modifier = Modifier
                    .weight(0.92f)
                    .fillMaxHeight()
                    .padding(top = 22.dp, end = 22.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                Text(
                    "CAN1  ${telemetry.can1.state.tftState()}",
                    color = palette.highBeam,
                    fontSize = 22.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                )
                TftDiagnosticRow(
                    "BLE",
                    if (data.bleConnected) "CONNECTED" else "LOST",
                    palette,
                )
                TftDiagnosticRow(
                    "CAN SAFETY",
                    "LISTEN-ONLY",
                    palette,
                )
                TftDiagnosticRow(
                    "RX FRAMES",
                    telemetry.can1.rxFrames.tftMeasurement("", 0),
                    palette,
                )
                TftDiagnosticRow(
                    "DROPPED",
                    telemetry.can1.droppedFrames.tftMeasurement("", 0),
                    palette,
                )
                TftDiagnosticRow(
                    "LAST FRAME",
                    telemetry.can1.lastFrameTimestamp.tftState(),
                    palette,
                )
                TftDiagnosticRow(
                    "LOGGER",
                    telemetry.storage.canLoggerState.tftState(),
                    palette,
                )
                TftDiagnosticRow(
                    "SD",
                    telemetry.storage.sdCardState.tftState(),
                    palette,
                )
                TftDiagnosticRow(
                    "DATA QUALITY",
                    telemetry.tftQualitySummary(),
                    palette,
                )
            }
            TftVerticalDivider(palette)
            Column(
                modifier = Modifier
                    .weight(1.25f)
                    .fillMaxHeight()
                    .padding(start = 22.dp, top = 22.dp),
            ) {
                Text(
                    "WARNING JOURNAL",
                    color = palette.secondaryText,
                    fontSize = 10.sp,
                    letterSpacing = 1.8.sp,
                )
                Spacer(Modifier.height(12.dp))
                if (telemetry.warnings.isEmpty()) {
                    Text(
                        "NO RECORDED WARNINGS",
                        color = palette.secondaryText,
                        fontSize = 13.sp,
                    )
                } else {
                    telemetry.warnings.take(6).forEach { warning ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                if (warning.active) "●" else "○",
                                color = if (warning.active) {
                                    if (warning.severity.equals("critical", true)) {
                                        palette.critical
                                    } else {
                                        palette.warning
                                    }
                                } else {
                                    palette.secondaryText
                                },
                                fontSize = 10.sp,
                            )
                            Text(
                                warning.code.uppercase(),
                                color = palette.primaryText,
                                fontSize = 12.sp,
                                fontFamily = FontFamily.Monospace,
                                modifier = Modifier.padding(start = 9.dp),
                            )
                            Spacer(Modifier.weight(1f))
                            Text(
                                warning.severity.uppercase(),
                                color = palette.secondaryText,
                                fontSize = 9.sp,
                            )
                        }
                        Spacer(
                            Modifier
                                .fillMaxWidth()
                                .height(1.dp)
                                .background(palette.divider.copy(alpha = 0.58f)),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun TftPageHeader(
    title: String,
    data: TftDashboardData,
    palette: RidePalette,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(28.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            title,
            color = palette.secondaryText,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 2.sp,
        )
        Spacer(Modifier.weight(1f))
        if (!data.bleConnected) {
            TftMiniConnection("BLE", false, palette)
        }
        if (!data.bleConnected && !data.canConnected) {
            Spacer(Modifier.width(10.dp))
        }
        if (!data.canConnected) {
            TftMiniConnection("CAN", false, palette)
        }
    }
}

@Composable
private fun TftMiniConnection(
    label: String,
    connected: Boolean,
    palette: RidePalette,
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Canvas(Modifier.size(5.dp)) {
            drawCircle(if (connected) palette.valid else palette.critical)
        }
        Text(
            label,
            color = palette.secondaryText,
            fontSize = 8.sp,
            modifier = Modifier.padding(start = 4.dp),
        )
    }
}

@Composable
private fun TftSideMetric(
    label: String,
    value: String,
    palette: RidePalette,
    alignEnd: Boolean = false,
) {
    Column(
        horizontalAlignment = if (alignEnd) Alignment.End else Alignment.Start,
    ) {
        Text(label, color = palette.secondaryText, fontSize = 9.sp, letterSpacing = 1.sp)
        Text(
            value,
            color = palette.primaryText,
            fontSize = 18.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

@Composable
private fun TftSportMetric(
    label: String,
    value: String,
    palette: RidePalette,
    compact: Boolean,
    valueColor: Color = palette.primaryText,
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            label,
            color = palette.secondaryText,
            fontSize = if (compact) 8.sp else 9.sp,
            letterSpacing = 1.4.sp,
        )
        Text(
            value,
            color = valueColor,
            fontSize = if (compact) 17.sp else 21.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun TftLargeZone(
    label: String,
    value: String,
    detail: String,
    palette: RidePalette,
    compact: Boolean,
    modifier: Modifier,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(label, color = palette.secondaryText, fontSize = 10.sp, letterSpacing = 2.sp)
        Text(
            value,
            color = palette.primaryText,
            fontSize = if (compact) 42.sp else 58.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Light,
        )
        Text(
            detail,
            color = palette.secondaryText,
            fontSize = if (compact) 11.sp else 14.sp,
            fontFamily = FontFamily.Monospace,
        )
    }
}

@Composable
private fun TirePressure(
    label: String,
    pressure: Double?,
    palette: RidePalette,
    compact: Boolean,
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Canvas(Modifier.size(width = if (compact) 34.dp else 42.dp, height = 54.dp)) {
            drawRoundRect(
                color = palette.divider,
                style = Stroke(2.dp.toPx()),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(8.dp.toPx()),
            )
            drawLine(
                palette.secondaryText,
                Offset(size.width * 0.25f, size.height * 0.22f),
                Offset(size.width * 0.75f, size.height * 0.22f),
                1.dp.toPx(),
            )
            drawLine(
                palette.secondaryText,
                Offset(size.width * 0.25f, size.height * 0.78f),
                Offset(size.width * 0.75f, size.height * 0.78f),
                1.dp.toPx(),
            )
        }
        Text(label, color = palette.secondaryText, fontSize = 8.sp)
        Text(
            pressure.tftValue("bar", 1),
            color = palette.primaryText,
            fontSize = if (compact) 16.sp else 20.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun TftInlineMetric(
    label: String,
    value: String,
    palette: RidePalette,
    modifier: Modifier,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(label, color = palette.secondaryText, fontSize = 9.sp, letterSpacing = 1.4.sp)
        Text(
            value,
            color = palette.primaryText,
            fontSize = 25.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

@Composable
private fun TftCompactOutputStates(
    palette: RidePalette,
    modifier: Modifier,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            "CONFIGURED OUTPUTS",
            color = palette.secondaryText,
            fontSize = 9.sp,
            letterSpacing = 1.2.sp,
        )
        Text(
            "FOG --   CHARGE --   AUX --",
            color = palette.disabledText,
            fontSize = 11.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

@Composable
private fun TftChannel(
    channel: ChannelTelemetry,
    palette: RidePalette,
    modifier: Modifier,
) {
    val current = channel.current.value
        ?.takeIf { channel.current.isUsable }
    val fraction = ((current ?: 0.0) / 10.0).coerceIn(0.0, 1.0).toFloat()
    val faulted = channel.fault.isUsable &&
        !channel.fault.value.equals("none", ignoreCase = true)
    Column(
        modifier = modifier.padding(horizontal = 3.dp, vertical = 4.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                channel.id,
                color = palette.secondaryText,
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
            )
            Spacer(Modifier.weight(1f))
            Text(
                channel.state.tftState(),
                color = if (faulted) palette.critical else palette.valid,
                fontSize = 8.sp,
            )
        }
        Text(
            channel.current.tftMeasurement("A", 1),
            color = palette.primaryText,
            fontSize = 18.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.SemiBold,
        )
        Box(
            Modifier
                .fillMaxWidth()
                .height(3.dp)
                .background(palette.divider.copy(alpha = 0.64f)),
        ) {
            Box(
                Modifier
                    .fillMaxWidth(fraction)
                    .fillMaxHeight()
                    .background(if (faulted) palette.critical else palette.accentBright),
            )
        }
    }
}

@Composable
private fun TftDiagnosticRow(
    label: String,
    value: String,
    palette: RidePalette,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label, color = palette.secondaryText, fontSize = 10.sp)
        Spacer(Modifier.weight(1f))
        Text(
            value,
            color = palette.primaryText,
            fontSize = 12.sp,
            fontFamily = FontFamily.Monospace,
            textAlign = TextAlign.End,
            maxLines = 1,
        )
    }
}

@Composable
private fun TftVerticalDivider(palette: RidePalette) {
    Spacer(
        Modifier
            .width(1.dp)
            .fillMaxHeight(0.7f)
            .background(palette.divider),
    )
}

@Composable
private fun RideControlsOverlay(
    brightness: Float,
    themeMode: RideThemeMode,
    stationaryControlsEnabled: Boolean,
    palette: RidePalette,
    onBrightnessChanged: (Float) -> Unit,
    onThemeModeChanged: (RideThemeMode) -> Unit,
    onExit: () -> Unit,
    onOpenSettings: () -> Unit,
) {
    Surface(
        color = palette.raisedSurface.copy(alpha = 0.96f),
        shape = RoundedCornerShape(4.dp),
        shadowElevation = 0.dp,
        modifier = Modifier
            .padding(horizontal = 36.dp)
            .testTag("rideControlsOverlay"),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            TextButton(
                onClick = onExit,
                enabled = stationaryControlsEnabled,
                modifier = Modifier.testTag("exitRideMode"),
            ) {
                Text("EXIT")
            }
            Text("BRIGHTNESS", color = palette.secondaryText, fontSize = 9.sp)
            Slider(
                value = brightness,
                onValueChange = onBrightnessChanged,
                valueRange = 0.05f..1f,
                modifier = Modifier
                    .width(180.dp)
                    .testTag("rideBrightness"),
            )
            RideThemeMode.entries.forEach { mode ->
                TextButton(
                    onClick = { onThemeModeChanged(mode) },
                    modifier = Modifier.testTag("rideTheme_${mode.name}"),
                ) {
                    Text(
                        when (mode) {
                            RideThemeMode.AUTOMATIC -> "AUTO"
                            RideThemeMode.DAY -> "DAY"
                            RideThemeMode.NIGHT -> "NIGHT"
                        },
                        color = if (themeMode == mode) {
                            palette.accentBright
                        } else {
                            palette.primaryText
                        },
                    )
                }
            }
            TextButton(
                onClick = onOpenSettings,
                enabled = stationaryControlsEnabled,
                modifier = Modifier.testTag("rideSettings"),
            ) {
                Text("SETTINGS")
            }
        }
    }
}

private fun Measurement<Double>.tftMeasurement(
    suffix: String,
    decimals: Int,
): String {
    val number = value?.takeIf { isUsable } ?: return "—"
    return String.format(Locale.US, "%.${decimals}f%s", number, suffix)
}

private fun Measurement<Double>.shortNumber(decimals: Int): String {
    val number = value?.takeIf { isUsable } ?: return "—"
    return String.format(Locale.US, "%.${decimals}f", number)
}

private fun Measurement<String>.tftState(): String =
    value?.takeIf { isUsable }?.uppercase() ?: "—"

private fun Double?.tftValue(suffix: String, decimals: Int): String {
    if (this == null) return "—"
    return String.format(Locale.US, "%.${decimals}f %s", this, suffix)
}

private fun Double?.signedTft(suffix: String, decimals: Int): String {
    if (this == null) return "—"
    return String.format(Locale.US, "%+.${decimals}f%s", this, suffix)
}

private fun Double.oneDecimal(): String =
    String.format(Locale.US, "%.1f", this)

private fun TelemetrySnapshot.tftQualitySummary(): String {
    val measurements = buildList {
        add(batteryVoltage)
        add(totalCurrent)
        add(ambientLight)
        add(leanAngle)
        add(accelerometer.x)
        add(accelerometer.y)
        add(accelerometer.z)
        add(vehicle.speed)
        add(vehicle.engineRpm)
        add(vehicle.engineTemperature)
        add(vehicle.instantFuelConsumption)
        add(vehicle.averageFuelConsumption)
        add(vehicle.fuelLevel)
        add(vehicle.ambientTemperature)
    }
    val usable = measurements.count { it.isUsable }
    return "$usable/${measurements.size} VALID"
}
