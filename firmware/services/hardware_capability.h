#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "svc_config.h"

#define SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE ((size_t)-1)

typedef struct {
    svc_output_id_t id;
    uint16_t max_fuse_a;
    uint16_t max_current_ma;
    bool pwm_supported;
    bool safe_default_off;
} svc_output_capability_t;

typedef struct {
    uint8_t output_count;
    uint32_t main_fuse_limit_ma;
    uint32_t board_continuous_limit_ma;
    uint32_t default_total_current_limit_ma;
    bool outputs_default_off;
    bool configuration_required_for_roles;
    bool can1_read_only_default;
    bool can1_tx_route_dnp_open;
    bool can1_tx_requires_future_adr;
    bool can1_hardware_action_required_for_tx;
    svc_output_capability_t outputs[SVC_OUTPUT_COUNT];
} svc_hardware_capability_t;

typedef enum {
    SVC_HARDWARE_CAPABILITY_OK = 0,
    SVC_HARDWARE_CAPABILITY_INVALID_NULL,
    SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_COUNT,
    SVC_HARDWARE_CAPABILITY_INVALID_POWER_BUDGET,
    SVC_HARDWARE_CAPABILITY_INVALID_SAFE_DEFAULT,
    SVC_HARDWARE_CAPABILITY_INVALID_CAN1_POLICY,
    SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_ID,
    SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_LIMIT,
    SVC_HARDWARE_CAPABILITY_INVALID_CONFIG_NULL,
    SVC_HARDWARE_CAPABILITY_CONFIG_OUTPUT_MISMATCH,
    SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_OUTPUT_CAPABILITY,
    SVC_HARDWARE_CAPABILITY_CONFIG_REQUIRES_PWM,
    SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_POWER_BUDGET
} svc_hardware_capability_status_t;

typedef struct {
    svc_hardware_capability_status_t status;
    size_t output_index;
} svc_hardware_capability_result_t;

svc_hardware_capability_result_t svc_hardware_capability_validate(
    const svc_hardware_capability_t *capability);

svc_hardware_capability_result_t svc_hardware_capability_validate_config(
    const svc_hardware_capability_t *capability,
    const svc_device_config_t *config);
