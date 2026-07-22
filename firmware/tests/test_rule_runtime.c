#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#include "can_decode.h"
#include "rule_runtime.h"
#include "svc_config.h"

static uint16_t mask_for(svc_output_id_t output_id)
{
    return (uint16_t)(1U << (uint8_t)output_id);
}

static svc_output_manager_t initialized_output_manager(void)
{
    svc_output_manager_t manager = {0};
    assert(svc_output_manager_init(&manager, &svc_default_config));
    return manager;
}

static svc_can_frame_t high_beam_frame(uint8_t byte_value)
{
    return (svc_can_frame_t){
        .port = SVC_CAN_PORT_CAN1_VEHICLE,
        .id = 0x123U,
        .dlc = 1U,
        .data = {byte_value},
        .timestamp_us = 100000U,
        .extended_id = false
    };
}

static svc_can_event_rule_t high_beam_rule(void)
{
    return (svc_can_event_rule_t){
        .port = SVC_CAN_PORT_CAN1_VEHICLE,
        .id = 0x123U,
        .id_mask = 0x7FFU,
        .byte_index = 0U,
        .bit_mask = 0x01U,
        .active_when_nonzero = true,
        .event_on_active = SVC_EVENT_HIGH_BEAM_ON,
        .event_on_inactive = SVC_EVENT_HIGH_BEAM_OFF,
        .initialized = false,
        .last_active = false
    };
}

static void test_can_event_runtime_enables_matching_rule_set(void)
{
    svc_can_event_rule_t can_rule = high_beam_rule();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_output_manager_t manager = initialized_output_manager();
    const svc_can_frame_t frame = high_beam_frame(0x01U);
    assert(svc_can_decode_frame_to_event(&can_rule, 1U, &frame, &bus).status ==
           SVC_CAN_DECODE_EVENT_PUBLISHED);

    const svc_rule_condition_t conditions[] = {
        {SVC_RULE_CONDITION_HIGH_BEAM, true}
    };
    const svc_rule_t rules[] = {
        {
            .conditions = conditions,
            .condition_count = sizeof(conditions) / sizeof(conditions[0]),
            .action = {SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_PRIMARY_LEFT, 40U}
        },
        {
            .conditions = conditions,
            .condition_count = sizeof(conditions) / sizeof(conditions[0]),
            .action = {SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_PRIMARY_RIGHT, 40U}
        }
    };

    const svc_rule_runtime_result_t result = svc_rule_runtime_process(
        &bus,
        &svc_default_config,
        &manager,
        &state,
        rules,
        sizeof(rules) / sizeof(rules[0]),
        1000U,
        true);

    assert(result.status == SVC_RULE_RUNTIME_OK);
    assert(result.bridge_result.processed_events == 1U);
    assert(result.bridge_result.condition_events == 1U);
    assert(result.dispatch_result.processed_events == 0U);
    assert(result.rule_result.status == SVC_RULE_ENGINE_OK);
    assert(result.rule_result.applied_actions == 2U);
    assert(svc_event_bus_is_empty(&bus));
    assert(state.high_beam);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 40U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT4) == 40U);
}

static void test_fault_dispatch_runs_before_rule_actions(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_output_manager_t manager = initialized_output_manager();
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT3, 1000U, true).status ==
           SVC_OUTPUT_MANAGER_OK);
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_FAULT, SVC_OUTPUT_OUT3, 1U}));
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U}));

    const svc_rule_condition_t conditions[] = {
        {SVC_RULE_CONDITION_HIGH_BEAM, true}
    };
    const svc_rule_t rules[] = {
        {
            .conditions = conditions,
            .condition_count = sizeof(conditions) / sizeof(conditions[0]),
            .action = {SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_PRIMARY_LEFT, 100U}
        }
    };

    const svc_rule_runtime_result_t result = svc_rule_runtime_process(
        &bus,
        &svc_default_config,
        &manager,
        &state,
        rules,
        sizeof(rules) / sizeof(rules[0]),
        1000U,
        true);

    assert(result.status == SVC_RULE_RUNTIME_OK);
    assert(result.bridge_result.condition_events == 1U);
    assert(result.bridge_result.retained_events == 1U);
    assert(result.dispatch_result.output_fault_events == 1U);
    assert((result.dispatch_result.locked_output_mask & mask_for(SVC_OUTPUT_OUT3)) != 0U);
    assert(result.rule_result.status == SVC_RULE_ENGINE_DENY_OUTPUT_MANAGER);
    assert(result.rule_result.failed_rule_index == 0U);
    assert(result.rule_result.last_result.output_result.status == SVC_OUTPUT_MANAGER_DENY_LOCKED_OUT);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT3)) == 0U);
}

static void test_telemetry_wrapper_denies_stale_matching_rule(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_output_manager_t manager = initialized_output_manager();
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U}));

    const svc_rule_condition_t conditions[] = {
        {SVC_RULE_CONDITION_HIGH_BEAM, true}
    };
    const svc_rule_t rules[] = {
        {
            .conditions = conditions,
            .condition_count = sizeof(conditions) / sizeof(conditions[0]),
            .action = {SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_PRIMARY_LEFT, 40U}
        }
    };
    svc_telemetry_snapshot_t telemetry = {0};
    svc_telemetry_snapshot_init(&telemetry);
    svc_telemetry_update_total_current(&telemetry, 1000U, true, 100U);

    const svc_rule_runtime_result_t result = svc_rule_runtime_process_with_telemetry(
        &bus,
        &svc_default_config,
        &manager,
        &state,
        rules,
        sizeof(rules) / sizeof(rules[0]),
        &telemetry,
        1200U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(result.status == SVC_RULE_RUNTIME_OK);
    assert(result.rule_result.status == SVC_RULE_ENGINE_DENY_OUTPUT_MANAGER);
    assert(result.rule_result.last_result.output_result.budget_decision ==
           SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

static void test_invalid_arguments_do_not_consume_events(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U}));

    const svc_rule_runtime_result_t result = svc_rule_runtime_process(
        &bus,
        &svc_default_config,
        NULL,
        &state,
        NULL,
        0U,
        1000U,
        true);

    assert(result.status == SVC_RULE_RUNTIME_INVALID_ARGUMENT);
    assert(result.bridge_result.processed_events == 0U);
    assert(svc_event_bus_count(&bus) == 1U);
    assert(!state.high_beam);
}

int main(void)
{
    test_can_event_runtime_enables_matching_rule_set();
    test_fault_dispatch_runs_before_rule_actions();
    test_telemetry_wrapper_denies_stale_matching_rule();
    test_invalid_arguments_do_not_consume_events();
    return 0;
}
