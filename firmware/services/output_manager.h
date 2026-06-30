#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "power_budget.h"
#include "svc_config.h"

typedef enum {
    SVC_OUTPUT_MANAGER_OK = 0,
    SVC_OUTPUT_MANAGER_DENY_INVALID_CONFIG,
    SVC_OUTPUT_MANAGER_DENY_INVALID_OUTPUT,
    SVC_OUTPUT_MANAGER_DENY_LOCKED_OUT,
    SVC_OUTPUT_MANAGER_DENY_BUDGET
} svc_output_manager_status_t;

typedef struct {
    svc_output_manager_status_t status;
    svc_power_budget_decision_t budget_decision;
    uint16_t active_output_mask;
    uint16_t locked_output_mask;
} svc_output_manager_result_t;

typedef struct {
    const svc_device_config_t *config;
    uint16_t active_output_mask;
    uint16_t locked_output_mask;
} svc_output_manager_t;

bool svc_output_manager_init(
    svc_output_manager_t *manager,
    const svc_device_config_t *config);

svc_output_manager_result_t svc_output_manager_request_enable(
    svc_output_manager_t *manager,
    svc_output_id_t output_id,
    uint32_t measured_total_current_ma,
    bool telemetry_valid);

svc_output_manager_result_t svc_output_manager_request_disable(
    svc_output_manager_t *manager,
    svc_output_id_t output_id);

svc_output_manager_result_t svc_output_manager_apply_fault(
    svc_output_manager_t *manager,
    svc_output_id_t output_id);

uint16_t svc_output_manager_active_mask(const svc_output_manager_t *manager);
uint16_t svc_output_manager_locked_mask(const svc_output_manager_t *manager);
