package com.avlyubimov.svc.mobile

import android.content.Context
import android.graphics.Color
import android.provider.Settings
import android.webkit.WebView
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.coroutines.delay

internal data class MobileBrandPack(
    val id: String,
    val theme: String,
    val manufacturer: String,
    val model: String,
    val generation: String,
    val year: Int,
    val logoAsset: String?,
    val wordmarkAsset: String?,
    val manufacturerWordmark: String,
    val vehicleModel: String,
    val vehicleGeneration: String,
    val brandTagline: String,
)

internal object MobileColors {
    val Background = androidx.compose.ui.graphics.Color(0xFF050505)
    val Surface = androidx.compose.ui.graphics.Color(0xFF111214)
    val PrimaryText = androidx.compose.ui.graphics.Color(0xFFF4F4F4)
    val SecondaryText = androidx.compose.ui.graphics.Color(0xFFA7A9AC)
    val BmwBlue = androidx.compose.ui.graphics.Color(0xFF1C69D4)
    val LightBlue = androidx.compose.ui.graphics.Color(0xFF4AA3FF)
    val Divider = androidx.compose.ui.graphics.Color(0xFF303236)
    val Warning = androidx.compose.ui.graphics.Color(0xFFFFB000)
    val Critical = androidx.compose.ui.graphics.Color(0xFFE32636)
}

internal class AppearancePreferences(context: Context) {
    private val values = context.getSharedPreferences("svc-appearance", Context.MODE_PRIVATE)

    var profileId: String
        get() = values.getString("vehicleProfile", BMW_PROFILE) ?: BMW_PROFILE
        set(value) = values.edit().putString("vehicleProfile", value).apply()

    var animationEnabled: Boolean
        get() = values.getBoolean("startupAnimationEnabled", true)
        set(value) = values.edit().putBoolean("startupAnimationEnabled", value).apply()

    var reduceMotionOverride: Boolean
        get() = values.getBoolean("startupReduceMotionOverride", false)
        set(value) = values.edit().putBoolean("startupReduceMotionOverride", value).apply()

    fun restoreScreen(): String = values.getString("lastSelectedScreen", "DASHBOARD")
        ?: "DASHBOARD"

    fun storeScreen(name: String) {
        values.edit().putString("lastSelectedScreen", name).apply()
    }

    fun brandPack(context: Context): MobileBrandPack {
        return resolveBrandPack(
            requestedProfile = profileId,
            hasLogo = hasAsset(context, "bmw-roundel.svg"),
            hasWordmark = hasAsset(context, "bmw-motorrad-wordmark.svg"),
        )
    }

    private fun hasAsset(context: Context, name: String): Boolean =
        runCatching { context.assets.open(name).use { } }.isSuccess

    companion object {
        const val BMW_PROFILE = "bmw-r1200gs-k25-personal"
        const val GENERIC_PROFILE = "generic-automotive"
    }
}

internal fun resolveBrandPack(
    requestedProfile: String,
    hasLogo: Boolean,
    hasWordmark: Boolean,
): MobileBrandPack {
    if (requestedProfile != AppearancePreferences.BMW_PROFILE || !hasLogo || !hasWordmark) {
        return genericBrandPack()
    }
    return MobileBrandPack(
            id = AppearancePreferences.BMW_PROFILE,
            theme = "svc-boxer-blue",
            manufacturer = "BMW",
            model = "R1200GS",
            generation = "K25",
            year = 2007,
            logoAsset = "bmw-roundel.svg",
            wordmarkAsset = "bmw-motorrad-wordmark.svg",
            manufacturerWordmark = "BMW MOTORRAD",
            vehicleModel = "R 1200 GS",
            vehicleGeneration = "K25 · 2007",
            brandTagline = "MAKE LIFE A RIDE",
        )
}

internal fun genericBrandPack() = MobileBrandPack(
            id = AppearancePreferences.GENERIC_PROFILE,
            theme = "svc-boxer-blue",
            manufacturer = "SVC",
            model = "Smart Vehicle Controller",
            generation = "Generic Automotive",
            year = 2026,
            logoAsset = null,
            wordmarkAsset = null,
            manufacturerWordmark = "SMART VEHICLE CONTROLLER",
            vehicleModel = "SVC",
            vehicleGeneration = "GENERIC AUTOMOTIVE",
            brandTagline = "ENGINEERED FOR THE RIDE",
        )

internal fun startupDurationMs(
    enabled: Boolean,
    reduceMotion: Boolean,
    critical: Boolean,
): Int = when {
    !enabled -> 0
    critical || reduceMotion -> 500
    else -> 2100
}

internal fun systemReduceMotion(context: Context): Boolean =
    runCatching {
        Settings.Global.getFloat(
            context.contentResolver,
            Settings.Global.ANIMATOR_DURATION_SCALE,
            1f,
        ) == 0f
    }.getOrDefault(false)

