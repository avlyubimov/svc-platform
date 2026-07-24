package com.avlyubimov.svc.mobile

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.avlyubimov.svc.core.model.RideResolvedTheme

internal data class RidePalette(
    val background: Color,
    val surface: Color,
    val raisedSurface: Color,
    val primaryText: Color,
    val secondaryText: Color,
    val divider: Color,
    val accent: Color,
    val accentBright: Color,
    val warning: Color,
    val critical: Color,
    val valid: Color,
    val degraded: Color,
) {
    companion object {
        fun resolve(theme: RideResolvedTheme): RidePalette = when (theme) {
            RideResolvedTheme.DAY -> RidePalette(
                background = Color(0xFF0B1118),
                surface = Color(0xFF141D27),
                raisedSurface = Color(0xFF1C2733),
                primaryText = Color.White,
                secondaryText = Color(0xFFBEC9D4),
                divider = Color(0xFF404E5C),
                accent = Color(0xFF1C69D4),
                accentBright = Color(0xFF4AA3FF),
                warning = Color(0xFFFFB000),
                critical = Color(0xFFE32636),
                valid = Color(0xFF5BD690),
                degraded = Color(0xFFFFB000),
            )
            RideResolvedTheme.NIGHT -> RidePalette(
                background = Color(0xFF030508),
                surface = Color(0xFF0A0E13),
                raisedSurface = Color(0xFF11171E),
                primaryText = Color(0xFFF4F7FA),
                secondaryText = Color(0xFF97A5B3),
                divider = Color(0xFF28323D),
                accent = Color(0xFF1454B1),
                accentBright = Color(0xFF398BE8),
                warning = Color(0xFFFFB000),
                critical = Color(0xFFE32636),
                valid = Color(0xFF4AC27E),
                degraded = Color(0xFFFFB000),
            )
        }
    }
}

internal object RideDesignTokens {
    val cornerRadius = 18.dp
    val compactCornerRadius = 12.dp
    val spacing = 14.dp
    val compactSpacing = 8.dp
    val contentPadding = 18.dp
    val statusHeight = 34.dp
    val gaugeLineWidth = 16.dp
    val metricMinimumWidth = 128.dp
    const val standardAnimationMillis = 180
    const val themeAnimationMillis = 300
}
