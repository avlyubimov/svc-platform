package com.avlyubimov.svc.mobile

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
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
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import java.util.Locale
import kotlin.math.min
import kotlin.math.roundToInt

@Composable
internal fun RideDashboardScreen(
    data: TftDashboardData,
    palette: RidePalette,
    reduceMotion: Boolean,
    modifier: Modifier = Modifier,
) {
    var toastVisible by remember(data.toastMessage) {
        mutableStateOf(data.toastMessage != null)
    }
    LaunchedEffect(data.toastMessage) {
        toastVisible = data.toastMessage != null
        if (data.toastMessage != null) {
            delay(TftDashboardPolicy.toastDurationMillis)
            toastVisible = false
        }
    }

    BoxWithConstraints(
        modifier = modifier
            .fillMaxSize()
            .background(palette.background)
            .testTag("tftDashboard"),
    ) {
        val compact = maxHeight < 390.dp || maxWidth < 760.dp
        val horizontalPadding = if (compact) 16.dp else 24.dp

        TftTachometer(
            data = data,
            palette = palette,
            reduceMotion = reduceMotion,
            modifier = Modifier
                .align(Alignment.TopCenter)
                .fillMaxWidth()
                .height(if (compact) 108.dp else 138.dp)
                .padding(horizontal = horizontalPadding)
                .testTag("tftTachometer"),
        )

        TftActiveIndicators(
            indicators = data.activeIndicators,
            palette = palette,
            compact = compact,
            modifier = Modifier
                .align(Alignment.CenterStart)
                .padding(start = horizontalPadding, bottom = 8.dp),
        )
        TftConnectionIcons(
            data = data,
            palette = palette,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(end = horizontalPadding, top = 10.dp),
        )

        TftSpeedCluster(
            data = data,
            palette = palette,
            compact = compact,
            modifier = Modifier
                .align(Alignment.Center)
                .padding(top = if (compact) 24.dp else 34.dp)
                .testTag("tftSpeed"),
        )
        TftGear(
            gear = data.gear,
            palette = palette,
            compact = compact,
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .padding(
                    end = if (compact) 62.dp else 94.dp,
                    top = if (compact) 18.dp else 30.dp,
                )
                .testTag("tftGear"),
        )

        data.criticalMessage?.let { message ->
            Text(
                text = message.uppercase(),
                color = palette.primaryText,
                fontSize = if (compact) 10.sp else 12.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .padding(bottom = if (compact) 72.dp else 86.dp)
                    .background(palette.critical.copy(alpha = 0.86f))
                    .padding(vertical = 5.dp)
                    .testTag("tftCriticalStrip"),
            )
        }

        AnimatedVisibility(
            visible = toastVisible,
            enter = fadeIn(tween(140)),
            exit = fadeOut(tween(220)),
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = if (compact) 80.dp else 96.dp),
        ) {
            Text(
                text = "●  ${data.toastMessage.orEmpty()}",
                color = palette.secondaryText,
                fontSize = if (compact) 10.sp else 12.sp,
                maxLines = 1,
                modifier = Modifier
                    .background(
                        Color.Black.copy(alpha = 0.86f),
                        RoundedCornerShape(18.dp),
                    )
                    .padding(horizontal = 14.dp, vertical = 7.dp)
                    .testTag("tftToast"),
            )
        }

        TftBottomTelemetry(
            data = data,
            palette = palette,
            compact = compact,
            horizontalPadding = horizontalPadding,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .height(if (compact) 68.dp else 82.dp)
                .testTag("tftBottomStrip"),
        )
    }
}

