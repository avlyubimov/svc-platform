#include "can_decode.h"

#include <stddef.h>

static bool port_is_valid(svc_can_port_t port)
{
    return port == SVC_CAN_PORT_CAN1_VEHICLE ||
           port == SVC_CAN_PORT_CAN2_EXPANSION;
}

static svc_can_decode_result_t make_result(
    svc_can_decode_status_t status,
    size_t rule_index,
    svc_event_type_t event_type,
    bool active)
{
    return (svc_can_decode_result_t){
        .status = status,
        .rule_index = rule_index,
        .event_type = event_type,
        .active = active
    };
}

static bool frame_is_valid(const svc_can_frame_t *frame)
{
    return frame != NULL &&
           port_is_valid(frame->port) &&
           frame->dlc <= SVC_CAN_FRAME_MAX_DATA_LEN;
}

static bool rule_matches_frame(
    const svc_can_event_rule_t *rule,
    const svc_can_frame_t *frame)
{
    return rule->port == frame->port &&
           ((frame->id ^ rule->id) & rule->id_mask) == 0U &&
           rule->byte_index < frame->dlc &&
           rule->bit_mask != 0U;
}

svc_can_decode_result_t svc_can_decode_frame_to_event(
    svc_can_event_rule_t *rules,
    size_t rule_count,
    const svc_can_frame_t *frame,
    svc_event_bus_t *event_bus)
{
    if (rules == NULL || rule_count == 0U || event_bus == NULL) {
        return make_result(
            SVC_CAN_DECODE_INVALID_ARGUMENT,
            SVC_CAN_DECODE_EVENT_RULE_INDEX_NONE,
            SVC_EVENT_NONE,
            false);
    }
    if (!frame_is_valid(frame)) {
        return make_result(
            SVC_CAN_DECODE_INVALID_FRAME,
            SVC_CAN_DECODE_EVENT_RULE_INDEX_NONE,
            SVC_EVENT_NONE,
            false);
    }

    for (size_t rule_index = 0U; rule_index < rule_count; ++rule_index) {
        svc_can_event_rule_t *rule = &rules[rule_index];
        if (!rule_matches_frame(rule, frame)) {
            continue;
        }

        const bool bit_is_set = (frame->data[rule->byte_index] & rule->bit_mask) != 0U;
        const bool active = rule->active_when_nonzero ? bit_is_set : !bit_is_set;
        const svc_event_type_t event_type = active
            ? rule->event_on_active
            : rule->event_on_inactive;

        if (event_type == SVC_EVENT_NONE) {
            rule->initialized = true;
            rule->last_active = active;
            return make_result(
                SVC_CAN_DECODE_EVENT_UNCHANGED,
                rule_index,
                SVC_EVENT_NONE,
                active);
        }
        if (rule->initialized && rule->last_active == active) {
            return make_result(
                SVC_CAN_DECODE_EVENT_UNCHANGED,
                rule_index,
                event_type,
                active);
        }

        const bool published = svc_event_bus_publish(
            event_bus,
            (svc_event_t){
                .type = event_type,
                .output_id = SVC_OUTPUT_OUT1,
                .value = frame->id
            });
        if (published) {
            rule->initialized = true;
            rule->last_active = active;
        }
        return make_result(
            published ? SVC_CAN_DECODE_EVENT_PUBLISHED : SVC_CAN_DECODE_EVENT_DROPPED,
            rule_index,
            event_type,
            active);
    }

    return make_result(
        SVC_CAN_DECODE_NO_MATCH,
        SVC_CAN_DECODE_EVENT_RULE_INDEX_NONE,
        SVC_EVENT_NONE,
        false);
}
