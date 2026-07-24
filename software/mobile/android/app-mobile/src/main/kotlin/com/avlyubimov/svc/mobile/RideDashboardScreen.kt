package com.avlyubimov.svc.mobile

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
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
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentHeight
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.PlatformTextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import java.util.Locale
import kotlin.math.pow
import kotlin.math.roundToInt

@Composable
internal fun RideDashboardScreen(
    data: TftDashboardData,
    palette: RidePalette,
    reduceMotion: Boolean,
    modifier: Modifier = Modifier,
) {
    val dashboardPalette = palette.interfaceDisplayPalette()
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
            .background(dashboardPalette.background)
            .testTag("tftDashboard"),
    ) {
        val scale = TftLayoutScale.resolve(maxHeight)
        val edgePadding = maxWidth * 0.04f

        TftRibbonTachometer(
            data = data,
            palette = dashboardPalette,
            reduceMotion = reduceMotion,
            scale = scale,
            modifier = Modifier
                .fillMaxSize()
                .testTag("tftTachometer"),
        )

        TftTopLine(
            data = data,
            palette = dashboardPalette,
            scale = scale,
            modifier = Modifier
                .align(Alignment.TopCenter)
                .fillMaxWidth()
                .height(maxHeight * 0.20f)
                .padding(
                    start = maxWidth * 0.14f,
                    end = maxWidth * 0.14f,
                    top = maxHeight * 0.058f,
                ),
        )

        TftSpeedCluster(
            data = data,
            palette = dashboardPalette,
            scale = scale,
            modifier = Modifier
                .align(Alignment.TopStart)
                .offset(x = maxWidth * 0.17f, y = maxHeight * 0.17f)
                .width(maxWidth * 0.38f)
                .height(maxHeight * 0.28f)
                .testTag("tftSpeed"),
        )

        TftGear(
            gear = data.gear,
            palette = dashboardPalette,
            scale = scale,
            modifier = Modifier
                .align(Alignment.TopStart)
                .offset(x = maxWidth * 0.74f, y = maxHeight * 0.54f)
                .width(maxWidth * 0.15f)
                .height(maxHeight * 0.25f)
                .testTag("tftGear"),
        )

        Text(
            text = "${data.engineRpm.wholeOrDash()} rpm",
            color = dashboardPalette.secondaryText,
            fontSize = scale.digitalRpm,
            lineHeight = scale.digitalRpm * 1.18f,
            fontFamily = FontFamily.Monospace,
            letterSpacing = 1.2.sp,
            maxLines = 1,
            softWrap = false,
            overflow = TextOverflow.Visible,
            modifier = Modifier
                .align(Alignment.TopStart)
                .offset(x = maxWidth * 0.45f, y = maxHeight * 0.67f)
                .wrapContentHeight(unbounded = true)
                .testTag("tftDigitalRpm"),
        )

        TftSideIndicators(
            side = TftIndicatorSide.LEFT,
            data = data,
            palette = dashboardPalette,
            scale = scale,
            modifier = Modifier
                .align(Alignment.TopStart)
                .offset(x = edgePadding, y = maxHeight * 0.17f)
                .width(scale.sideRailWidth)
                .height(maxHeight * 0.61f),
        )
        TftSideIndicators(
            side = TftIndicatorSide.RIGHT,
            data = data,
            palette = dashboardPalette,
            scale = scale,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .offset(x = -edgePadding, y = maxHeight * 0.17f)
                .width(scale.sideRailWidth)
                .height(maxHeight * 0.61f),
        )

        TftConnectionStatus(
            data = data,
            palette = dashboardPalette,
            scale = scale,
            modifier = Modifier
                .align(Alignment.TopStart)
                .offset(x = maxWidth * 0.43f, y = maxHeight * 0.755f)
                .width(maxWidth * 0.24f)
                .testTag("tftConnectionIcons"),
        )

        data.criticalMessage?.let { message ->
            Text(
                text = message.uppercase(),
                color = dashboardPalette.primaryText,
                fontSize = scale.status,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .padding(bottom = maxHeight * 0.14f)
                    .background(dashboardPalette.critical.copy(alpha = 0.9f))
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
                .padding(bottom = maxHeight * 0.15f),
        ) {
            Text(
                text = "●  ${data.toastMessage.orEmpty()}",
                color = dashboardPalette.secondaryText,
                fontSize = scale.status,
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
            palette = dashboardPalette,
            scale = scale,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .offset(y = -(maxHeight * 0.04f))
                .fillMaxWidth()
                .height(maxHeight * 0.14f)
                .padding(horizontal = maxWidth * 0.10f)
                .testTag("tftBottomStrip"),
        )
    }
}

@Composable
private fun TftRibbonTachometer(
    data: TftDashboardData,
    palette: RidePalette,
    reduceMotion: Boolean,
    scale: TftLayoutScale,
    modifier: Modifier,
) {
    val maximumRpm = data.tachometerMaximumRpm ?: 9_000.0
    val targetFraction = if (maximumRpm > 0) {
        ((data.engineRpm ?: 0.0) / maximumRpm).coerceIn(0.0, 1.0).toFloat()
    } else {
        0f
    }
    val activeFraction by animateFloatAsState(
        targetValue = targetFraction,
        animationSpec = tween(
            durationMillis = if (reduceMotion) 0 else 280,
            easing = FastOutSlowInEasing,
        ),
        label = "tft-ribbon-fill",
    )
    val textMeasurer = rememberTextMeasurer()
    val numberStyle = TextStyle(
        color = palette.primaryText,
        fontFamily = FontFamily.Monospace,
        fontSize = scale.tachometerNumber,
        fontWeight = FontWeight.Bold,
        platformStyle = PlatformTextStyle(includeFontPadding = true),
    )
    val multiplierStyle = TextStyle(
        color = palette.secondaryText,
        fontFamily = FontFamily.Monospace,
        fontSize = scale.tachometerMultiplier,
        fontWeight = FontWeight.Medium,
        letterSpacing = 0.7.sp,
    )

    Canvas(modifier) {
        val geometry = TftRibbonGeometry.resolve(size)
        val ribbon = geometry.closedPath()
        val warningFraction = ((data.warningStartRpm ?: 7_000.0) / maximumRpm)
            .coerceIn(0.0, 1.0)
            .toFloat()
        val redFraction = ((data.redStartRpm ?: 8_000.0) / maximumRpm)
            .coerceIn(warningFraction.toDouble(), 1.0)
            .toFloat()

        drawPath(ribbon, TftRibbonColors.inactive)

        val blueFillEnd = geometry.xAt(activeFraction.coerceAtMost(warningFraction))
        clipRect(
            left = geometry.upperStart.x,
            right = blueFillEnd,
        ) {
            drawPath(
                path = ribbon,
                brush = Brush.linearGradient(
                    colors = listOf(
                        TftRibbonColors.activeStart,
                        TftRibbonColors.activeEnd,
                    ),
                    start = geometry.upperStart,
                    end = geometry.upperEnd,
                ),
            )
        }

        clipRect(
            left = geometry.xAt(warningFraction),
            right = geometry.xAt(redFraction),
        ) {
            drawPath(ribbon, TftRibbonColors.warning)
        }
        clipRect(left = geometry.xAt(redFraction)) {
            drawPath(ribbon, TftRibbonColors.red)
        }

        drawPath(
            geometry.upperPath(),
            palette.primaryText.copy(alpha = 0.76f),
            style = Stroke(1.1.dp.toPx(), cap = StrokeCap.Round),
        )
        drawPath(
            geometry.lowerPath(),
            TftRibbonColors.activeEnd.copy(alpha = 0.72f),
            style = Stroke(1.1.dp.toPx(), cap = StrokeCap.Round),
        )

        for (index in 0..9) {
            val point = geometry.upperPoint(index / 9f)
            val label = textMeasurer.measure(index.toString(), numberStyle)
            drawText(
                textLayoutResult = label,
                topLeft = Offset(
                    x = point.x - label.size.width / 2f,
                    y = point.y - label.size.height - scale.tachometerLabelGap.toPx(),
                ),
            )
        }

        val multiplier = textMeasurer.measure("×1000 RPM", multiplierStyle)
        val multiplierPoint = geometry.bandCenter(0.47f)
        drawText(
            textLayoutResult = multiplier,
            topLeft = Offset(
                x = multiplierPoint.x - multiplier.size.width / 2f,
                y = multiplierPoint.y - multiplier.size.height / 2f,
            ),
        )
    }
}

@Composable
private fun TftTopLine(
    data: TftDashboardData,
    palette: RidePalette,
    scale: TftLayoutScale,
    modifier: Modifier,
) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.Top,
    ) {
        TftTopValue(
            label = "TRIP",
            value = data.tripDistanceKm.valueOrDash("km", 1),
            palette = palette,
            scale = scale,
        )
        TftTopValue(
            label = "MODE",
            value = "ROAD",
            palette = palette,
            scale = scale,
            selected = true,
        )
        TftTopValue(
            label = "RANGE",
            value = data.rangeKm.valueOrDash("km", 0),
            palette = palette,
            scale = scale,
        )
    }
}

