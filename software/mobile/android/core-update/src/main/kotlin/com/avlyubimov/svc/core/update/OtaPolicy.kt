package com.avlyubimov.svc.core.update

import com.avlyubimov.svc.core.model.TelemetrySnapshot

enum class OtaDenialReason {
    VEHICLE_MOVING,
    ENGINE_RUNNING,
    OUTPUTS_ACTIVE,
    CRITICAL_FAULT,
    BATTERY_OUT_OF_RANGE,
    TEMPERATURE_OUT_OF_RANGE,
    LINK_UNSTABLE,
    FILE_INCOMPLETE,
}

object OtaPolicy {
    fun denials(
        telemetry: TelemetrySnapshot,
        linkStable: Boolean = true,
        fileComplete: Boolean = true,
    ): Set<OtaDenialReason> = buildSet {
        if (!telemetry.vehicle.speed.isUsable || telemetry.vehicle.speed.value != 0.0) {
            add(OtaDenialReason.VEHICLE_MOVING)
        }
        if (!telemetry.vehicle.engineRpm.isUsable || telemetry.vehicle.engineRpm.value != 0.0) {
            add(OtaDenialReason.ENGINE_RUNNING)
        }
        if (telemetry.channels.any { it.state.value != "off" }) {
            add(OtaDenialReason.OUTPUTS_ACTIVE)
        }
        if (telemetry.warnings.any { it.active && it.severity == "critical" }) {
            add(OtaDenialReason.CRITICAL_FAULT)
        }
        val battery = telemetry.batteryVoltage.value
        if (!telemetry.batteryVoltage.isUsable || battery == null || battery !in 11.8..14.8) {
            add(OtaDenialReason.BATTERY_OUT_OF_RANGE)
        }
        if (
            telemetry.powerZoneTemperatures.any {
                !it.valid || it.stale || (it.value ?: Double.POSITIVE_INFINITY) > 85.0
            }
        ) {
            add(OtaDenialReason.TEMPERATURE_OUT_OF_RANGE)
        }
        if (!linkStable) add(OtaDenialReason.LINK_UNSTABLE)
        if (!fileComplete) add(OtaDenialReason.FILE_INCOMPLETE)
    }
}
