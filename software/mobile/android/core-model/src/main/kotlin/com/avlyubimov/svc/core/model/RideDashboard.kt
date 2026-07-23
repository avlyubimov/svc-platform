package com.avlyubimov.svc.core.model

enum class RideDataState {
    VALID,
    STALE,
    DEGRADED,
    INVALID,
    UNAVAILABLE,
}

data class RideValue<T>(
    val value: T?,
    val unit: String,
    val state: RideDataState,
) {
    val displayValue: T?
        get() = when (state) {
            RideDataState.VALID,
            RideDataState.DEGRADED,
            -> value
            RideDataState.STALE,
            RideDataState.INVALID,
            RideDataState.UNAVAILABLE,
            -> null
        }
}

fun <T> Measurement<T>.toRideValue(): RideValue<T> {
    val state = when {
        stale -> RideDataState.STALE
        !valid || value == null -> if (quality == MeasurementQuality.INVALID) {
            RideDataState.INVALID
        } else {
            RideDataState.UNAVAILABLE
        }
        quality == MeasurementQuality.GOOD -> RideDataState.VALID
        quality == MeasurementQuality.DEGRADED -> RideDataState.DEGRADED
        quality == MeasurementQuality.INVALID -> RideDataState.INVALID
        else -> RideDataState.UNAVAILABLE
    }
    return RideValue(value = value, unit = unit, state = state)
}

enum class RideGear(val displayValue: String) {
    NEUTRAL("N"),
    FIRST("1"),
    SECOND("2"),
    THIRD("3"),
    FOURTH("4"),
    FIFTH("5"),
    SIXTH("6"),
    BETWEEN("BETWEEN"),
    UNAVAILABLE("—"),
}

enum class TachometerZone {
    NORMAL,
    WARNING,
    RED,
    UNAVAILABLE,
}

object TachometerZoneResolver {
    fun zone(rpm: Double?, profile: VehiclePerformanceProfile): TachometerZone {
        if (rpm == null || profile.tachometerScaleMaxRpm == null) {
            return TachometerZone.UNAVAILABLE
        }
        if (profile.redZoneStartRpm?.let { rpm >= it } == true) {
            return TachometerZone.RED
        }
        if (profile.warningStartRpm?.let { rpm >= it } == true) {
            return TachometerZone.WARNING
        }
        return TachometerZone.NORMAL
    }

    fun zoneWithHysteresis(
        rpm: Double?,
        profile: VehiclePerformanceProfile,
        previous: TachometerZone,
        hysteresisRpm: Double = 80.0,
    ): TachometerZone {
        if (rpm == null) return TachometerZone.UNAVAILABLE
        val raw = zone(rpm, profile)
        return when (previous) {
            TachometerZone.RED -> {
                if (
                    profile.redZoneStartRpm?.let {
                        rpm >= it - hysteresisRpm
                    } == true
                ) {
                    TachometerZone.RED
                } else {
                    raw
                }
            }
            TachometerZone.WARNING -> when {
                profile.redZoneStartRpm?.let { rpm >= it } == true ->
                    TachometerZone.RED
                profile.warningStartRpm?.let {
                    rpm >= it - hysteresisRpm
                } == true ->
                    TachometerZone.WARNING
                else -> raw
            }
            TachometerZone.NORMAL,
            TachometerZone.UNAVAILABLE,
            -> raw
        }
    }
}

data class LeanExtrema(
    val maximumLeftDegrees: Double = 0.0,
    val maximumRightDegrees: Double = 0.0,
) {
    fun observe(leanDegrees: Double?): LeanExtrema = when {
        leanDegrees == null -> this
        leanDegrees < 0 -> copy(
            maximumLeftDegrees = maxOf(maximumLeftDegrees, kotlin.math.abs(leanDegrees)),
        )
        else -> copy(maximumRightDegrees = maxOf(maximumRightDegrees, leanDegrees))
    }

    fun resetIfStationary(speed: RideValue<Double>): LeanExtrema =
        if (speed.displayValue == 0.0) LeanExtrema() else this
}

data class MotorcycleMountingTransform(
    val rollDegrees: Double,
    val pitchDegrees: Double,
    val yawDegrees: Double,
    val zeroOffsetDegrees: Double,
)

