#include "rule_runtime.h"

#include <stddef.h>

static svc_rule_runtime_result_t make_result(svc_rule_runtime_status_t status)
{
    return (svc_rule_runtime_result_t){
        .status = status,
        .bridge_result = {0},
        .dispatch_result = {0},
        .rule_result = {
            .status = SVC_RULE_ENGINE_DENY_INVALID_ARGUMENT,
            .evaluated_rules = 0U,
            .matched_rules = 0U,
            .skipped_rules = 0U,
            .applied_actions = 0U,
            .failed_rule_index = SVC_RULE_ENGINE_RULE_INDEX_NONE,
            .last_result = {0}
        }
    };
}

static bool arguments_are_valid(
    const svc_event_bus_t *event_bus,
    const svc_device_config_t *config,
    const svc_output_manager_t *output_manager,
    const svc_rule_state_t *rule_state,
    const svc_rule_t *rules,
    size_t rule_count)
{
    return event_bus != NULL &&
           config != NULL &&
           output_manager != NULL &&
           rule_state != NULL &&
           (rule_count == 0U || rules != NULL);
}

svc_rule_runtime_result_t svc_rule_runtime_process(
    svc_event_bus_t *event_bus,
    const svc_device_config_t *config,
    svc_output_manager_t *output_manager,
    svc_rule_state_t *rule_state,
    const svc_rule_t *rules,
    size_t rule_count,
    uint32_t measured_total_current_ma,
    bool telemetry_valid)
{
    if (!arguments_are_valid(event_bus, config, output_manager, rule_state, rules, rule_count)) {
        return make_result(SVC_RULE_RUNTIME_INVALID_ARGUMENT);
    }

    svc_rule_runtime_result_t result = make_result(SVC_RULE_RUNTIME_OK);
    result.bridge_result = svc_rule_event_bridge_drain(event_bus, rule_state);
    result.dispatch_result = svc_event_dispatcher_drain(event_bus, output_manager);
    result.rule_result = svc_rule_engine_evaluate_rules(
        config,
        output_manager,
        rule_state,
        rules,
        rule_count,
        measured_total_current_ma,
        telemetry_valid);
    return result;
}

svc_rule_runtime_result_t svc_rule_runtime_process_with_telemetry(
    svc_event_bus_t *event_bus,
    const svc_device_config_t *config,
    svc_output_manager_t *output_manager,
    svc_rule_state_t *rule_state,
    const svc_rule_t *rules,
    size_t rule_count,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    if (!arguments_are_valid(event_bus, config, output_manager, rule_state, rules, rule_count)) {
        return make_result(SVC_RULE_RUNTIME_INVALID_ARGUMENT);
    }

    const svc_telemetry_power_budget_input_t input = svc_telemetry_power_budget_input(
        telemetry,
        now_ms,
        stale_after_ms);
    return svc_rule_runtime_process(
        event_bus,
        config,
        output_manager,
        rule_state,
        rules,
        rule_count,
        input.measured_total_current_ma,
        input.telemetry_valid);
}
