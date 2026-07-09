#include <assert.h>
#include <stdbool.h>
#include <stddef.h>

#include "hardware_capability.h"
#include "pb100_capability.h"
#include "svc_config.h"

static svc_output_capability_t output_capability(
    svc_output_id_t output_id,
    uint16_t max_fuse_a,
    uint16_t max_current_ma,
    bool pwm_supported)
{
    return (svc_output_capability_t){
        .id = output_id,
        .max_fuse_a = max_fuse_a,
        .max_current_ma = max_current_ma,
        .pwm_supported = pwm_supported,
        .safe_default_off = true
    };
}

static svc_hardware_capability_t pb100_capability_fixture(void)
{
    return svc_pb100_hardware_capability;
}

static void test_pb100_capability_accepts_default_config(void)
{
    const svc_hardware_capability_t capability = pb100_capability_fixture();

    const svc_hardware_capability_result_t result =
        svc_hardware_capability_validate_config(&capability, &svc_default_config);

    assert(result.status == SVC_HARDWARE_CAPABILITY_OK);
    assert(result.output_index == SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
}

static void test_role_remap_does_not_affect_hardware_capability(void)
{
    const svc_hardware_capability_t capability = pb100_capability_fixture();
    svc_device_config_t config = svc_default_config;
    config.outputs[0].role = OUT_ROLE_DVR;
    config.outputs[1].role = OUT_ROLE_USB;
    config.outputs[9].role = OUT_ROLE_NONE;

    const svc_hardware_capability_result_t result =
        svc_hardware_capability_validate_config(&capability, &config);

    assert(result.status == SVC_HARDWARE_CAPABILITY_OK);
}

static void test_rejects_can1_tx_enabled_capability(void)
{
    svc_hardware_capability_t capability = pb100_capability_fixture();
    capability.can1_tx_route_dnp_open = false;

    const svc_hardware_capability_result_t result =
        svc_hardware_capability_validate(&capability);

    assert(result.status == SVC_HARDWARE_CAPABILITY_INVALID_CAN1_POLICY);
    assert(result.output_index == SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
}

static void test_rejects_non_sequential_output_capability(void)
{
    svc_hardware_capability_t capability = pb100_capability_fixture();
    capability.outputs[4] = output_capability(SVC_OUTPUT_OUT6, 5U, 4000U, true);

    const svc_hardware_capability_result_t result =
        svc_hardware_capability_validate(&capability);

    assert(result.status == SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_ID);
    assert(result.output_index == 4U);
}

static void test_rejects_config_current_above_capability(void)
{
    svc_hardware_capability_t capability = pb100_capability_fixture();
    capability.outputs[0].max_current_ma = 11000U;

    const svc_hardware_capability_result_t result =
        svc_hardware_capability_validate_config(&capability, &svc_default_config);

    assert(result.status == SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_OUTPUT_CAPABILITY);
    assert(result.output_index == 0U);
}

static void test_rejects_config_pwm_when_hardware_lacks_pwm(void)
{
    svc_hardware_capability_t capability = pb100_capability_fixture();
    capability.outputs[2].pwm_supported = false;

    const svc_hardware_capability_result_t result =
        svc_hardware_capability_validate_config(&capability, &svc_default_config);

    assert(result.status == SVC_HARDWARE_CAPABILITY_CONFIG_REQUIRES_PWM);
    assert(result.output_index == 2U);
}

static void test_rejects_config_above_board_budget(void)
{
    const svc_hardware_capability_t capability = pb100_capability_fixture();
    svc_device_config_t config = svc_default_config;
    config.power_budget.total_current_limit_ma = 41000U;

    const svc_hardware_capability_result_t result =
        svc_hardware_capability_validate_config(&capability, &config);

    assert(result.status == SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_POWER_BUDGET);
    assert(result.output_index == SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
}

int main(void)
{
    test_pb100_capability_accepts_default_config();
    test_role_remap_does_not_affect_hardware_capability();
    test_rejects_can1_tx_enabled_capability();
    test_rejects_non_sequential_output_capability();
    test_rejects_config_current_above_capability();
    test_rejects_config_pwm_when_hardware_lacks_pwm();
    test_rejects_config_above_board_budget();
    return 0;
}
