#include "system_safety.h"

#include <stddef.h>

#include "config_validator.h"

static uint16_t output_mask_for_id(svc_output_id_t output_id)
{
    return (uint16_t)(1U << (uint8_t)output_id);
}

static svc_system_safety_result_t make_fail_safe_result(uint16_t measured_mv, bool telemetry_valid)
{
    return (svc_system_safety_result_t){
        .battery = {
            .action = SVC_BATTERY_ACTION_CUTOFF,
            .measured_mv = measured_mv,
            .telemetry_valid = telemetry_valid,
            .cutoff_latched = true
        },
        .active_output_mask = 0U,
        .disabled_output_mask = 0U,
        .event_publish_attempted = false,
        .event_published = false
    };
}

static bool battery_action_event_type(
    svc_battery_action_t action,
    svc_event_type_t *event_type)
{
    if (event_type == NULL) {
        return false;
    }
    if (action == SVC_BATTERY_ACTION_WARN) {
        *event_type = SVC_EVENT_LOW_BATTERY_WARN;
        return true;
    }
    if (action == SVC_BATTERY_ACTION_CUTOFF) {
        *event_type = SVC_EVENT_LOW_BATTERY_CUTOFF;
        return true;
    }
    return false;
}

static uint16_t disable_active_outputs(svc_output_manager_t *output_manager)
{
    const uint16_t active_mask = svc_output_manager_active_mask(output_manager);
    uint16_t disabled_mask = 0U;

    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        const svc_output_id_t output_id = (svc_output_id_t)output_index;
        const uint16_t output_mask = output_mask_for_id(output_id);
        if ((active_mask & output_mask) == 0U) {
            continue;
        }

        const svc_output_manager_result_t result = svc_output_manager_request_disable(
            output_manager,
            output_id);
        if (result.status == SVC_OUTPUT_MANAGER_OK) {
            disabled_mask |= output_mask;
        }
    }

    return disabled_mask;
}

bool svc_system_safety_init(
    svc_system_safety_t *safety,
    const svc_device_config_t *config)
{
    if (safety == NULL || svc_config_validate_device(config).status != SVC_CONFIG_OK) {
        return false;
    }

    safety->config = config;
    svc_battery_monitor_init(&safety->battery_monitor);
    safety->last_battery_action = SVC_BATTERY_ACTION_ALLOW;
    safety->initialized = true;
    return true;
}

svc_system_safety_result_t svc_system_safety_update_battery(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    uint16_t measured_mv,
    bool telemetry_valid)
{
    if (safety == NULL || !safety->initialized || safety->config == NULL) {
        svc_system_safety_result_t result = make_fail_safe_result(measured_mv, telemetry_valid);
        result.disabled_output_mask = disable_active_outputs(output_manager);
        result.active_output_mask = svc_output_manager_active_mask(output_manager);
        return result;
    }

    svc_system_safety_result_t result = {
        .battery = svc_battery_update(
            &safety->battery_monitor,
            &safety->config->battery,
            measured_mv,
            telemetry_valid),
        .active_output_mask = svc_output_manager_active_mask(output_manager),
        .disabled_output_mask = 0U,
        .event_publish_attempted = false,
        .event_published = false
    };

    svc_event_type_t event_type = SVC_EVENT_NONE;
    if (result.battery.action != safety->last_battery_action &&
        battery_action_event_type(result.battery.action, &event_type)) {
        result.event_publish_attempted = true;
        result.event_published = svc_event_bus_publish(
            event_bus,
            (svc_event_t){
                .type = event_type,
                .output_id = SVC_OUTPUT_OUT1,
                .value = measured_mv
            });
        if (result.event_published) {
            safety->last_battery_action = result.battery.action;
        }
    } else {
        safety->last_battery_action = result.battery.action;
    }

    if (result.battery.action == SVC_BATTERY_ACTION_CUTOFF) {
        result.disabled_output_mask = disable_active_outputs(output_manager);
    }

    result.active_output_mask = svc_output_manager_active_mask(output_manager);
    return result;
}

svc_system_safety_result_t svc_system_safety_update_from_telemetry(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    const svc_telemetry_battery_input_t input = svc_telemetry_battery_input(
        telemetry,
        now_ms,
        stale_after_ms);
    return svc_system_safety_update_battery(
        safety,
        output_manager,
        event_bus,
        input.measured_battery_mv,
        input.telemetry_valid);
}
