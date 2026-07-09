#include <assert.h>
#include <stddef.h>

#include "pb100_capability.h"
#include "runtime_boot.h"
#include "svc_config.h"

static void test_boot_accepts_pb100_default_config_with_outputs_off(void)
{
    svc_runtime_t runtime = {0};

    const svc_runtime_boot_result_t result =
        svc_runtime_boot(&runtime, &svc_default_config, &svc_pb100_hardware_capability);

    assert(result.status == SVC_RUNTIME_BOOT_OK);
    assert(result.acceptance.status == SVC_CONFIG_ACCEPTANCE_OK);
    assert(result.event_bus_initialized);
    assert(result.output_manager_initialized);
    assert(result.system_safety_initialized);
    assert(result.active_output_mask == 0U);
    assert(result.locked_output_mask == 0U);
    assert(runtime.initialized);
    assert(svc_event_bus_is_empty(&runtime.event_bus));
}

static void test_boot_rejects_config_exceeding_pb100_limit(void)
{
    svc_runtime_t runtime = {0};
    svc_device_config_t config = svc_default_config;
    config.outputs[0].current_limit_ma = 13000U;

    const svc_runtime_boot_result_t result =
        svc_runtime_boot(&runtime, &config, &svc_pb100_hardware_capability);

    assert(result.status == SVC_RUNTIME_BOOT_REJECTED_CONFIG);
    assert(result.acceptance.status == SVC_CONFIG_ACCEPTANCE_CONFIG_EXCEEDS_HARDWARE);
    assert(result.active_output_mask == 0U);
    assert(result.locked_output_mask == 0U);
    assert(!runtime.initialized);
    assert(svc_event_bus_is_empty(&runtime.event_bus));
}

static void test_boot_rejects_invalid_hardware_capability(void)
{
    svc_runtime_t runtime = {0};
    svc_hardware_capability_t capability = svc_pb100_hardware_capability;
    capability.can1_tx_route_dnp_open = false;

    const svc_runtime_boot_result_t result =
        svc_runtime_boot(&runtime, &svc_default_config, &capability);

    assert(result.status == SVC_RUNTIME_BOOT_REJECTED_CONFIG);
    assert(result.acceptance.status == SVC_CONFIG_ACCEPTANCE_INVALID_HARDWARE_CAPABILITY);
    assert(result.acceptance.hardware_status == SVC_HARDWARE_CAPABILITY_INVALID_CAN1_POLICY);
    assert(result.active_output_mask == 0U);
    assert(!runtime.initialized);
}

static void test_boot_handles_null_runtime(void)
{
    const svc_runtime_boot_result_t result =
        svc_runtime_boot(NULL, &svc_default_config, &svc_pb100_hardware_capability);

    assert(result.status == SVC_RUNTIME_BOOT_INVALID_ARGUMENT);
    assert(!result.event_bus_initialized);
    assert(!result.output_manager_initialized);
    assert(!result.system_safety_initialized);
    assert(result.active_output_mask == 0U);
}

int main(void)
{
    test_boot_accepts_pb100_default_config_with_outputs_off();
    test_boot_rejects_config_exceeding_pb100_limit();
    test_boot_rejects_invalid_hardware_capability();
    test_boot_handles_null_runtime();
    return 0;
}
