package com.avlyubimov.svc.mobile

import kotlin.test.Test
import kotlin.test.assertEquals

class TftDashboardDataTests {
    @Test
    fun presentationDemoContainsApprovedReviewValues() {
        val demo = TftDashboardData.demo()

        assertEquals(87.0, demo.speedKmh)
        assertEquals(4_200.0, demo.engineRpm)
        assertEquals(9_000.0, demo.tachometerMaximumRpm)
        assertEquals(7_000.0, demo.warningStartRpm)
        assertEquals(8_000.0, demo.redStartRpm)
        assertEquals("4", demo.gear)
        assertEquals(18.0, demo.leanDegrees)
        assertEquals(0.32, demo.accelerationG)
        assertEquals(0.08, demo.brakingG)
        assertEquals(227.8, demo.tripDistanceKm)
        assertEquals(214.0, demo.rangeKm)
        assertEquals(62.0, demo.fuelPercent)
        assertEquals(14.2, demo.batteryVoltage)
        assertEquals(8.4, demo.svcCurrentA)
        assertEquals(92.0, demo.engineTemperatureCelsius)
        assertEquals(2.3, demo.frontPressureBar)
        assertEquals(2.6, demo.rearPressureBar)
        assertEquals(16.0, demo.ambientTemperatureCelsius)
        assertEquals("10:42", demo.currentTime)
    }
}
