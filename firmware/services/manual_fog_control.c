#include "manual_fog_control.h"

#include <stddef.h>

static bool input_is_pressed(const svc_manual_fog_config_t *config, bool input_level_high)
{
    return config->active_low ? !input_level_high : input_level_high;
}

static bool config_is_valid(const svc_manual_fog_config_t *config)
{
    return config != NULL && config->active_low && config->debounce_ms > 0U &&
        config->stuck_timeout_ms > config->debounce_ms && config->pair_delay_ms > 0U &&
        !config->restore_on_boot && config->output_manager_authority;
}

static svc_manual_fog_result_t make_result(const svc_manual_fog_control_t *control)
{
    const bool primary_requested = control->request_on && !control->stuck_fault;
    return (svc_manual_fog_result_t){
        .request_on = control->request_on,
        .primary_pair_requested = primary_requested,
        .secondary_pair_requested = false,
        .stuck_fault = control->stuck_fault
    };
}

bool svc_manual_fog_control_init(
    svc_manual_fog_control_t *control,
    const svc_manual_fog_config_t *config,
    bool input_level_high,
    uint32_t now_ms)
{
    if (control == NULL || !config_is_valid(config)) {
        return false;
    }

    const bool pressed = input_is_pressed(config, input_level_high);
    *control = (svc_manual_fog_control_t){
        .config = config,
        .sampled_pressed = pressed,
        .debounced_pressed = pressed,
        .armed = !pressed,
        .request_on = false,
        .stuck_fault = false,
        .sampled_changed_at_ms = now_ms,
        .pressed_at_ms = now_ms,
        .request_enabled_at_ms = now_ms
    };
    return true;
}

svc_manual_fog_result_t svc_manual_fog_control_update(
    svc_manual_fog_control_t *control,
    bool input_level_high,
    uint32_t now_ms,
    bool configuration_valid,
    bool faults_clear,
    bool voltage_permits)
{
    if (control == NULL || !config_is_valid(control->config)) {
        return (svc_manual_fog_result_t){0};
    }

    const bool safety_allows = configuration_valid && faults_clear && voltage_permits;
    if (!safety_allows) {
        control->request_on = false;
    }

    const bool pressed = input_is_pressed(control->config, input_level_high);
    if (pressed != control->sampled_pressed) {
        control->sampled_pressed = pressed;
        control->sampled_changed_at_ms = now_ms;
    }

    if (control->sampled_pressed != control->debounced_pressed &&
        (uint32_t)(now_ms - control->sampled_changed_at_ms) >= control->config->debounce_ms) {
        control->debounced_pressed = control->sampled_pressed;
        if (!control->debounced_pressed) {
            control->armed = true;
            control->stuck_fault = false;
        } else {
            control->pressed_at_ms = now_ms;
            if (control->armed) {
                control->armed = false;
                control->request_on = safety_allows ? !control->request_on : false;
                if (control->request_on) {
                    control->request_enabled_at_ms = now_ms;
                }
            }
        }
    }

    if (control->debounced_pressed &&
        (uint32_t)(now_ms - control->pressed_at_ms) >= control->config->stuck_timeout_ms) {
        control->stuck_fault = true;
        control->request_on = false;
    }

    svc_manual_fog_result_t result = make_result(control);
    result.secondary_pair_requested = result.primary_pair_requested &&
        (uint32_t)(now_ms - control->request_enabled_at_ms) >= control->config->pair_delay_ms;
    return result;
}
