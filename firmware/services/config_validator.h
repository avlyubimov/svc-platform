#pragma once

#include <stdbool.h>
#include <stddef.h>

#include "svc_config.h"

#define SVC_CONFIG_OUTPUT_INDEX_NONE ((size_t)-1)

typedef enum {
    SVC_CONFIG_OK = 0,
    SVC_CONFIG_INVALID_NULL,
    SVC_CONFIG_INVALID_BATTERY,
    SVC_CONFIG_INVALID_THERMAL,
    SVC_CONFIG_INVALID_POWER_BUDGET,
    SVC_CONFIG_INVALID_TELEMETRY,
    SVC_CONFIG_INVALID_OUTPUT_ROLE
} svc_config_status_t;

typedef struct {
    svc_config_status_t status;
    size_t output_index;
} svc_config_validation_result_t;

bool svc_output_role_is_valid(output_role_t role);
svc_config_validation_result_t svc_config_validate_device(const svc_device_config_t *config);
