package com.avlyubimov.svc.mobile

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.LeanExtrema
import com.avlyubimov.svc.core.model.RideAlert
import com.avlyubimov.svc.core.model.RideAlertSeverity
import com.avlyubimov.svc.core.model.RideDashboardState
import com.avlyubimov.svc.core.model.RideDataState
import com.avlyubimov.svc.core.model.RideGear
import com.avlyubimov.svc.core.model.RideMotionPolicy
import com.avlyubimov.svc.core.model.RideResolvedTheme
import com.avlyubimov.svc.core.model.RideThemeMode
import com.avlyubimov.svc.core.model.RideThemeResolver
import com.avlyubimov.svc.core.model.RideThemeThresholds
import com.avlyubimov.svc.core.model.RideValue
import com.avlyubimov.svc.core.model.TachometerZone
import com.avlyubimov.svc.core.model.TachometerZoneResolver
import com.avlyubimov.svc.core.model.TelemetrySnapshot
import com.avlyubimov.svc.core.model.VehiclePerformanceProfile
import java.util.Locale
import kotlin.math.cos
import kotlin.math.sin

@Composable
internal fun RideDashboardScreen(
    telemetry: TelemetrySnapshot,
    connectionState: ConnectionState,
    isConnecting: Boolean,
    profile: VehiclePerformanceProfile,
    themeMode: RideThemeMode,
    themeThresholds: RideThemeThresholds,
    reduceMotion: Boolean,
    modifier: Modifier = Modifier,
) {
    val state = remember(
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
    RideDashboardContent(
        state = state,
        themeMode = themeMode,
        themeThresholds = themeThresholds,
        reduceMotion = reduceMotion,
        modifier = modifier,
    )
}

@Composable
private fun RideDashboardContent(
    state: RideDashboardState,
    themeMode: RideThemeMode,
    themeThresholds: RideThemeThresholds,
    reduceMotion: Boolean,
    modifier: Modifier = Modifier,
) {
    var resolvedTheme by remember(themeMode) {
        mutableStateOf(
            if (themeMode == RideThemeMode.DAY) {
                RideResolvedTheme.DAY
            } else {
                RideResolvedTheme.NIGHT
            },
        )
    }
    LaunchedEffect(themeMode, state.ambientLight, themeThresholds) {
        resolvedTheme = RideThemeResolver.resolve(
            mode = themeMode,
            ambientLight = state.ambientLight,
            previous = resolvedTheme,
            thresholds = themeThresholds,
        )
    }
    val targetPalette = RidePalette.resolve(resolvedTheme)
    val background by animateColorAsState(
        targetValue = targetPalette.background,
        animationSpec = tween(
            RideMotionPolicy.durationMillis(
                reduceMotion,
                RideDesignTokens.themeAnimationMillis,
            ),
        ),
        label = "ride-background",
    )
    val palette = targetPalette.copy(background = background)

    BoxWithConstraints(
        modifier = modifier
            .fillMaxSize()
            .background(palette.background)
            .padding(RideDesignTokens.contentPadding),
    ) {
        val landscape = maxWidth > maxHeight
        if (landscape) {
            LandscapeDashboard(
                state = state,
                palette = palette,
                reduceMotion = reduceMotion,
            )
        } else {
            PortraitDashboard(
                state = state,
                palette = palette,
                reduceMotion = reduceMotion,
            )
        }
    }
}

@Composable
private fun LandscapeDashboard(
    state: RideDashboardState,
    palette: RidePalette,
    reduceMotion: Boolean,
) {
    Column(
        Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(RideDesignTokens.spacing),
    ) {
        RideStatusStrip(state, palette)
        Row(
            modifier = Modifier.weight(1f),
            horizontalArrangement = Arrangement.spacedBy(RideDesignTokens.spacing),
        ) {
            LeanGauge(
                state = state,
                palette = palette,
                reduceMotion = reduceMotion,
                modifier = Modifier
                    .weight(0.27f)
                    .fillMaxHeight(),
            )
            CenterCluster(
                state = state,
                palette = palette,
                reduceMotion = reduceMotion,
                modifier = Modifier
                    .weight(0.46f)
                    .fillMaxHeight(),
            )
            MetricColumn(
                state = state,
                palette = palette,
                modifier = Modifier
                    .weight(0.27f)
                    .fillMaxHeight(),
            )
        }
        state.activeAlert?.let { ActiveWarning(it, palette) }
    }
}

@Composable
private fun PortraitDashboard(
    state: RideDashboardState,
    palette: RidePalette,
    reduceMotion: Boolean,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(RideDesignTokens.spacing),
    ) {
        RideStatusStrip(state, palette)
        CenterCluster(
            state = state,
            palette = palette,
            reduceMotion = reduceMotion,
            modifier = Modifier
                .fillMaxWidth()
                .height(430.dp),
        )
        LeanGauge(
            state = state,
            palette = palette,
            reduceMotion = reduceMotion,
            modifier = Modifier
                .fillMaxWidth()
                .height(250.dp),
        )
        MetricColumn(
            state = state,
            palette = palette,
            modifier = Modifier
                .fillMaxWidth()
                .height(360.dp),
        )
        state.activeAlert?.let { ActiveWarning(it, palette) }
    }
}

