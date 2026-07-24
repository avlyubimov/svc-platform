package com.avlyubimov.svc.mobile

import com.avlyubimov.svc.core.model.RideDashboardState
import com.avlyubimov.svc.core.model.RideDataState
import com.avlyubimov.svc.core.model.TelemetrySnapshot
import java.time.LocalTime
import java.time.format.DateTimeFormatter

internal enum class TftIndicator(val label: String) {
    TURN_LEFT("←"),
    TURN_RIGHT("→"),
    HIGH_BEAM("HIGH"),
    FOG_LIGHTS("FOG"),
    NEUTRAL("N"),
    ABS("ABS"),
    ENGINE_WARNING("ENGINE"),
    TIRE_PRESSURE("RDC"),
    LOW_VOLTAGE("V"),
    SVC_ERROR("SVC"),
}

internal data class TftDashboardData(
    val speedKmh: Double?,
    val engineRpm: Double?,
    val tachometerMaximumRpm: Double?,
    val warningStartRpm: Double?,
    val redStartRpm: Double?,
    val gear: String,
    val leanDegrees: Double?,
    val leanDegraded: Boolean,
    val accelerationG: Double?,
    val brakingG: Double?,
    val fuelPercent: Double?,
    val tripDistanceKm: Double?,
    val rangeKm: Double?,
    val batteryVoltage: Double?,
    val svcCurrentA: Double?,
    val engineTemperatureCelsius: Double?,
    val ambientTemperatureCelsius: Double?,
    val frontPressureBar: Double?,
    val rearPressureBar: Double?,
    val currentTime: String,
    val canRecording: Boolean,
    val bleConnected: Boolean,
    val canConnected: Boolean,
    val activeIndicators: List<TftIndicator>,
    val criticalMessage: String?,
    val toastMessage: String?,
) {
    companion object {
        private const val TFT_MAXIMUM_RPM = 9_000.0
        private const val TFT_WARNING_START_RPM = 7_000.0
        private const val TFT_RED_START_RPM = 8_000.0

        fun resolve(
            dashboard: RideDashboardState,
            telemetry: TelemetrySnapshot,
            demoMode: Boolean,
        ): TftDashboardData {
            if (demoMode) return demo()

            val activeWarnings = telemetry.warnings.filter { it.active }
            val indicators = buildList {
                if (dashboard.gear.displayValue == "N") add(TftIndicator.NEUTRAL)
                if ((dashboard.batteryVoltage.displayValue ?: Double.MAX_VALUE) < 11.8) {
                    add(TftIndicator.LOW_VOLTAGE)
                }
                if (activeWarnings.any { it.code.contains("abs", ignoreCase = true) }) {
                    add(TftIndicator.ABS)
                }
                if (
                    activeWarnings.any {
                        it.code.contains("tire", ignoreCase = true) ||
                            it.code.contains("pressure", ignoreCase = true)
                    }
                ) {
                    add(TftIndicator.TIRE_PRESSURE)
                }
                if (activeWarnings.any { it.code.contains("engine", ignoreCase = true) }) {
                    add(TftIndicator.ENGINE_WARNING)
                }
                if (
                    activeWarnings.any { it.severity.equals("critical", true) } ||
                    telemetry.channels.any {
                        it.fault.isUsable &&
                            !it.fault.value.equals("none", ignoreCase = true)
                    }
                ) {
                    add(TftIndicator.SVC_ERROR)
                }
            }
            val loggerRecording = telemetry.storage.canLoggerState.isUsable &&
                telemetry.storage.canLoggerState.value.equals(
                    "recording",
                    ignoreCase = true,
                )
            val sdMissing = activeWarnings.firstOrNull {
                it.code == "sd_card_missing"
            }?.message
            val longitudinalAcceleration = telemetry.accelerometer.x.value
                ?.takeIf { telemetry.accelerometer.x.isUsable }
            return TftDashboardData(
                speedKmh = dashboard.speed.displayValue,
                engineRpm = dashboard.engineRpm.displayValue,
                tachometerMaximumRpm = TFT_MAXIMUM_RPM,
                warningStartRpm = TFT_WARNING_START_RPM,
                redStartRpm = TFT_RED_START_RPM,
                gear = dashboard.gear.displayValue,
                leanDegrees = dashboard.leanAngle.displayValue,
                leanDegraded = dashboard.leanAngle.state == RideDataState.DEGRADED,
                accelerationG = longitudinalAcceleration?.coerceAtLeast(0.0),
                brakingG = longitudinalAcceleration
                    ?.coerceAtMost(0.0)
                    ?.let { -it },
                fuelPercent = dashboard.fuelLevel.displayValue,
                tripDistanceKm = null,
                rangeKm = null,
                batteryVoltage = dashboard.batteryVoltage.displayValue,
                svcCurrentA = telemetry.totalCurrent.value
                    ?.takeIf { telemetry.totalCurrent.isUsable },
                engineTemperatureCelsius = dashboard.engineTemperature.displayValue,
                ambientTemperatureCelsius = dashboard.ambientTemperature.displayValue,
                frontPressureBar = null,
                rearPressureBar = null,
                currentTime = LocalTime.now().format(
                    DateTimeFormatter.ofPattern("HH:mm"),
                ),
                canRecording = loggerRecording,
                bleConnected = dashboard.bleState == RideDataState.VALID,
                canConnected = dashboard.canState.displayValue != null,
                activeIndicators = indicators,
                criticalMessage = activeWarnings.firstOrNull {
                    it.severity.equals("critical", true)
                }?.message,
                toastMessage = sdMissing,
            )
        }

        fun demo(): TftDashboardData = TftDashboardData(
            speedKmh = 87.0,
            engineRpm = 4_200.0,
            tachometerMaximumRpm = 9_000.0,
            warningStartRpm = 7_000.0,
            redStartRpm = 8_000.0,
            gear = "4",
            leanDegrees = 18.0,
            leanDegraded = false,
            accelerationG = 0.32,
            brakingG = 0.08,
            fuelPercent = 62.0,
            tripDistanceKm = 227.8,
            rangeKm = 214.0,
            batteryVoltage = 14.2,
            svcCurrentA = 8.4,
            engineTemperatureCelsius = 92.0,
            ambientTemperatureCelsius = 16.0,
            frontPressureBar = 2.3,
            rearPressureBar = 2.6,
            currentTime = "10:42",
            canRecording = true,
            bleConnected = true,
            canConnected = true,
            activeIndicators = listOf(
                TftIndicator.HIGH_BEAM,
                TftIndicator.FOG_LIGHTS,
                TftIndicator.ABS,
            ),
            criticalMessage = null,
            toastMessage = null,
        )
    }
}
