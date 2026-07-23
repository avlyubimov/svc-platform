#include "telemetry_stub.h"

#include <stddef.h>

#include "update_state.h"

void svc_e73_telemetry_stub_init(svc_e73_telemetry_stub_t *telemetry)
{
    if (telemetry == NULL) {
        return;
    }

    *telemetry = (svc_e73_telemetry_stub_t){
        .protocol_version = SVC_UPDATE_PROTOCOL_V1,
        .telemetry_available = false
    };
}

void svc_e73_telemetry_stub_set_stm32_connected(
    svc_e73_telemetry_stub_t *telemetry,
    bool connected)
{
    if (telemetry == NULL) {
        return;
    }

    telemetry->stm32_connected = connected;
    if (!connected) {
        telemetry->telemetry_available = false;
    }
}
