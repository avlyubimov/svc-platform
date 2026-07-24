package com.avlyubimov.svc.mobile

import android.content.Intent
import android.view.WindowManager
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsNotDisplayed
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.test.swipe
import androidx.compose.ui.test.swipeLeft
import androidx.compose.ui.test.swipeRight
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.Lifecycle
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.After
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class RideModeUiTests {
    @get:Rule
    val composeRule = createEmptyComposeRule()

    private lateinit var scenario: ActivityScenario<MainActivity>

    @Before
    fun launchRideMode() {
        InstrumentationRegistry.getInstrumentation().uiAutomation
            .executeShellCommand(
                "settings put secure immersive_mode_confirmations confirmed",
            )
            .close()
        InstrumentationRegistry.getInstrumentation().uiAutomation
            .executeShellCommand("wm set-user-rotation lock 1")
            .close()
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        context.getSharedPreferences(
            "svc-ride-dashboard",
            android.content.Context.MODE_PRIVATE,
        ).edit().clear().commit()
        scenario = ActivityScenario.launch(
            Intent(context, MainActivity::class.java)
                .putExtra("skipStartup", true),
        )
        composeRule.onNodeWithTag("rideModeRoot").assertIsDisplayed()
    }

    @After
    fun closeActivity() {
        if (::scenario.isInitialized) {
            scenario.close()
        }
        InstrumentationRegistry.getInstrumentation().uiAutomation
            .executeShellCommand("wm set-user-rotation free")
            .close()
    }

    @Test
    fun rideModeHidesSystemBarsAndKeepsScreenOn() {
        waitForSystemBars(visible = false)
        scenario.onActivity { activity ->
            assertTrue(activity.rideModeWindowController.isActive)
            assertTrue(
                activity.window.attributes.flags and
                    WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON != 0,
            )
        }
        composeRule.onNodeWithText("Menu").assertDoesNotExist()
        composeRule.onNodeWithText("SVC Ride").assertDoesNotExist()
    }

    @Test
    fun systemBackRestoresBarsAndKeepScreenOn() {
        scenario.onActivity {
            it.onBackPressedDispatcher.onBackPressed()
        }
        composeRule.onNodeWithText("Enter Ride Mode").assertIsDisplayed()
        waitForSystemBars(visible = true)
        scenario.onActivity { activity ->
            assertFalse(activity.rideModeWindowController.isActive)
            assertFalse(
                activity.window.attributes.flags and
                    WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON != 0,
            )
        }
    }

    @Test
    fun horizontalSwipesMoveBothDirectionsWithoutCycling() {
        assertPageDisplayed("MAIN_DASHBOARD")
        composeRule.onNodeWithTag("rideModeRoot").performTouchInput { swipeLeft() }
        assertPageDisplayed("LEAN_IMU")
        composeRule.onNodeWithTag("rideModeRoot").performTouchInput { swipeRight() }
        assertPageDisplayed("MAIN_DASHBOARD")
        composeRule.onNodeWithTag("rideModeRoot").performTouchInput { swipeRight() }
        assertPageDisplayed("MAIN_DASHBOARD")
    }

    @Test
    fun verticalMovementDoesNotChangePage() {
        composeRule.onNodeWithTag("rideModeRoot").performTouchInput {
            swipe(
                start = Offset(center.x, height * 0.82f),
                end = Offset(center.x + 8f, height * 0.18f),
                durationMillis = 280,
            )
        }
        composeRule.onNodeWithTag("ridePage_MAIN_DASHBOARD").assertIsDisplayed()
        composeRule.onNodeWithTag("ridePage_LEAN_IMU").assertIsNotDisplayed()
    }

    @Test
    fun currentPageStaysInsideCutoutAndSystemGestureEdges() {
        val pageBounds = composeRule
            .onNodeWithTag("ridePage_MAIN_DASHBOARD")
            .fetchSemanticsNode()
            .boundsInRoot
        var minimumLeft = 0f
        var maximumRight = 0f
        var minimumTop = 0f
        var maximumBottom = 0f
        scenario.onActivity { activity ->
            val rootInsets = ViewCompat.getRootWindowInsets(
                activity.window.decorView,
            )
            val cutoutInsets = rootInsets?.getInsets(
                WindowInsetsCompat.Type.displayCutout(),
            )
            val density = activity.resources.displayMetrics.density
            minimumLeft = maxOf(
                cutoutInsets?.left?.toFloat() ?: 0f,
                24f * density,
            )
            maximumRight = activity.window.decorView.width - maxOf(
                cutoutInsets?.right?.toFloat() ?: 0f,
                24f * density,
            )
            minimumTop = cutoutInsets?.top?.toFloat() ?: 0f
            maximumBottom = activity.window.decorView.height -
                (cutoutInsets?.bottom?.toFloat() ?: 0f)
        }

        assertTrue(pageBounds.left >= minimumLeft - 1f)
        assertTrue(pageBounds.right <= maximumRight + 1f)
        assertTrue(pageBounds.top >= minimumTop - 1f)
        assertTrue(pageBounds.bottom <= maximumBottom + 1f)
    }

    @Test
    fun tftCoreElementsAreVisibleAndDoNotOverlap() {
        val page = composeRule
            .onNodeWithTag("ridePage_MAIN_DASHBOARD")
            .fetchSemanticsNode()
            .boundsInRoot
        val tachometer = composeRule
            .onNodeWithTag("tftTachometer", useUnmergedTree = true)
            .fetchSemanticsNode()
            .boundsInRoot
        val speed = composeRule
            .onNodeWithTag("tftSpeed", useUnmergedTree = true)
            .fetchSemanticsNode()
            .boundsInRoot
        val gear = composeRule
            .onNodeWithTag("tftGear", useUnmergedTree = true)
            .fetchSemanticsNode()
            .boundsInRoot
        val bottomStrip = composeRule
            .onNodeWithTag("tftBottomStrip", useUnmergedTree = true)
            .fetchSemanticsNode()
            .boundsInRoot

        assertTrue(tachometer.left >= page.left)
        assertTrue(tachometer.top >= page.top)
        assertTrue(tachometer.right <= page.right)
        assertTrue(tachometer.bottom <= page.bottom)
        assertTrue(speed.left >= page.left)
        assertTrue(speed.right < gear.left)
        assertTrue(speed.bottom < bottomStrip.top)
        assertTrue(gear.right <= page.right)
        assertTrue(gear.bottom < bottomStrip.top)
    }

    @Test
    fun selectedPageSurvivesBackgroundForeground() {
        composeRule.onNodeWithTag("rideModeRoot").performTouchInput { swipeLeft() }
        assertPageDisplayed("LEAN_IMU")
        scenario.moveToState(Lifecycle.State.STARTED)
        scenario.moveToState(Lifecycle.State.RESUMED)
        assertPageDisplayed("LEAN_IMU")
        waitForSystemBars(visible = false)
    }

    @Test
    fun newActivityRestoresLastRidePageWithoutNavigationChrome() {
        composeRule.onNodeWithTag("rideModeRoot").performTouchInput { swipeLeft() }
        assertPageDisplayed("LEAN_IMU")
        scenario.close()
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        scenario = ActivityScenario.launch(
            Intent(context, MainActivity::class.java)
                .putExtra("skipStartup", true),
        )
        composeRule.onNodeWithTag("rideModeRoot").assertIsDisplayed()
        assertPageDisplayed("LEAN_IMU")
        composeRule.onNodeWithText("Menu").assertDoesNotExist()
        composeRule.onNodeWithText("Settings and calibration").assertDoesNotExist()
    }

    private fun waitForSystemBars(visible: Boolean) {
        composeRule.waitUntil(timeoutMillis = 5_000) {
            var matches = false
            scenario.onActivity { activity ->
                val insets = ViewCompat.getRootWindowInsets(activity.window.decorView)
                val statusBarsVisible =
                    insets?.isVisible(WindowInsetsCompat.Type.statusBars())
                val navigationBarsVisible =
                    insets?.isVisible(WindowInsetsCompat.Type.navigationBars())
                matches = statusBarsVisible == visible &&
                    navigationBarsVisible == visible
            }
            matches
        }
    }

    private fun assertPageDisplayed(pageName: String) {
        composeRule.waitUntil(timeoutMillis = 5_000) {
            runCatching {
                composeRule.onNodeWithTag("ridePage_$pageName").assertIsDisplayed()
            }.isSuccess
        }
    }
}
