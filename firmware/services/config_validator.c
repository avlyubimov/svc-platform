#include "config_validator.h"

#include "battery_service.h"
#include "power_budget.h"
#include "thermal_service.h"

static svc_config_validation_result_t make_result(
    svc_config_status_t status,
    size_t output_index)
{
    return (svc_config_validation_result_t){
        .status = status,
        .output_index = output_index
    };
}

static uint32_t total_current_full_scale_ma(const svc_total_current_telemetry_config_t *config)
{
    return (uint32_t)(((uint64_t)config->monitor_range_uv * 1000ULL) / config->shunt_microohm);
}

static bool svc_telemetry_config_is_valid(
    const svc_telemetry_config_t *telemetry,
    const svc_power_budget_config_t *power_budget,
    const svc_output_config_t *outputs)
{
    if (telemetry == NULL || power_budget == NULL || outputs == NULL) {
        return false;
    }

    const svc_total_current_telemetry_config_t *total_current = &telemetry->total_current;
    if (total_current->shunt_microohm == 0U ||
        total_current->monitor_range_uv == 0U ||
        total_current->gain_ppm == 0U ||
        total_current->stale_timeout_ms == 0U ||
        total_current->plausible_max_ma == 0U) {
        return false;
    }
    if (total_current->plausible_max_ma < power_budget->total_current_limit_ma) {
        return false;
    }
    if (total_current->plausible_max_ma > total_current_full_scale_ma(total_current)) {
        return false;
    }

    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        const svc_output_current_telemetry_config_t *output_current =
            &telemetry->output_current[output_index];
        if (output_current->range_ma == 0U ||
            output_current->gain_ppm == 0U ||
            output_current->stale_timeout_ms == 0U ||
            output_current->plausible_max_ma == 0U) {
            return false;
        }
        if (output_current->plausible_max_ma < outputs[output_index].current_limit_ma) {
            return false;
        }
        if (output_current->plausible_max_ma > output_current->range_ma) {
            return false;
        }
    }
    return true;
}

bool svc_output_role_is_valid(output_role_t role)
{
    return role >= OUT_ROLE_NONE && role < OUT_ROLE_COUNT;
}

svc_config_validation_result_t svc_config_validate_device(const svc_device_config_t *config)
{
    if (config == NULL) {
        return make_result(SVC_CONFIG_INVALID_NULL, SVC_CONFIG_OUTPUT_INDEX_NONE);
    }
    if (!svc_battery_config_is_valid(&config->battery)) {
        return make_result(SVC_CONFIG_INVALID_BATTERY, SVC_CONFIG_OUTPUT_INDEX_NONE);
    }
    if (!svc_thermal_config_is_valid(config)) {
        return make_result(SVC_CONFIG_INVALID_THERMAL, SVC_CONFIG_OUTPUT_INDEX_NONE);
    }
    if (!svc_power_budget_validate_config(config)) {
        return make_result(SVC_CONFIG_INVALID_POWER_BUDGET, SVC_CONFIG_OUTPUT_INDEX_NONE);
    }
    if (!svc_telemetry_config_is_valid(&config->telemetry, &config->power_budget, config->outputs)) {
        return make_result(SVC_CONFIG_INVALID_TELEMETRY, SVC_CONFIG_OUTPUT_INDEX_NONE);
    }

    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        if (!svc_output_role_is_valid(config->outputs[output_index].role)) {
            return make_result(SVC_CONFIG_INVALID_OUTPUT_ROLE, output_index);
        }
    }

    return make_result(SVC_CONFIG_OK, SVC_CONFIG_OUTPUT_INDEX_NONE);
}
