#include "output_manager.h"

#include <stddef.h>

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

static uint32_t saturated_subtract_u32(uint32_t value, uint32_t subtract)
{
    return subtract >= value ? 0U : value - subtract;
}

static uint32_t saturated_add_u32(uint32_t left, uint32_t right)
{
    const uint32_t sum = left + right;
    return sum < left ? UINT32_MAX : sum;
}

static uint32_t output_current_limit_ma(
    const svc_device_config_t *config,
    svc_output_id_t output_id)
{
    return config->outputs[(uint8_t)output_id].current_limit_ma;
}

static uint32_t scaled_current_delta_ma(uint32_t current_limit_ma, uint8_t from_duty_percent, uint8_t to_duty_percent)
{
    if (to_duty_percent <= from_duty_percent) {
        return 0U;
    }

    const uint32_t duty_delta = (uint32_t)to_duty_percent - from_duty_percent;
    return (current_limit_ma * duty_delta + 99U) / 100U;
}

static bool priority_shed_rank(
    const svc_device_config_t *config,
    svc_load_priority_t priority,
    size_t *rank)
{
    for (size_t priority_index = 0U; priority_index < 3U; ++priority_index) {
        if (config->power_budget.shed_order[priority_index] == priority) {
            if (rank != NULL) {
                *rank = priority_index;
            }
            return true;
        }
    }
    return false;
}

static bool output_is_sheddable_for_request(
    const svc_device_config_t *config,
    svc_output_id_t shed_output,
    svc_output_id_t requested_output)
{
    size_t shed_rank = 0U;
    size_t requested_rank = 0U;
    if (!priority_shed_rank(config, config->outputs[(uint8_t)shed_output].priority, &shed_rank) ||
        !priority_shed_rank(config, config->outputs[(uint8_t)requested_output].priority, &requested_rank)) {
        return false;
    }

    return shed_rank < requested_rank;
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
        .locked_output_mask = 0U,
        .shed_output_mask = 0U,
        .derated_output_mask = 0U,
        .pwm_duty_percent = 0U
    };

    if (manager != NULL) {
        result.active_output_mask = manager->active_output_mask;
        result.locked_output_mask = manager->locked_output_mask;
    }

    return result;
}

static void disable_output_without_validation(
    svc_output_manager_t *manager,
    svc_output_id_t output_id)
{
    manager->active_output_mask &= (uint16_t)~output_mask_for_id(output_id);
    manager->pwm_duty_percent[(uint8_t)output_id] = 0U;
}

static svc_power_budget_result_t validate_pwm_increase_budget(
    const svc_output_manager_t *manager,
    svc_output_id_t output_id,
    uint8_t duty_percent,
    uint32_t measured_total_current_ma,
    bool telemetry_valid)
{
    svc_power_budget_result_t result = {
        .decision = SVC_POWER_BUDGET_DENY_INVALID_CONFIG,
        .measured_total_current_ma = measured_total_current_ma,
        .projected_total_current_ma = measured_total_current_ma,
        .configured_limit_ma = 0U
    };

    if (!svc_power_budget_validate_config(manager->config)) {
        return result;
    }
    result.configured_limit_ma = manager->config->power_budget.total_current_limit_ma;

    if (!telemetry_valid) {
        result.decision = SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID;
        return result;
    }

    const uint8_t previous_duty_percent = manager->pwm_duty_percent[(uint8_t)output_id];
    const uint32_t additional_current_ma = scaled_current_delta_ma(
        output_current_limit_ma(manager->config, output_id),
        previous_duty_percent,
        duty_percent);
    result.projected_total_current_ma = saturated_add_u32(
        measured_total_current_ma,
        additional_current_ma);
    if (result.projected_total_current_ma > result.configured_limit_ma) {
        result.decision = SVC_POWER_BUDGET_DENY_TOTAL_LIMIT;
        return result;
    }

    result.decision = SVC_POWER_BUDGET_ALLOW;
    return result;
}