@Composable
internal fun StartupAnimation(
    brandPack: MobileBrandPack,
    enabled: Boolean,
    reduceMotion: Boolean,
    critical: Boolean,
    replayKey: Int,
    onComplete: () -> Unit,
) {
    val progress = remember(replayKey) { Animatable(0f) }
    val durationMs = startupDurationMs(enabled, reduceMotion, critical)
    LaunchedEffect(replayKey, enabled, durationMs) {
        if (durationMs > 0) {
            progress.animateTo(
                1f,
                animationSpec = tween(durationMillis = durationMs, easing = LinearEasing),
            )
        } else {
            progress.snapTo(1f)
        }
        onComplete()
    }
    StartupVisual(brandPack, progress.value)
}

@Composable
private fun StartupVisual(brandPack: MobileBrandPack, progress: Float) {
    val logo = phase(progress, 0.12f, 0.33f)
    val identity = phase(progress, 0.33f, 0.57f)
    val tagline = phase(progress, 0.57f, 0.76f)
    val transition = phase(progress, 0.76f, 1f)
    Box(
        Modifier
            .fillMaxSize()
            .background(MobileColors.Background.copy(alpha = 1f - transition)),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.fillMaxSize().alpha(phase(progress, 0f, 0.16f))) {
            drawCircle(
                brush = Brush.radialGradient(
                    listOf(MobileColors.LightBlue.copy(alpha = 0.12f), androidx.compose.ui.graphics.Color.Transparent),
                    center = center,
                    radius = size.minDimension * 0.38f,
                ),
            )
        }
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.scale(1f - 0.04f * transition),
        ) {
            Box(
                Modifier
                    .size(112.dp)
                    .scale(0.92f + 0.08f * logo - 0.06f * transition)
                    .alpha(logo * (1f - transition)),
            ) {
                BrandLogo(brandPack, Modifier.fillMaxSize())
                Canvas(
                    Modifier
                        .fillMaxSize()
                        .alpha(
                            phase(progress, 0.20f, 0.24f) *
                                (1f - phase(progress, 0.24f, 0.29f)),
                        ),
                ) {
                    drawArc(
                        color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.82f),
                        startAngle = 205f,
                        sweepAngle = 70f,
                        useCenter = false,
                        style = Stroke(1.dp.toPx()),
                    )
                }
            }
            Spacer(Modifier.height(15.dp))
            if (brandPack.wordmarkAsset != null) {
                LocalSvgAsset(
                    brandPack.wordmarkAsset,
                    Modifier
                        .size(width = 210.dp, height = 28.dp)
                        .alpha(identity * (1f - transition)),
                )
            } else {
                Text(
                    brandPack.manufacturerWordmark,
                    color = MobileColors.PrimaryText,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.SemiBold,
                    letterSpacing = 4.5.sp,
                    modifier = Modifier.alpha(identity * (1f - transition)),
                )
            }
            Spacer(Modifier.height(7.dp))
            Text(
                brandPack.vehicleModel,
                color = MobileColors.PrimaryText,
                fontSize = 15.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 2.2.sp,
                modifier = Modifier.alpha(identity * (1f - transition)),
            )
            Text(
                brandPack.vehicleGeneration,
                color = MobileColors.SecondaryText,
                fontSize = 12.sp,
                letterSpacing = 1.8.sp,
                modifier = Modifier.alpha(identity * (1f - transition)),
            )
            Spacer(Modifier.height(15.dp))
            Text(
                brandPack.brandTagline,
                color = MobileColors.PrimaryText,
                fontSize = 12.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 2.8.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier.alpha(tagline * (1f - transition)),
            )
        }
        Canvas(Modifier.fillMaxSize().alpha(transition * (1f - transition))) {
            drawLine(
                brush = Brush.horizontalGradient(
                    listOf(
                        androidx.compose.ui.graphics.Color.Transparent,
                        MobileColors.BmwBlue,
                        androidx.compose.ui.graphics.Color.White,
                        androidx.compose.ui.graphics.Color.Transparent,
                    ),
                ),
                start = center.copy(x = center.x * (1f - transition)),
                end = center.copy(x = center.x * (1f + transition)),
                strokeWidth = 1.dp.toPx(),
            )
        }
    }
}

@Composable
private fun BrandLogo(brandPack: MobileBrandPack, modifier: Modifier) {
    if (brandPack.logoAsset != null) {
        LocalSvgAsset(brandPack.logoAsset, modifier)
    } else {
        Box(modifier, contentAlignment = Alignment.Center) {
            Canvas(Modifier.fillMaxSize()) {
                drawCircle(MobileColors.Surface)
                drawCircle(MobileColors.PrimaryText.copy(alpha = 0.72f), style = Stroke(2.dp.toPx()))
            }
            Text(
                "SVC",
                color = MobileColors.PrimaryText,
                fontSize = 26.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.5.sp,
            )
        }
    }
}

@Composable
private fun LocalSvgAsset(asset: String, modifier: Modifier) {
    AndroidView(
        modifier = modifier,
        factory = { context ->
            WebView(context).apply {
                setBackgroundColor(Color.TRANSPARENT)
                settings.allowFileAccess = true
                isVerticalScrollBarEnabled = false
                isHorizontalScrollBarEnabled = false
                loadUrl("file:///android_asset/$asset")
            }
        },
    )
}

private fun phase(value: Float, start: Float, end: Float): Float =
    ((value - start) / (end - start)).coerceIn(0f, 1f)
