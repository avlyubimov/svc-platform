#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "svc_config.h"

#define SVC_EVENT_BUS_CAPACITY 32U

typedef enum {
    SVC_EVENT_NONE = 0,
    SVC_EVENT_ENGINE_STARTED,
    SVC_EVENT_ENGINE_STOPPED,
    SVC_EVENT_HIGH_BEAM_ON,
    SVC_EVENT_HIGH_BEAM_OFF,
    SVC_EVENT_LEFT_INDICATOR_ON,
    SVC_EVENT_LEFT_INDICATOR_OFF,
    SVC_EVENT_AMBIENT_LIGHT_DAY,
    SVC_EVENT_AMBIENT_LIGHT_DUSK,
    SVC_EVENT_AMBIENT_LIGHT_NIGHT,
    SVC_EVENT_LOW_BATTERY_WARN,
    SVC_EVENT_LOW_BATTERY_CUTOFF,
    SVC_EVENT_THERMAL_DERATE,
    SVC_EVENT_THERMAL_CUTOFF,
    SVC_EVENT_OUTPUT_OVERCURRENT,
    SVC_EVENT_OUTPUT_FAULT,
    SVC_EVENT_OUTPUT_STATE_CHANGED
} svc_event_type_t;

typedef struct {
    svc_event_type_t type;
    svc_output_id_t output_id;
    uint32_t value;
} svc_event_t;

typedef struct {
    svc_event_t events[SVC_EVENT_BUS_CAPACITY];
    size_t head;
    size_t tail;
    size_t count;
} svc_event_bus_t;

void svc_event_bus_init(svc_event_bus_t *bus);
bool svc_event_bus_publish(svc_event_bus_t *bus, svc_event_t event);
bool svc_event_bus_pop(svc_event_bus_t *bus, svc_event_t *event);
size_t svc_event_bus_count(const svc_event_bus_t *bus);
bool svc_event_bus_is_empty(const svc_event_bus_t *bus);
bool svc_event_bus_is_full(const svc_event_bus_t *bus);