static svc_power_budget_result_t find_shed_plan_for_enable(
    const svc_output_manager_t *manager,
    svc_output_id_t requested_output,
    uint32_t measured_total_current_ma,
    uint16_t *shed_output_mask)
{
    svc_power_budget_result_t result = {
        .decision = SVC_POWER_BUDGET_DENY_TOTAL_LIMIT,
        .measured_total_current_ma = measured_total_current_ma,
        .projected_total_current_ma = measured_total_current_ma,
        .configured_limit_ma = manager->config->power_budget.total_current_limit_ma
    };
    svc_output_id_t shed_outputs[SVC_OUTPUT_COUNT] = {SVC_OUTPUT_OUT1};
    uint16_t candidate_shed_mask = 0U;
    uint16_t candidate_active_mask = manager->active_output_mask;
    uint32_t shed_current_ma = 0U;
    const size_t shed_count = svc_power_budget_build_shed_list(
        manager->config,
        manager->active_output_mask,
        shed_outputs,
        SVC_OUTPUT_COUNT);

    for (size_t shed_index = 0U; shed_index < shed_count; ++shed_index) {
        const svc_output_id_t candidate_output = shed_outputs[shed_index];
        if (!output_is_sheddable_for_request(manager->config, candidate_output, requested_output)) {
            continue;
        }

        candidate_shed_mask |= output_mask_for_id(candidate_output);
        candidate_active_mask &= (uint16_t)~output_mask_for_id(candidate_output);
        shed_current_ma += output_current_limit_ma(manager->config, candidate_output);

        const uint32_t effective_total_current_ma = saturated_subtract_u32(
            measured_total_current_ma,
            shed_current_ma);
        result = svc_power_budget_can_enable_output(
            manager->config,
            candidate_active_mask,
            requested_output,
            effective_total_current_ma,
            true);
        if (result.decision == SVC_POWER_BUDGET_ALLOW) {
            if (shed_output_mask != NULL) {
                *shed_output_mask = candidate_shed_mask;
            }
            return result;
        }
    }

    return result;
}

static svc_output_manager_result_t make_output_result(
    const svc_output_manager_t *manager,
    svc_output_manager_status_t status,
    svc_power_budget_decision_t budget_decision,
    svc_output_id_t output_id)
{
    svc_output_manager_result_t result = make_result(manager, status, budget_decision);
    if (manager != NULL && output_id_is_valid(output_id)) {
        result.pwm_duty_percent = manager->pwm_duty_percent[(uint8_t)output_id];
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
    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        manager->pwm_duty_percent[output_index] = 0U;
    }
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
        return make_output_result(manager, SVC_OUTPUT_MANAGER_DENY_LOCKED_OUT, SVC_POWER_BUDGET_ALLOW, output_id);
    }

    const svc_power_budget_result_t budget_result = svc_power_budget_can_enable_output(
        manager->config,
        manager->active_output_mask,
        output_id,
        measured_total_current_ma,
        telemetry_valid);

    if (budget_result.decision != SVC_POWER_BUDGET_ALLOW) {
        if (budget_result.decision == SVC_POWER_BUDGET_DENY_TOTAL_LIMIT) {
            uint16_t shed_output_mask = 0U;
            const svc_power_budget_result_t shed_budget_result = find_shed_plan_for_enable(
                manager,
                output_id,
                measured_total_current_ma,
                &shed_output_mask);
            if (shed_budget_result.decision == SVC_POWER_BUDGET_ALLOW) {
                for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
                    const svc_output_id_t shed_output = (svc_output_id_t)output_index;
                    if ((shed_output_mask & output_mask_for_id(shed_output)) != 0U) {
                        disable_output_without_validation(manager, shed_output);
                    }
                }
                manager->active_output_mask |= output_mask;
                manager->pwm_duty_percent[(uint8_t)output_id] = 100U;
                svc_output_manager_result_t result = make_output_result(
                    manager,
                    SVC_OUTPUT_MANAGER_OK,
                    shed_budget_result.decision,
                    output_id);
                result.shed_output_mask = shed_output_mask;
                return result;
            }
        }
        return make_output_result(manager, SVC_OUTPUT_MANAGER_DENY_BUDGET, budget_result.decision, output_id);
    }

    manager->active_output_mask |= output_mask;
    manager->pwm_duty_percent[(uint8_t)output_id] = 100U;
    return make_output_result(manager, SVC_OUTPUT_MANAGER_OK, budget_result.decision, output_id);
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
    manager->pwm_duty_percent[(uint8_t)output_id] = 0U;
    return make_output_result(manager, SVC_OUTPUT_MANAGER_OK, SVC_POWER_BUDGET_ALLOW, output_id);
}

