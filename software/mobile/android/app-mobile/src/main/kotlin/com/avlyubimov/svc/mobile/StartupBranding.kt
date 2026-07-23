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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
internal data class MobileBrandAssets(
    val logo: String,
    val wordmark: String? = null,
)

@Serializable
internal data class MobileBrandPack(
    val schemaVersion: Int,
    val id: String,
    val displayName: String,
    val theme: String,
    val manufacturer: String,
    val model: String,
    val generation: String,
    val year: Int,
    val manufacturerWordmark: String,
    val vehicleModel: String,
    val vehicleGeneration: String,
    val brandTagline: String,
    val accentColor: String,
    val assets: MobileBrandAssets,
)

@Serializable
private data class MobileBrandCatalogEntry(
    val id: String,
    val configuration: String,
)

@Serializable
private data class MobileBrandCatalogDocument(
    val schemaVersion: Int,
    val defaultProfileId: String,
    val fallbackProfileId: String,
    val profiles: List<MobileBrandCatalogEntry>,
)

internal class MobileBrandCatalog private constructor(
    val defaultProfileId: String,
    val fallbackProfileId: String,
    val profiles: List<MobileBrandPack>,
    private val assetExists: (String) -> Boolean,
) {
    private val definitions = profiles.associateBy(MobileBrandPack::id)

    fun resolve(requestedProfileId: String): MobileBrandPack {
        val fallback = definitions[fallbackProfileId] ?: emergencyProfile
        val requested = definitions[requestedProfileId] ?: fallback
        return if (assetExists(requested.assets.logo)) requested else fallback
    }

    companion object {
        private val json = Json {
            ignoreUnknownKeys = false
        }

        fun load(context: Context): MobileBrandCatalog = runCatching {
            decode(
                indexJson = context.readBrandAsset("brand-pack-index-v1.json"),
                configurationJson = { context.readBrandAsset(it) },
                assetExists = { context.hasBrandAsset(it) },
            )
        }.getOrElse { emergency }

        internal fun decode(
            indexJson: String,
            configurationJson: (String) -> String,
            assetExists: (String) -> Boolean,
        ): MobileBrandCatalog {
            val document = json.decodeFromString<MobileBrandCatalogDocument>(indexJson)
            require(document.schemaVersion == 1)
            val profiles = document.profiles.map { entry ->
                json.decodeFromString<MobileBrandPack>(
                    configurationJson(entry.configuration),
                ).also {
                    require(it.schemaVersion == 1)
                    require(it.id == entry.id)
                }
            }
            require(profiles.map(MobileBrandPack::id).distinct().size == profiles.size)
            require(profiles.any { it.id == document.defaultProfileId })
            require(profiles.any { it.id == document.fallbackProfileId })
            return MobileBrandCatalog(
                defaultProfileId = document.defaultProfileId,
                fallbackProfileId = document.fallbackProfileId,
                profiles = profiles,
                assetExists = assetExists,
            )
        }

        private val emergencyProfile = MobileBrandPack(
            schemaVersion = 1,
            id = "emergency-svc",
            displayName = "SVC",
            theme = "svc-dark",
            manufacturer = "SVC",
            model = "Mobile",
            generation = "Fallback",
            year = 0,
            manufacturerWordmark = "SVC",
            vehicleModel = "SVC",
            vehicleGeneration = "",
            brandTagline = "",
            accentColor = "#1C69D4",
            assets = MobileBrandAssets(logo = ""),
        )

        private val emergency = MobileBrandCatalog(
            defaultProfileId = emergencyProfile.id,
            fallbackProfileId = emergencyProfile.id,
            profiles = listOf(emergencyProfile),
            assetExists = { false },
        )
    }
}

@Serializable
internal data class MobileStartupPhases(
    val screenOnEndMs: Int,
    val logoEndMs: Int,
    val identityEndMs: Int,
    val taglineEndMs: Int,
    val dashboardEndMs: Int,
)

@Serializable
internal data class MobileStartupTimeline(
    val schemaVersion: Int,
    val durationMs: Int,
    val criticalDurationMs: Int,
    val phases: MobileStartupPhases,
) {
    fun durationMs(
        enabled: Boolean,
        reduceMotion: Boolean,
        critical: Boolean,
    ): Int = when {
        !enabled -> 0
        reduceMotion || critical -> criticalDurationMs
        else -> durationMs
    }

    fun progress(milliseconds: Int): Float = milliseconds.toFloat() / durationMs

    companion object {
        fun load(context: Context): MobileStartupTimeline = runCatching {
            Json.decodeFromString<MobileStartupTimeline>(
                context.readBrandAsset("startup-animation-v1.json"),
            ).also {
                require(it.schemaVersion == 1)
                require(it.phases.dashboardEndMs == it.durationMs)
            }
        }.getOrElse {
            MobileStartupTimeline(
                schemaVersion = 1,
                durationMs = 300,
                criticalDurationMs = 300,
                phases = MobileStartupPhases(50, 100, 160, 220, 300),
            )
        }
    }
}