@Composable
private fun RowScope.TftTopValue(
    label: String,
    value: String,
    palette: RidePalette,
    scale: TftLayoutScale,
    selected: Boolean = false,
) {
    Column(
        modifier = Modifier
            .weight(1f)
            .wrapContentHeight(unbounded = true),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = label,
            color = palette.secondaryText,
            fontSize = scale.topLabel,
            lineHeight = scale.topLabel * 1.20f,
            letterSpacing = 1.sp,
            maxLines = 1,
            softWrap = false,
            overflow = TextOverflow.Visible,
            modifier = Modifier.wrapContentHeight(unbounded = true),
        )
        Text(
            text = value,
            color = if (selected) TftRibbonColors.activeEnd else palette.primaryText,
            fontSize = scale.topValue,
            lineHeight = scale.topValue * 1.18f,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Bold,
            maxLines = 1,
            softWrap = false,
            overflow = TextOverflow.Visible,
            modifier = Modifier.wrapContentHeight(unbounded = true),
        )
        if (selected) {
            Spacer(
                Modifier
                    .padding(top = 3.dp)
                    .width(scale.modeUnderlineWidth)
                    .height(2.dp)
                    .background(palette.accent),
            )
        }
    }
}

@Composable
private fun TftSpeedCluster(
    data: TftDashboardData,
    palette: RidePalette,
    scale: TftLayoutScale,
    modifier: Modifier,
) {
    Column(
        horizontalAlignment = Alignment.Start,
        verticalArrangement = Arrangement.Center,
        modifier = modifier,
    ) {
        Row(verticalAlignment = Alignment.Bottom) {
            Text(
                text = data.speedKmh.wholeOrDash(),
                color = palette.primaryText,
                fontSize = scale.speed,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Light,
                lineHeight = scale.speed,
                maxLines = 1,
                softWrap = false,
                overflow = TextOverflow.Visible,
            )
            Text(
                text = "km/h",
                color = palette.secondaryText,
                fontSize = scale.speedUnit,
                fontFamily = FontFamily.Monospace,
                maxLines = 1,
                softWrap = false,
                overflow = TextOverflow.Visible,
                modifier = Modifier.padding(
                    start = 3.dp,
                    bottom = scale.speedUnitBaseline,
                ),
            )
        }
    }
}

