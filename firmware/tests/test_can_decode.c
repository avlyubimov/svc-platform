#include <assert.h>
#include <stddef.h>

#include "can_decode.h"

static svc_can_frame_t frame_with_byte(uint8_t byte_value)
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

static void test_publishes_event_on_rising_edge(void)
{
    svc_can_event_rule_t rule = high_beam_rule();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    const svc_can_frame_t frame = frame_with_byte(0x01U);

    const svc_can_decode_result_t result = svc_can_decode_frame_to_event(&rule, 1U, &frame, &bus);

    assert(result.status == SVC_CAN_DECODE_EVENT_PUBLISHED);
    assert(result.rule_index == 0U);
    assert(result.event_type == SVC_EVENT_HIGH_BEAM_ON);
    assert(result.active);
    assert(svc_event_bus_count(&bus) == 1U);

    svc_event_t event = {0};
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_HIGH_BEAM_ON);
    assert(event.value == 0x123U);
}

static void test_does_not_repeat_unchanged_event(void)
{
    svc_can_event_rule_t rule = high_beam_rule();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    const svc_can_frame_t frame = frame_with_byte(0x01U);

    assert(svc_can_decode_frame_to_event(&rule, 1U, &frame, &bus).status == SVC_CAN_DECODE_EVENT_PUBLISHED);
    assert(svc_can_decode_frame_to_event(&rule, 1U, &frame, &bus).status == SVC_CAN_DECODE_EVENT_UNCHANGED);
    assert(svc_event_bus_count(&bus) == 1U);
}

static void test_publishes_event_on_falling_edge(void)
{
    svc_can_event_rule_t rule = high_beam_rule();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    const svc_can_frame_t active_frame = frame_with_byte(0x01U);
    const svc_can_frame_t inactive_frame = frame_with_byte(0x00U);

    assert(svc_can_decode_frame_to_event(&rule, 1U, &active_frame, &bus).status == SVC_CAN_DECODE_EVENT_PUBLISHED);
    const svc_can_decode_result_t result = svc_can_decode_frame_to_event(&rule, 1U, &inactive_frame, &bus);

    assert(result.status == SVC_CAN_DECODE_EVENT_PUBLISHED);
    assert(result.event_type == SVC_EVENT_HIGH_BEAM_OFF);
    assert(!result.active);
    assert(svc_event_bus_count(&bus) == 2U);
}

static void test_ignores_mismatched_frame(void)
{
    svc_can_event_rule_t rule = high_beam_rule();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_can_frame_t frame = frame_with_byte(0x01U);
    frame.id = 0x124U;

    const svc_can_decode_result_t result = svc_can_decode_frame_to_event(&rule, 1U, &frame, &bus);

    assert(result.status == SVC_CAN_DECODE_NO_MATCH);
    assert(svc_event_bus_is_empty(&bus));
}

static void test_invalid_frame_is_rejected(void)
{
    svc_can_event_rule_t rule = high_beam_rule();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_can_frame_t frame = frame_with_byte(0x01U);
    frame.dlc = SVC_CAN_FRAME_MAX_DATA_LEN + 1U;

    const svc_can_decode_result_t result = svc_can_decode_frame_to_event(&rule, 1U, &frame, &bus);

    assert(result.status == SVC_CAN_DECODE_INVALID_FRAME);
    assert(svc_event_bus_is_empty(&bus));
}

static void test_event_bus_full_reports_dropped_event(void)
{
    svc_can_event_rule_t rule = high_beam_rule();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    for (size_t index = 0U; index < SVC_EVENT_BUS_CAPACITY; ++index) {
        assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_STATE_CHANGED, SVC_OUTPUT_OUT1, (uint32_t)index}));
    }
    const svc_can_frame_t frame = frame_with_byte(0x01U);

    const svc_can_decode_result_t result = svc_can_decode_frame_to_event(&rule, 1U, &frame, &bus);

    assert(result.status == SVC_CAN_DECODE_EVENT_DROPPED);
    assert(svc_event_bus_count(&bus) == SVC_EVENT_BUS_CAPACITY);
}

static void test_dropped_event_does_not_advance_rule_state(void)
{
    svc_can_event_rule_t rule = high_beam_rule();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    for (size_t index = 0U; index < SVC_EVENT_BUS_CAPACITY; ++index) {
        assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_STATE_CHANGED, SVC_OUTPUT_OUT1, (uint32_t)index}));
    }
    const svc_can_frame_t frame = frame_with_byte(0x01U);

    assert(svc_can_decode_frame_to_event(&rule, 1U, &frame, &bus).status ==
           SVC_CAN_DECODE_EVENT_DROPPED);
    assert(!rule.initialized);
    assert(!rule.last_active);

    svc_event_t dropped_space = {0};
    assert(svc_event_bus_pop(&bus, &dropped_space));
    assert(svc_can_decode_frame_to_event(&rule, 1U, &frame, &bus).status ==
           SVC_CAN_DECODE_EVENT_PUBLISHED);
    assert(rule.initialized);
    assert(rule.last_active);
}

int main(void)
{
    test_publishes_event_on_rising_edge();
    test_does_not_repeat_unchanged_event();
    test_publishes_event_on_falling_edge();
    test_ignores_mismatched_frame();
    test_invalid_frame_is_rejected();
    test_event_bus_full_reports_dropped_event();
    test_dropped_event_does_not_advance_rule_state();
    return 0;
}
