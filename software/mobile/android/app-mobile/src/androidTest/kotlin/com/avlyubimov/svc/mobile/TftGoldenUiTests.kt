package com.avlyubimov.svc.mobile

import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.math.abs

@RunWith(AndroidJUnit4::class)
class TftGoldenUiTests {
    private lateinit var activity: MainActivity

    @Before
    fun launchChigeeSizedDemo() {
        shell("wm size 921x2048")
        shell("wm density 420")
        shell("wm set-user-rotation lock 1")
        shell("settings put secure immersive_mode_confirmations confirmed")
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        activity = InstrumentationRegistry.getInstrumentation().startActivitySync(
            Intent(context, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra("skipStartup", true)
                .putExtra("presentationDemo", true),
        ) as MainActivity
        InstrumentationRegistry.getInstrumentation().waitForIdleSync()
        Thread.sleep(1_500)
        Thread.sleep(3_500)
    }

    @After
    fun restoreDisplay() {
        if (::activity.isInitialized) {
            activity.finish()
        }
        shell("wm size reset")
        shell("wm density reset")
        shell("wm set-user-rotation free")
    }

    @Test
    fun chigeeGoldenMatchesAndContainsNoSystemBars() {
        val actual = InstrumentationRegistry
            .getInstrumentation()
            .uiAutomation
            .takeScreenshot()
        val expected = InstrumentationRegistry
            .getInstrumentation()
            .context
            .assets
            .open("goldens/tft-main-2048x921.png")
            .use(BitmapFactory::decodeStream)

        assertEquals(2048, actual.width)
        assertEquals(921, actual.height)
        assertEquals(expected.width, actual.width)
        assertEquals(expected.height, actual.height)
        assertTrue(meanPixelDifference(expected, actual) < 0.045)

        val insets = ViewCompat.getRootWindowInsets(activity.window.decorView)
        assertFalse(
            insets?.isVisible(WindowInsetsCompat.Type.statusBars()) ?: true,
        )
        assertFalse(
            insets?.isVisible(WindowInsetsCompat.Type.navigationBars()) ?: true,
        )
    }

    @Test
    fun sportGoldenMatchesWithoutOverlappingTelemetry() {
        activity.finish()
        InstrumentationRegistry.getInstrumentation().waitForIdleSync()
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        activity = InstrumentationRegistry.getInstrumentation().startActivitySync(
            Intent(context, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra("skipStartup", true)
                .putExtra("presentationDemo", true)
                .putExtra("presentationPage", 1),
        ) as MainActivity
        InstrumentationRegistry.getInstrumentation().waitForIdleSync()
        Thread.sleep(1_500)
        Thread.sleep(3_500)

        val actual = InstrumentationRegistry
            .getInstrumentation()
            .uiAutomation
            .takeScreenshot()
        val expected = InstrumentationRegistry
            .getInstrumentation()
            .context
            .assets
            .open("goldens/tft-sport-2048x921.png")
            .use(BitmapFactory::decodeStream)

        assertEquals(2048, actual.width)
        assertEquals(921, actual.height)
        assertEquals(expected.width, actual.width)
        assertEquals(expected.height, actual.height)
        assertTrue(meanPixelDifference(expected, actual) < 0.045)
    }

    private fun meanPixelDifference(expected: Bitmap, actual: Bitmap): Double {
        var difference = 0L
        var samples = 0L
        for (y in 0 until expected.height step 8) {
            for (x in 0 until expected.width step 8) {
                val left = expected.getPixel(x, y)
                val right = actual.getPixel(x, y)
                difference += abs(android.graphics.Color.red(left) - android.graphics.Color.red(right))
                difference += abs(
                    android.graphics.Color.green(left) -
                        android.graphics.Color.green(right),
                )
                difference += abs(
                    android.graphics.Color.blue(left) -
                        android.graphics.Color.blue(right),
                )
                samples += 3
            }
        }
        return difference.toDouble() / (samples * 255.0)
    }

    private fun shell(command: String) {
        InstrumentationRegistry.getInstrumentation().uiAutomation
            .executeShellCommand(command)
            .close()
    }

}
