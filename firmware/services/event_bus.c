#include "event_bus.h"

#include <stddef.h>

void svc_event_bus_init(svc_event_bus_t *bus)
{
    if (bus == NULL) {
        return;
    }
    bus->head = 0U;
    bus->tail = 0U;
    bus->count = 0U;
}

bool svc_event_bus_publish(svc_event_bus_t *bus, svc_event_t event)
{
    if (bus == NULL || svc_event_bus_is_full(bus)) {
        return false;
    }
    bus->events[bus->tail] = event;
    bus->tail = (bus->tail + 1U) % SVC_EVENT_BUS_CAPACITY;
    ++bus->count;
    return true;
}

bool svc_event_bus_pop(svc_event_bus_t *bus, svc_event_t *event)
{
    if (bus == NULL || event == NULL || svc_event_bus_is_empty(bus)) {
        return false;
    }
    *event = bus->events[bus->head];
    bus->head = (bus->head + 1U) % SVC_EVENT_BUS_CAPACITY;
    --bus->count;
    return true;
}

size_t svc_event_bus_count(const svc_event_bus_t *bus)
{
    return bus == NULL ? 0U : bus->count;
}

bool svc_event_bus_is_empty(const svc_event_bus_t *bus)
{
    return svc_event_bus_count(bus) == 0U;
}

bool svc_event_bus_is_full(const svc_event_bus_t *bus)
{
    return bus != NULL && bus->count == SVC_EVENT_BUS_CAPACITY;
}
