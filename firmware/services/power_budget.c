#include "power_budget.h"

static bool is_valid_output_id(svc_output_id_t output_id)
{
    return output_id >= SVC_OUTPUT_OUT1 && output_id <= SVC_OUTPUT_OUT10;
}

static uint16_t output_mask_for_id(svc_output_id_t output_id)
{
    return (uint16_t)(1U << (uint8_t)output_id);
}

static uint32_t saturated_add_u32(uint32_t left, uint32_t right)
{
    const uint32_t sum = left + right;
    return sum < left ? UINT32_MAX : sum;
}

static bool priority_seen(bool seen_priorities[3], svc_load_priority_t priority)
{
    if (priority < SVC_PRIORITY_A || priority > SVC_PRIORITY_C) {
        return false;
    }
    return seen_priorities[(uint8_t)priority];
}

bool svc_power_budget_validate_config(const svc_device_config_t *config)
{
    if (config == NULL) {
        return false;
    }
    if (config->power_budget.total_current_limit_ma == 0U) {
        return false;
    }
    if (config->power_budget.total_current_limit_ma > SVC_MAIN_FUSE_LIMIT_MA) {
        return false;
    }

    bool seen_shed_priorities[3] = {false, false, false};
    for (size_t priority_index = 0; priority_index < 3U; ++priority_index) {
        const svc_load_priority_t priority = config->power_budget.shed_order[priority_index];
        if (priority < SVC_PRIORITY_A || priority > SVC_PRIORITY_C) {
            return false;
        }
        if (priority_seen(seen_shed_priorities, priority)) {
            return false;
        }
        seen_shed_priorities[(uint8_t)priority] = true;
    }

    for (size_t output_index = 0; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        const svc_output_config_t *output = &config->outputs[output_index];
        if (output->id != (svc_output_id_t)output_index) {
            return false;
        }
        if (output->current_limit_ma == 0U) {
            return false;
        }
        if ((uint32_t)output->current_limit_ma > (uint32_t)output->fuse_limit_a * 1000U) {
            return false;
        }
        if (output->priority < SVC_PRIORITY_A || output->priority > SVC_PRIORITY_C) {
            return false;
        }
    }

    return true;
}

svc_power_budget_result_t svc_power_budget_can_enable_output(
    const svc_device_config_t *config,
    uint16_t active_output_mask,
    svc_output_id_t requested_output,
    uint32_t measured_total_current_ma,
    bool telemetry_valid)
{
    svc_power_budget_result_t result = {
        .decision = SVC_POWER_BUDGET_DENY_INVALID_CONFIG,
        .measured_total_current_ma = measured_total_current_ma,
        .projected_total_current_ma = measured_total_current_ma,
        .configured_limit_ma = 0U
    };

    if (!svc_power_budget_validate_config(config)) {
        return result;
    }
    result.configured_limit_ma = config->power_budget.total_current_limit_ma;

    if (!is_valid_output_id(requested_output)) {
        result.decision = SVC_POWER_BUDGET_DENY_INVALID_OUTPUT;
        return result;
    }
    if ((active_output_mask & output_mask_for_id(requested_output)) != 0U) {
        result.decision = SVC_POWER_BUDGET_DENY_ALREADY_ACTIVE;
        return result;
    }
    if (!telemetry_valid) {
        result.decision = SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID;
        return result;
    }

    const svc_output_config_t *output = &config->outputs[(uint8_t)requested_output];
    result.projected_total_current_ma = saturated_add_u32(
        measured_total_current_ma,
        output->current_limit_ma);
    if (result.projected_total_current_ma > config->power_budget.total_current_limit_ma) {
        result.decision = SVC_POWER_BUDGET_DENY_TOTAL_LIMIT;
        return result;
    }

    result.decision = SVC_POWER_BUDGET_ALLOW;
    return result;
}

size_t svc_power_budget_build_shed_list(
    const svc_device_config_t *config,
    uint16_t active_output_mask,
    svc_output_id_t *shed_outputs,
    size_t shed_outputs_capacity)
{
    if (!svc_power_budget_validate_config(config) || shed_outputs == NULL || shed_outputs_capacity == 0U) {
        return 0U;
    }

    size_t shed_count = 0U;
    for (size_t shed_priority_index = 0; shed_priority_index < 3U; ++shed_priority_index) {
        const svc_load_priority_t priority = config->power_budget.shed_order[shed_priority_index];
        for (size_t output_index = 0; output_index < SVC_OUTPUT_COUNT; ++output_index) {
            const svc_output_id_t output_id = (svc_output_id_t)output_index;
            if ((active_output_mask & output_mask_for_id(output_id)) == 0U) {
                continue;
            }
            if (config->outputs[output_index].priority != priority) {
                continue;
            }
            shed_outputs[shed_count] = output_id;
            ++shed_count;
            if (shed_count == shed_outputs_capacity) {
                return shed_count;
            }
        }
    }

    return shed_count;
}
