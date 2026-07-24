package com.avlyubimov.svc.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.avlyubimov.svc.core.mock.MockDeviceRepository

class MainActivity : ComponentActivity() {
    internal lateinit var rideModeWindowController: RideModeWindowController
        private set

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        rideModeWindowController = RideModeWindowController(this)
        setContent {
            SVCMobileApp(
                repository = MockDeviceRepository(),
                rideModeWindowController = rideModeWindowController,
            )
        }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus && ::rideModeWindowController.isInitialized) {
            rideModeWindowController.reassertImmersiveMode()
        }
    }

    override fun onDestroy() {
        if (::rideModeWindowController.isInitialized) {
            rideModeWindowController.exit()
        }
        super.onDestroy()
    }
}