internal object MobileColors {
    val Background = androidx.compose.ui.graphics.Color(0xFF050505)
    val Surface = androidx.compose.ui.graphics.Color(0xFF111214)
    val PrimaryText = androidx.compose.ui.graphics.Color(0xFFF4F4F4)
    val SecondaryText = androidx.compose.ui.graphics.Color(0xFFA7A9AC)
    val AccentBlue = androidx.compose.ui.graphics.Color(0xFF1C69D4)
    val LightBlue = androidx.compose.ui.graphics.Color(0xFF4AA3FF)
    val Divider = androidx.compose.ui.graphics.Color(0xFF303236)
    val Warning = androidx.compose.ui.graphics.Color(0xFFFFB000)
    val Critical = androidx.compose.ui.graphics.Color(0xFFE32636)
}

internal class AppearancePreferences(
    context: Context,
    private val catalog: MobileBrandCatalog,
) {
    private val values = context.getSharedPreferences("svc-appearance", Context.MODE_PRIVATE)

    var profileId: String
        get() {
            val stored = values.getString("vehicleProfile", catalog.defaultProfileId)
                ?: catalog.defaultProfileId
            return stored.takeIf { candidate ->
                catalog.profiles.any { it.id == candidate }
            } ?: catalog.fallbackProfileId
        }
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

    fun brandPack(): MobileBrandPack = catalog.resolve(profileId)
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
    timeline: MobileStartupTimeline,
    enabled: Boolean,
    reduceMotion: Boolean,
    critical: Boolean,
    replayKey: Int,
    onComplete: () -> Unit,
) {
    val progress = remember(replayKey) { Animatable(0f) }
    val durationMs = timeline.durationMs(enabled, reduceMotion, critical)
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
    StartupVisual(brandPack, timeline, progress.value)
}

@Composable
private fun StartupVisual(
    brandPack: MobileBrandPack,
    timeline: MobileStartupTimeline,
    progress: Float,
) {
    val screenOnEnd = timeline.progress(timeline.phases.screenOnEndMs)
    val logoEnd = timeline.progress(timeline.phases.logoEndMs)
    val identityEnd = timeline.progress(timeline.phases.identityEndMs)
    val taglineEnd = timeline.progress(timeline.phases.taglineEndMs)
    val logo = phase(progress, screenOnEnd, logoEnd)
    val identity = phase(progress, logoEnd, identityEnd)
    val tagline = phase(progress, identityEnd, taglineEnd)
    val transition = phase(progress, taglineEnd, 1f)
    val accent = brandPack.accentColor.toComposeColor()
    Box(
        Modifier
            .fillMaxSize()
            .background(MobileColors.Background.copy(alpha = 1f - transition)),
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.fillMaxSize().alpha(phase(progress, 0f, screenOnEnd))) {
            drawCircle(
                brush = Brush.radialGradient(
                    listOf(
                        MobileColors.LightBlue.copy(alpha = 0.12f),
                        androidx.compose.ui.graphics.Color.Transparent,
                    ),
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
                            phase(logo, 0.38f, 0.48f) *
                                (1f - phase(logo, 0.48f, 0.72f)),
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
            if (brandPack.assets.wordmark != null) {
                LocalSvgAsset(
                    brandPack.assets.wordmark,
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
                        accent,
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
    if (brandPack.assets.logo.isNotEmpty()) {
        LocalSvgAsset(brandPack.assets.logo, modifier)
    } else {
        Box(modifier, contentAlignment = Alignment.Center) {
            Canvas(Modifier.fillMaxSize()) {
                drawCircle(MobileColors.Surface)
                drawCircle(
                    MobileColors.PrimaryText.copy(alpha = 0.72f),
                    style = Stroke(2.dp.toPx()),
                )
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

private fun Context.readBrandAsset(path: String): String =
    assets.open(path).bufferedReader().use { it.readText() }

private fun Context.hasBrandAsset(path: String): Boolean =
    runCatching { assets.open(path).use { } }.isSuccess

internal fun String.toComposeColor(): androidx.compose.ui.graphics.Color =
    androidx.compose.ui.graphics.Color(android.graphics.Color.parseColor(this))

private fun phase(value: Float, start: Float, end: Float): Float =
    ((value - start) / (end - start)).coerceIn(0f, 1f)
