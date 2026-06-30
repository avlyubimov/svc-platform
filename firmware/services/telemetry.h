#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "svc_config.h"

#define SVC_TELEMETRY_DEFAULT_STALE_MS 1000U

typedef struct {
    uint16_t battery_mv;
    int16_t thermal_c[SVC_THERMAL_ZONE_COUNT];
    uint32_t total_current_ma;
    uint32_t output_current_ma[SVC_OUTPUT_COUNT];
    uint32_t battery_updated_ms;
    uint32_t thermal_updated_ms[SVC_THERMAL_ZONE_COUNT];
    uint32_t total_current_updated_ms;
    uint32_t output_current_updated_ms[SVC_OUTPUT_COUNT];
    bool battery_valid;
    bool thermal_valid[SVC_THERMAL_ZONE_COUNT];
    bool total_current_valid;
    bool output_current_valid[SVC_OUTPUT_COUNT];
} svc_telemetry_snapshot_t;

typedef struct {
    uint32_t measured_total_current_ma;
    bool telemetry_valid;
} svc_telemetry_power_budget_input_t;

typedef struct {
    uint16_t measured_battery_mv;
    bool telemetry_valid;
} svc_telemetry_battery_input_t;

typedef struct {
    int16_t measured_temperature_c;
    bool telemetry_valid;
} svc_telemetry_thermal_input_t;

void svc_telemetry_snapshot_init(svc_telemetry_snapshot_t *snapshot);

void svc_telemetry_update_battery(
    svc_telemetry_snapshot_t *snapshot,
    uint16_t battery_mv,
    bool valid,
    uint32_t now_ms);

void svc_telemetry_update_total_current(
    svc_telemetry_snapshot_t *snapshot,
    uint32_t total_current_ma,
    bool valid,
    uint32_t now_ms);

bool svc_telemetry_update_output_current(
    svc_telemetry_snapshot_t *snapshot,
    svc_output_id_t output_id,
    uint32_t output_current_ma,
    bool valid,
    uint32_t now_ms);

bool svc_telemetry_update_thermal(
    svc_telemetry_snapshot_t *snapshot,
    svc_thermal_zone_t zone,
    int16_t temperature_c,
    bool valid,
    uint32_t now_ms);

bool svc_telemetry_battery_is_valid(
    const svc_telemetry_snapshot_t *snapshot,
    uint32_t now_ms,
    uint32_t stale_after_ms);

bool svc_telemetry_total_current_is_valid(
    const svc_telemetry_snapshot_t *snapshot,
    uint32_t now_ms,
    uint32_t stale_after_ms);

bool svc_telemetry_output_current_is_valid(
    const svc_telemetry_snapshot_t *snapshot,
    svc_output_id_t output_id,
    uint32_t now_ms,
    uint32_t stale_after_ms);

bool svc_telemetry_thermal_is_valid(
    const svc_telemetry_snapshot_t *snapshot,
    svc_thermal_zone_t zone,
    uint32_t now_ms,
    uint32_t stale_after_ms);

svc_telemetry_power_budget_input_t svc_telemetry_power_budget_input(
    const svc_telemetry_snapshot_t *snapshot,
    uint32_t now_ms,
    uint32_t stale_after_ms);

svc_telemetry_battery_input_t svc_telemetry_battery_input(
    const svc_telemetry_snapshot_t *snapshot,
    uint32_t now_ms,
    uint32_t stale_after_ms);

svc_telemetry_thermal_input_t svc_telemetry_thermal_input(
    const svc_telemetry_snapshot_t *snapshot,
    svc_thermal_zone_t zone,
    uint32_t now_ms,
    uint32_t stale_after_ms);
