package com.avlyubimov.svc.mobile

import com.avlyubimov.svc.core.mock.MockDeviceRepository
import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.DeviceRepository
import com.avlyubimov.svc.core.model.DeviceSnapshot
import com.avlyubimov.svc.core.model.DeviceWarning
import com.avlyubimov.svc.core.model.DiscoveredDevice
import com.avlyubimov.svc.core.model.Measurement
import com.avlyubimov.svc.core.model.MeasurementQuality
import com.avlyubimov.svc.core.model.RideGear
import com.avlyubimov.svc.core.model.TelemetrySnapshot
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlin.math.pow

internal data class DemoRideSample(
    val elapsedSeconds: Double,
    val speedKmh: Double,
    val engineRpm: Double,
    val gear: RideGear,
    val batteryVoltage: Double,
    val absSelfTestActive: Boolean,
)

internal object DemoRideScenario {
    const val durationSeconds = 9.0

    fun sampleAt(elapsedSeconds: Double): DemoRideSample {
        val time = elapsedSeconds.coerceIn(0.0, durationSeconds)
        val speed: Double
        val rpm: Double
        val gear: RideGear

        when {
            time < 1.0 -> {
                speed = 0.0
                rpm = 1_100.0
                gear = RideGear.NEUTRAL
            }
            time < 1.2 -> {
                val progress = smoothStep((time - 1.0) / 0.2)
                speed = 0.0
                rpm = interpolate(1_100.0, 1_800.0, progress)
                gear = RideGear.FIRST
            }
            time < 3.6 -> {
                val progress = (time - 1.2) / 2.4
                val nonlinearSpeed = 1.0 - (1.0 - progress).pow(1.72)
                speed = 70.0 * nonlinearSpeed
                val coupledRpm = 1_800.0 + 5_400.0 * (
                    nonlinearSpeed * 0.82 + progress * 0.18
                    )
                rpm = coupledRpm.coerceAtMost(7_200.0)
                gear = RideGear.FIRST
            }
            time < 3.8 -> {
                val progress = smoothStep((time - 3.6) / 0.2)
                speed = interpolate(70.0, 70.8, progress)
                rpm = interpolate(7_200.0, 4_200.0, progress)
                gear = if (time < 3.7) RideGear.FIRST else RideGear.SECOND
            }
            time < 5.5 -> {
                val progress = (time - 3.8) / 1.7
                val nonlinearSpeed = 1.0 - (1.0 - progress).pow(1.55)
                speed = interpolate(70.8, 100.0, nonlinearSpeed)
                rpm = interpolate(
                    4_200.0,
                    6_100.0,
                    nonlinearSpeed * 0.88 + progress * 0.12,
                )
                gear = RideGear.SECOND
            }
            else -> {
                speed = 100.0
                rpm = 6_100.0
                gear = RideGear.SECOND
            }
        }

        return DemoRideSample(
            elapsedSeconds = time,
            speedKmh = speed,
            engineRpm = rpm,
            gear = gear,
            batteryVoltage = interpolate(
                12.7,
                14.2,
                smoothStep((time / 2.5).coerceIn(0.0, 1.0)),
            ),
            absSelfTestActive = speed < 5.0,
        )
    }

    private fun smoothStep(value: Double): Double {
        val progress = value.coerceIn(0.0, 1.0)
        return progress * progress * (3.0 - 2.0 * progress)
    }

    private fun interpolate(start: Double, end: Double, progress: Double): Double =
        start + (end - start) * progress.coerceIn(0.0, 1.0)
}

internal data class DemoRideFrame(
    val sample: DemoRideSample,
    val snapshot: DeviceSnapshot,
)