@Composable
private fun RideStatusStrip(
    state: RideDashboardState,
    palette: RidePalette,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(RideDesignTokens.statusHeight),
        horizontalArrangement = Arrangement.spacedBy(RideDesignTokens.compactSpacing),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            "SVC RIDE",
            color = palette.primaryText,
            fontSize = 15.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 2.sp,
        )
        Text(
            state.profile.displayName.uppercase(),
            color = palette.secondaryText,
            fontSize = 11.sp,
            modifier = Modifier.weight(1f),
            maxLines = 1,
        )
        StatusChip(state.bleLabel, state.bleState, palette)
        StatusChip(
            label = state.canState.displayValue?.let { "CAN ${it.uppercase()}" }
                ?: "CAN —",
            state = state.canState.state,
            palette = palette,
        )
    }
}

@Composable
private fun StatusChip(
    label: String,
    state: RideDataState,
    palette: RidePalette,
) {
    Row(
        modifier = Modifier
            .background(
                colorForState(state, palette).copy(alpha = 0.16f),
                shape = RoundedCornerShape(50),
            )
            .padding(horizontal = 10.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Box(
            Modifier
                .size(7.dp)
                .background(colorForState(state, palette), RoundedCornerShape(50)),
        )
        Text(
            label,
            color = palette.primaryText,
            fontSize = 10.sp,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

@Composable
private fun CenterCluster(
    state: RideDashboardState,
    palette: RidePalette,
    reduceMotion: Boolean,
    modifier: Modifier,
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(RideDesignTokens.cornerRadius),
        colors = CardDefaults.cardColors(containerColor = palette.surface),
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(RideDesignTokens.spacing),
        ) {
            TachometerGauge(
                rpm = state.engineRpm,
                profile = state.profile,
                initialZone = state.tachometerZone,
                palette = palette,
                reduceMotion = reduceMotion,
                modifier = Modifier.fillMaxSize(),
            )
            Row(
                modifier = Modifier
                    .align(Alignment.Center)
                    .offset(y = (-22).dp),
                verticalAlignment = Alignment.Bottom,
                horizontalArrangement = Arrangement.Center,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        state.speed.number(0),
                        color = palette.primaryText,
                        fontSize = 70.sp,
                        lineHeight = 70.sp,
                        fontWeight = FontWeight.Light,
                        fontFamily = FontFamily.Monospace,
                    )
                    Text(
                        "km/h",
                        color = palette.secondaryText,
                        fontSize = 13.sp,
                        letterSpacing = 2.sp,
                    )
                    QualityLabel(state.speed.state, palette)
                }
                Column(
                    modifier = Modifier.padding(start = 24.dp, bottom = 7.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text(
                        state.gear.displayValue,
                        color = palette.accentBright,
                        fontSize = if (state.gear == RideGear.BETWEEN) 30.sp else 60.sp,
                        lineHeight = 64.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                    )
                    Text(
                        "GEAR",
                        color = palette.secondaryText,
                        fontSize = 10.sp,
                        letterSpacing = 2.sp,
                    )
                }
            }
        }
    }
}

@Composable
private fun TachometerGauge(
    rpm: RideValue<Double>,
    profile: VehiclePerformanceProfile,
    initialZone: TachometerZone,
    palette: RidePalette,
    reduceMotion: Boolean,
    modifier: Modifier,
) {
    var activeZone by remember(profile.id) { mutableStateOf(initialZone) }
    LaunchedEffect(rpm.displayValue, profile) {
        activeZone = TachometerZoneResolver.zoneWithHysteresis(
            rpm = rpm.displayValue,
            profile = profile,
            previous = activeZone,
        )
    }
    val scaleMax = profile.tachometerScaleMaxRpm?.toFloat()
    val targetProgress = if (scaleMax != null) {
        ((rpm.displayValue?.toFloat() ?: 0f) / scaleMax).coerceIn(0f, 1f)
    } else {
        0f
    }
    val progress by animateFloatAsState(
        targetValue = targetProgress,
        animationSpec = tween(
            RideMotionPolicy.durationMillis(
                reduceMotion,
                RideDesignTokens.standardAnimationMillis,
            ),
        ),
        label = "tachometer-progress",
    )
    val activeColor = when (activeZone) {
        TachometerZone.NORMAL -> palette.accentBright
        TachometerZone.WARNING -> palette.warning
        TachometerZone.RED -> palette.critical
        TachometerZone.UNAVAILABLE -> palette.divider
    }

    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Canvas(
            Modifier
                .fillMaxWidth()
                .weight(1f)
                .aspectRatio(2.1f),
        ) {
            val strokeWidth = RideDesignTokens.gaugeLineWidth.toPx()
            val inset = strokeWidth
            val arcSize = Size(size.minDimension - inset * 2, size.minDimension - inset * 2)
            val topLeft = Offset(
                (size.width - arcSize.width) / 2,
                (size.height - arcSize.height) / 2,
            )
            val warningFraction = profile.warningStartRpm
                ?.toFloat()
                ?.div(scaleMax ?: 1f)
                ?.coerceIn(0f, 1f)
                ?: 1f
            val redFraction = profile.redZoneStartRpm
                ?.toFloat()
                ?.div(scaleMax ?: 1f)
                ?.coerceIn(warningFraction, 1f)
                ?: 1f
            drawArc(
                color = if (scaleMax == null) {
                    palette.divider
                } else {
                    palette.accent.copy(alpha = 0.35f)
                },
                startAngle = 135f,
                sweepAngle = 270f * warningFraction,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = Stroke(strokeWidth),
            )
            if (warningFraction < redFraction) {
                drawArc(
                    color = palette.warning.copy(alpha = 0.55f),
                    startAngle = 135f + 270f * warningFraction,
                    sweepAngle = 270f * (redFraction - warningFraction),
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(strokeWidth),
                )
            }
            if (redFraction < 1f) {
                drawArc(
                    color = palette.critical.copy(alpha = 0.58f),
                    startAngle = 135f + 270f * redFraction,
                    sweepAngle = 270f * (1f - redFraction),
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(strokeWidth),
                )
            }
            drawArc(
                color = activeColor,
                startAngle = 135f,
                sweepAngle = 270f * progress,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = Stroke(strokeWidth, cap = StrokeCap.Round),
            )
            val center = Offset(size.width / 2, size.height / 2)
            val radius = arcSize.width / 2 - strokeWidth * 0.8f
            (0..9).forEach { tick ->
                val fraction = tick / 9f
                val angle = Math.toRadians((135 + 270 * fraction).toDouble())
                val outer = Offset(
                    center.x + cos(angle).toFloat() * radius,
                    center.y + sin(angle).toFloat() * radius,
                )
                val inner = Offset(
                    center.x + cos(angle).toFloat() * (radius - 10.dp.toPx()),
                    center.y + sin(angle).toFloat() * (radius - 10.dp.toPx()),
                )
                drawLine(palette.secondaryText, inner, outer, 1.5.dp.toPx())
            }
        }
        Row(
            modifier = Modifier
                .align(Alignment.End)
                .padding(end = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                rpm.number(0),
                color = activeColor,
                fontSize = 27.sp,
                lineHeight = 29.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.SemiBold,
            )
            Text(
                "RPM",
                color = palette.secondaryText,
                fontSize = 11.sp,
                letterSpacing = 2.sp,
            )
            QualityLabel(rpm.state, palette)
        }
    }
}

