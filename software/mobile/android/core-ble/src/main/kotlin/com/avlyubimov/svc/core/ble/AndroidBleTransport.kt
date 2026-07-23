package com.avlyubimov.svc.core.ble

import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.os.Build
import com.avlyubimov.svc.core.model.ConnectionState
import com.avlyubimov.svc.core.model.DiscoveredDevice
import java.util.UUID
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class AndroidBleTransport(context: Context) : BleTransport {
    private val applicationContext = context.applicationContext
    private val bluetoothManager =
        applicationContext.getSystemService(BluetoothManager::class.java)
    private val adapter get() = bluetoothManager.adapter
    private val mutableState = MutableStateFlow(ConnectionState.DISCONNECTED)
    private val mutableDevices = MutableStateFlow<List<DiscoveredDevice>>(emptyList())
    private val bluetoothDevices = mutableMapOf<String, BluetoothDevice>()
    private val rssiByAddress = mutableMapOf<String, Int>()
    private var gatt: BluetoothGatt? = null

    override val connectionState: StateFlow<ConnectionState> = mutableState.asStateFlow()
    override val devices: StateFlow<List<DiscoveredDevice>> = mutableDevices.asStateFlow()

    private val scanCallback = object : ScanCallback() {
        @SuppressLint("MissingPermission")
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device
            bluetoothDevices[device.address] = device
            rssiByAddress[device.address] = result.rssi
            mutableDevices.value = bluetoothDevices.values.map {
                DiscoveredDevice(
                    id = it.address,
                    name = it.name ?: "SVC",
                    signalStrength = rssiByAddress[it.address] ?: 0,
                )
            }
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(
            gatt: BluetoothGatt,
            status: Int,
            newState: Int,
        ) {
            mutableState.value = if (
                status == BluetoothGatt.GATT_SUCCESS &&
                newState == BluetoothProfile.STATE_CONNECTED
            ) {
                ConnectionState.CONNECTED
            } else {
                ConnectionState.DISCONNECTED
            }
        }
    }

    @SuppressLint("MissingPermission")
    override fun startScan() {
        mutableState.value = ConnectionState.SCANNING
        adapter.bluetoothLeScanner?.startScan(scanCallback)
    }

    @SuppressLint("MissingPermission")
    override fun stopScan() {
        adapter.bluetoothLeScanner?.stopScan(scanCallback)
    }

    @SuppressLint("MissingPermission")
    override fun connect(deviceId: String) {
        val device = bluetoothDevices[deviceId] ?: run {
            mutableState.value = ConnectionState.DISCONNECTED
            return
        }
        gatt = device.connectGatt(applicationContext, false, gattCallback)
    }

    @SuppressLint("MissingPermission")
    @Suppress("DEPRECATION")
    override fun write(characteristicUuid: String, data: ByteArray) {
        val activeGatt = gatt ?: return
        val characteristic = activeGatt.services
            .asSequence()
            .flatMap { it.characteristics.asSequence() }
            .firstOrNull { it.uuid == UUID.fromString(characteristicUuid) }
            ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            activeGatt.writeCharacteristic(
                characteristic,
                data,
                BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE,
            )
        } else {
            characteristic.writeType = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
            characteristic.value = data
            activeGatt.writeCharacteristic(characteristic)
        }
    }
}
