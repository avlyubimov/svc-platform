package com.avlyubimov.svc.core.model

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class RideDashboardTests {
    private val profile = VehiclePerformanceProfile(
        schemaVersion = 1,
        id = "bmw-r1200gs-k25-2007",
        manufacturer = "BMW",
        model = "R1200GS",
        generation = "K25",
        yearFrom = 2007,
        yearTo = 2007,
        engineName = "1170 cc two-cylinder boxer",
        engineDisplacementCc = 1170.0,
        maximumTorqueNm = 115.0,
        nominalPowerKw = 74.0,
        gearboxGears = 6,
        fuelCapacityLiters = 20.0,
        fuelReserveLiters = 4.0,
        iceWarningTemperatureCelsius = 3.0,
        idleRpm = 1150,
        idleToleranceRpm = 50,
        torquePeakRpm = 5500,
        powerPeakRpm = 7000,
        tachometerScaleMinRpm = 0,
        tachometerScaleMaxRpm = 9000,
        warningStartRpm = 7000,
        redZoneStartRpm = 7800,
        revLimiterRpm = null,
        source = "test",
        reference = "test",
        confidence = "test",
    )

    @Test
    fun tachometerBoundariesAreExact() {
        val expected = mapOf(
            0.0 to TachometerZone.NORMAL,
            6999.0 to TachometerZone.NORMAL,
            7000.0 to TachometerZone.WARNING,
            7799.0 to TachometerZone.WARNING,
            7800.0 to TachometerZone.RED,
            9000.0 to TachometerZone.RED,
        )
        expected.forEach { (rpm, zone) ->
            assertEquals(zone, TachometerZoneResolver.zone(rpm, profile))
        }
        assertNull(profile.revLimiterRpm)
    }

    @Test
    fun tachometerUsesBoundaryHysteresis() {
        assertEquals(
            TachometerZone.RED,
            TachometerZoneResolver.zoneWithHysteresis(
                rpm = 7750.0,
                profile = profile,
                previous = TachometerZone.RED,
            ),
        )
        assertEquals(
            TachometerZone.WARNING,
            TachometerZoneResolver.zoneWithHysteresis(
                rpm = 6950.0,
                profile = profile,
                previous = TachometerZone.WARNING,
            ),
        )
    }

    @Test
    fun allGearPresentationStatesAreExplicit() {
        assertEquals(
            listOf("N", "1", "2", "3", "4", "5", "6", "BETWEEN", "—"),
            RideGear.entries.map(RideGear::displayValue),
        )
    }

    @Test
    fun staleInvalidAndUnavailableNeverDisplayValues() {
        assertNull(RideValue(1200.0, "rpm", RideDataState.STALE).displayValue)
        assertNull(RideValue(1200.0, "rpm", RideDataState.INVALID).displayValue)
        assertNull(RideValue(1200.0, "rpm", RideDataState.UNAVAILABLE).displayValue)
        assertEquals(
            1200.0,
            RideValue(1200.0, "rpm", RideDataState.DEGRADED).displayValue,
        )
    }

    @Test
    fun leanExtremaTrackBothSidesAndResetOnlyAtZero() {
        val extrema = LeanExtrema()
            .observe(-34.0)
            .observe(42.0)
            .observe(-12.0)
        assertEquals(34.0, extrema.maximumLeftDegrees)
        assertEquals(42.0, extrema.maximumRightDegrees)
        assertEquals(
            extrema,
            extrema.resetIfStationary(
                RideValue(2.0, "km/h", RideDataState.VALID),
            ),
        )
        assertEquals(
            LeanExtrema(),
            extrema.resetIfStationary(
                RideValue(0.0, "km/h", RideDataState.VALID),
            ),
        )
    }

    @Test
    fun calibrationRequiresDemoAndConfirmedStationarySpeed() {
        val stopped = RideValue(0.0, "km/h", RideDataState.VALID)
        val moving = RideValue(1.0, "km/h", RideDataState.VALID)
        val unavailable = RideValue<Double>(
            null,
            "km/h",
            RideDataState.UNAVAILABLE,
        )
        assertTrue(MotorcycleCalibrationPolicy.canCalibrate(stopped, demoMode = true))
        assertFalse(MotorcycleCalibrationPolicy.canCalibrate(stopped, demoMode = false))
        assertFalse(MotorcycleCalibrationPolicy.canCalibrate(moving, demoMode = true))
        assertFalse(
            MotorcycleCalibrationPolicy.canCalibrate(unavailable, demoMode = true),
        )
    }

    @Test
    fun automaticThemeUsesHysteresisAndRetainsUnknownState() {
        val low = RideValue(200.0, "lux", RideDataState.VALID)
        val middle = RideValue(450.0, "lux", RideDataState.VALID)
        val high = RideValue(700.0, "lux", RideDataState.VALID)
        val unavailable = RideValue<Double>(
            null,
            "lux",
            RideDataState.UNAVAILABLE,
        )

        assertEquals(
            RideResolvedTheme.NIGHT,
            RideThemeResolver.resolve(
                RideThemeMode.AUTOMATIC,
                low,
                RideResolvedTheme.DAY,
            ),
        )
        assertEquals(
            RideResolvedTheme.NIGHT,
            RideThemeResolver.resolve(
                RideThemeMode.AUTOMATIC,
                middle,
                RideResolvedTheme.NIGHT,
            ),
        )
        assertEquals(
            RideResolvedTheme.DAY,
            RideThemeResolver.resolve(
                RideThemeMode.AUTOMATIC,
                high,
                RideResolvedTheme.NIGHT,
            ),
        )
        assertEquals(
            RideResolvedTheme.DAY,
            RideThemeResolver.resolve(
                RideThemeMode.AUTOMATIC,
                unavailable,
                RideResolvedTheme.DAY,
            ),
        )
    }

    @Test
    fun reduceMotionDisablesDashboardAnimationDuration() {
        assertEquals(0, RideMotionPolicy.durationMillis(reduceMotion = true))
        assertEquals(180, RideMotionPolicy.durationMillis(reduceMotion = false))
        assertEquals(
            300,
            RideMotionPolicy.durationMillis(
                reduceMotion = false,
                standardDurationMillis = 300,
            ),
        )
    }
}
