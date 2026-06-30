#include "output_manager.h"

#include "config_validator.h"

static bool config_is_valid(const svc_device_config_t *config)
{
    return svc_config_validate_device(config).status == SVC_CONFIG_OK;
}

static bool output_id_is_valid(svc_output_id_t output_id)
{
    return output_id >= SVC_OUTPUT_OUT1 && output_id <= SVC_OUTPUT_OUT10;
}

static uint16_t output_mask_for_id(svc_output_id_t output_id)
{
    return (uint16_t)(1U << (uint8_t)output_id);
}

static svc_output_manager_result_t make_result(
    const svc_output_manager_t *manager,
    svc_output_manager_status_t status,
    svc_power_budget_decision_t budget_decision)
{
    svc_output_manager_result_t result = {
        .status = status,
        .budget_decision = budget_decision,
        .active_output_mask = 0U,
        .locked_output_mask = 0U
    };

    if (manager != NULL) {
        result.active_output_mask = manager->active_output_mask;
        result.locked_output_mask = manager->locked_output_mask;
    }

    return result;
}

bool svc_output_manager_init(
    svc_output_manager_t *manager,
    const svc_device_config_t *config)
{
    if (manager == NULL || !config_is_valid(config)) {
        return false;
    }

    manager->config = config;
    manager->active_output_mask = 0U;
    manager->locked_output_mask = 0U;
    return true;
}

svc_output_manager_result_t svc_output_manager_request_enable(
    svc_output_manager_t *manager,
    svc_output_id_t output_id,
    uint32_t measured_total_current_ma,
    bool telemetry_valid)
{
    if (manager == NULL || !config_is_valid(manager->config)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_CONFIG, SVC_POWER_BUDGET_DENY_INVALID_CONFIG);
    }
    if (!output_id_is_valid(output_id)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_OUTPUT, SVC_POWER_BUDGET_DENY_INVALID_OUTPUT);
    }

    const uint16_t output_mask = output_mask_for_id(output_id);
    if ((manager->locked_output_mask & output_mask) != 0U) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_LOCKED_OUT, SVC_POWER_BUDGET_ALLOW);
    }

    const svc_power_budget_result_t budget_result = svc_power_budget_can_enable_output(
        manager->config,
        manager->active_output_mask,
        output_id,
        measured_total_current_ma,
        telemetry_valid);

    if (budget_result.decision != SVC_POWER_BUDGET_ALLOW) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_BUDGET, budget_result.decision);
    }

    manager->active_output_mask |= output_mask;
    return make_result(manager, SVC_OUTPUT_MANAGER_OK, budget_result.decision);
}

svc_output_manager_result_t svc_output_manager_request_disable(
    svc_output_manager_t *manager,
    svc_output_id_t output_id)
{
    if (manager == NULL || !config_is_valid(manager->config)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_CONFIG, SVC_POWER_BUDGET_DENY_INVALID_CONFIG);
    }
    if (!output_id_is_valid(output_id)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_OUTPUT, SVC_POWER_BUDGET_DENY_INVALID_OUTPUT);
    }

    manager->active_output_mask &= (uint16_t)~output_mask_for_id(output_id);
    return make_result(manager, SVC_OUTPUT_MANAGER_OK, SVC_POWER_BUDGET_ALLOW);
}

svc_output_manager_result_t svc_output_manager_apply_fault(
    svc_output_manager_t *manager,
    svc_output_id_t output_id)
{
    if (manager == NULL || !config_is_valid(manager->config)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_CONFIG, SVC_POWER_BUDGET_DENY_INVALID_CONFIG);
    }
    if (!output_id_is_valid(output_id)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_OUTPUT, SVC_POWER_BUDGET_DENY_INVALID_OUTPUT);
    }

    const uint16_t output_mask = output_mask_for_id(output_id);
    manager->active_output_mask &= (uint16_t)~output_mask;
    manager->locked_output_mask |= output_mask;
    return make_result(manager, SVC_OUTPUT_MANAGER_OK, SVC_POWER_BUDGET_ALLOW);
}

uint16_t svc_output_manager_active_mask(const svc_output_manager_t *manager)
{
    return manager == NULL ? 0U : manager->active_output_mask;
}

uint16_t svc_output_manager_locked_mask(const svc_output_manager_t *manager)
{
    return manager == NULL ? 0U : manager->locked_output_mask;
}
