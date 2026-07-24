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
    val disabledText: Color,
    val divider: Color,
    val accent: Color,
    val accentBright: Color,
    val warning: Color,
    val critical: Color,
    val valid: Color,
    val degraded: Color,
    val highBeam: Color,
    val fogLight: Color,
) {
    companion object {
        fun resolve(theme: RideResolvedTheme): RidePalette = when (theme) {
            RideResolvedTheme.DAY -> RidePalette(
                background = Color(0xFF050607),
                surface = Color(0xFF111418),
                raisedSurface = Color(0xFF171D24),
                primaryText = Color(0xFFF4F6F8),
                secondaryText = Color(0xFFAEB5BD),
                disabledText = Color(0xFF626B76),
                divider = Color(0xFF343A42),
                accent = Color(0xFFE21B2D),
                accentBright = Color(0xFFE21B2D),
                warning = Color(0xFFFFB000),
                critical = Color(0xFFFF3B30),
                valid = Color(0xFF35D07F),
                degraded = Color(0xFFFFB000),
                highBeam = Color(0xFF3DA5FF),
                fogLight = Color(0xFF66D6E8),
            )
            RideResolvedTheme.NIGHT -> RidePalette(
                background = Color(0xFF050607),
                surface = Color(0xFF111418),
                raisedSurface = Color(0xFF171D24),
                primaryText = Color(0xFFF4F6F8),
                secondaryText = Color(0xFFAEB5BD),
                disabledText = Color(0xFF626B76),
                divider = Color(0xFF343A42),
                accent = Color(0xFFE21B2D),
                accentBright = Color(0xFFE21B2D),
                warning = Color(0xFFFFB000),
                critical = Color(0xFFFF3B30),
                valid = Color(0xFF35D07F),
                degraded = Color(0xFFFFB000),
                highBeam = Color(0xFF3DA5FF),
                fogLight = Color(0xFF66D6E8),
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
