#include "manual_fog_control.h"

#include <stddef.h>

static bool input_is_pressed(const svc_manual_fog_input_config_t *config, bool input_level_high)
{
    return config->active_low ? !input_level_high : input_level_high;
}

static bool input_config_is_valid(const svc_manual_fog_input_config_t *config)
{
    return config != NULL && config->active_low && config->debounce_ms > 0U &&
        config->stuck_timeout_ms > config->debounce_ms && config->channel_delay_ms > 0U &&
        (config->behavior == SVC_MANUAL_INPUT_MOMENTARY_TOGGLE ||
         config->behavior == SVC_MANUAL_INPUT_MAINTAINED);
}

static bool config_is_valid(const svc_manual_fog_config_t *config)
{
    return config != NULL && input_config_is_valid(&config->pair_a) &&
        input_config_is_valid(&config->pair_b) && !config->restore_on_boot &&
        config->output_manager_authority;
}

static svc_manual_fog_input_state_t initial_state(
    const svc_manual_fog_input_config_t *config,
    bool input_level_high,
    uint32_t now_ms)
{
    const bool pressed = input_is_pressed(config, input_level_high);
    return (svc_manual_fog_input_state_t){
        .sampled_pressed = pressed,
        .debounced_pressed = pressed,
        .armed = !pressed,
        .request_on = false,
        .stuck_fault = false,
        .sampled_changed_at_ms = now_ms,
        .pressed_at_ms = now_ms,
        .request_enabled_at_ms = now_ms
    };
}

static void update_input(
    svc_manual_fog_input_state_t *state,
    const svc_manual_fog_input_config_t *config,
    bool input_level_high,
    uint32_t now_ms,
    bool safety_allows)
{
    if (!safety_allows) {
        state->request_on = false;
    }

    const bool pressed = input_is_pressed(config, input_level_high);
    if (pressed != state->sampled_pressed) {
        state->sampled_pressed = pressed;
        state->sampled_changed_at_ms = now_ms;
    }

    if (state->sampled_pressed != state->debounced_pressed &&
        (uint32_t)(now_ms - state->sampled_changed_at_ms) >= config->debounce_ms) {
        state->debounced_pressed = state->sampled_pressed;
        if (!state->debounced_pressed) {
            state->armed = true;
            state->stuck_fault = false;
            if (config->behavior == SVC_MANUAL_INPUT_MAINTAINED) {
                state->request_on = false;
            }
        } else {
            state->pressed_at_ms = now_ms;
            if (state->armed) {
                if (config->behavior == SVC_MANUAL_INPUT_MOMENTARY_TOGGLE) {
                    state->armed = false;
                    state->request_on = safety_allows ? !state->request_on : false;
                } else {
                    state->request_on = safety_allows;
                }
                if (state->request_on) {
                    state->request_enabled_at_ms = now_ms;
                }
            }
        }
    }

    if (config->behavior == SVC_MANUAL_INPUT_MOMENTARY_TOGGLE && state->debounced_pressed &&
        (uint32_t)(now_ms - state->pressed_at_ms) >= config->stuck_timeout_ms) {
        state->stuck_fault = true;
        state->request_on = false;
    }
}

static bool safety_allows(svc_manual_fog_safety_t safety)
{
    return safety.configuration_valid && safety.faults_clear && safety.voltage_permits &&
        safety.current_permits && safety.thermal_permits;
}

bool svc_manual_fog_control_init(
    svc_manual_fog_control_t *control,
    const svc_manual_fog_config_t *config,
    bool pair_a_input_level_high,
    bool pair_b_input_level_high,
    uint32_t now_ms)
{
    if (control == NULL || !config_is_valid(config)) {
        return false;
    }

    *control = (svc_manual_fog_control_t){
        .config = config,
        .pair_a = initial_state(&config->pair_a, pair_a_input_level_high, now_ms),
        .pair_b = initial_state(&config->pair_b, pair_b_input_level_high, now_ms)
    };
    return true;
}

svc_manual_fog_result_t svc_manual_fog_control_update(
    svc_manual_fog_control_t *control,
    bool pair_a_input_level_high,
    bool pair_b_input_level_high,
    uint32_t now_ms,
    svc_manual_fog_safety_t safety)
{
    if (control == NULL || !config_is_valid(control->config)) {
        return (svc_manual_fog_result_t){0};
    }

    const bool allowed = safety_allows(safety);
    update_input(&control->pair_a, &control->config->pair_a, pair_a_input_level_high, now_ms, allowed);
    update_input(&control->pair_b, &control->config->pair_b, pair_b_input_level_high, now_ms, allowed);

    const bool pair_a_on = control->pair_a.request_on && !control->pair_a.stuck_fault;
    const bool pair_b_on = control->pair_b.request_on && !control->pair_b.stuck_fault;
    return (svc_manual_fog_result_t){
        .pair_a_request_on = control->pair_a.request_on,
        .pair_b_request_on = control->pair_b.request_on,
        .pair_a_channel_1_requested = pair_a_on,
        .pair_a_channel_2_requested = pair_a_on &&
            (uint32_t)(now_ms - control->pair_a.request_enabled_at_ms) >= control->config->pair_a.channel_delay_ms,
        .pair_b_channel_1_requested = pair_b_on,
        .pair_b_channel_2_requested = pair_b_on &&
            (uint32_t)(now_ms - control->pair_b.request_enabled_at_ms) >= control->config->pair_b.channel_delay_ms,
        .pair_a_stuck_fault = control->pair_a.stuck_fault,
        .pair_b_stuck_fault = control->pair_b.stuck_fault
    };
}