@Composable
private fun TftGear(
    gear: String,
    palette: RidePalette,
    scale: TftLayoutScale,
    modifier: Modifier,
) {
    Box(contentAlignment = Alignment.Center, modifier = modifier) {
        Text(
            text = gear.ifBlank { "—" },
            color = if (gear == "N") palette.valid else palette.primaryText,
            fontSize = scale.gear,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Medium,
            lineHeight = scale.gear,
            maxLines = 1,
            softWrap = false,
            overflow = TextOverflow.Visible,
        )
    }
}

@Composable
private fun TftSideIndicators(
    side: TftIndicatorSide,
    data: TftDashboardData,
    palette: RidePalette,
    scale: TftLayoutScale,
    modifier: Modifier,
) {
    val entries = if (side == TftIndicatorSide.LEFT) {
        listOf(
            TftSideIndicator(
                TftSideIcon.TURN_LEFT,
                TftIndicator.TURN_LEFT in data.activeIndicators,
                palette.valid,
            ),
            TftSideIndicator(
                TftSideIcon.HIGH_BEAM,
                TftIndicator.HIGH_BEAM in data.activeIndicators,
                palette.highBeam,
            ),
            TftSideIndicator(TftSideIcon.LOW_BEAM, true, palette.primaryText),
            TftSideIndicator(
                TftSideIcon.FOG_LIGHT,
                TftIndicator.FOG_LIGHTS in data.activeIndicators,
                palette.primaryText,
            ),
        )
    } else {
        listOf(
            TftSideIndicator(
                TftSideIcon.TURN_RIGHT,
                TftIndicator.TURN_RIGHT in data.activeIndicators,
                palette.valid,
            ),
            TftSideIndicator(
                TftSideIcon.ABS,
                TftIndicator.ABS in data.activeIndicators,
                palette.warning,
            ),
            TftSideIndicator(
                TftSideIcon.ENGINE,
                TftIndicator.ENGINE_WARNING in data.activeIndicators,
                palette.warning,
            ),
            TftSideIndicator(
                TftSideIcon.WARNING,
                TftIndicator.SVC_ERROR in data.activeIndicators,
                palette.critical,
            ),
            TftSideIndicator(
                TftSideIcon.RECORDING,
                data.canRecording,
                palette.valid,
            ),
        )
    }

    Column(
        modifier = modifier.testTag("tftSideIndicators_${side.name}"),
        verticalArrangement = Arrangement.SpaceEvenly,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        entries.forEach { indicator ->
            TftSideIndicatorGlyph(
                indicator = indicator,
                inactive = palette.disabledText.copy(alpha = 0.46f),
                scale = scale,
            )
        }
    }
}

