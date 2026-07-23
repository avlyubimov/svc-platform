package com.avlyubimov.svc.mobile

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class StartupBrandingTests {
    @Test
    fun vehicleProfileUsesCatalogPreferredLogoAndTextName() {
        val preferred = "vehicle-brands/brands/test-brand/period-logo.svg"
        val catalog = catalog { it == preferred || it.startsWith("svc/") }
        val resolved = catalog.resolve("personal-profile")

        assertEquals("personal-profile", resolved.id)
        assertEquals(preferred, resolved.logoAsset)
        assertEquals("Test Manufacturer", resolved.manufacturerDisplayName)
        assertEquals("#123456", resolved.accentColor)
        assertNull(resolved.wordmarkAsset)
    }

    @Test
    fun missingVehicleLogoUsesSvcFallback() {
        assertEquals(
            "svc-fallback",
            catalog { it.startsWith("svc/") }.resolve("personal-profile").id,
        )
    }

    @Test
    fun startupDurationsComeFromDecodedTimeline() {
        val timeline = MobileStartupTimeline(
            schemaVersion = 1,
            durationMs = 2_100,
            criticalDurationMs = 500,
            phases = MobileStartupPhases(250, 700, 1_200, 1_600, 2_100),
        )
        assertEquals(2_100, timeline.durationMs(true, false, false))
        assertEquals(500, timeline.durationMs(true, true, false))
        assertEquals(500, timeline.durationMs(true, false, true))
        assertEquals(0, timeline.durationMs(false, false, false))
    }

    @Test
    fun unknownProfileUsesConfiguredFallback() {
        assertEquals(
            "svc-fallback",
            catalog { it.startsWith("svc/") }.resolve("removed-profile").id,
        )
    }

    private fun catalog(assetExists: (String) -> Boolean): MobileBrandCatalog {
        val index = """
            {
              "schemaVersion": 1,
              "defaultProfileId": "personal-profile",
              "fallbackProfileId": "svc-fallback",
              "profiles": [
                {"id": "personal-profile", "configuration": "personal-profile.json"},
                {"id": "svc-fallback", "configuration": "svc-fallback.json"}
              ]
            }
        """.trimIndent()
        val configurations = mapOf(
            "personal-profile.json" to profile(
                id = "personal-profile",
                brandId = "test-brand",
                assets = "",
            ),
            "svc-fallback.json" to profile(
                id = "svc-fallback",
                brandId = "svc",
                assets = """
                    ,
                    "assets": {
                      "logo": "svc/svg/emblem.svg",
                      "wordmark": "svc/svg/wordmark.svg"
                    }
                """.trimIndent(),
            ),
        )
        return MobileBrandCatalog.decode(
            indexJson = index,
            configurationJson = configurations::getValue,
            vehicleCatalogJson = """
                {
                  "schemaVersion": 1,
                  "simpleIconsVersion": "test",
                  "brands": [
                    {
                      "id": "test-brand",
                      "name": "Test Manufacturer",
                      "categories": ["motorcycle"],
                      "accentColor": "#123456",
                      "source": "https://example.test",
                      "preferredAsset": "period-logo.svg"
                    }
                  ]
                }
            """.trimIndent(),
            assetExists = assetExists,
        )
    }

    private fun profile(id: String, brandId: String, assets: String): String = """
        {
          "schemaVersion": 1,
          "id": "$id",
          "displayName": "$id",
          "brandId": "$brandId",
          "theme": "test-theme",
          "manufacturer": "Test",
          "model": "Test Model",
          "generation": "Test Generation",
          "year": 2026,
          "manufacturerWordmark": "TEST",
          "vehicleModel": "TEST MODEL",
          "vehicleGeneration": "TEST GENERATION · 2026",
          "brandTagline": "TEST",
          "accentColor": "#1C69D4"
          $assets
        }
    """.trimIndent()
}