svc_output_manager_result_t svc_output_manager_request_pwm(
    svc_output_manager_t *manager,
    svc_output_id_t output_id,
    uint8_t duty_percent,
    uint32_t measured_total_current_ma,
    bool telemetry_valid)
{
    if (manager == NULL || !config_is_valid(manager->config)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_CONFIG, SVC_POWER_BUDGET_DENY_INVALID_CONFIG);
    }
    if (!output_id_is_valid(output_id)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_OUTPUT, SVC_POWER_BUDGET_DENY_INVALID_OUTPUT);
    }
    if (duty_percent > 100U) {
        return make_output_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_PWM, SVC_POWER_BUDGET_ALLOW, output_id);
    }
    if (duty_percent == 0U) {
        return svc_output_manager_request_disable(manager, output_id);
    }
    if (duty_percent < 100U && !manager->config->outputs[(uint8_t)output_id].pwm_allowed) {
        return make_output_result(manager, SVC_OUTPUT_MANAGER_DENY_PWM_NOT_ALLOWED, SVC_POWER_BUDGET_ALLOW, output_id);
    }

    const uint16_t output_mask = output_mask_for_id(output_id);
    if ((manager->locked_output_mask & output_mask) != 0U) {
        return make_output_result(manager, SVC_OUTPUT_MANAGER_DENY_LOCKED_OUT, SVC_POWER_BUDGET_ALLOW, output_id);
    }

    if ((manager->active_output_mask & output_mask) == 0U) {
        const svc_output_manager_result_t enable_result = svc_output_manager_request_enable(
            manager,
            output_id,
            measured_total_current_ma,
            telemetry_valid);
        if (enable_result.status != SVC_OUTPUT_MANAGER_OK) {
            return enable_result;
        }
    } else if (duty_percent > manager->pwm_duty_percent[(uint8_t)output_id]) {
        const svc_power_budget_result_t budget_result = validate_pwm_increase_budget(
            manager,
            output_id,
            duty_percent,
            measured_total_current_ma,
            telemetry_valid);
        if (budget_result.decision != SVC_POWER_BUDGET_ALLOW) {
            return make_output_result(manager, SVC_OUTPUT_MANAGER_DENY_BUDGET, budget_result.decision, output_id);
        }
    }

    manager->pwm_duty_percent[(uint8_t)output_id] = duty_percent;
    return make_output_result(manager, SVC_OUTPUT_MANAGER_OK, SVC_POWER_BUDGET_ALLOW, output_id);
}