@Composable
private fun TftSideIndicatorGlyph(
    indicator: TftSideIndicator,
    inactive: Color,
    scale: TftLayoutScale,
) {
    val isTurnSignal = indicator.icon == TftSideIcon.TURN_LEFT ||
        indicator.icon == TftSideIcon.TURN_RIGHT
    val blinkTransition = rememberInfiniteTransition(label = "turn-signal")
    val blinkAlpha by blinkTransition.animateFloat(
        initialValue = 1f,
        targetValue = 0.22f,
        animationSpec = infiniteRepeatable(
            animation = tween(440),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "turn-signal-alpha",
    )
    val baseColor = if (indicator.active) indicator.color else inactive
    val color = baseColor.copy(
        alpha = if (indicator.active && isTurnSignal) blinkAlpha else baseColor.alpha,
    )
    val iconSize = if (isTurnSignal) scale.turnIndicator else scale.standardIndicator
    when (indicator.icon) {
        TftSideIcon.TURN_LEFT,
        TftSideIcon.TURN_RIGHT,
        -> Canvas(Modifier.size(width = iconSize, height = iconSize * 0.62f)) {
            val left = indicator.icon == TftSideIcon.TURN_LEFT
            val path = Path().apply {
                if (left) {
                    moveTo(size.width, size.height * 0.36f)
                    lineTo(size.width * 0.38f, size.height * 0.36f)
                    lineTo(size.width * 0.38f, 0f)
                    lineTo(0f, size.height * 0.50f)
                    lineTo(size.width * 0.38f, size.height)
                    lineTo(size.width * 0.38f, size.height * 0.64f)
                    lineTo(size.width, size.height * 0.64f)
                } else {
                    moveTo(0f, size.height * 0.36f)
                    lineTo(size.width * 0.62f, size.height * 0.36f)
                    lineTo(size.width * 0.62f, 0f)
                    lineTo(size.width, size.height * 0.50f)
                    lineTo(size.width * 0.62f, size.height)
                    lineTo(size.width * 0.62f, size.height * 0.64f)
                    lineTo(0f, size.height * 0.64f)
                }
                close()
            }
            drawPath(path, color)
        }
        TftSideIcon.HIGH_BEAM,
        TftSideIcon.LOW_BEAM,
        TftSideIcon.FOG_LIGHT,
        -> TftLampGlyph(
            icon = indicator.icon,
            color = color,
            iconSize = iconSize,
        )
        TftSideIcon.ABS -> Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier.size(iconSize),
        ) {
            Canvas(Modifier.fillMaxSize()) {
                drawCircle(color, style = Stroke(1.5.dp.toPx()))
            }
            Text(
                "ABS",
                color = color,
                fontSize = scale.indicatorLabel,
                fontWeight = FontWeight.Bold,
            )
        }
        TftSideIcon.ENGINE -> TftEngineGlyph(color, iconSize)
        TftSideIcon.WARNING -> TftWarningGlyph(color, iconSize)
        TftSideIcon.RECORDING -> TftRecordingGlyph(color, iconSize)
    }
}