@Composable
private fun TftTachometer(
    data: TftDashboardData,
    palette: RidePalette,
    reduceMotion: Boolean,
    modifier: Modifier,
) {
    val maximumRpm = data.tachometerMaximumRpm
    val targetFraction = if (maximumRpm != null && maximumRpm > 0) {
        ((data.engineRpm ?: 0.0) / maximumRpm).coerceIn(0.0, 1.0).toFloat()
    } else {
        0f
    }
    val activeFraction by animateFloatAsState(
        targetValue = targetFraction,
        animationSpec = tween(if (reduceMotion) 0 else 220),
        label = "tft-rpm-fill",
    )
    val textMeasurer = rememberTextMeasurer()
    val labelStyle = TextStyle(
        color = palette.secondaryText,
        fontFamily = FontFamily.Monospace,
        fontSize = 11.sp,
        fontWeight = FontWeight.SemiBold,
    )
    val multiplierStyle = TextStyle(
        color = palette.secondaryText.copy(alpha = 0.78f),
        fontFamily = FontFamily.Monospace,
        fontSize = 8.sp,
        fontWeight = FontWeight.Medium,
        letterSpacing = 0.8.sp,
    )

    Canvas(modifier) {
        val maximum = maximumRpm ?: 0.0
        val warningRatio = data.warningStartRpm
            ?.takeIf { maximum > 0 }
            ?.div(maximum)
            ?.coerceIn(0.0, 1.0)
            ?.toFloat()
            ?: 1f
        val redRatio = data.redStartRpm
            ?.takeIf { maximum > 0 }
            ?.div(maximum)
            ?.coerceIn(warningRatio.toDouble(), 1.0)
            ?.toFloat()
            ?: 1f
        val segmentCount = 45
        val left = size.width * 0.035f
        val right = size.width * 0.965f
        val width = right - left
        val gap = min(4.dp.toPx(), width * 0.004f)
        val segmentWidth = (width - gap * (segmentCount - 1)) / segmentCount
        val barTop = size.height * 0.22f
        val barHeight = min(23.dp.toPx(), size.height * 0.24f)

        repeat(segmentCount) { segment ->
            val startRatio = segment.toFloat() / segmentCount
            val endRatio = (segment + 1).toFloat() / segmentCount
            val x = left + segment * (segmentWidth + gap)
            val inactiveColor = when {
                endRatio > redRatio ->
                    palette.accent.copy(alpha = 0.42f)
                endRatio > warningRatio ->
                    palette.warning.copy(alpha = 0.34f)
                else -> palette.divider
            }
            val activeColor = when {
                endRatio > redRatio -> palette.accent
                endRatio > warningRatio -> palette.warning
                else -> palette.primaryText
            }
            drawRect(
                color = if (startRatio < activeFraction) activeColor else inactiveColor,
                topLeft = Offset(x, barTop),
                size = Size(segmentWidth, barHeight),
            )
        }

        val maximumLabel = if (maximum > 0) {
            (maximum / 1_000.0).roundToInt()
        } else {
            9
        }
        for (index in 1..maximumLabel) {
            val label = textMeasurer.measure(index.toString(), labelStyle)
            val labelX = left + width * (index.toFloat() / maximumLabel)
            drawText(
                textLayoutResult = label,
                topLeft = Offset(
                    labelX - label.size.width / 2f,
                    barTop + barHeight + 7.dp.toPx(),
                ),
            )
        }
        val multiplier = textMeasurer.measure("×1000  RPM", multiplierStyle)
        drawText(
            textLayoutResult = multiplier,
            topLeft = Offset(
                size.width / 2f - multiplier.size.width / 2f,
                1.dp.toPx(),
            ),
        )
    }
}

@Composable
private fun TftSpeedCluster(
    data: TftDashboardData,
    palette: RidePalette,
    compact: Boolean,
    modifier: Modifier,
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier,
    ) {
        Row(verticalAlignment = Alignment.Bottom) {
            Text(
                text = data.speedKmh.wholeOrDash(),
                color = palette.primaryText,
                fontSize = if (compact) 84.sp else 104.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Light,
                lineHeight = if (compact) 84.sp else 104.sp,
                maxLines = 1,
            )
            Text(
                text = "km/h",
                color = palette.secondaryText,
                fontSize = if (compact) 15.sp else 18.sp,
                fontFamily = FontFamily.Monospace,
                modifier = Modifier.padding(
                    start = 2.dp,
                    bottom = if (compact) 12.dp else 15.dp,
                ),
            )
        }
        Text(
            text = "${data.engineRpm.wholeOrDash()} rpm",
            color = palette.secondaryText,
            fontSize = if (compact) 11.sp else 13.sp,
            fontFamily = FontFamily.Monospace,
            letterSpacing = 1.2.sp,
            modifier = Modifier.testTag("tftDigitalRpm"),
        )
    }
}

