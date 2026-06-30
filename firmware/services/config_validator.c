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

    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        if (!svc_output_role_is_valid(config->outputs[output_index].role)) {
            return make_result(SVC_CONFIG_INVALID_OUTPUT_ROLE, output_index);
        }
    }

    return make_result(SVC_CONFIG_OK, SVC_CONFIG_OUTPUT_INDEX_NONE);
}
