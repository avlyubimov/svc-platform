#include <assert.h>
#include <stddef.h>

#include "config_store.h"
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

static void test_boot_from_store_uses_persisted_config(void)
{
    svc_device_config_t user_config = svc_default_config;
    user_config.battery.warn_mv = 12100U;
    user_config.battery.recovery_mv = 12500U;
    svc_config_record_t user_record = {0};
    assert(svc_config_store_build_record(&user_config, 5U, &user_record) == SVC_CONFIG_STORE_OK);

    svc_runtime_t runtime = {0};
    svc_device_config_t loaded_config = {0};
    const svc_runtime_store_boot_result_t result = svc_runtime_boot_from_store(
        &runtime,
        &user_record,
        NULL,
        &svc_default_config,
        &svc_pb100_hardware_capability,
        &loaded_config);

    assert(result.status == SVC_RUNTIME_STORE_BOOT_OK);
    assert(result.store.source == SVC_CONFIG_STORE_SOURCE_SLOT_A);
    assert(result.boot.status == SVC_RUNTIME_BOOT_OK);
    assert(loaded_config.battery.warn_mv == 12100U);
    assert(runtime.output_manager.config == &loaded_config);
    assert(runtime.initialized);
}

static void test_boot_from_store_uses_default_when_no_records_exist(void)
{
    svc_runtime_t runtime = {0};
    svc_device_config_t loaded_config = {0};
    const svc_runtime_store_boot_result_t result = svc_runtime_boot_from_store(
        &runtime,
        NULL,
        NULL,
        &svc_default_config,
        &svc_pb100_hardware_capability,
        &loaded_config);

    assert(result.status == SVC_RUNTIME_STORE_BOOT_OK);
    assert(result.store.status == SVC_CONFIG_STORE_LOAD_FALLBACK_DEFAULT);
    assert(result.store.source == SVC_CONFIG_STORE_SOURCE_FALLBACK_DEFAULT);
    assert(result.boot.status == SVC_RUNTIME_BOOT_OK);
    assert(runtime.initialized);
}

static void test_boot_from_store_fails_when_loaded_config_exceeds_hardware(void)
{
    svc_device_config_t user_config = svc_default_config;
    user_config.outputs[0].current_limit_ma = 13000U;
    svc_config_record_t user_record = {0};
    assert(svc_config_store_build_record(&user_config, 6U, &user_record) == SVC_CONFIG_STORE_OK);

    svc_runtime_t runtime = {0};
    svc_device_config_t loaded_config = {0};
    const svc_runtime_store_boot_result_t result = svc_runtime_boot_from_store(
        &runtime,
        &user_record,
        NULL,
        &svc_default_config,
        &svc_pb100_hardware_capability,
        &loaded_config);

    assert(result.status == SVC_RUNTIME_STORE_BOOT_BOOT_FAILED);
    assert(result.store.status == SVC_CONFIG_STORE_LOAD_OK);
    assert(result.boot.status == SVC_RUNTIME_BOOT_REJECTED_CONFIG);
    assert(result.boot.acceptance.status == SVC_CONFIG_ACCEPTANCE_CONFIG_EXCEEDS_HARDWARE);
    assert(!runtime.initialized);
}

static void test_boot_from_store_fails_when_no_config_can_load(void)
{
    svc_device_config_t invalid_fallback = svc_default_config;
    invalid_fallback.outputs[0].role = OUT_ROLE_COUNT;
    svc_runtime_t runtime = {0};
    svc_device_config_t loaded_config = {0};

    const svc_runtime_store_boot_result_t result = svc_runtime_boot_from_store(
        &runtime,
        NULL,
        NULL,
        &invalid_fallback,
        &svc_pb100_hardware_capability,
        &loaded_config);

    assert(result.status == SVC_RUNTIME_STORE_BOOT_LOAD_FAILED);
    assert(result.store.status == SVC_CONFIG_STORE_LOAD_NO_VALID_CONFIG);
    assert(result.boot.status == SVC_RUNTIME_BOOT_REJECTED_CONFIG);
    assert(!runtime.initialized);
}

int main(void)
{
    test_boot_accepts_pb100_default_config_with_outputs_off();
    test_boot_rejects_config_exceeding_pb100_limit();
    test_boot_rejects_invalid_hardware_capability();
    test_boot_handles_null_runtime();
    test_boot_from_store_uses_persisted_config();
    test_boot_from_store_uses_default_when_no_records_exist();
    test_boot_from_store_fails_when_loaded_config_exceeds_hardware();
    test_boot_from_store_fails_when_no_config_can_load();
    return 0;
}
