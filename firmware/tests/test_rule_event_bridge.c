#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#include "can_decode.h"
#include "event_dispatcher.h"
#include "output_manager.h"
#include "rule_engine.h"
#include "rule_event_bridge.h"
#include "svc_config.h"

static uint16_t mask_for(svc_output_id_t output_id)
{
    return (uint16_t)(1U << (uint8_t)output_id);
}

static svc_can_frame_t high_beam_frame(uint8_t byte_value)
{
    return (svc_can_frame_t){
        .port = SVC_CAN_PORT_CAN1_VEHICLE,
        .id = 0x123U,
        .dlc = 1U,
        .data = {byte_value},
        .timestamp_ms = 100U,
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

static svc_output_manager_t initialized_output_manager(void)
{
    svc_output_manager_t manager = {0};
    assert(svc_output_manager_init(&manager, &svc_default_config));
    return manager;
}

static void test_can_event_updates_state_and_rule_engine_path(void)
{
    svc_can_event_rule_t can_rule = high_beam_rule();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);

    const svc_can_frame_t frame = high_beam_frame(0x01U);
    assert(svc_can_decode_frame_to_event(&can_rule, 1U, &frame, &bus).status ==
           SVC_CAN_DECODE_EVENT_PUBLISHED);

    const svc_rule_event_bridge_result_t bridge_result =
        svc_rule_event_bridge_drain(&bus, &state);

    assert(bridge_result.processed_events == 1U);
    assert(bridge_result.condition_events == 1U);
    assert(bridge_result.retained_events == 0U);
    assert(bridge_result.retain_failures == 0U);
    assert(state.high_beam);
    assert(svc_event_bus_is_empty(&bus));

    svc_output_manager_t manager = initialized_output_manager();
    const svc_rule_condition_t conditions[] = {
        {SVC_RULE_CONDITION_HIGH_BEAM, true}
    };
    const svc_rule_t rule = {
        .conditions = conditions,
        .condition_count = sizeof(conditions) / sizeof(conditions[0]),
        .action = {SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_PRIMARY_LEFT, 100U}
    };

    const svc_rule_engine_result_t rule_result = svc_rule_engine_evaluate_rule(
        &svc_default_config,
        &manager,
        &state,
        &rule,
        1000U,
        true);

    assert(rule_result.status == SVC_RULE_ENGINE_OK);
    assert(rule_result.role_result.output_id == SVC_OUTPUT_OUT3);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT3)) != 0U);
}

static void test_non_rule_events_are_retained_in_fifo_order(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);

    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_FAULT, SVC_OUTPUT_OUT5, 1U}));
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U}));
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_LOW_BATTERY_WARN, SVC_OUTPUT_OUT1, 11900U}));

    const svc_rule_event_bridge_result_t result = svc_rule_event_bridge_drain(&bus, &state);

    assert(result.processed_events == 3U);
    assert(result.condition_events == 1U);
    assert(result.retained_events == 2U);
    assert(result.retain_failures == 0U);
    assert(state.high_beam);
    assert(svc_event_bus_count(&bus) == 2U);

    svc_event_t event = {0};
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_OUTPUT_FAULT);
    assert(event.output_id == SVC_OUTPUT_OUT5);
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_LOW_BATTERY_WARN);
    assert(event.value == 11900U);
}

static void test_bridge_then_fault_dispatcher_preserves_lockout_path(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_output_manager_t manager = initialized_output_manager();

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT5, 1000U, true).status ==
           SVC_OUTPUT_MANAGER_OK);
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_FAULT, SVC_OUTPUT_OUT5, 1U}));
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_ENGINE_STARTED, SVC_OUTPUT_OUT1, 1U}));

    const svc_rule_event_bridge_result_t bridge_result =
        svc_rule_event_bridge_drain(&bus, &state);
    const svc_event_dispatcher_result_t dispatch_result =
        svc_event_dispatcher_drain(&bus, &manager);

    assert(bridge_result.processed_events == 2U);
    assert(bridge_result.condition_events == 1U);
    assert(bridge_result.retained_events == 1U);
    assert(state.engine_running);
    assert(dispatch_result.processed_events == 1U);
    assert(dispatch_result.output_fault_events == 1U);
    assert((dispatch_result.locked_output_mask & mask_for(SVC_OUTPUT_OUT5)) != 0U);
    assert(svc_event_bus_is_empty(&bus));
}

static void test_ordered_condition_events_update_final_state(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);

    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U}));
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_HIGH_BEAM_OFF, SVC_OUTPUT_OUT1, 0U}));
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_LEFT_INDICATOR_ON, SVC_OUTPUT_OUT1, 1U}));

    const svc_rule_event_bridge_result_t result = svc_rule_event_bridge_drain(&bus, &state);

    assert(result.processed_events == 3U);
    assert(result.condition_events == 3U);
    assert(result.retained_events == 0U);
    assert(!state.high_beam);
    assert(state.left_indicator);
    assert(svc_event_bus_is_empty(&bus));
}

static void test_ambient_condition_events_are_consumed(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);

    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_AMBIENT_LIGHT_DAY, SVC_OUTPUT_OUT1, 10000U}));
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_AMBIENT_LIGHT_NIGHT, SVC_OUTPUT_OUT1, 1000U}));

    const svc_rule_event_bridge_result_t result = svc_rule_event_bridge_drain(&bus, &state);

    assert(result.processed_events == 2U);
    assert(result.condition_events == 2U);
    assert(result.retained_events == 0U);
    assert(!state.ambient_day);
    assert(!state.ambient_dusk);
    assert(state.ambient_night);
    assert(svc_event_bus_is_empty(&bus));
}

static void test_null_arguments_do_not_consume_events(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U}));

    const svc_rule_event_bridge_result_t result = svc_rule_event_bridge_drain(&bus, NULL);

    assert(result.processed_events == 0U);
    assert(result.condition_events == 0U);
    assert(svc_event_bus_count(&bus) == 1U);
}

int main(void)
{
    test_can_event_updates_state_and_rule_engine_path();
    test_non_rule_events_are_retained_in_fifo_order();
    test_bridge_then_fault_dispatcher_preserves_lockout_path();
    test_ordered_condition_events_update_final_state();
    test_ambient_condition_events_are_consumed();
    test_null_arguments_do_not_consume_events();
    return 0;
}
