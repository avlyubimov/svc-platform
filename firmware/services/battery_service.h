#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "svc_config.h"

typedef enum {
    SVC_BATTERY_ACTION_ALLOW = 0,
    SVC_BATTERY_ACTION_WARN,
    SVC_BATTERY_ACTION_CUTOFF
} svc_battery_action_t;

typedef struct {
    bool cutoff_latched;
    uint16_t undervoltage_duration_s;
} svc_battery_monitor_t;

typedef struct {
    svc_battery_action_t action;
    uint16_t measured_mv;
    bool telemetry_valid;
    bool cutoff_latched;
    uint16_t undervoltage_duration_s;
} svc_battery_result_t;

bool svc_battery_config_is_valid(const svc_battery_config_t *config);

void svc_battery_monitor_init(svc_battery_monitor_t *monitor);

svc_battery_result_t svc_battery_update(
    svc_battery_monitor_t *monitor,
    const svc_battery_config_t *config,
    uint16_t measured_mv,
    bool telemetry_valid);

svc_battery_result_t svc_battery_update_elapsed_s(
    svc_battery_monitor_t *monitor,
    const svc_battery_config_t *config,
    uint16_t measured_mv,
    bool telemetry_valid,
    uint16_t elapsed_s);