@Composable
private fun TftLampGlyph(
    icon: TftSideIcon,
    color: Color,
    iconSize: androidx.compose.ui.unit.Dp,
) {
    Canvas(Modifier.size(width = iconSize, height = iconSize * 0.66f)) {
        val stroke = 1.6.dp.toPx()
        drawArc(
            color = color,
            startAngle = 90f,
            sweepAngle = 180f,
            useCenter = false,
            topLeft = Offset(0f, size.height * 0.18f),
            size = Size(size.width * 0.38f, size.height * 0.64f),
            style = Stroke(stroke, cap = StrokeCap.Round),
        )
        drawLine(
            color,
            Offset(size.width * 0.31f, size.height * 0.18f),
            Offset(size.width * 0.31f, size.height * 0.82f),
            stroke,
        )
        repeat(3) { index ->
            val y = size.height * (0.28f + index * 0.22f)
            val path = Path().apply {
                moveTo(size.width * 0.48f, y)
                when (icon) {
                    TftSideIcon.FOG_LIGHT -> {
                        quadraticTo(
                            size.width * 0.64f,
                            y - size.height * 0.10f,
                            size.width * 0.78f,
                            y,
                        )
                        quadraticTo(
                            size.width * 0.90f,
                            y + size.height * 0.10f,
                            size.width,
                            y,
                        )
                    }
                    TftSideIcon.LOW_BEAM -> lineTo(
                        size.width,
                        y + size.height * 0.12f,
                    )
                    else -> lineTo(size.width, y)
                }
            }
            drawPath(path, color, style = Stroke(stroke, cap = StrokeCap.Round))
        }
    }
}

@Composable
private fun TftEngineGlyph(
    color: Color,
    iconSize: androidx.compose.ui.unit.Dp,
) {
    Canvas(Modifier.size(iconSize)) {
        val path = Path().apply {
            moveTo(size.width * 0.12f, size.height * 0.34f)
            lineTo(size.width * 0.30f, size.height * 0.34f)
            lineTo(size.width * 0.39f, size.height * 0.20f)
            lineTo(size.width * 0.68f, size.height * 0.20f)
            lineTo(size.width * 0.76f, size.height * 0.34f)
            lineTo(size.width * 0.90f, size.height * 0.34f)
            lineTo(size.width * 0.90f, size.height * 0.72f)
            lineTo(size.width * 0.72f, size.height * 0.72f)
            lineTo(size.width * 0.63f, size.height * 0.82f)
            lineTo(size.width * 0.27f, size.height * 0.82f)
            lineTo(size.width * 0.18f, size.height * 0.68f)
            lineTo(size.width * 0.12f, size.height * 0.68f)
            close()
        }
        drawPath(path, color, style = Stroke(1.6.dp.toPx()))
    }
}

@Composable
private fun TftWarningGlyph(
    color: Color,
    iconSize: androidx.compose.ui.unit.Dp,
) {
    Canvas(Modifier.size(iconSize)) {
        val path = Path().apply {
            moveTo(size.width * 0.50f, size.height * 0.08f)
            lineTo(size.width * 0.92f, size.height * 0.86f)
            lineTo(size.width * 0.08f, size.height * 0.86f)
            close()
        }
        drawPath(path, color, style = Stroke(1.6.dp.toPx()))
        drawLine(
            color,
            Offset(size.width * 0.50f, size.height * 0.34f),
            Offset(size.width * 0.50f, size.height * 0.59f),
            1.6.dp.toPx(),
        )
        drawCircle(color, 1.4.dp.toPx(), Offset(size.width * 0.50f, size.height * 0.71f))
    }
}

@Composable
private fun TftRecordingGlyph(
    color: Color,
    iconSize: androidx.compose.ui.unit.Dp,
) {
    Canvas(Modifier.size(iconSize)) {
        drawRoundRect(
            color = color,
            topLeft = Offset(size.width * 0.18f, size.height * 0.12f),
            size = Size(size.width * 0.64f, size.height * 0.76f),
            cornerRadius = androidx.compose.ui.geometry.CornerRadius(
                size.width * 0.08f,
                size.width * 0.08f,
            ),
            style = Stroke(1.5.dp.toPx()),
        )
        drawCircle(
            color,
            radius = size.width * 0.12f,
            center = Offset(size.width * 0.50f, size.height * 0.50f),
        )
    }
}

