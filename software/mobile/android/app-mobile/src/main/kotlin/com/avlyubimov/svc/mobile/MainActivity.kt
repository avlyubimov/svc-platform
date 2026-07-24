package com.avlyubimov.svc.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.avlyubimov.svc.core.mock.MockDeviceRepository

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SVCMobileApp(repository = MockDeviceRepository())
        }
    }
}
