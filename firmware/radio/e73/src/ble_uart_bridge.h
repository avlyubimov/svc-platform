#pragma once

#include <stddef.h>
#include <stdint.h>

int svc_e73_uart_bridge_init(void);

int svc_e73_uart_bridge_write(const uint8_t *data, size_t length);

int svc_e73_uart_bridge_read(uint8_t *data, size_t capacity, size_t *length);
