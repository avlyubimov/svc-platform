#include <assert.h>

#include "config_acceptance.h"
#include "pb100_capability.h"
#include "svc_config.h"

static void test_accepts_default_config_for_pb100(void)
{
    const svc_config_acceptance_result_t result =
        svc_config_accept_for_hardware(&svc_default_config, &svc_pb100_hardware_capability);

    assert(result.status == SVC_CONFIG_ACCEPTANCE_OK);
    assert(result.config_status == SVC_CONFIG_OK);
    assert(result.hardware_status == SVC_HARDWARE_CAPABILITY_OK);
    assert(result.output_index == SVC_CONFIG_OUTPUT_INDEX_NONE);
}

static void test_accepts_role_remap_inside_pb100_limits(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[0].role = OUT_ROLE_SPARE;
    config.outputs[9].role = OUT_ROLE_NONE;

    const svc_config_acceptance_result_t result =
        svc_config_accept_for_hardware(&config, &svc_pb100_hardware_capability);

    assert(result.status == SVC_CONFIG_ACCEPTANCE_OK);
}

static void test_rejects_invalid_device_config_first(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[3].role = OUT_ROLE_COUNT;

    const svc_config_acceptance_result_t result =
        svc_config_accept_for_hardware(&config, &svc_pb100_hardware_capability);

    assert(result.status == SVC_CONFIG_ACCEPTANCE_INVALID_DEVICE_CONFIG);
    assert(result.config_status == SVC_CONFIG_INVALID_OUTPUT_ROLE);
    assert(result.hardware_status == SVC_HARDWARE_CAPABILITY_OK);
    assert(result.output_index == 3U);
}

static void test_rejects_invalid_hardware_capability(void)
{
    svc_hardware_capability_t capability = svc_pb100_hardware_capability;
    capability.can1_read_only_default = false;

    const svc_config_acceptance_result_t result =
        svc_config_accept_for_hardware(&svc_default_config, &capability);

    assert(result.status == SVC_CONFIG_ACCEPTANCE_INVALID_HARDWARE_CAPABILITY);
    assert(result.config_status == SVC_CONFIG_OK);
    assert(result.hardware_status == SVC_HARDWARE_CAPABILITY_INVALID_CAN1_POLICY);
    assert(result.output_index == SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
}

static void test_rejects_config_exceeding_hardware_output_limit(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[0].current_limit_ma = 13000U;
    config.outputs[0].fuse_limit_a = 15U;

    const svc_config_acceptance_result_t result =
        svc_config_accept_for_hardware(&config, &svc_pb100_hardware_capability);

    assert(result.status == SVC_CONFIG_ACCEPTANCE_CONFIG_EXCEEDS_HARDWARE);
    assert(result.config_status == SVC_CONFIG_OK);
    assert(result.hardware_status == SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_OUTPUT_CAPABILITY);
    assert(result.output_index == 0U);
}

static void test_rejects_config_exceeding_hardware_board_budget(void)
{
    svc_device_config_t config = svc_default_config;
    config.power_budget.total_current_limit_ma = 41000U;

    const svc_config_acceptance_result_t result =
        svc_config_accept_for_hardware(&config, &svc_pb100_hardware_capability);

    assert(result.status == SVC_CONFIG_ACCEPTANCE_CONFIG_EXCEEDS_HARDWARE);
    assert(result.config_status == SVC_CONFIG_OK);
    assert(result.hardware_status == SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_POWER_BUDGET);
    assert(result.output_index == SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
}

int main(void)
{
    test_accepts_default_config_for_pb100();
    test_accepts_role_remap_inside_pb100_limits();
    test_rejects_invalid_device_config_first();
    test_rejects_invalid_hardware_capability();
    test_rejects_config_exceeding_hardware_output_limit();
    test_rejects_config_exceeding_hardware_board_budget();
    return 0;
}
