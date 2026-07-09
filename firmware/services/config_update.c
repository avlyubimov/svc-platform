#include "config_update.h"

#include <stddef.h>

static svc_config_update_result_t make_result(
    svc_config_update_status_t status,
    svc_config_acceptance_result_t acceptance,
    svc_config_store_status_t store_status)
{
    return (svc_config_update_result_t){
        .status = status,
        .acceptance = acceptance,
        .store_status = store_status
    };
}

svc_config_update_result_t svc_config_update_prepare_record(
    const svc_device_config_t *config,
    const svc_hardware_capability_t *capability,
    uint32_t sequence,
    svc_config_record_t *record)
{
    const svc_config_acceptance_result_t acceptance =
        svc_config_accept_for_hardware(config, capability);
    if (record == NULL) {
        return make_result(
            SVC_CONFIG_UPDATE_INVALID_ARGUMENT,
            acceptance,
            SVC_CONFIG_STORE_INVALID_NULL);
    }

    *record = (svc_config_record_t){0};
    if (acceptance.status != SVC_CONFIG_ACCEPTANCE_OK) {
        return make_result(
            SVC_CONFIG_UPDATE_REJECTED,
            acceptance,
            SVC_CONFIG_STORE_INVALID_CONFIG);
    }

    const svc_config_store_status_t store_status = svc_config_store_build_record(
        config,
        sequence,
        record);
    return make_result(
        store_status == SVC_CONFIG_STORE_OK
            ? SVC_CONFIG_UPDATE_OK
            : SVC_CONFIG_UPDATE_RECORD_BUILD_FAILED,
        acceptance,
        store_status);
}