@Composable
private fun LeanGauge(
    state: RideDashboardState,
    palette: RidePalette,
    reduceMotion: Boolean,
    modifier: Modifier,
) {
    var extrema by remember { mutableStateOf(LeanExtrema()) }
    LaunchedEffect(state.leanAngle.displayValue) {
        extrema = extrema.observe(state.leanAngle.displayValue)
    }
    val targetLean = state.leanAngle.displayValue
        ?.coerceIn(-60.0, 60.0)
        ?.toFloat()
        ?: 0f
    val lean by animateFloatAsState(
        targetValue = targetLean,
        animationSpec = tween(
            if (reduceMotion) 0 else RideDesignTokens.standardAnimationMillis,
        ),
        label = "lean-angle",
    )
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(RideDesignTokens.cornerRadius),
        colors = CardDefaults.cardColors(containerColor = palette.surface),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(RideDesignTokens.spacing),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(RideDesignTokens.compactSpacing),
        ) {
            Text(
                "SVC ESTIMATED LEAN",
                color = palette.secondaryText,
                fontSize = 10.sp,
                letterSpacing = 1.5.sp,
            )
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center,
            ) {
                Canvas(Modifier.fillMaxSize()) {
                    val center = Offset(size.width / 2, size.height * 0.58f)
                    val radius = minOf(size.width, size.height) * 0.34f
                    listOf(0, 10, 20, 30, 45, 60).forEach { mark ->
                        listOf(-mark, mark).distinct().forEach { signed ->
                            val angle = Math.toRadians((270 + signed).toDouble())
                            val outer = Offset(
                                center.x + cos(angle).toFloat() * radius,
                                center.y + sin(angle).toFloat() * radius,
                            )
                            val inner = Offset(
                                center.x + cos(angle).toFloat() * (radius - 8.dp.toPx()),
                                center.y + sin(angle).toFloat() * (radius - 8.dp.toPx()),
                            )
                            drawLine(palette.divider, inner, outer, 1.dp.toPx())
                        }
                    }
                    val horizonAngle = Math.toRadians(lean.toDouble())
                    val dx = cos(horizonAngle).toFloat() * radius
                    val dy = sin(horizonAngle).toFloat() * radius
                    drawLine(
                        color = palette.accentBright,
                        start = Offset(center.x - dx, center.y - dy),
                        end = Offset(center.x + dx, center.y + dy),
                        strokeWidth = 3.dp.toPx(),
                        cap = StrokeCap.Round,
                    )
                    drawLine(
                        color = palette.primaryText,
                        start = Offset(center.x, center.y - 20.dp.toPx()),
                        end = Offset(center.x, center.y + 20.dp.toPx()),
                        strokeWidth = 5.dp.toPx(),
                        cap = StrokeCap.Round,
                    )
                }
            }
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(7.dp),
            ) {
                Text(
                    state.leanAngle.number(1, signed = true),
                    color = palette.primaryText,
                    fontSize = 24.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.SemiBold,
                )
                Text("°", color = palette.secondaryText, fontSize = 12.sp)
                QualityLabel(state.leanAngle.state, palette)
            }
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    "L ${extrema.maximumLeftDegrees.oneDecimal()}°",
                    color = palette.secondaryText,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 11.sp,
                )
                Text(
                    "R ${extrema.maximumRightDegrees.oneDecimal()}°",
                    color = palette.secondaryText,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 11.sp,
                )
            }
            TextButton(
                enabled = state.speed.displayValue == 0.0,
                onClick = { extrema = extrema.resetIfStationary(state.speed) },
            ) {
                Text("RESET MAX", fontSize = 10.sp, letterSpacing = 1.sp)
            }
        }
    }
}

