package com.avlyubimov.svc.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class RideVehicleProfilesTests {
    @Test
    fun catalogSwitchesProfileAndFallsBackWithoutAssumptions() {
        val catalog = MobileVehiclePerformanceCatalog.decode(
            indexJson = """
                {
                  "schemaVersion": 1,
                  "defaultProfileId": "test-bike",
                  "fallbackProfileId": "generic-motorcycle",
                  "profiles": [
                    {"id": "test-bike", "configuration": "test-bike.json"},
                    {
                      "id": "generic-motorcycle",
                      "configuration": "generic-motorcycle.json"
                    }
                  ]
                }
            """.trimIndent(),
            configurationJson = {
                when (it) {
                    "test-bike.json" -> profile(
                        id = "test-bike",
                        manufacturer = "SVC",
                        model = "Test Bike",
                        scaleMaxRpm = 9_000,
                        warningStartRpm = 7_000,
                        redZoneStartRpm = 7_800,
                    )
                    else -> profile(
                        id = "generic-motorcycle",
                        manufacturer = "Generic",
                        model = "Motorcycle",
                        scaleMaxRpm = null,
                        warningStartRpm = null,
                        redZoneStartRpm = null,
                    )
                }
            },
        )

        assertEquals(7_800, catalog.resolve("test-bike").redZoneStartRpm)
        assertNull(catalog.resolve("generic-motorcycle").redZoneStartRpm)
        assertEquals(
            "generic-motorcycle",
            catalog.resolve("removed-profile").id,
        )
    }

    private fun profile(
        id: String,
        manufacturer: String,
        model: String,
        scaleMaxRpm: Int?,
        warningStartRpm: Int?,
        redZoneStartRpm: Int?,
    ): String = """
        {
          "schemaVersion": 1,
          "id": "$id",
          "manufacturer": "$manufacturer",
          "model": "$model",
          "generation": null,
          "yearFrom": null,
          "yearTo": null,
          "engineName": null,
          "engineDisplacementCc": null,
          "maximumTorqueNm": null,
          "nominalPowerKw": null,
          "gearboxGears": null,
          "fuelCapacityLiters": null,
          "fuelReserveLiters": null,
          "iceWarningTemperatureCelsius": null,
          "idleRpm": null,
          "idleToleranceRpm": null,
          "torquePeakRpm": null,
          "powerPeakRpm": null,
          "tachometerScaleMinRpm": 0,
          "tachometerScaleMaxRpm": $scaleMaxRpm,
          "warningStartRpm": $warningStartRpm,
          "redZoneStartRpm": $redZoneStartRpm,
          "revLimiterRpm": null,
          "source": "test",
          "reference": "test",
          "confidence": "test"
        }
    """.trimIndent()
}
