#include <errno.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "ble_uart_bridge.h"
#include "telemetry_stub.h"
#include "update_state.h"

LOG_MODULE_REGISTER(svc_e73, LOG_LEVEL_INF);

static svc_e73_telemetry_stub_t telemetry;
static svc_update_transfer_t update_transfer;

static void connected(struct bt_conn *connection, uint8_t error)
{
    if (error != 0U) {
        LOG_WRN("BLE connection failed: %u", error);
        return;
    }

    const int security_error = bt_conn_set_security(connection, BT_SECURITY_L2);
    if (security_error != 0 && security_error != -EALREADY) {
        LOG_WRN("BLE security request failed: %d", security_error);
    }
}

static void disconnected(struct bt_conn *connection, uint8_t reason)
{
    (void)connection;
    LOG_INF("BLE disconnected: %u", reason);
    if (update_transfer.state == SVC_UPDATE_RECEIVING) {
        (void)svc_update_interrupt(&update_transfer);
    }
}

BT_CONN_CB_DEFINE(connection_callbacks) = {
    .connected = connected,
    .disconnected = disconnected
};

int main(void)
{
    svc_e73_telemetry_stub_init(&telemetry);
    svc_update_transfer_init(&update_transfer);

    const int uart_error = svc_e73_uart_bridge_init();
    if (uart_error != 0) {
        LOG_WRN("UART bridge unavailable: %d", uart_error);
    }

    const int bluetooth_error = bt_enable(NULL);
    if (bluetooth_error != 0) {
        LOG_ERR("Bluetooth initialization failed: %d", bluetooth_error);
        return bluetooth_error;
    }

    const int advertising_error = bt_le_adv_start(
        BT_LE_ADV_CONN_FAST_1,
        NULL,
        0,
        NULL,
        0);
    if (advertising_error != 0) {
        LOG_ERR("Advertising failed: %d", advertising_error);
        return advertising_error;
    }

    LOG_INF("SVC E73 scaffold ready; telemetry remains unavailable until UART data");
    for (;;) {
        k_sleep(K_SECONDS(1));
    }
    return 0;
}