@Composable
private fun TftGear(
    gear: String,
    palette: RidePalette,
    compact: Boolean,
    modifier: Modifier,
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = modifier) {
        Text(
            text = gear.ifBlank { "—" },
            color = if (gear == "N") palette.valid else palette.primaryText,
            fontSize = if (compact) 68.sp else 88.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Medium,
            lineHeight = if (compact) 68.sp else 88.sp,
            maxLines = 1,
        )
    }
}

@Composable
private fun TftBottomTelemetry(
    data: TftDashboardData,
    palette: RidePalette,
    compact: Boolean,
    horizontalPadding: Dp,
    modifier: Modifier,
) {
    Row(
        modifier = modifier
            .background(palette.surface)
            .padding(horizontal = horizontalPadding),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        TftMetric(
            "FUEL",
            data.fuelPercent.valueOrDash("%", 0),
            palette,
            compact,
            selected = true,
        )
        TftMetric("RANGE", data.rangeKm.valueOrDash("km", 0), palette, compact)
        TftMetric("BAT", data.batteryVoltage.valueOrDash("V", 1), palette, compact)
        TftMetric(
            "ENGINE",
            data.engineTemperatureCelsius.valueOrDash("°C", 0),
            palette,
            compact,
        )
        TftMetric("TIME", data.currentTime, palette, compact, drawDivider = false)
    }
}

@Composable
private fun RowScope.TftMetric(
    label: String,
    value: String,
    palette: RidePalette,
    compact: Boolean,
    degraded: Boolean = false,
    selected: Boolean = false,
    drawDivider: Boolean = true,
) {
    Row(
        modifier = Modifier
            .weight(1f)
            .fillMaxHeight(),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxHeight(),
        ) {
            if (selected) {
                Spacer(
                    Modifier
                        .align(Alignment.TopCenter)
                        .fillMaxWidth()
                        .height(3.dp)
                        .background(palette.accent),
                )
            }
            Column(
                modifier = Modifier.align(Alignment.Center),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text(
                    text = label,
                    color = palette.secondaryText.copy(alpha = 0.86f),
                    fontSize = if (compact) 8.sp else 10.sp,
                    letterSpacing = 0.9.sp,
                    maxLines = 1,
                )
                Row(
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = value,
                        color = palette.primaryText,
                        fontSize = if (compact) 13.sp else 17.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                    )
                    if (degraded) {
                        Text(
                            text = " ▲",
                            color = palette.degraded,
                            fontSize = if (compact) 7.sp else 8.sp,
                        )
                    }
                }
            }
        }
        if (drawDivider) {
            Spacer(
                Modifier
                    .width(1.dp)
                    .fillMaxHeight(0.54f)
                    .background(palette.divider.copy(alpha = 0.7f)),
            )
        }
    }
}

@Composable
private fun TftActiveIndicators(
    indicators: List<TftIndicator>,
    palette: RidePalette,
    compact: Boolean,
    modifier: Modifier,
) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(if (compact) 8.dp else 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        modifier = modifier.testTag("tftActiveIndicators"),
    ) {
        indicators.forEach { indicator ->
            TftIndicatorGlyph(indicator, palette, compact)
        }
    }
}

