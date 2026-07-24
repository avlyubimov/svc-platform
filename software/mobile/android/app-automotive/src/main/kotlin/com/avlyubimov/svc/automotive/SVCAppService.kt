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
            "Speed" to "—",
            "Gear" to "—",
            "Battery" to "—",
            "SVC current" to "—",
            "Main warning" to "Connection required",
            "Connection" to "Unavailable",
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
            .setTitle("SVC Ride")
            .setSingleList(list.build())
            .build()
    }
}