@Composable
private fun TftConnectionStatus(
    data: TftDashboardData,
    palette: RidePalette,
    scale: TftLayoutScale,
    modifier: Modifier,
) {
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.SpaceEvenly,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        TftStatusDot("BLE", data.bleConnected, palette, scale)
        TftStatusDot("CAN", data.canConnected, palette, scale)
        TftStatusDot("REC", data.canRecording, palette, scale)
    }
}

@Composable
private fun TftStatusDot(
    label: String,
    active: Boolean,
    palette: RidePalette,
    scale: TftLayoutScale,
) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Canvas(Modifier.size(scale.statusDot)) {
            drawCircle(if (active) palette.valid else palette.critical)
        }
        Text(
            text = label,
            color = palette.secondaryText,
            fontSize = scale.status,
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.7.sp,
        )
    }
}

@Composable
private fun TftBottomTelemetry(
    data: TftDashboardData,
    palette: RidePalette,
    scale: TftLayoutScale,
    modifier: Modifier,
) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        TftMetric("FUEL", data.fuelPercent.valueOrDash("%", 0), palette, scale)
        TftMetric("BAT", data.batteryVoltage.valueOrDash("V", 1), palette, scale)
        TftMetric("SVC", data.svcCurrentA.valueOrDash("A", 1), palette, scale)
        TftMetric(
            "ENGINE",
            data.engineTemperatureCelsius.valueOrDash("°C", 0),
            palette,
            scale,
        )
        TftMetric("TIME", data.currentTime, palette, scale)
    }
}

