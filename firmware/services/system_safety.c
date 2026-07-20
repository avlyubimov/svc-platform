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
            .cutoff_latched = true,
            .undervoltage_duration_s = 0U
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

static bool thermal_action_event_type(
    svc_thermal_action_t action,
    svc_event_type_t *event_type)
{
    if (event_type == NULL) {
        return false;
    }
    if (action == SVC_THERMAL_ACTION_DERATE) {
        *event_type = SVC_EVENT_THERMAL_DERATE;
        return true;
    }
    if (action == SVC_THERMAL_ACTION_CUTOFF) {
        *event_type = SVC_EVENT_THERMAL_CUTOFF;
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

static uint16_t elapsed_ms_to_s(uint32_t elapsed_ms)
{
    uint32_t elapsed_s = (elapsed_ms + 999U) / 1000U;
    if (elapsed_s == 0U) {
        elapsed_s = 1U;
    }
    return elapsed_s > UINT16_MAX ? UINT16_MAX : (uint16_t)elapsed_s;
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
    svc_thermal_monitor_init(&safety->thermal_monitor);
    safety->last_battery_action = SVC_BATTERY_ACTION_ALLOW;
    safety->last_thermal_action = SVC_THERMAL_ACTION_ALLOW;
    safety->last_battery_update_ms = 0U;
    safety->battery_update_time_valid = false;
    safety->initialized = true;
    return true;
}

static svc_system_safety_result_t update_battery_elapsed(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    uint16_t measured_mv,
    bool telemetry_valid,
    uint16_t elapsed_s)
{
    if (safety == NULL || !safety->initialized || safety->config == NULL) {
        svc_system_safety_result_t result = make_fail_safe_result(measured_mv, telemetry_valid);
        result.disabled_output_mask = disable_active_outputs(output_manager);
        result.active_output_mask = svc_output_manager_active_mask(output_manager);
        return result;
    }

    svc_system_safety_result_t result = {
        .battery = svc_battery_update_elapsed_s(
            &safety->battery_monitor,
            &safety->config->battery,
            measured_mv,
            telemetry_valid,
            elapsed_s),
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

svc_system_safety_result_t svc_system_safety_update_battery(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    uint16_t measured_mv,
    bool telemetry_valid)
{
    return update_battery_elapsed(
        safety,
        output_manager,
        event_bus,
        measured_mv,
        telemetry_valid,
        1U);
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

    uint16_t elapsed_s = 1U;
    if (safety != NULL && safety->initialized && safety->battery_update_time_valid) {
        elapsed_s = elapsed_ms_to_s(now_ms - safety->last_battery_update_ms);
    }
    if (safety != NULL && safety->initialized) {
        safety->last_battery_update_ms = now_ms;
        safety->battery_update_time_valid = true;
    }

    return update_battery_elapsed(
        safety,
        output_manager,
        event_bus,
        input.measured_battery_mv,
        input.telemetry_valid,
        elapsed_s);
}

svc_system_thermal_safety_result_t svc_system_safety_update_thermal_from_telemetry(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    svc_system_thermal_safety_result_t result = {
        .thermal = {
            .action = SVC_THERMAL_ACTION_CUTOFF,
            .derate_zone_mask = 0U,
            .cutoff_zone_mask = 0U,
            .telemetry_valid = false
        },
        .active_output_mask = svc_output_manager_active_mask(output_manager),
        .disabled_output_mask = 0U,
        .derated_output_mask = 0U,
        .event_publish_attempted = false,
        .event_published = false
    };

    if (safety == NULL || !safety->initialized || safety->config == NULL) {
        result.disabled_output_mask = disable_active_outputs(output_manager);
        result.active_output_mask = svc_output_manager_active_mask(output_manager);
        return result;
    }

    result.thermal = svc_thermal_update_from_telemetry(
        &safety->thermal_monitor,
        safety->config,
        telemetry,
        now_ms,
        stale_after_ms);

    svc_event_type_t event_type = SVC_EVENT_NONE;
    if (result.thermal.action != safety->last_thermal_action &&
        thermal_action_event_type(result.thermal.action, &event_type)) {
        result.event_publish_attempted = true;
        result.event_published = svc_event_bus_publish(
            event_bus,
            (svc_event_t){
                .type = event_type,
                .output_id = SVC_OUTPUT_OUT1,
                .value = ((uint32_t)result.thermal.cutoff_zone_mask << 8U) | result.thermal.derate_zone_mask
            });
        if (result.event_published) {
            safety->last_thermal_action = result.thermal.action;
        }
    } else {
        safety->last_thermal_action = result.thermal.action;
    }

    if (result.thermal.action == SVC_THERMAL_ACTION_CUTOFF) {
        result.disabled_output_mask = disable_active_outputs(output_manager);
    } else if (result.thermal.action == SVC_THERMAL_ACTION_DERATE) {
        const svc_output_manager_result_t derate_result = svc_output_manager_apply_thermal_derate(
            output_manager,
            SVC_THERMAL_DERATE_PWM_MAX_PERCENT);
        if (derate_result.status == SVC_OUTPUT_MANAGER_OK) {
            result.disabled_output_mask = derate_result.shed_output_mask;
            result.derated_output_mask = derate_result.derated_output_mask;
        }
    }

    result.active_output_mask = svc_output_manager_active_mask(output_manager);
    return result;
}

svc_system_power_budget_safety_result_t svc_system_safety_update_power_budget(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    uint32_t measured_total_current_ma,
    bool telemetry_valid)
{
    svc_system_power_budget_safety_result_t result = {
        .budget = {
            .status = SVC_OUTPUT_MANAGER_DENY_INVALID_CONFIG,
            .budget_decision = SVC_POWER_BUDGET_DENY_INVALID_CONFIG,
            .active_output_mask = svc_output_manager_active_mask(output_manager),
            .locked_output_mask = svc_output_manager_locked_mask(output_manager),
            .shed_output_mask = 0U,
            .derated_output_mask = 0U,
            .pwm_duty_percent = 0U
        },
        .active_output_mask = svc_output_manager_active_mask(output_manager),
        .disabled_output_mask = 0U,
        .event_publish_attempted = false,
        .event_published = false
    };

    if (safety == NULL || !safety->initialized || safety->config == NULL) {
        result.disabled_output_mask = disable_active_outputs(output_manager);
        result.active_output_mask = svc_output_manager_active_mask(output_manager);
        return result;
    }

    result.budget = svc_output_manager_enforce_budget(
        output_manager,
        measured_total_current_ma,
        telemetry_valid);
    result.disabled_output_mask = result.budget.shed_output_mask;
    if (result.budget.status == SVC_OUTPUT_MANAGER_DENY_BUDGET &&
        result.budget.budget_decision == SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID) {
        result.disabled_output_mask |= disable_active_outputs(output_manager);
    }

    if (result.disabled_output_mask != 0U) {
        result.event_publish_attempted = true;
        result.event_published = svc_event_bus_publish(
            event_bus,
            (svc_event_t){
                .type = SVC_EVENT_POWER_BUDGET_SHED,
                .output_id = SVC_OUTPUT_OUT1,
                .value = measured_total_current_ma
            });
    }

    result.active_output_mask = svc_output_manager_active_mask(output_manager);
    return result;
}

svc_system_power_budget_safety_result_t svc_system_safety_update_power_budget_from_telemetry(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    const svc_telemetry_power_budget_input_t input = svc_telemetry_power_budget_input(
        telemetry,
        now_ms,
        stale_after_ms);
    return svc_system_safety_update_power_budget(
        safety,
        output_manager,
        event_bus,
        input.measured_total_current_ma,
        input.telemetry_valid);
}
