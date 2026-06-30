#include "event_dispatcher.h"

#include <stdbool.h>

static bool event_is_output_fault(svc_event_type_t event_type)
{
    return event_type == SVC_EVENT_OUTPUT_OVERCURRENT ||
           event_type == SVC_EVENT_OUTPUT_FAULT;
}

static svc_event_dispatcher_result_t make_result(const svc_output_manager_t *output_manager)
{
    return (svc_event_dispatcher_result_t){
        .processed_events = 0U,
        .ignored_events = 0U,
        .output_fault_events = 0U,
        .output_fault_failures = 0U,
        .active_output_mask = svc_output_manager_active_mask(output_manager),
        .locked_output_mask = svc_output_manager_locked_mask(output_manager)
    };
}

svc_event_dispatcher_result_t svc_event_dispatcher_drain(
    svc_event_bus_t *event_bus,
    svc_output_manager_t *output_manager)
{
    svc_event_dispatcher_result_t result = make_result(output_manager);
    if (event_bus == NULL || output_manager == NULL) {
        return result;
    }

    svc_event_t event = {0};
    while (svc_event_bus_pop(event_bus, &event)) {
        ++result.processed_events;

        if (!event_is_output_fault(event.type)) {
            ++result.ignored_events;
            continue;
        }

        ++result.output_fault_events;
        const svc_output_manager_result_t fault_result = svc_output_manager_apply_fault(
            output_manager,
            event.output_id);
        if (fault_result.status != SVC_OUTPUT_MANAGER_OK) {
            ++result.output_fault_failures;
        }
    }

    result.active_output_mask = svc_output_manager_active_mask(output_manager);
    result.locked_output_mask = svc_output_manager_locked_mask(output_manager);
    return result;
}
