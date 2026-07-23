#include "ble_uart_bridge.h"

#include <errno.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/uart.h>

static const struct device *const bridge_uart =
    DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

int svc_e73_uart_bridge_init(void)
{
    return device_is_ready(bridge_uart) ? 0 : -ENODEV;
}

int svc_e73_uart_bridge_write(const uint8_t *data, size_t length)
{
    if (data == NULL && length != 0U) {
        return -EINVAL;
    }
    if (!device_is_ready(bridge_uart)) {
        return -ENODEV;
    }

    for (size_t data_index = 0U; data_index < length; ++data_index) {
        uart_poll_out(bridge_uart, data[data_index]);
    }
    return 0;
}

int svc_e73_uart_bridge_read(uint8_t *data, size_t capacity, size_t *length)
{
    if (data == NULL || length == NULL) {
        return -EINVAL;
    }
    if (!device_is_ready(bridge_uart)) {
        return -ENODEV;
    }

    size_t received = 0U;
    while (received < capacity) {
        unsigned char byte = 0U;
        if (uart_poll_in(bridge_uart, &byte) != 0) {
            break;
        }
        data[received] = byte;
        received += 1U;
    }

    *length = received;
    return 0;
}
