#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "svc_config.h"
#include "telemetry.h"

typedef enum {
    SVC_THERMAL_ACTION_ALLOW = 0,
    SVC_THERMAL_ACTION_DERATE,
    SVC_THERMAL_ACTION_CUTOFF
} svc_thermal_action_t;

typedef struct {
    uint8_t cutoff_latched_mask;
} svc_thermal_monitor_t;

typedef struct {
    svc_thermal_action_t action;
    uint8_t derate_zone_mask;
    uint8_t cutoff_zone_mask;
    bool telemetry_valid;
} svc_thermal_result_t;

bool svc_thermal_zone_config_is_valid(const svc_thermal_zone_config_t *config);
bool svc_thermal_config_is_valid(const svc_device_config_t *config);

void svc_thermal_monitor_init(svc_thermal_monitor_t *monitor);

svc_thermal_result_t svc_thermal_update_zone(
    svc_thermal_monitor_t *monitor,
    const svc_thermal_zone_config_t *config,
    svc_thermal_zone_t zone,
    int16_t measured_c,
    bool telemetry_valid);

svc_thermal_result_t svc_thermal_update_from_telemetry(
    svc_thermal_monitor_t *monitor,
    const svc_device_config_t *config,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms);
