#include "runtime_boot.h"

#include <stddef.h>

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
    const svc_config_acceptance_result_t empty_acceptance = {
        .status = SVC_CONFIG_ACCEPTANCE_INVALID_DEVICE_CONFIG,
        .config_status = SVC_CONFIG_INVALID_NULL,
        .hardware_status = SVC_HARDWARE_CAPABILITY_OK,
        .output_index = SVC_CONFIG_OUTPUT_INDEX_NONE
    };

    if (runtime == NULL) {
        return make_result(SVC_RUNTIME_BOOT_INVALID_ARGUMENT, empty_acceptance, NULL);
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
