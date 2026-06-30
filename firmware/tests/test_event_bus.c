#include <assert.h>
#include <stdbool.h>
#include <stddef.h>

#include "event_bus.h"

static void test_init_starts_empty(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    assert(svc_event_bus_is_empty(&bus));
    assert(!svc_event_bus_is_full(&bus));
    assert(svc_event_bus_count(&bus) == 0U);
}

static void test_publish_and_pop_preserve_order(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_ENGINE_STARTED, SVC_OUTPUT_OUT1, 1U}));
    assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT2, 2U}));
    assert(svc_event_bus_count(&bus) == 2U);

    svc_event_t event = {0};
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_ENGINE_STARTED);
    assert(event.output_id == SVC_OUTPUT_OUT1);
    assert(event.value == 1U);

    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_HIGH_BEAM_ON);
    assert(event.output_id == SVC_OUTPUT_OUT2);
    assert(event.value == 2U);
    assert(svc_event_bus_is_empty(&bus));
}

static void test_overflow_is_rejected(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    for (size_t event_index = 0U; event_index < SVC_EVENT_BUS_CAPACITY; ++event_index) {
        assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_STATE_CHANGED, SVC_OUTPUT_OUT1, (uint32_t)event_index}));
    }

    assert(svc_event_bus_is_full(&bus));
    assert(!svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_FAULT, SVC_OUTPUT_OUT1, 0U}));
}

static void test_pop_empty_is_rejected(void)
{
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    svc_event_t event = {0};
    assert(!svc_event_bus_pop(&bus, &event));
}

int main(void)
{
    test_init_starts_empty();
    test_publish_and_pop_preserve_order();
    test_overflow_is_rejected();
    test_pop_empty_is_rejected();
    return 0;
}
