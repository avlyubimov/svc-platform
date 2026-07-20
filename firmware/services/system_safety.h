#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "battery_service.h"
#include "event_bus.h"
#include "output_manager.h"
#include "svc_config.h"
#include "telemetry.h"
#include "thermal_service.h"

#define SVC_THERMAL_DERATE_PWM_MAX_PERCENT 50U

typedef struct {
    svc_battery_result_t battery;
    uint16_t active_output_mask;
    uint16_t disabled_output_mask;
    bool event_publish_attempted;
    bool event_published;
} svc_system_safety_result_t;

typedef struct {
    svc_thermal_result_t thermal;
    uint16_t active_output_mask;
    uint16_t disabled_output_mask;
    uint16_t derated_output_mask;
    bool event_publish_attempted;
    bool event_published;
} svc_system_thermal_safety_result_t;

typedef struct {
    svc_output_manager_result_t budget;
    uint16_t active_output_mask;
    uint16_t disabled_output_mask;
    bool event_publish_attempted;
    bool event_published;
} svc_system_power_budget_safety_result_t;

typedef struct {
    const svc_device_config_t *config;
    svc_battery_monitor_t battery_monitor;
    svc_thermal_monitor_t thermal_monitor;
    svc_battery_action_t last_battery_action;
    svc_thermal_action_t last_thermal_action;
    uint32_t last_battery_update_ms;
    uint32_t pending_power_budget_shed_value;
    bool battery_update_time_valid;
    bool power_budget_shed_event_pending;
    bool initialized;
} svc_system_safety_t;

bool svc_system_safety_init(
    svc_system_safety_t *safety,
    const svc_device_config_t *config);

svc_system_safety_result_t svc_system_safety_update_battery(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    uint16_t measured_mv,
    bool telemetry_valid);

svc_system_safety_result_t svc_system_safety_update_from_telemetry(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms);

svc_system_thermal_safety_result_t svc_system_safety_update_thermal_from_telemetry(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms);

svc_system_power_budget_safety_result_t svc_system_safety_update_power_budget(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    uint32_t measured_total_current_ma,
    bool telemetry_valid);

svc_system_power_budget_safety_result_t svc_system_safety_update_power_budget_from_telemetry(
    svc_system_safety_t *safety,
    svc_output_manager_t *output_manager,
    svc_event_bus_t *event_bus,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms);