object MotorcycleCalibrationPolicy {
    fun canCalibrate(speed: RideValue<Double>, demoMode: Boolean): Boolean =
        demoMode && speed.displayValue == 0.0
}

enum class RideAlertSeverity(val priority: Int) {
    INFO(0),
    WARNING(1),
    CRITICAL(2),
}

data class RideAlert(
    val id: String,
    val title: String,
    val severity: RideAlertSeverity,
)

data class RideDashboardState(
    val speed: RideValue<Double>,
    val engineRpm: RideValue<Double>,
    val gear: RideGear,
    val leanAngle: RideValue<Double>,
    val engineTemperature: RideValue<Double>,
    val fuelLevel: RideValue<Double>,
    val ambientTemperature: RideValue<Double>,
    val ambientLight: RideValue<Double>,
    val batteryVoltage: RideValue<Double>,
    val totalCurrent: RideValue<Double>,
    val canState: RideValue<String>,
    val bleLabel: String,
    val bleState: RideDataState,
    val tachometerZone: TachometerZone,
    val alerts: List<RideAlert>,
    val profile: VehiclePerformanceProfile,
) {
    val activeAlert: RideAlert?
        get() = alerts.maxWithOrNull(
            compareBy<RideAlert> { it.severity.priority }.thenByDescending { it.id },
        )

    companion object {
        fun build(
            telemetry: TelemetrySnapshot,
            connectionState: ConnectionState,
            isConnecting: Boolean,
            profile: VehiclePerformanceProfile,
            leanCalibrated: Boolean = false,
        ): RideDashboardState {
            val speed = telemetry.vehicle.speed.toRideValue()
            val rpm = telemetry.vehicle.engineRpm.toRideValue()
            val rawLean = telemetry.leanAngle.toRideValue()
            val lean = rawLean.copy(
                state = if (
                    rawLean.state == RideDataState.VALID && !leanCalibrated
                ) {
                    RideDataState.DEGRADED
                } else {
                    rawLean.state
                },
            )
            val ble = when {
                isConnecting -> "CONNECTING" to RideDataState.DEGRADED
                connectionState == ConnectionState.CONNECTED ->
                    "BLE" to RideDataState.VALID
                connectionState == ConnectionState.SCANNING ->
                    "SCANNING" to RideDataState.DEGRADED
                else -> "BLE LOST" to RideDataState.UNAVAILABLE
            }
            val zone = TachometerZoneResolver.zone(rpm.displayValue, profile)
            return RideDashboardState(
                speed = speed,
                engineRpm = rpm,
                gear = RideGear.UNAVAILABLE,
                leanAngle = lean,
                engineTemperature = telemetry.vehicle.engineTemperature.toRideValue(),
                fuelLevel = telemetry.vehicle.fuelLevel.toRideValue(),
                ambientTemperature = telemetry.vehicle.ambientTemperature.toRideValue(),
                ambientLight = telemetry.ambientLight.toRideValue(),
                batteryVoltage = telemetry.batteryVoltage.toRideValue(),
                totalCurrent = telemetry.totalCurrent.toRideValue(),
                canState = telemetry.can1.state.toRideValue(),
                bleLabel = ble.first,
                bleState = ble.second,
                tachometerZone = zone,
                alerts = buildAlerts(
                    telemetry = telemetry,
                    rpm = rpm,
                    zone = zone,
                    connectionState = connectionState,
                    isConnecting = isConnecting,
                    profile = profile,
                ),
                profile = profile,
            )
        }

        private fun buildAlerts(
            telemetry: TelemetrySnapshot,
            rpm: RideValue<Double>,
            zone: TachometerZone,
            connectionState: ConnectionState,
            isConnecting: Boolean,
            profile: VehiclePerformanceProfile,
        ): List<RideAlert> {
            val alerts = telemetry.warnings
                .filter { it.active }
                .associateBy(
                    keySelector = DeviceWarning::code,
                    valueTransform = {
                        RideAlert(
                            id = it.code,
                            title = it.message,
                            severity = severity(it.severity),
                        )
                    },
                )
                .toMutableMap()
            if (zone == TachometerZone.RED && rpm.displayValue != null) {
                alerts.putIfAbsent(
                    "high_rpm",
                    RideAlert("high_rpm", "HIGH RPM", RideAlertSeverity.CRITICAL),
                )
            }
            val fuel = telemetry.vehicle.fuelLevel.toRideValue().displayValue
            val capacity = profile.fuelCapacityLiters
            val reserve = profile.fuelReserveLiters
            if (
                fuel != null &&
                capacity != null &&
                reserve != null &&
                capacity > 0 &&
                fuel <= reserve / capacity * 100
            ) {
                alerts.putIfAbsent(
                    "fuel_reserve",
                    RideAlert(
                        "fuel_reserve",
                        "FUEL RESERVE",
                        RideAlertSeverity.WARNING,
                    ),
                )
            }
            val ambient = telemetry.vehicle.ambientTemperature
                .toRideValue()
                .displayValue
            val iceThreshold = profile.iceWarningTemperatureCelsius
            if (ambient != null && iceThreshold != null && ambient < iceThreshold) {
                alerts.putIfAbsent(
                    "ice_warning",
                    RideAlert(
                        "ice_warning",
                        "ICE WARNING",
                        RideAlertSeverity.WARNING,
                    ),
                )
            }
            if (connectionState == ConnectionState.DISCONNECTED && !isConnecting) {
                alerts.putIfAbsent(
                    "ble_lost",
                    RideAlert(
                        "ble_lost",
                        "SVC CONNECTION LOST",
                        RideAlertSeverity.WARNING,
                    ),
                )
            }
            if (telemetry.can1.state.toRideValue().displayValue == null) {
                alerts.putIfAbsent(
                    "can_unavailable",
                    RideAlert(
                        "can_unavailable",
                        "CAN UNAVAILABLE",
                        RideAlertSeverity.WARNING,
                    ),
                )
            }
            if (telemetry.storage.sdCardState.toRideValue().displayValue == "missing") {
                alerts.putIfAbsent(
                    "sd_card_missing",
                    RideAlert(
                        "sd_card_missing",
                        "SD CARD MISSING",
                        RideAlertSeverity.WARNING,
                    ),
                )
            }
            return alerts.values.toList()
        }

        private fun severity(value: String): RideAlertSeverity = when (
            value.lowercase()
        ) {
            "critical" -> RideAlertSeverity.CRITICAL
            "warning" -> RideAlertSeverity.WARNING
            else -> RideAlertSeverity.INFO
        }
    }
}

