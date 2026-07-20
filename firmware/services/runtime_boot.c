#include "runtime_boot.h"

#include <stddef.h>

static svc_config_acceptance_result_t invalid_argument_acceptance(void)
{
    return (svc_config_acceptance_result_t){
        .status = SVC_CONFIG_ACCEPTANCE_INVALID_DEVICE_CONFIG,
        .config_status = SVC_CONFIG_INVALID_NULL,
        .hardware_status = SVC_HARDWARE_CAPABILITY_OK,
        .output_index = SVC_CONFIG_OUTPUT_INDEX_NONE
    };
}

static svc_runtime_boot_result_t make_result(
    svc_runtime_boot_status_t status,
    svc_config_acceptance_result_t acceptance,
    const svc_runtime_t *runtime)
{
    svc_runtime_boot_result_t result = {
        .status = status,
        .acceptance = acceptance,
        .event_bus_initialized = false,
        .output_manager_initialized = false,
        .system_safety_initialized = false,
        .active_output_mask = 0U,
        .locked_output_mask = 0U
    };

    if (runtime != NULL) {
        result.event_bus_initialized = true;
        result.output_manager_initialized = runtime->output_manager.config != 0;
        result.system_safety_initialized = runtime->system_safety.initialized;
        result.active_output_mask = svc_output_manager_active_mask(&runtime->output_manager);
        result.locked_output_mask = svc_output_manager_locked_mask(&runtime->output_manager);
    }

    return result;
}

svc_runtime_boot_result_t svc_runtime_boot(
    svc_runtime_t *runtime,
    const svc_device_config_t *config,
    const svc_hardware_capability_t *capability)
{
    if (runtime == NULL) {
        return make_result(SVC_RUNTIME_BOOT_INVALID_ARGUMENT, invalid_argument_acceptance(), NULL);
    }

    *runtime = (svc_runtime_t){0};
    svc_event_bus_init(&runtime->event_bus);

    const svc_config_acceptance_result_t acceptance =
        svc_config_accept_for_hardware(config, capability);
    if (acceptance.status != SVC_CONFIG_ACCEPTANCE_OK) {
        return make_result(SVC_RUNTIME_BOOT_REJECTED_CONFIG, acceptance, runtime);
    }

    if (!svc_output_manager_init(&runtime->output_manager, config) ||
        !svc_system_safety_init(&runtime->system_safety, config)) {
        *runtime = (svc_runtime_t){0};
        svc_event_bus_init(&runtime->event_bus);
        return make_result(SVC_RUNTIME_BOOT_INIT_FAILED, acceptance, runtime);
    }

    runtime->initialized = true;
    return make_result(SVC_RUNTIME_BOOT_OK, acceptance, runtime);
}

static svc_runtime_store_boot_result_t make_store_boot_result(
    svc_runtime_store_boot_status_t status,
    svc_config_store_load_result_t store,
    svc_runtime_boot_result_t boot)
{
    return (svc_runtime_store_boot_result_t){
        .status = status,
        .store = store,
        .boot = boot
    };
}

svc_runtime_store_boot_result_t svc_runtime_boot_from_store(
    svc_runtime_t *runtime,
    const svc_config_record_t *slot_a,
    const svc_config_record_t *slot_b,
    const svc_device_config_t *fallback_config,
    const svc_hardware_capability_t *capability,
    svc_device_config_t *loaded_config)
{
    const svc_config_store_load_result_t empty_store = {
        .status = SVC_CONFIG_STORE_LOAD_INVALID_ARGUMENT,
        .source = SVC_CONFIG_STORE_SOURCE_NONE,
        .slot_a_status = SVC_CONFIG_STORE_INVALID_NULL,
        .slot_b_status = SVC_CONFIG_STORE_INVALID_NULL,
        .sequence = 0U
    };

    if (runtime == NULL || loaded_config == NULL) {
        if (runtime != NULL) {
            *runtime = (svc_runtime_t){0};
            svc_event_bus_init(&runtime->event_bus);
        }
        const svc_runtime_boot_result_t boot = make_result(
            SVC_RUNTIME_BOOT_INVALID_ARGUMENT,
            invalid_argument_acceptance(),
            runtime);
        return make_store_boot_result(
            SVC_RUNTIME_STORE_BOOT_INVALID_ARGUMENT,
            empty_store,
            boot);
    }

    const svc_config_store_load_result_t store = svc_config_store_load_latest(
        slot_a,
        slot_b,
        fallback_config,
        loaded_config);
    if (store.status != SVC_CONFIG_STORE_LOAD_OK &&
        store.status != SVC_CONFIG_STORE_LOAD_FALLBACK_DEFAULT) {
        *runtime = (svc_runtime_t){0};
        svc_event_bus_init(&runtime->event_bus);
        const svc_runtime_boot_result_t boot = svc_runtime_boot(runtime, NULL, capability);
        return make_store_boot_result(
            SVC_RUNTIME_STORE_BOOT_LOAD_FAILED,
            store,
            boot);
    }

    const svc_runtime_boot_result_t boot = svc_runtime_boot(
        runtime,
        loaded_config,
        capability);
    return make_store_boot_result(
        boot.status == SVC_RUNTIME_BOOT_OK
            ? SVC_RUNTIME_STORE_BOOT_OK
            : SVC_RUNTIME_STORE_BOOT_BOOT_FAILED,
        store,
        boot);
}