@Composable
private fun MetricColumn(
    state: RideDashboardState,
    palette: RidePalette,
    modifier: Modifier,
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(RideDesignTokens.compactSpacing),
    ) {
        MetricCard(
            "ENGINE / OIL",
            state.engineTemperature.format(0),
            state.engineTemperature.state,
            palette,
            Modifier.weight(1f),
        )
        MetricCard(
            "FUEL",
            state.fuelLevel.format(0),
            state.fuelLevel.state,
            palette,
            Modifier.weight(1f),
        )
        MetricCard(
            "BATTERY",
            state.batteryVoltage.format(1),
            state.batteryVoltage.state,
            palette,
            Modifier.weight(1f),
        )
        MetricCard(
            "SVC CURRENT",
            state.totalCurrent.format(1),
            state.totalCurrent.state,
            palette,
            Modifier.weight(1f),
        )
    }
}

@Composable
private fun MetricCard(
    label: String,
    value: String,
    state: RideDataState,
    palette: RidePalette,
    modifier: Modifier,
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .widthIn(min = RideDesignTokens.metricMinimumWidth),
        shape = RoundedCornerShape(RideDesignTokens.compactCornerRadius),
        colors = CardDefaults.cardColors(containerColor = palette.raisedSurface),
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 8.dp, vertical = 4.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                if (state == RideDataState.VALID) {
                    label
                } else {
                    "$label · ${state.name}"
                },
                color = colorForState(state, palette),
                fontSize = 7.sp,
                letterSpacing = 0.8.sp,
                maxLines = 1,
            )
            Text(
                value,
                color = palette.primaryText,
                fontSize = 14.sp,
                fontWeight = FontWeight.SemiBold,
                fontFamily = FontFamily.Monospace,
                maxLines = 1,
            )
        }
    }
}

