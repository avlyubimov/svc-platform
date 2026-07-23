package com.avlyubimov.svc.automotive

import android.content.Intent
import android.content.pm.ApplicationInfo
import androidx.car.app.CarAppService
import androidx.car.app.Screen
import androidx.car.app.Session
import androidx.car.app.model.ItemList
import androidx.car.app.model.ListTemplate
import androidx.car.app.model.Row
import androidx.car.app.model.Template
import androidx.car.app.validation.HostValidator

class SVCAppService : CarAppService() {
    override fun createHostValidator(): HostValidator =
        if (applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0) {
            HostValidator.ALLOW_ALL_HOSTS_VALIDATOR
        } else {
            HostValidator.Builder(applicationContext).build()
        }

    override fun onCreateSession(): Session = SVCSession()
}

private class SVCSession : Session() {
    override fun onCreateScreen(intent: Intent): Screen = StatusScreen(carContext)
}

private class StatusScreen(
    carContext: androidx.car.app.CarContext,
) : Screen(carContext) {
    override fun onGetTemplate(): Template {
        val rows = listOf(
            "Battery" to "12.7 V",
            "Total current" to "8.4 A",
            "Speed" to "0 km/h",
            "Engine RPM" to "0 rpm",
            "Engine temperature" to "Unavailable",
            "Fuel consumption" to "Unavailable",
            "Ambient temperature" to "Unavailable",
            "Ambient light" to "820 lux",
            "Lean angle" to "0.8°",
            "Warnings" to "SD card missing",
            "Channels" to "OUT1..OUT10 status only",
        )
        val list = ItemList.Builder()
        rows.forEach { (title, value) ->
            list.addItem(
                Row.Builder()
                    .setTitle(title)
                    .addText(value)
                    .build(),
            )
        }
        return ListTemplate.Builder()
            .setTitle("BMW R1200GS · SVC")
            .setSingleList(list.build())
            .build()
    }
}
