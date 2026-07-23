package com.avlyubimov.svc.core.mock

import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.MeasurementQuality
import com.avlyubimov.svc.core.model.RideDashboardState
import com.avlyubimov.svc.core.model.RideDataState
import com.avlyubimov.svc.core.model.RideGear
import com.avlyubimov.svc.core.model.VehiclePerformanceProfile
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class MockDeviceRepositoryTests {
    @Test
    fun parsesTelemetryAndConnectsWithoutHardware() = runTest {
        val repository = MockDeviceRepository()
        assertEquals(10, repository.snapshot.value.telemetry.channels.size)
        assertNull(repository.snapshot.value.telemetry.vehicle.engineTemperature.value)
        assertEquals(
            MeasurementQuality.UNAVAILABLE,
            repository.snapshot.value.telemetry.vehicle.engineTemperature.quality,
        )
        repository.connect(repository.discover().single().id)
        assertEquals(ConnectionState.CONNECTED, repository.snapshot.value.connectionState)
        assertEquals(
            "missing",
            repository.snapshot.value.telemetry.storage.sdCardState.value,
        )
    }

    @Test
    fun dashboardKeepsUnverifiedGearUnavailableAndSurfacesWarnings() {
        val snapshot = MockDeviceRepository().snapshot.value
        val dashboard = RideDashboardState.build(
            telemetry = snapshot.telemetry,
            connectionState = snapshot.connectionState,
            isConnecting = false,
            profile = genericProfile,
        )

        assertEquals(RideGear.UNAVAILABLE, dashboard.gear)
        assertEquals(RideDataState.DEGRADED, dashboard.leanAngle.state)
        assertTrue(dashboard.alerts.any { it.id == "sd_card_missing" })
        assertTrue(dashboard.alerts.any { it.id == "ble_lost" })
    }

    private val genericProfile = VehiclePerformanceProfile(
        schemaVersion = 1,
        id = "generic-motorcycle",
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
        source = "test",
        reference = "test",
        confidence = "test",
    )
}