@Composable
private fun QualityLabel(
    state: RideDataState,
    palette: RidePalette,
) {
    if (state != RideDataState.VALID) {
        Text(
            state.name,
            color = colorForState(state, palette),
            fontSize = 8.sp,
            letterSpacing = 1.sp,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun ActiveWarning(
    warning: RideAlert,
    palette: RidePalette,
) {
    val color = when (warning.severity) {
        RideAlertSeverity.CRITICAL -> palette.critical
        RideAlertSeverity.WARNING -> palette.warning
        RideAlertSeverity.INFO -> palette.accentBright
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color.copy(alpha = 0.18f),
                RoundedCornerShape(RideDesignTokens.compactCornerRadius),
            )
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(
            Modifier
                .size(9.dp)
                .background(color, RoundedCornerShape(50)),
        )
        Text(
            warning.title,
            color = palette.primaryText,
            fontSize = 13.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 1.sp,
        )
    }
}

private fun RideValue<Double>.format(
    decimals: Int,
): String {
    val number = displayValue ?: return "—"
    val rendered = String.format(Locale.US, "%.${decimals}f", number)
    return "$rendered ${unit.symbol()}".trim()
}

private fun RideValue<Double>.number(
    decimals: Int,
    signed: Boolean = false,
): String {
    val number = displayValue ?: return "—"
    val format = if (signed) "%+.${decimals}f" else "%.${decimals}f"
    return String.format(Locale.US, format, number)
}

private fun String.symbol(): String = when (this) {
    "degC" -> "°C"
    "deg" -> "°"
    "%" -> "%"
    else -> this
}

private fun Double.oneDecimal(): String = String.format(Locale.US, "%.1f", this)

private fun colorForState(
    state: RideDataState,
    palette: RidePalette,
): Color = when (state) {
    RideDataState.VALID -> palette.valid
    RideDataState.DEGRADED, RideDataState.STALE -> palette.degraded
    RideDataState.INVALID -> palette.critical
    RideDataState.UNAVAILABLE -> palette.secondaryText
}

private val previewProfile = VehiclePerformanceProfile(
    schemaVersion = 1,
    id = "svc-ride-preview",
    manufacturer = "SVC",
    model = "Ride",
    generation = "Preview",
    yearFrom = null,
    yearTo = null,
    engineName = null,
    engineDisplacementCc = null,
    maximumTorqueNm = null,
    nominalPowerKw = null,
    gearboxGears = 6,
    fuelCapacityLiters = 20.0,
    fuelReserveLiters = 4.0,
    iceWarningTemperatureCelsius = 3.0,
    idleRpm = 1150,
    idleToleranceRpm = 50,
    torquePeakRpm = 5500,
    powerPeakRpm = 7000,
    tachometerScaleMinRpm = 0,
    tachometerScaleMaxRpm = 9000,
    warningStartRpm = 7000,
    redZoneStartRpm = 7800,
    revLimiterRpm = null,
    source = "Preview only",
    reference = "Preview only",
    confidence = "preview",
)

private val previewState = RideDashboardState(
    speed = RideValue(86.0, "km/h", RideDataState.VALID),
    engineRpm = RideValue(4620.0, "rpm", RideDataState.VALID),
    gear = RideGear.UNAVAILABLE,
    leanAngle = RideValue(-24.6, "deg", RideDataState.DEGRADED),
    engineTemperature = RideValue(92.0, "degC", RideDataState.VALID),
    fuelLevel = RideValue(64.0, "%", RideDataState.VALID),
    ambientTemperature = RideValue(16.0, "degC", RideDataState.VALID),
    ambientLight = RideValue(800.0, "lux", RideDataState.VALID),
    batteryVoltage = RideValue(14.1, "V", RideDataState.VALID),
    totalCurrent = RideValue(8.4, "A", RideDataState.VALID),
    canState = RideValue("listen-only", "state", RideDataState.VALID),
    bleLabel = "BLE",
    bleState = RideDataState.VALID,
    tachometerZone = TachometerZone.NORMAL,
    alerts = listOf(
        RideAlert("preview", "SVC PREVIEW DATA", RideAlertSeverity.INFO),
    ),
    profile = previewProfile,
)

@Preview(
    name = "SVC Ride Landscape",
    widthDp = 960,
    heightDp = 540,
    showBackground = true,
)
@Composable
private fun RideDashboardLandscapePreview() {
    RideDashboardContent(
        state = previewState,
        themeMode = RideThemeMode.DAY,
        themeThresholds = RideThemeThresholds.DEFAULT,
        reduceMotion = false,
    )
}

@Preview(
    name = "SVC Ride Portrait",
    widthDp = 430,
    heightDp = 900,
    showBackground = true,
)
@Composable
private fun RideDashboardPortraitPreview() {
    RideDashboardContent(
        state = previewState,
        themeMode = RideThemeMode.NIGHT,
        themeThresholds = RideThemeThresholds.DEFAULT,
        reduceMotion = true,
    )
}
