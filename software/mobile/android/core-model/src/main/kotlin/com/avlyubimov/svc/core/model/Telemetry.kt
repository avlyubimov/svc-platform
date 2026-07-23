package com.avlyubimov.svc.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class MeasurementSource {
    @SerialName("adc") ADC,
    @SerialName("can1") CAN1,
    @SerialName("imu") IMU,
    @SerialName("sensor") SENSOR,
    @SerialName("output-manager") OUTPUT_MANAGER,
    @SerialName("storage") STORAGE,
    @SerialName("firmware") FIRMWARE,
    @SerialName("derived") DERIVED,
}

@Serializable
enum class MeasurementQuality {
    @SerialName("good") GOOD,
    @SerialName("degraded") DEGRADED,
    @SerialName("invalid") INVALID,
    @SerialName("unavailable") UNAVAILABLE,
}

@Serializable
data class Measurement<T>(
    val value: T?,
    val unit: String,
    val timestamp: String,
    val valid: Boolean,
    val stale: Boolean,
    val source: MeasurementSource,
    val quality: MeasurementQuality,
) {
    val isUsable: Boolean
        get() = valid && !stale &&
            quality != MeasurementQuality.INVALID &&
            quality != MeasurementQuality.UNAVAILABLE
}

@Serializable
data class IdentifiedNumberMeasurement(
    val id: String,
    val value: Double?,
    val unit: String,
    val timestamp: String,
    val valid: Boolean,
    val stale: Boolean,
    val source: MeasurementSource,
    val quality: MeasurementQuality,
)

@Serializable
data class ChannelTelemetry(
    val id: String,
    val current: Measurement<Double>,
    val state: Measurement<String>,
    val fault: Measurement<String>,
)

@Serializable
data class VectorTelemetry(
    val x: Measurement<Double>,
    val y: Measurement<Double>,
    val z: Measurement<Double>,
)

@Serializable
data class VehicleTelemetry(
    val speed: Measurement<Double>,
    val engineRpm: Measurement<Double>,
    val engineTemperature: Measurement<Double>,
    val instantFuelConsumption: Measurement<Double>,
    val averageFuelConsumption: Measurement<Double>,
    val fuelLevel: Measurement<Double>,
    val ambientTemperature: Measurement<Double>,
)

@Serializable
data class CanStatus(
    val state: Measurement<String>,
    val rxFrames: Measurement<Double>,
    val droppedFrames: Measurement<Double>,
    val lastFrameTimestamp: Measurement<String>,
)

@Serializable
data class StorageStatus(
    val sdCardState: Measurement<String>,
    val canLoggerState: Measurement<String>,
    val freeBytes: Measurement<Double>,
)

@Serializable
data class FirmwareVersions(
    val stm32: Measurement<String>,
    val e73: Measurement<String>,
    val protocol: Measurement<String>,
)

@Serializable
data class DeviceWarning(
    val code: String,
    val severity: String,
    val message: String,
    val timestamp: String,
    val active: Boolean,
)

@Serializable
data class TelemetrySnapshot(
    val schemaVersion: Int,
    val protocolVersion: Int,
    val deviceId: String,
    val sequence: Long,
    val timestamp: String,
    val batteryVoltage: Measurement<Double>,
    val totalCurrent: Measurement<Double>,
    val channels: List<ChannelTelemetry>,
    val powerZoneTemperatures: List<IdentifiedNumberMeasurement>,
    val ambientLight: Measurement<Double>,
    val accelerometer: VectorTelemetry,
    val gyroscope: VectorTelemetry,
    val leanAngle: Measurement<Double>,
    val vehicle: VehicleTelemetry,
    val can1: CanStatus,
    val storage: StorageStatus,
    val versions: FirmwareVersions,
    val warnings: List<DeviceWarning>,
)
