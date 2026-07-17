#include <assert.h>
#include <stddef.h>

#include "config_validator.h"
#include "output_manager.h"
#include "svc_config.h"
#include "system_safety.h"

static void test_default_config_is_valid(void)
{
    const svc_config_validation_result_t result = svc_config_validate_device(&svc_default_config);

    assert(result.status == SVC_CONFIG_OK);
    assert(result.output_index == SVC_CONFIG_OUTPUT_INDEX_NONE);
}

static void test_none_role_is_valid(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[0].role = OUT_ROLE_NONE;

    const svc_config_validation_result_t result = svc_config_validate_device(&config);

    assert(result.status == SVC_CONFIG_OK);
}

static void test_invalid_role_is_rejected_without_role_to_output_assumption(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[4].role = OUT_ROLE_COUNT;

    const svc_config_validation_result_t result = svc_config_validate_device(&config);

    assert(result.status == SVC_CONFIG_INVALID_OUTPUT_ROLE);
    assert(result.output_index == 4U);
}

static void test_invalid_battery_config_is_rejected(void)
{
    svc_device_config_t config = svc_default_config;
    config.battery.cutoff_mv = config.battery.warn_mv;

    const svc_config_validation_result_t result = svc_config_validate_device(&config);

    assert(result.status == SVC_CONFIG_INVALID_BATTERY);
    assert(result.output_index == SVC_CONFIG_OUTPUT_INDEX_NONE);
}

static void test_invalid_power_budget_config_is_rejected(void)
{
    svc_device_config_t config = svc_default_config;
    config.power_budget.total_current_limit_ma = SVC_MAIN_FUSE_LIMIT_MA + 1U;

    const svc_config_validation_result_t result = svc_config_validate_device(&config);

    assert(result.status == SVC_CONFIG_INVALID_POWER_BUDGET);
    assert(result.output_index == SVC_CONFIG_OUTPUT_INDEX_NONE);
}

static void test_invalid_telemetry_config_is_rejected(void)
{
    svc_device_config_t config = svc_default_config;
    config.telemetry.total_current.shunt_microohm = 0U;

    const svc_config_validation_result_t result = svc_config_validate_device(&config);

    assert(result.status == SVC_CONFIG_INVALID_TELEMETRY);
    assert(result.output_index == SVC_CONFIG_OUTPUT_INDEX_NONE);
}

static void test_total_current_plausibility_must_fit_monitor_range(void)
{
    svc_device_config_t config = svc_default_config;
    config.telemetry.total_current.plausible_max_ma = 82000U;

    const svc_config_validation_result_t result = svc_config_validate_device(&config);

    assert(result.status == SVC_CONFIG_INVALID_TELEMETRY);
}

static void test_invalid_thermal_config_is_rejected(void)
{
    svc_device_config_t config = svc_default_config;
    config.thermal[SVC_THERMAL_ZONE_PCB].recovery_c = config.thermal[SVC_THERMAL_ZONE_PCB].warn_c;

    const svc_config_validation_result_t result = svc_config_validate_device(&config);

    assert(result.status == SVC_CONFIG_INVALID_THERMAL);
    assert(result.output_index == SVC_CONFIG_OUTPUT_INDEX_NONE);
}

static void test_output_manager_rejects_invalid_role_config(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[0].role = OUT_ROLE_COUNT;

    svc_output_manager_t manager = {0};

    assert(!svc_output_manager_init(&manager, &config));
}

static void test_system_safety_rejects_invalid_role_config(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[0].role = OUT_ROLE_COUNT;

    svc_system_safety_t safety = {0};

    assert(!svc_system_safety_init(&safety, &config));
}

int main(void)
{
    test_default_config_is_valid();
    test_none_role_is_valid();
    test_invalid_role_is_rejected_without_role_to_output_assumption();
    test_invalid_battery_config_is_rejected();
    test_invalid_thermal_config_is_rejected();
    test_invalid_power_budget_config_is_rejected();
    test_invalid_telemetry_config_is_rejected();
    test_total_current_plausibility_must_fit_monitor_range();
    test_output_manager_rejects_invalid_role_config();
    test_system_safety_rejects_invalid_role_config();
    return 0;
}