internal class DemoRideRepository(
    private val baseTelemetry: TelemetrySnapshot =
        MockDeviceRepository().snapshot.value.telemetry,
) : DeviceRepository {
    private val initialFrame = createFrame(DemoRideScenario.sampleAt(0.0))
    private val mutableFrame = MutableStateFlow(initialFrame)
    private val mutableSnapshot = MutableStateFlow(initialFrame.snapshot)
    private val mutableRestartGeneration = MutableStateFlow(0)

    val frame: StateFlow<DemoRideFrame> = mutableFrame.asStateFlow()
    val restartGeneration: StateFlow<Int> = mutableRestartGeneration.asStateFlow()
    override val snapshot: StateFlow<DeviceSnapshot> = mutableSnapshot.asStateFlow()

    fun seek(elapsedSeconds: Double) {
        val next = createFrame(DemoRideScenario.sampleAt(elapsedSeconds))
        mutableFrame.value = next
        mutableSnapshot.value = next.snapshot
    }

    fun restart() {
        seek(0.0)
        mutableRestartGeneration.value += 1
    }

    override suspend fun discover(): List<DiscoveredDevice> = listOf(
        DiscoveredDevice(
            id = "SVC-DEBUG-DEMO-RIDE",
            name = "SVC Demo Ride",
            signalStrength = -32,
        ),
    )

    override suspend fun connect(id: String) = Unit

    override suspend fun refresh() = Unit

    private fun createFrame(sample: DemoRideSample): DemoRideFrame {
        val timestamp = "demo+%.3fs".format(sample.elapsedSeconds)
        val absWarning = DeviceWarning(
            code = "abs_self_test",
            severity = "warning",
            message = "ABS self-test",
            timestamp = timestamp,
            active = sample.absSelfTestActive,
        )
        val telemetry = baseTelemetry.copy(
            sequence = (sample.elapsedSeconds * 60.0).toLong(),
            timestamp = timestamp,
            batteryVoltage = baseTelemetry.batteryVoltage.demoValue(
                sample.batteryVoltage,
                timestamp,
            ),
            totalCurrent = baseTelemetry.totalCurrent.demoValue(8.4, timestamp),
            vehicle = baseTelemetry.vehicle.copy(
                speed = baseTelemetry.vehicle.speed.demoValue(
                    sample.speedKmh,
                    timestamp,
                ),
                engineRpm = baseTelemetry.vehicle.engineRpm.demoValue(
                    sample.engineRpm,
                    timestamp,
                ),
                engineTemperature = baseTelemetry.vehicle.engineTemperature.demoValue(
                    92.0,
                    timestamp,
                ),
                fuelLevel = baseTelemetry.vehicle.fuelLevel.demoValue(
                    62.0,
                    timestamp,
                ),
                ambientTemperature = baseTelemetry.vehicle.ambientTemperature.demoValue(
                    16.0,
                    timestamp,
                ),
            ),
            can1 = baseTelemetry.can1.copy(
                state = baseTelemetry.can1.state.demoValue("listen-only", timestamp),
                rxFrames = baseTelemetry.can1.rxFrames.demoValue(
                    1_204.0 + sample.elapsedSeconds * 420.0,
                    timestamp,
                ),
                droppedFrames = baseTelemetry.can1.droppedFrames.demoValue(0.0, timestamp),
                lastFrameTimestamp = baseTelemetry.can1.lastFrameTimestamp.demoValue(
                    timestamp,
                    timestamp,
                ),
            ),
            storage = baseTelemetry.storage.copy(
                sdCardState = baseTelemetry.storage.sdCardState.demoValue(
                    "ready",
                    timestamp,
                ),
                canLoggerState = baseTelemetry.storage.canLoggerState.demoValue(
                    "recording",
                    timestamp,
                ),
                freeBytes = baseTelemetry.storage.freeBytes.demoValue(
                    15_800_000_000.0,
                    timestamp,
                ),
            ),
            warnings = listOf(absWarning),
        )
        return DemoRideFrame(
            sample = sample,
            snapshot = DeviceSnapshot(
                connectionState = ConnectionState.CONNECTED,
                telemetry = telemetry,
                events = listOf("Debug-only Demo Ride active"),
            ),
        )
    }

    private fun <T> Measurement<T>.demoValue(
        value: T,
        timestamp: String,
    ): Measurement<T> = copy(
        value = value,
        timestamp = timestamp,
        valid = true,
        stale = false,
        quality = MeasurementQuality.GOOD,
    )
}
