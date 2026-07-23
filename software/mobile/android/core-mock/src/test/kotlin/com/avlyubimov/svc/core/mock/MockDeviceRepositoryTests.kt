package com.avlyubimov.svc.core.mock

import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.MeasurementQuality
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

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
}
