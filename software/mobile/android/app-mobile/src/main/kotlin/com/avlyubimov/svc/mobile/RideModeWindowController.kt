package com.avlyubimov.svc.mobile

import android.app.Activity
import android.content.pm.ActivityInfo
import android.provider.Settings
import android.view.WindowManager
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat

internal class RideModeWindowController(
    private val activity: Activity,
) {
    private var active = false
    private var previousOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
    private var previousWindowFlags = 0
    private var previousCutoutMode =
        WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_DEFAULT
    private var previousBrightness = WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_NONE

    val isActive: Boolean
        get() = active

    fun enter() {
        if (active) return
        val window = activity.window
        val attributes = window.attributes
        active = true
        previousOrientation = activity.requestedOrientation
        previousWindowFlags = attributes.flags
        previousCutoutMode = attributes.layoutInDisplayCutoutMode
        previousBrightness = attributes.screenBrightness

        activity.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE
        WindowCompat.setDecorFitsSystemWindows(window, false)
        attributes.layoutInDisplayCutoutMode =
            WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
        window.attributes = attributes
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        hideSystemBars()
    }

    fun exit() {
        if (!active) return
        val window = activity.window
        active = false
        WindowCompat.setDecorFitsSystemWindows(window, true)
        val insetsController = WindowCompat.getInsetsController(
            window,
            window.decorView,
        )
        insetsController.show(WindowInsetsCompat.Type.systemBars())
        val attributes = window.attributes
        attributes.layoutInDisplayCutoutMode = previousCutoutMode
        attributes.screenBrightness = previousBrightness
        window.attributes = attributes
        if (
            previousWindowFlags and WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON == 0
        ) {
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
        activity.requestedOrientation = previousOrientation
        window.decorView.post {
            if (!active) {
                WindowCompat.getInsetsController(window, window.decorView).show(
                    WindowInsetsCompat.Type.systemBars(),
                )
            }
        }
    }

    fun reassertImmersiveMode() {
        if (active) hideSystemBars()
    }

    fun currentBrightness(): Float {
        val windowBrightness = activity.window.attributes.screenBrightness
        if (windowBrightness >= 0f) return windowBrightness
        return runCatching {
            Settings.System.getInt(
                activity.contentResolver,
                Settings.System.SCREEN_BRIGHTNESS,
            ) / 255f
        }.getOrDefault(0.65f).coerceIn(0.05f, 1f)
    }

    fun setBrightness(value: Float) {
        if (!active) return
        activity.window.attributes = activity.window.attributes.apply {
            screenBrightness = value.coerceIn(0.05f, 1f)
        }
    }

    private fun hideSystemBars() {
        val window = activity.window
        WindowCompat.getInsetsController(window, window.decorView).apply {
            systemBarsBehavior =
                WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            hide(WindowInsetsCompat.Type.statusBars())
            hide(WindowInsetsCompat.Type.navigationBars())
        }
    }
}
