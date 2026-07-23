#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint16_t protocol_version;
    uint32_t sequence;
    bool stm32_connected;
    bool telemetry_available;
} svc_e73_telemetry_stub_t;

void svc_e73_telemetry_stub_init(svc_e73_telemetry_stub_t *telemetry);

void svc_e73_telemetry_stub_set_stm32_connected(
    svc_e73_telemetry_stub_t *telemetry,
    bool connected);
