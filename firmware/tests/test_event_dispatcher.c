#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "event_bus.h"
#include "event_dispatcher.h"
#include "output_manager.h"
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

static void test_overcurrent_event_locks_output_off(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_output_manager_t manager = initialized_output_manager();

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_OVERCURRENT, SVC_OUTPUT_OUT9, 4200U}));

    const svc_event_dispatcher_result_t result = svc_event_dispatcher_drain(&bus, &manager);

    assert(result.processed_events == 1U);
    assert(result.output_fault_events == 1U);
    assert(result.output_fault_failures == 0U);
    assert(result.active_output_mask == 0U);
    assert((result.locked_output_mask & mask_for(SVC_OUTPUT_OUT9)) != 0U);
    assert(svc_event_bus_is_empty(&bus));
}

static void test_output_fault_locks_inactive_output(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_output_manager_t manager = initialized_output_manager();

    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_FAULT, SVC_OUTPUT_OUT5, 1U}));

    const svc_event_dispatcher_result_t result = svc_event_dispatcher_drain(&bus, &manager);

    assert(result.processed_events == 1U);
    assert(result.output_fault_events == 1U);
    assert(result.output_fault_failures == 0U);
    assert(result.active_output_mask == 0U);
    assert((result.locked_output_mask & mask_for(SVC_OUTPUT_OUT5)) != 0U);
}

static void test_non_fault_events_are_ignored(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_output_manager_t manager = initialized_output_manager();

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_ENGINE_STARTED, SVC_OUTPUT_OUT1, 1U}));
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_LOW_BATTERY_WARN, SVC_OUTPUT_OUT1, 11900U}));

    const svc_event_dispatcher_result_t result = svc_event_dispatcher_drain(&bus, &manager);

    assert(result.processed_events == 2U);
    assert(result.ignored_events == 2U);
    assert(result.output_fault_events == 0U);
    assert((result.active_output_mask & mask_for(SVC_OUTPUT_OUT9)) != 0U);
    assert(result.locked_output_mask == 0U);
}

static void test_invalid_output_fault_is_counted(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_output_manager_t manager = initialized_output_manager();

    assert(svc_event_bus_publish(&bus, (svc_event_t){
        SVC_EVENT_OUTPUT_OVERCURRENT,
        (svc_output_id_t)SVC_OUTPUT_COUNT,
        1U
    }));

    const svc_event_dispatcher_result_t result = svc_event_dispatcher_drain(&bus, &manager);

    assert(result.processed_events == 1U);
    assert(result.output_fault_events == 1U);
    assert(result.output_fault_failures == 1U);
    assert(result.active_output_mask == 0U);
    assert(result.locked_output_mask == 0U);
}

static void test_null_dispatcher_arguments_do_not_consume_events(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_FAULT, SVC_OUTPUT_OUT9, 1U}));

    const svc_event_dispatcher_result_t result = svc_event_dispatcher_drain(&bus, NULL);

    assert(result.processed_events == 0U);
    assert(svc_event_bus_count(&bus) == 1U);
}

int main(void)
{
    test_overcurrent_event_locks_output_off();
    test_output_fault_locks_inactive_output();
    test_non_fault_events_are_ignored();
    test_invalid_output_fault_is_counted();
    test_null_dispatcher_arguments_do_not_consume_events();
    return 0;
}