enum class RideThemeMode {
    DAY,
    NIGHT,
    AUTOMATIC,
}

enum class RideResolvedTheme {
    DAY,
    NIGHT,
}

data class RideThemeThresholds(
    val nightEnterLux: Double,
    val dayEnterLux: Double,
) {
    companion object {
        val DEFAULT = RideThemeThresholds(
            nightEnterLux = 250.0,
            dayEnterLux = 650.0,
        )
    }
}

object RideThemeResolver {
    fun resolve(
        mode: RideThemeMode,
        ambientLight: RideValue<Double>,
        previous: RideResolvedTheme,
        thresholds: RideThemeThresholds = RideThemeThresholds.DEFAULT,
    ): RideResolvedTheme = when (mode) {
        RideThemeMode.DAY -> RideResolvedTheme.DAY
        RideThemeMode.NIGHT -> RideResolvedTheme.NIGHT
        RideThemeMode.AUTOMATIC -> {
            val lux = ambientLight.displayValue ?: return previous
            when (previous) {
                RideResolvedTheme.DAY ->
                    if (lux <= thresholds.nightEnterLux) {
                        RideResolvedTheme.NIGHT
                    } else {
                        RideResolvedTheme.DAY
                    }
                RideResolvedTheme.NIGHT ->
                    if (lux >= thresholds.dayEnterLux) {
                        RideResolvedTheme.DAY
                    } else {
                        RideResolvedTheme.NIGHT
                    }
            }
        }
    }
}

object RideMotionPolicy {
    fun durationMillis(
        reduceMotion: Boolean,
        standardDurationMillis: Int = 180,
    ): Int = if (reduceMotion) 0 else standardDurationMillis
}
