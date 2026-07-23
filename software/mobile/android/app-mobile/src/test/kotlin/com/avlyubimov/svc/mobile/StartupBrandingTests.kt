package com.avlyubimov.svc.mobile

import kotlin.test.Test
import kotlin.test.assertEquals

class StartupBrandingTests {
    @Test
    fun manufacturerLogoIsRequiredButWordmarkIsOptional() {
        val catalogWithLogo = catalog { it == "local/personal/logo.svg" }
        assertEquals("personal-profile", catalogWithLogo.resolve("personal-profile").id)

        val catalogWithoutLogo = catalog { it.startsWith("svc/") }
        assertEquals("svc-fallback", catalogWithoutLogo.resolve("personal-profile").id)
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
                logo = "local/personal/logo.svg",
                wordmark = "local/personal/wordmark.svg",
            ),
            "svc-fallback.json" to profile(
                id = "svc-fallback",
                logo = "svc/logo.svg",
                wordmark = "svc/wordmark.svg",
            ),
        )
        return MobileBrandCatalog.decode(
            indexJson = index,
            configurationJson = configurations::getValue,
            assetExists = assetExists,
        )
    }

    private fun profile(id: String, logo: String, wordmark: String): String = """
        {
          "schemaVersion": 1,
          "id": "$id",
          "displayName": "$id",
          "theme": "test-theme",
          "manufacturer": "Test",
          "model": "Test",
          "generation": "Test",
          "year": 2026,
          "manufacturerWordmark": "TEST",
          "vehicleModel": "TEST",
          "vehicleGeneration": "TEST",
          "brandTagline": "TEST",
          "accentColor": "#1C69D4",
          "assets": {
            "logo": "$logo",
            "wordmark": "$wordmark"
          }
        }
    """.trimIndent()
}
