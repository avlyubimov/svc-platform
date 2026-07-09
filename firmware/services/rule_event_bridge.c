#include "rule_event_bridge.h"

#include <stdbool.h>
#include <stddef.h>

static bool event_updates_rule_state(svc_event_type_t event_type)
{
    return event_type == SVC_EVENT_ENGINE_STARTED ||
           event_type == SVC_EVENT_ENGINE_STOPPED ||
           event_type == SVC_EVENT_HIGH_BEAM_ON ||
           event_type == SVC_EVENT_HIGH_BEAM_OFF ||
           event_type == SVC_EVENT_LEFT_INDICATOR_ON ||
           event_type == SVC_EVENT_LEFT_INDICATOR_OFF;
}

svc_rule_event_bridge_result_t svc_rule_event_bridge_drain(
    svc_event_bus_t *event_bus,
    svc_rule_state_t *rule_state)
{
    svc_rule_event_bridge_result_t result = {0};
    if (event_bus == NULL || rule_state == NULL) {
        return result;
    }

    svc_event_t retained_events[SVC_EVENT_BUS_CAPACITY] = {0};
    size_t retained_count = 0U;
    svc_event_t event = {0};
    while (svc_event_bus_pop(event_bus, &event)) {
        ++result.processed_events;
        if (event_updates_rule_state(event.type)) {
            svc_rule_state_apply_event(rule_state, event);
            ++result.condition_events;
            continue;
        }

        if (retained_count < SVC_EVENT_BUS_CAPACITY) {
            retained_events[retained_count] = event;
            ++retained_count;
        } else {
            ++result.retain_failures;
        }
    }

    for (size_t event_index = 0U; event_index < retained_count; ++event_index) {
        if (svc_event_bus_publish(event_bus, retained_events[event_index])) {
            ++result.retained_events;
        } else {
            ++result.retain_failures;
        }
    }

    return result;
}