svc_output_manager_result_t svc_output_manager_enforce_budget(
    svc_output_manager_t *manager,
    uint32_t measured_total_current_ma,
    bool telemetry_valid)
{
    if (manager == NULL || !config_is_valid(manager->config)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_CONFIG, SVC_POWER_BUDGET_DENY_INVALID_CONFIG);
    }
    if (!telemetry_valid) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_BUDGET, SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID);
    }

    const uint32_t configured_limit_ma = manager->config->power_budget.total_current_limit_ma;
    if (measured_total_current_ma <= configured_limit_ma) {
        return make_result(manager, SVC_OUTPUT_MANAGER_OK, SVC_POWER_BUDGET_ALLOW);
    }

    svc_output_id_t shed_outputs[SVC_OUTPUT_COUNT] = {SVC_OUTPUT_OUT1};
    const size_t shed_count = svc_power_budget_build_shed_list(
        manager->config,
        manager->active_output_mask,
        shed_outputs,
        SVC_OUTPUT_COUNT);
    uint16_t shed_output_mask = 0U;
    uint32_t effective_total_current_ma = measured_total_current_ma;

    for (size_t shed_index = 0U; shed_index < shed_count; ++shed_index) {
        const svc_output_id_t shed_output = shed_outputs[shed_index];
        if ((manager->active_output_mask & output_mask_for_id(shed_output)) == 0U) {
            continue;
        }

        disable_output_without_validation(manager, shed_output);
        shed_output_mask |= output_mask_for_id(shed_output);
        effective_total_current_ma = saturated_subtract_u32(
            effective_total_current_ma,
            output_current_limit_ma(manager->config, shed_output));
        if (effective_total_current_ma <= configured_limit_ma) {
            svc_output_manager_result_t result = make_result(
                manager,
                SVC_OUTPUT_MANAGER_OK,
                SVC_POWER_BUDGET_ALLOW);
            result.shed_output_mask = shed_output_mask;
            return result;
        }
    }

    svc_output_manager_result_t result = make_result(
        manager,
        SVC_OUTPUT_MANAGER_DENY_BUDGET,
        SVC_POWER_BUDGET_DENY_TOTAL_LIMIT);
    result.shed_output_mask = shed_output_mask;
    return result;
}

svc_output_manager_result_t svc_output_manager_apply_thermal_derate(
    svc_output_manager_t *manager,
    uint8_t max_pwm_duty_percent)
{
    if (manager == NULL || !config_is_valid(manager->config)) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_CONFIG, SVC_POWER_BUDGET_DENY_INVALID_CONFIG);
    }
    if (max_pwm_duty_percent > 100U) {
        return make_result(manager, SVC_OUTPUT_MANAGER_DENY_INVALID_PWM, SVC_POWER_BUDGET_ALLOW);
    }

    uint16_t derated_output_mask = 0U;
    uint16_t shed_output_mask = 0U;
    const uint16_t active_mask = manager->active_output_mask;
    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        const svc_output_id_t output_id = (svc_output_id_t)output_index;
        const uint16_t output_mask = output_mask_for_id(output_id);
        if ((active_mask & output_mask) == 0U) {
            continue;
        }

        const svc_output_config_t *output_config = &manager->config->outputs[output_index];
        if (max_pwm_duty_percent == 0U ||
            (!output_config->pwm_allowed && output_config->priority == SVC_PRIORITY_C)) {
            disable_output_without_validation(manager, output_id);
            shed_output_mask |= output_mask;
            continue;
        }
        if (output_config->pwm_allowed &&
            manager->pwm_duty_percent[output_index] > max_pwm_duty_percent) {
            manager->pwm_duty_percent[output_index] = max_pwm_duty_percent;
            derated_output_mask |= output_mask;
        }
    }

    svc_output_manager_result_t result = make_result(
        manager,
        SVC_OUTPUT_MANAGER_OK,
        SVC_POWER_BUDGET_ALLOW);
    result.shed_output_mask = shed_output_mask;
    result.derated_output_mask = derated_output_mask;
    return result;
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
    disable_output_without_validation(manager, output_id);
    manager->locked_output_mask |= output_mask;
    return make_output_result(manager, SVC_OUTPUT_MANAGER_OK, SVC_POWER_BUDGET_ALLOW, output_id);
}

uint16_t svc_output_manager_active_mask(const svc_output_manager_t *manager)
{
    return manager == NULL ? 0U : manager->active_output_mask;
}

uint16_t svc_output_manager_locked_mask(const svc_output_manager_t *manager)
{
    return manager == NULL ? 0U : manager->locked_output_mask;
}

uint8_t svc_output_manager_pwm_duty_percent(
    const svc_output_manager_t *manager,
    svc_output_id_t output_id)
{
    if (manager == NULL || !output_id_is_valid(output_id)) {
        return 0U;
    }
    return manager->pwm_duty_percent[(uint8_t)output_id];
}
