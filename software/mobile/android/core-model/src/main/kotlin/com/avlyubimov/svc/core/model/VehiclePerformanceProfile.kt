package com.avlyubimov.svc.core.model

import kotlinx.serialization.Serializable

@Serializable
data class VehiclePerformanceProfile(
    val schemaVersion: Int,
    val id: String,
    val manufacturer: String,
    val model: String,
    val generation: String?,
    val yearFrom: Int?,
    val yearTo: Int?,
    val engineName: String?,
    val engineDisplacementCc: Double?,
    val maximumTorqueNm: Double?,
    val nominalPowerKw: Double?,
    val gearboxGears: Int?,
    val fuelCapacityLiters: Double?,
    val fuelReserveLiters: Double?,
    val iceWarningTemperatureCelsius: Double?,
    val idleRpm: Int?,
    val idleToleranceRpm: Int?,
    val torquePeakRpm: Int?,
    val powerPeakRpm: Int?,
    val tachometerScaleMinRpm: Int,
    val tachometerScaleMaxRpm: Int?,
    val warningStartRpm: Int?,
    val redZoneStartRpm: Int?,
    val revLimiterRpm: Int?,
    val source: String,
    val reference: String,
    val confidence: String,
) {
    val displayName: String
        get() = listOfNotNull(manufacturer, model, generation).joinToString(" ")
}
