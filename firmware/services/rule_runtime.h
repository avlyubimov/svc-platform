#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "event_dispatcher.h"
#include "rule_engine.h"
#include "rule_event_bridge.h"
#include "telemetry.h"

typedef enum {
    SVC_RULE_RUNTIME_OK = 0,
    SVC_RULE_RUNTIME_INVALID_ARGUMENT
} svc_rule_runtime_status_t;

typedef struct {
    svc_rule_runtime_status_t status;
    svc_rule_event_bridge_result_t bridge_result;
    svc_event_dispatcher_result_t dispatch_result;
    svc_rule_engine_run_result_t rule_result;
} svc_rule_runtime_result_t;

svc_rule_runtime_result_t svc_rule_runtime_process(
    svc_event_bus_t *event_bus,
    const svc_device_config_t *config,
    svc_output_manager_t *output_manager,
    svc_rule_state_t *rule_state,
    const svc_rule_t *rules,
    size_t rule_count,
    uint32_t measured_total_current_ma,
    bool telemetry_valid);

svc_rule_runtime_result_t svc_rule_runtime_process_with_telemetry(
    svc_event_bus_t *event_bus,
    const svc_device_config_t *config,
    svc_output_manager_t *output_manager,
    svc_rule_state_t *rule_state,
    const svc_rule_t *rules,
    size_t rule_count,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms);