@Composable
private fun TftIndicatorGlyph(
    indicator: TftIndicator,
    palette: RidePalette,
    compact: Boolean,
) {
    val color = indicator.color(palette)
    when (indicator) {
        TftIndicator.HIGH_BEAM,
        TftIndicator.FOG_LIGHTS,
        -> Canvas(
            Modifier.size(
                width = if (compact) 28.dp else 34.dp,
                height = if (compact) 18.dp else 22.dp,
            ),
        ) {
            val stroke = 1.8.dp.toPx()
            drawArc(
                color = color,
                startAngle = 90f,
                sweepAngle = 180f,
                useCenter = false,
                topLeft = Offset(1.dp.toPx(), size.height * 0.18f),
                size = Size(size.width * 0.36f, size.height * 0.64f),
                style = Stroke(stroke, cap = StrokeCap.Round),
            )
            drawLine(
                color,
                Offset(size.width * 0.30f, size.height * 0.18f),
                Offset(size.width * 0.30f, size.height * 0.82f),
                stroke,
            )
            repeat(3) { index ->
                val y = size.height * (0.29f + index * 0.21f)
                val start = Offset(size.width * 0.48f, y)
                val end = Offset(size.width * 0.96f, y)
                if (indicator == TftIndicator.FOG_LIGHTS) {
                    val path = Path().apply {
                        moveTo(start.x, start.y)
                        quadraticTo(
                            size.width * 0.61f,
                            y - size.height * 0.08f,
                            size.width * 0.73f,
                            y,
                        )
                        quadraticTo(
                            size.width * 0.85f,
                            y + size.height * 0.08f,
                            end.x,
                            end.y,
                        )
                    }
                    drawPath(path, color, style = Stroke(stroke, cap = StrokeCap.Round))
                } else {
                    drawLine(color, start, end, stroke, cap = StrokeCap.Round)
                }
            }
            if (indicator == TftIndicator.FOG_LIGHTS) {
                drawLine(
                    color,
                    Offset(size.width * 0.70f, size.height * 0.12f),
                    Offset(size.width * 0.60f, size.height * 0.88f),
                    stroke,
                )
            }
        }
        TftIndicator.ABS -> Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier.size(if (compact) 26.dp else 31.dp),
        ) {
            Canvas(Modifier.fillMaxSize()) {
                drawCircle(color, style = Stroke(1.6.dp.toPx()))
            }
            Text(
                "ABS",
                color = color,
                fontSize = if (compact) 7.sp else 8.sp,
                fontWeight = FontWeight.Bold,
            )
        }
        else -> Text(
            text = indicator.label,
            color = color,
            fontSize = if (indicator.label.length > 3) {
                if (compact) 9.sp else 11.sp
            } else {
                if (compact) 15.sp else 18.sp
            },
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.8.sp,
        )
    }
}

@Composable
private fun TftConnectionIcons(
    data: TftDashboardData,
    palette: RidePalette,
    modifier: Modifier,
) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(10.dp),
        verticalAlignment = Alignment.CenterVertically,
        modifier = modifier.testTag("tftConnectionIcons"),
    ) {
        if (!data.bleConnected) TftConnectionIcon("BLE", false, palette)
        if (!data.canConnected) TftConnectionIcon("CAN", false, palette)
    }
}

@Composable
private fun TftConnectionIcon(
    label: String,
    connected: Boolean,
    palette: RidePalette,
) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Canvas(Modifier.size(6.dp)) {
            drawCircle(if (connected) palette.valid else palette.critical)
        }
        Text(
            text = label,
            color = palette.secondaryText,
            fontSize = 8.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.8.sp,
        )
    }
}

private object TftDashboardPolicy {
    const val toastDurationMillis = 4_000L
}

private fun TftIndicator.color(palette: RidePalette): Color = when (this) {
    TftIndicator.TURN_LEFT,
    TftIndicator.TURN_RIGHT,
    TftIndicator.NEUTRAL,
    -> palette.valid
    TftIndicator.HIGH_BEAM -> palette.highBeam
    TftIndicator.FOG_LIGHTS -> palette.fogLight
    TftIndicator.ABS,
    TftIndicator.ENGINE_WARNING,
    TftIndicator.TIRE_PRESSURE,
    TftIndicator.LOW_VOLTAGE,
    -> palette.warning
    TftIndicator.SVC_ERROR -> palette.critical
}

private fun Double?.wholeOrDash(): String =
    this?.roundToInt()?.toString() ?: "—"

private fun Double?.numberOrDash(decimals: Int): String = if (this == null) {
    "—"
} else {
    String.format(Locale.US, "%.${decimals}f", this)
}

private fun Double?.valueOrDash(unit: String, decimals: Int): String =
    if (this == null) "—" else "${numberOrDash(decimals)} $unit"

private fun Double?.signedValueOrDash(unit: String, decimals: Int): String =
    if (this == null) {
        "—"
    } else {
        "${String.format(Locale.US, "%+.${decimals}f", this)} $unit"
    }
