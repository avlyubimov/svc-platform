#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "svc_config.h"

typedef struct {
    bool sampled_pressed;
    bool debounced_pressed;
    bool armed;
    bool request_on;
    bool stuck_fault;
    uint32_t sampled_changed_at_ms;
    uint32_t pressed_at_ms;
    uint32_t request_enabled_at_ms;
} svc_manual_fog_input_state_t;

typedef struct {
    const svc_manual_fog_config_t *config;
    svc_manual_fog_input_state_t pair_a;
    svc_manual_fog_input_state_t pair_b;
} svc_manual_fog_control_t;

typedef struct {
    bool configuration_valid;
    bool faults_clear;
    bool voltage_permits;
    bool current_permits;
    bool thermal_permits;
} svc_manual_fog_safety_t;

typedef struct {
    bool pair_a_request_on;
    bool pair_b_request_on;
    bool pair_a_channel_1_requested;
    bool pair_a_channel_2_requested;
    bool pair_b_channel_1_requested;
    bool pair_b_channel_2_requested;
    bool pair_a_stuck_fault;
    bool pair_b_stuck_fault;
} svc_manual_fog_result_t;

bool svc_manual_fog_control_init(
    svc_manual_fog_control_t *control,
    const svc_manual_fog_config_t *config,
    bool pair_a_input_level_high,
    bool pair_b_input_level_high,
    uint32_t now_ms);

svc_manual_fog_result_t svc_manual_fog_control_update(
    svc_manual_fog_control_t *control,
    bool pair_a_input_level_high,
    bool pair_b_input_level_high,
    uint32_t now_ms,
    svc_manual_fog_safety_t safety);
