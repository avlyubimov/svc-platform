package com.avlyubimov.svc.mobile

import android.content.Context
import android.provider.Settings
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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
    val brandId: String,
    val theme: String,
    val manufacturer: String? = null,
    val model: String,
    val generation: String,
    val year: Int,
    val manufacturerWordmark: String? = null,
    val vehicleModel: String,
    val vehicleGeneration: String,
    val brandTagline: String,
    val accentColor: String,
    val assets: MobileBrandAssets? = null,
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

@Serializable
internal data class MobileVehicleBrand(
    val id: String,
    val name: String,
    val categories: List<String>,
    val accentColor: String,
    val source: String,
    val preferredAsset: String? = null,
)

@Serializable
private data class MobileVehicleBrandCatalog(
    val schemaVersion: Int,
    val simpleIconsVersion: String,
    val brands: List<MobileVehicleBrand>,
)

internal data class ResolvedMobileBrandPack(
    val id: String,
    val logoAsset: String?,
    val wordmarkAsset: String?,
    val manufacturerDisplayName: String,
    val vehicleModel: String,
    val vehicleGeneration: String,
    val brandTagline: String,
    val accentColor: String,
)

internal class MobileBrandCatalog private constructor(
    val defaultProfileId: String,
    val fallbackProfileId: String,
    val profiles: List<MobileBrandPack>,
    vehicleBrands: List<MobileVehicleBrand>,
    private val assetExists: (String) -> Boolean,
) {
    private val definitions = profiles.associateBy(MobileBrandPack::id)
    private val vehicleDefinitions = vehicleBrands.associateBy(MobileVehicleBrand::id)

    fun resolve(requestedProfileId: String): ResolvedMobileBrandPack {
        val fallback = definitions[fallbackProfileId] ?: emergencyProfile
        val requested = definitions[requestedProfileId] ?: fallback
        if (requested.brandId != "svc") {
            val brand = vehicleDefinitions[requested.brandId]
            if (brand != null) {
                val standardLogo = vehicleBrandAsset(brand.id, "logo-on-dark.svg")
                val preferredLogo = brand.preferredAsset
                    ?.let { vehicleBrandAsset(brand.id, it) }
                    ?.takeIf(assetExists)
                val logo = preferredLogo ?: standardLogo.takeIf(assetExists)
                if (logo != null) {
                    return ResolvedMobileBrandPack(
                        id = requested.id,
                        logoAsset = logo,
                        wordmarkAsset = requested.assets?.wordmark?.takeIf(assetExists),
                        manufacturerDisplayName = brand.name,
                        vehicleModel = requested.vehicleModel,
                        vehicleGeneration = requested.vehicleGeneration,
                        brandTagline = requested.brandTagline,
                        accentColor = brand.accentColor,
                    )
                }
            }
        }
        return resolveSvc(fallback)
    }

    private fun resolveSvc(definition: MobileBrandPack): ResolvedMobileBrandPack =
        ResolvedMobileBrandPack(
            id = definition.id,
            logoAsset = definition.assets?.logo?.takeIf(assetExists),
            wordmarkAsset = definition.assets?.wordmark?.takeIf(assetExists),
            manufacturerDisplayName = definition.manufacturerWordmark
                ?: definition.manufacturer
                ?: "SVC",
            vehicleModel = definition.vehicleModel,
            vehicleGeneration = definition.vehicleGeneration,
            brandTagline = definition.brandTagline,
            accentColor = definition.accentColor,
        )

    private fun vehicleBrandAsset(brandId: String, fileName: String): String =
        "vehicle-brands/brands/$brandId/$fileName"

    companion object {
        private val json = Json {
            ignoreUnknownKeys = false
        }
        private val vehicleJson = Json {
            ignoreUnknownKeys = true
        }

        fun load(context: Context): MobileBrandCatalog = runCatching {
            decode(
                indexJson = context.readBrandAsset("brand-pack-index-v1.json"),
                configurationJson = { context.readBrandAsset(it) },
                vehicleCatalogJson = context.readBrandAsset(
                    "vehicle-brands/vehicle-brands-v1.json",
                ),
                assetExists = { context.hasBrandAsset(it) },
            )
        }.getOrElse { emergency }

        internal fun decode(
            indexJson: String,
            configurationJson: (String) -> String,
            vehicleCatalogJson: String,
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
            val vehicleCatalog = vehicleJson.decodeFromString<MobileVehicleBrandCatalog>(
                vehicleCatalogJson,
            )
            require(vehicleCatalog.schemaVersion == 1)
            require(
                vehicleCatalog.brands.map(MobileVehicleBrand::id).distinct().size ==
                    vehicleCatalog.brands.size,
            )
            require(
                profiles.all { profile ->
                    profile.brandId == "svc" ||
                        vehicleCatalog.brands.any { it.id == profile.brandId }
                },
            )
            return MobileBrandCatalog(
                defaultProfileId = document.defaultProfileId,
                fallbackProfileId = document.fallbackProfileId,
                profiles = profiles,
                vehicleBrands = vehicleCatalog.brands,
                assetExists = assetExists,
            )
        }

        private val emergencyProfile = MobileBrandPack(
            schemaVersion = 1,
            id = "emergency-svc",
            displayName = "SVC",
            brandId = "svc",
            theme = "svc-dark",
            manufacturer = "SVC",
            model = "Mobile",
            generation = "Fallback",
            year = 0,
            manufacturerWordmark = "SVC",
            vehicleModel = "SVC",
            vehicleGeneration = "",
            brandTagline = "",
            accentColor = "#E21B2D",
            assets = MobileBrandAssets(logo = ""),
        )

        private val emergency = MobileBrandCatalog(
            defaultProfileId = emergencyProfile.id,
            fallbackProfileId = emergencyProfile.id,
            profiles = listOf(emergencyProfile),
            vehicleBrands = emptyList(),
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
    val Background = androidx.compose.ui.graphics.Color(0xFF050607)
    val Surface = androidx.compose.ui.graphics.Color(0xFF111418)
    val PrimaryText = androidx.compose.ui.graphics.Color(0xFFF4F6F8)
    val SecondaryText = androidx.compose.ui.graphics.Color(0xFFAEB5BD)
    val ActiveRed = androidx.compose.ui.graphics.Color(0xFFE21B2D)
    val LightBlue = androidx.compose.ui.graphics.Color(0xFF3DA5FF)
    val Divider = androidx.compose.ui.graphics.Color(0xFF343A42)
    val Warning = androidx.compose.ui.graphics.Color(0xFFFFB000)
    val Critical = androidx.compose.ui.graphics.Color(0xFFFF3B30)
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

    fun brandPack(): ResolvedMobileBrandPack = catalog.resolve(profileId)
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
    brandPack: ResolvedMobileBrandPack,
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
    brandPack: ResolvedMobileBrandPack,
    timeline: MobileStartupTimeline,
    progress: Float,
) {
    val logo = phase(progress, 0.02f, 0.20f) *
        (1f - phase(progress, 0.25f, 0.36f))
    val lampCheck = phase(progress, 0.16f, 0.28f) *
        (1f - phase(progress, 0.38f, 0.48f))
    val sweep = if (progress < 0.62f) {
        phase(progress, 0.28f, 0.62f)
    } else {
        1f - phase(progress, 0.62f, 0.80f)
    }
    val cluster = phase(progress, 0.72f, 0.90f)
    val transition = phase(
        progress,
        timeline.progress(timeline.phases.taglineEndMs),
        1f,
    )
    val accent = MobileColors.ActiveRed
    Box(
        Modifier
            .fillMaxSize()
            .background(
                MobileColors.Background
                    .copy(alpha = 1f - transition),
            ),
    ) {
        Canvas(Modifier.fillMaxSize().alpha(phase(progress, 0f, 0.18f))) {
            val centerY = size.height * 0.5f
            drawLine(
                MobileColors.ActiveRed,
                start = androidx.compose.ui.geometry.Offset(size.width * 0.12f, centerY - 14.dp.toPx()),
                end = androidx.compose.ui.geometry.Offset(size.width * 0.43f, centerY - 14.dp.toPx()),
                strokeWidth = 2.dp.toPx(),
            )
            drawLine(
                MobileColors.PrimaryText,
                start = androidx.compose.ui.geometry.Offset(size.width * 0.10f, centerY),
                end = androidx.compose.ui.geometry.Offset(size.width * 0.40f, centerY),
                strokeWidth = 1.dp.toPx(),
            )
            drawLine(
                MobileColors.LightBlue,
                start = androidx.compose.ui.geometry.Offset(size.width * 0.15f, centerY + 14.dp.toPx()),
                end = androidx.compose.ui.geometry.Offset(size.width * 0.34f, centerY + 14.dp.toPx()),
                strokeWidth = 1.dp.toPx(),
            )
            drawLine(
                MobileColors.ActiveRed,
                start = androidx.compose.ui.geometry.Offset(size.width * 0.57f, centerY - 14.dp.toPx()),
                end = androidx.compose.ui.geometry.Offset(size.width * 0.88f, centerY - 14.dp.toPx()),
                strokeWidth = 2.dp.toPx(),
            )
            drawLine(
                MobileColors.PrimaryText,
                start = androidx.compose.ui.geometry.Offset(size.width * 0.60f, centerY),
                end = androidx.compose.ui.geometry.Offset(size.width * 0.90f, centerY),
                strokeWidth = 1.dp.toPx(),
            )
            drawLine(
                MobileColors.LightBlue,
                start = androidx.compose.ui.geometry.Offset(size.width * 0.66f, centerY + 14.dp.toPx()),
                end = androidx.compose.ui.geometry.Offset(size.width * 0.85f, centerY + 14.dp.toPx()),
                strokeWidth = 1.dp.toPx(),
            )
        }
        Box(
            modifier = Modifier
                .align(Alignment.Center)
                .size(116.dp)
                .scale(0.88f + logo * 0.12f)
                .alpha(logo),
            contentAlignment = Alignment.Center,
        ) {
            Canvas(Modifier.fillMaxSize()) {
                drawCircle(MobileColors.Surface)
                drawCircle(
                    color = accent,
                    style = Stroke(2.dp.toPx()),
                )
            }
            Text(
                "SVC",
                color = MobileColors.PrimaryText,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 2.sp,
            )
        }

        Row(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = 18.dp)
                .alpha(lampCheck),
            horizontalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            listOf(
                "←" to androidx.compose.ui.graphics.Color(0xFF4AC27E),
                "HIGH" to MobileColors.LightBlue,
                "ABS" to MobileColors.Warning,
                "ENGINE" to MobileColors.Warning,
                "SVC" to MobileColors.Critical,
                "→" to androidx.compose.ui.graphics.Color(0xFF4AC27E),
            ).forEach { (label, color) ->
                Text(
                    label,
                    color = color,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                )
            }
        }

        Canvas(
            Modifier
                .fillMaxSize()
                .alpha(phase(progress, 0.24f, 0.34f) * (1f - transition)),
        ) {
            val segmentCount = 45
            val left = size.width * 0.06f
            val right = size.width * 0.94f
            val width = right - left
            val gap = 4.dp.toPx()
            val segmentWidth = (width - gap * (segmentCount - 1)) / segmentCount
            val top = size.height * 0.08f
            val height = 20.dp.toPx()
            repeat(segmentCount) { segment ->
                val ratio = (segment + 1f) / segmentCount
                val inactive = when {
                    ratio > 8f / 9f -> accent.copy(alpha = 0.42f)
                    ratio > 7f / 9f -> MobileColors.Warning.copy(alpha = 0.34f)
                    else -> MobileColors.Divider
                }
                val active = when {
                    ratio > 8f / 9f -> accent
                    ratio > 7f / 9f -> MobileColors.Warning
                    else -> MobileColors.PrimaryText
                }
                drawRect(
                    color = if (segment.toFloat() / segmentCount < sweep) active else inactive,
                    topLeft = androidx.compose.ui.geometry.Offset(
                        left + segment * (segmentWidth + gap),
                        top,
                    ),
                    size = androidx.compose.ui.geometry.Size(segmentWidth, height),
                )
            }
        }

        Row(
            modifier = Modifier
                .align(Alignment.Center)
                .fillMaxWidth(0.46f)
                .alpha(cluster * (1f - transition)),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    "0",
                    color = MobileColors.PrimaryText,
                    fontSize = 82.sp,
                    fontWeight = FontWeight.Light,
                )
                Text(
                    "km/h",
                    color = MobileColors.SecondaryText,
                    fontSize = 14.sp,
                    letterSpacing = 1.2.sp,
                )
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    "N",
                    color = androidx.compose.ui.graphics.Color(0xFF35D07F),
                    fontSize = 58.sp,
                    fontWeight = FontWeight.Medium,
                )
            }
        }
    }
}

private fun Context.readBrandAsset(path: String): String =
    assets.open(path).bufferedReader().use { it.readText() }

private fun Context.hasBrandAsset(path: String): Boolean =
    runCatching { assets.open(path).use { } }.isSuccess

internal fun String.toComposeColor(): androidx.compose.ui.graphics.Color =
    androidx.compose.ui.graphics.Color(android.graphics.Color.parseColor(this))

private fun phase(value: Float, start: Float, end: Float): Float =
    ((value - start) / (end - start)).coerceIn(0f, 1f)
