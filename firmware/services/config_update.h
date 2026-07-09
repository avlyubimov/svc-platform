#pragma once

#include <stdint.h>

#include "config_acceptance.h"
#include "config_store.h"

typedef enum {
    SVC_CONFIG_UPDATE_OK = 0,
    SVC_CONFIG_UPDATE_INVALID_ARGUMENT,
    SVC_CONFIG_UPDATE_REJECTED,
    SVC_CONFIG_UPDATE_RECORD_BUILD_FAILED
} svc_config_update_status_t;

typedef struct {
    svc_config_update_status_t status;
    svc_config_acceptance_result_t acceptance;
    svc_config_store_status_t store_status;
} svc_config_update_result_t;

svc_config_update_result_t svc_config_update_prepare_record(
    const svc_device_config_t *config,
    const svc_hardware_capability_t *capability,
    uint32_t sequence,
    svc_config_record_t *record);
