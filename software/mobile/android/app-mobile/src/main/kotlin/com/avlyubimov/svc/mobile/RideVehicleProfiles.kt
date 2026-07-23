package com.avlyubimov.svc.mobile

import android.content.Context
import com.avlyubimov.svc.core.model.RideThemeMode
import com.avlyubimov.svc.core.model.RideThemeThresholds
import com.avlyubimov.svc.core.model.VehiclePerformanceProfile
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
private data class VehiclePerformanceCatalogEntry(
    val id: String,
    val configuration: String,
)

@Serializable
private data class VehiclePerformanceCatalogDocument(
    val schemaVersion: Int,
    val defaultProfileId: String,
    val fallbackProfileId: String,
    val profiles: List<VehiclePerformanceCatalogEntry>,
)

internal class MobileVehiclePerformanceCatalog private constructor(
    val defaultProfileId: String,
    val fallbackProfileId: String,
    val profiles: List<VehiclePerformanceProfile>,
) {
    private val definitions = profiles.associateBy(VehiclePerformanceProfile::id)

    fun resolve(profileId: String): VehiclePerformanceProfile =
        definitions[profileId]
            ?: definitions[fallbackProfileId]
            ?: emergencyProfile

    companion object {
        private val json = Json { ignoreUnknownKeys = false }

        fun load(context: Context): MobileVehiclePerformanceCatalog = runCatching {
            decode(
                indexJson = context.readRideAsset(
                    "vehicle-profiles/vehicle-profile-index-v1.json",
                ),
                configurationJson = {
                    context.readRideAsset("vehicle-profiles/$it")
                },
            )
        }.getOrElse { emergency }

        internal fun decode(
            indexJson: String,
            configurationJson: (String) -> String,
        ): MobileVehiclePerformanceCatalog {
            val document = json.decodeFromString<VehiclePerformanceCatalogDocument>(
                indexJson,
            )
            require(document.schemaVersion == 1)
            val profiles = document.profiles.map { entry ->
                json.decodeFromString<VehiclePerformanceProfile>(
                    configurationJson(entry.configuration),
                ).also {
                    require(it.schemaVersion == 1)
                    require(it.id == entry.id)
                }
            }
            require(profiles.map(VehiclePerformanceProfile::id).distinct().size == profiles.size)
            require(profiles.any { it.id == document.defaultProfileId })
            require(profiles.any { it.id == document.fallbackProfileId })
            return MobileVehiclePerformanceCatalog(
                defaultProfileId = document.defaultProfileId,
                fallbackProfileId = document.fallbackProfileId,
                profiles = profiles,
            )
        }

        private val emergencyProfile = VehiclePerformanceProfile(
            schemaVersion = 1,
            id = "emergency-generic-motorcycle",
            manufacturer = "Generic",
            model = "Motorcycle",
            generation = null,
            yearFrom = null,
            yearTo = null,
            engineName = null,
            engineDisplacementCc = null,
            maximumTorqueNm = null,
            nominalPowerKw = null,
            gearboxGears = null,
            fuelCapacityLiters = null,
            fuelReserveLiters = null,
            iceWarningTemperatureCelsius = null,
            idleRpm = null,
            idleToleranceRpm = null,
            torquePeakRpm = null,
            powerPeakRpm = null,
            tachometerScaleMinRpm = 0,
            tachometerScaleMaxRpm = null,
            warningStartRpm = null,
            redZoneStartRpm = null,
            revLimiterRpm = null,
            source = "Emergency no-assumption fallback",
            reference = "docs/reference-vehicle/bmw-k25-2007/dashboard-profile.md",
            confidence = "unknown",
        )

        private val emergency = MobileVehiclePerformanceCatalog(
            defaultProfileId = emergencyProfile.id,
            fallbackProfileId = emergencyProfile.id,
            profiles = listOf(emergencyProfile),
        )
    }
}

internal class RidePreferences(
    context: Context,
    private val catalog: MobileVehiclePerformanceCatalog,
) {
    private val values = context.getSharedPreferences(
        "svc-ride-dashboard",
        Context.MODE_PRIVATE,
    )

    var vehicleProfileId: String
        get() {
            val stored = values.getString("vehiclePerformanceProfile", null)
            return when {
                stored == null -> catalog.defaultProfileId
                catalog.profiles.any { it.id == stored } -> stored
                else -> catalog.fallbackProfileId
            }
        }
        set(value) {
            values.edit().putString("vehiclePerformanceProfile", value).apply()
        }

    var themeMode: RideThemeMode
        get() = values.getString("rideThemeMode", null)
            ?.let { runCatching { RideThemeMode.valueOf(it) }.getOrNull() }
            ?: RideThemeMode.AUTOMATIC
        set(value) {
            values.edit().putString("rideThemeMode", value.name).apply()
        }

    var nightEnterLux: Double
        get() = values.getFloat(
            "rideNightEnterLux",
            RideThemeThresholds.DEFAULT.nightEnterLux.toFloat(),
        ).toDouble()
        set(value) {
            values.edit().putFloat("rideNightEnterLux", value.toFloat()).apply()
        }

    var dayEnterLux: Double
        get() = values.getFloat(
            "rideDayEnterLux",
            RideThemeThresholds.DEFAULT.dayEnterLux.toFloat(),
        ).toDouble()
        set(value) {
            values.edit().putFloat("rideDayEnterLux", value.toFloat()).apply()
        }

    fun vehicleProfile(): VehiclePerformanceProfile =
        catalog.resolve(vehicleProfileId)

    fun themeThresholds(): RideThemeThresholds = RideThemeThresholds(
        nightEnterLux = minOf(nightEnterLux, dayEnterLux - 50),
        dayEnterLux = maxOf(dayEnterLux, nightEnterLux + 50),
    )
}

private fun Context.readRideAsset(path: String): String =
    assets.open(path).bufferedReader().use { it.readText() }
