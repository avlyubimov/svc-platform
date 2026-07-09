#pragma once

#include <stddef.h>

#include "config_validator.h"
#include "hardware_capability.h"

typedef enum {
    SVC_CONFIG_ACCEPTANCE_OK = 0,
    SVC_CONFIG_ACCEPTANCE_INVALID_DEVICE_CONFIG,
    SVC_CONFIG_ACCEPTANCE_INVALID_HARDWARE_CAPABILITY,
    SVC_CONFIG_ACCEPTANCE_CONFIG_EXCEEDS_HARDWARE
} svc_config_acceptance_status_t;

typedef struct {
    svc_config_acceptance_status_t status;
    svc_config_status_t config_status;
    svc_hardware_capability_status_t hardware_status;
    size_t output_index;
} svc_config_acceptance_result_t;

svc_config_acceptance_result_t svc_config_accept_for_hardware(
    const svc_device_config_t *config,
    const svc_hardware_capability_t *capability);
