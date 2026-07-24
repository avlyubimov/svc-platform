package com.avlyubimov.svc.mobile

import com.avlyubimov.svc.core.model.DeviceRepository
import com.avlyubimov.svc.core.model.RideGear
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue

class DemoRideScenarioTests {
    @Test
    fun followsNeutralFirstSecondSequenceAndReachesOneHundred() {
        assertEquals(RideGear.NEUTRAL, DemoRideScenario.sampleAt(0.5).gear)
        assertEquals(RideGear.FIRST, DemoRideScenario.sampleAt(1.0).gear)
        assertEquals(RideGear.FIRST, DemoRideScenario.sampleAt(3.65).gear)
        assertEquals(RideGear.SECOND, DemoRideScenario.sampleAt(3.75).gear)
        assertEquals(100.0, DemoRideScenario.sampleAt(5.5).speedKmh, 0.001)
        assertEquals(100.0, DemoRideScenario.sampleAt(9.0).speedKmh, 0.001)
        assertEquals(6_100.0, DemoRideScenario.sampleAt(9.0).engineRpm, 0.001)
    }

    @Test
    fun accelerationIsNonlinearAndShiftKeepsSpeedContinuous() {
        val accelerationMidpoint = DemoRideScenario.sampleAt(2.4)
        val beforeShift = DemoRideScenario.sampleAt(3.65)
        val afterShift = DemoRideScenario.sampleAt(3.75)

        assertTrue(accelerationMidpoint.speedKmh > 35.0)
        assertTrue(afterShift.speedKmh - beforeShift.speedKmh < 1.0)
        assertTrue(afterShift.engineRpm < beforeShift.engineRpm)
    }

    @Test
    fun debugRepositoryUsesDeviceRepositoryTelemetryInterface() {
        val repository = DemoRideRepository()
        assertIs<DeviceRepository>(repository)

        repository.seek(5.5)

        val telemetry = repository.snapshot.value.telemetry
        assertEquals(100.0, telemetry.vehicle.speed.value)
        assertEquals(6_100.0, telemetry.vehicle.engineRpm.value)
        assertEquals(
            14.2,
            telemetry.batteryVoltage.value ?: error("battery voltage is missing"),
            0.001,
        )
        assertEquals("recording", telemetry.storage.canLoggerState.value)
    }
}
