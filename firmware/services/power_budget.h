#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "svc_config.h"

#define SVC_MAIN_FUSE_LIMIT_MA 50000U

typedef enum {
    SVC_POWER_BUDGET_ALLOW = 0,
    SVC_POWER_BUDGET_DENY_INVALID_CONFIG,
    SVC_POWER_BUDGET_DENY_INVALID_OUTPUT,
    SVC_POWER_BUDGET_DENY_ALREADY_ACTIVE,
    SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID,
    SVC_POWER_BUDGET_DENY_TOTAL_LIMIT
} svc_power_budget_decision_t;

typedef struct {
    svc_power_budget_decision_t decision;
    uint32_t measured_total_current_ma;
    uint32_t projected_total_current_ma;
    uint32_t configured_limit_ma;
} svc_power_budget_result_t;

bool svc_power_budget_validate_config(const svc_device_config_t *config);

svc_power_budget_result_t svc_power_budget_can_enable_output(
    const svc_device_config_t *config,
    uint16_t active_output_mask,
    svc_output_id_t requested_output,
    uint32_t measured_total_current_ma,
    bool telemetry_valid);

size_t svc_power_budget_build_shed_list(
    const svc_device_config_t *config,
    uint16_t active_output_mask,
    svc_output_id_t *shed_outputs,
    size_t shed_outputs_capacity);