@Composable
private fun RowScope.TftMetric(
    label: String,
    value: String,
    palette: RidePalette,
    scale: TftLayoutScale,
) {
    Column(
        modifier = Modifier
            .weight(1f)
            .fillMaxHeight(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(
            text = label,
            color = palette.secondaryText,
            fontSize = scale.metricLabel,
            lineHeight = scale.metricLabel * 1.18f,
            letterSpacing = 0.9.sp,
            maxLines = 1,
            softWrap = false,
            overflow = TextOverflow.Visible,
        )
        Text(
            text = value,
            color = palette.primaryText,
            fontSize = scale.metricValue,
            lineHeight = scale.metricValue * 1.18f,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.SemiBold,
            maxLines = 1,
            softWrap = false,
            overflow = TextOverflow.Visible,
        )
    }
}

private data class TftLayoutScale(
    val topLabel: TextUnit,
    val topValue: TextUnit,
    val tachometerNumber: TextUnit,
    val tachometerMultiplier: TextUnit,
    val digitalRpm: TextUnit,
    val metricLabel: TextUnit,
    val metricValue: TextUnit,
    val status: TextUnit,
    val indicatorLabel: TextUnit,
    val speed: TextUnit,
    val speedUnit: TextUnit,
    val gear: TextUnit,
    val tachometerLabelGap: Dp,
    val modeUnderlineWidth: Dp,
    val speedUnitBaseline: Dp,
    val turnIndicator: Dp,
    val standardIndicator: Dp,
    val sideRailWidth: Dp,
    val statusDot: Dp,
) {
    companion object {
        fun resolve(height: Dp): TftLayoutScale {
            val value = height.value
            return TftLayoutScale(
                topLabel = (value * 0.026f).coerceIn(8.5f, 11f).sp,
                topValue = (value * 0.048f).coerceIn(15f, 20f).sp,
                tachometerNumber = (value * 0.033f).coerceIn(11f, 15f).sp,
                tachometerMultiplier = (value * 0.025f).coerceIn(8.5f, 11f).sp,
                digitalRpm = (value * 0.043f).coerceIn(15f, 19f).sp,
                metricLabel = (value * 0.026f).coerceIn(8.5f, 11f).sp,
                metricValue = (value * 0.047f).coerceIn(15.5f, 20f).sp,
                status = (value * 0.025f).coerceIn(8.5f, 11f).sp,
                indicatorLabel = (value * 0.020f).coerceIn(7f, 9f).sp,
                speed = (value * 0.245f).coerceIn(84f, 118f).sp,
                speedUnit = (value * 0.050f).coerceIn(17f, 22f).sp,
                gear = (value * 0.225f).coerceIn(80f, 104f).sp,
                tachometerLabelGap = (value * 0.028f).coerceIn(10f, 14f).dp,
                modeUnderlineWidth = (value * 0.12f).coerceIn(42f, 54f).dp,
                speedUnitBaseline = (value * 0.038f).coerceIn(13f, 18f).dp,
                turnIndicator = (value * 0.112f).coerceIn(32f, 42f).dp,
                standardIndicator = (value * 0.098f).coerceIn(30f, 40f).dp,
                sideRailWidth = (value * 0.128f).coerceIn(40f, 52f).dp,
                statusDot = (value * 0.018f).coerceIn(6f, 8f).dp,
            )
        }
    }
}

private enum class TftIndicatorSide {
    LEFT,
    RIGHT,
}

private enum class TftSideIcon {
    TURN_LEFT,
    TURN_RIGHT,
    HIGH_BEAM,
    LOW_BEAM,
    FOG_LIGHT,
    ABS,
    ENGINE,
    WARNING,
    RECORDING,
}

private data class TftSideIndicator(
    val icon: TftSideIcon,
    val active: Boolean,
    val color: Color,
)

private data class TftRibbonGeometry(
    val upperStart: Offset,
    val upperControl1: Offset,
    val upperControl2: Offset,
    val upperMid: Offset,
    val upperControl3: Offset,
    val upperControl4: Offset,
    val upperEnd: Offset,
    val lowerStart: Offset,
    val lowerControl1: Offset,
    val lowerControl2: Offset,
    val lowerMid: Offset,
    val lowerControl3: Offset,
    val lowerControl4: Offset,
    val lowerEnd: Offset,
) {
    fun closedPath(): Path = Path().apply {
        moveTo(upperStart.x, upperStart.y)
        cubicTo(
            upperControl1.x,
            upperControl1.y,
            upperControl2.x,
            upperControl2.y,
            upperMid.x,
            upperMid.y,
        )
        cubicTo(
            upperControl3.x,
            upperControl3.y,
            upperControl4.x,
            upperControl4.y,
            upperEnd.x,
            upperEnd.y,
        )
        lineTo(lowerEnd.x, lowerEnd.y)
        cubicTo(
            lowerControl4.x,
            lowerControl4.y,
            lowerControl3.x,
            lowerControl3.y,
            lowerMid.x,
            lowerMid.y,
        )
        cubicTo(
            lowerControl2.x,
            lowerControl2.y,
            lowerControl1.x,
            lowerControl1.y,
            lowerStart.x,
            lowerStart.y,
        )
        close()
    }

    fun upperPath(): Path = Path().apply {
        moveTo(upperStart.x, upperStart.y)
        cubicTo(
            upperControl1.x,
            upperControl1.y,
            upperControl2.x,
            upperControl2.y,
            upperMid.x,
            upperMid.y,
        )
        cubicTo(
            upperControl3.x,
            upperControl3.y,
            upperControl4.x,
            upperControl4.y,
            upperEnd.x,
            upperEnd.y,
        )
    }

    fun lowerPath(): Path = Path().apply {
        moveTo(lowerStart.x, lowerStart.y)
        cubicTo(
            lowerControl1.x,
            lowerControl1.y,
            lowerControl2.x,
            lowerControl2.y,
            lowerMid.x,
            lowerMid.y,
        )
        cubicTo(
            lowerControl3.x,
            lowerControl3.y,
            lowerControl4.x,
            lowerControl4.y,
            lowerEnd.x,
            lowerEnd.y,
        )
    }

    fun upperPoint(fraction: Float): Offset = piecewiseCubic(
        fraction,
        upperStart,
        upperControl1,
        upperControl2,
        upperMid,
        upperControl3,
        upperControl4,
        upperEnd,
    )

    fun lowerPoint(fraction: Float): Offset = piecewiseCubic(
        fraction,
        lowerStart,
        lowerControl1,
        lowerControl2,
        lowerMid,
        lowerControl3,
        lowerControl4,
        lowerEnd,
    )

    fun xAt(fraction: Float): Float = upperPoint(fraction).x

    fun bandCenter(fraction: Float): Offset {
        val upper = upperPoint(fraction)
        val lower = lowerPoint(fraction)
        return Offset(
            x = (upper.x + lower.x) / 2f,
            y = (upper.y + lower.y) / 2f,
        )
    }

    companion object {
        fun resolve(size: Size): TftRibbonGeometry = TftRibbonGeometry(
            upperStart = Offset(size.width * 0.14f, size.height * 0.62f),
            upperControl1 = Offset(size.width * 0.27f, size.height * 0.64f),
            upperControl2 = Offset(size.width * 0.35f, size.height * 0.54f),
            upperMid = Offset(size.width * 0.47f, size.height * 0.43f),
            upperControl3 = Offset(size.width * 0.59f, size.height * 0.33f),
            upperControl4 = Offset(size.width * 0.72f, size.height * 0.25f),
            upperEnd = Offset(size.width * 0.85f, size.height * 0.27f),
            lowerStart = Offset(size.width * 0.14f, size.height * 0.69f),
            lowerControl1 = Offset(size.width * 0.27f, size.height * 0.72f),
            lowerControl2 = Offset(size.width * 0.38f, size.height * 0.65f),
            lowerMid = Offset(size.width * 0.51f, size.height * 0.56f),
            lowerControl3 = Offset(size.width * 0.64f, size.height * 0.48f),
            lowerControl4 = Offset(size.width * 0.76f, size.height * 0.43f),
            lowerEnd = Offset(size.width * 0.85f, size.height * 0.45f),
        )
    }
}

private object TftRibbonColors {
    val inactive = Color(0xFF14253A)
    val activeStart = Color(0xFF0066B1)
    val activeEnd = Color(0xFF2D9CFF)
    val warning = Color(0xFFF2A900)
    val red = Color(0xFFE21B2D)
}

private object TftDashboardPolicy {
    const val toastDurationMillis = 4_000L
}

private fun piecewiseCubic(
    fraction: Float,
    start: Offset,
    control1: Offset,
    control2: Offset,
    middle: Offset,
    control3: Offset,
    control4: Offset,
    end: Offset,
): Offset {
    val clamped = fraction.coerceIn(0f, 1f)
    return if (clamped <= 0.5f) {
        cubicPoint(
            clamped * 2f,
            start,
            control1,
            control2,
            middle,
        )
    } else {
        cubicPoint(
            (clamped - 0.5f) * 2f,
            middle,
            control3,
            control4,
            end,
        )
    }
}

private fun cubicPoint(
    fraction: Float,
    start: Offset,
    control1: Offset,
    control2: Offset,
    end: Offset,
): Offset {
    val inverse = 1f - fraction
    val startWeight = inverse.pow(3)
    val firstWeight = 3f * inverse.pow(2) * fraction
    val secondWeight = 3f * inverse * fraction.pow(2)
    val endWeight = fraction.pow(3)
    return Offset(
        x = start.x * startWeight +
            control1.x * firstWeight +
            control2.x * secondWeight +
            end.x * endWeight,
        y = start.y * startWeight +
            control1.y * firstWeight +
            control2.y * secondWeight +
            end.y * endWeight,
    )
}

private fun RidePalette.interfaceDisplayPalette(): RidePalette = copy(
    background = Color(0xFF030507),
    primaryText = Color(0xFFF4F6F8),
    secondaryText = Color(0xFFAAB2BC),
    divider = Color(0xFF29313A),
    accent = Color(0xFFE21B2D),
    accentBright = Color(0xFFE21B2D),
    warning = Color(0xFFF2A900),
    valid = Color(0xFF42D77D),
    degraded = Color(0xFFF2A900),
    highBeam = Color(0xFF44A6FF),
    fogLight = Color(0xFFF4F6F8),
)

private fun Double?.wholeOrDash(): String =
    this?.roundToInt()?.toString() ?: "—"

private fun Double?.numberOrDash(decimals: Int): String = if (this == null) {
    "—"
} else {
    String.format(Locale.US, "%.${decimals}f", this)
}

private fun Double?.valueOrDash(unit: String, decimals: Int): String =
    if (this == null) "—" else "${numberOrDash(decimals)} $unit"
