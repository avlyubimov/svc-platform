package com.avlyubimov.svc.mobile

import kotlin.test.Test
import kotlin.test.assertEquals

class StartupBrandingTests {
    @Test
    fun bmwAssetsAreAllOrNothing() {
        assertEquals(
            AppearancePreferences.BMW_PROFILE,
            resolveBrandPack(
                AppearancePreferences.BMW_PROFILE,
                hasLogo = true,
                hasWordmark = true,
            ).id,
        )
        assertEquals(
            AppearancePreferences.GENERIC_PROFILE,
            resolveBrandPack(
                AppearancePreferences.BMW_PROFILE,
                hasLogo = true,
                hasWordmark = false,
            ).id,
        )
    }

    @Test
    fun startupDurationsMatchContract() {
        assertEquals(2100, startupDurationMs(true, false, false))
        assertEquals(500, startupDurationMs(true, true, false))
        assertEquals(500, startupDurationMs(true, false, true))
        assertEquals(0, startupDurationMs(false, false, false))
    }

    @Test
    fun genericProfileNeverUsesBmwAssets() {
        assertEquals(
            AppearancePreferences.GENERIC_PROFILE,
            resolveBrandPack(
                AppearancePreferences.GENERIC_PROFILE,
                hasLogo = true,
                hasWordmark = true,
            ).id,
        )
    }
}
