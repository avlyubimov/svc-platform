#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "svc_config.h"

typedef struct {
    const svc_manual_fog_config_t *config;
    bool sampled_pressed;
    bool debounced_pressed;
    bool armed;
    bool request_on;
    bool stuck_fault;
    uint32_t sampled_changed_at_ms;
    uint32_t pressed_at_ms;
    uint32_t request_enabled_at_ms;
} svc_manual_fog_control_t;

typedef struct {
    bool request_on;
    bool primary_pair_requested;
    bool secondary_pair_requested;
    bool stuck_fault;
} svc_manual_fog_result_t;

bool svc_manual_fog_control_init(
    svc_manual_fog_control_t *control,
    const svc_manual_fog_config_t *config,
    bool input_level_high,
    uint32_t now_ms);

svc_manual_fog_result_t svc_manual_fog_control_update(
    svc_manual_fog_control_t *control,
    bool input_level_high,
    uint32_t now_ms,
    bool configuration_valid,
    bool faults_clear,
    bool voltage_permits);
