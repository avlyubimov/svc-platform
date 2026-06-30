#pragma once

#include <stddef.h>
#include <stdint.h>

#include "event_bus.h"
#include "output_manager.h"

typedef struct {
    size_t processed_events;
    size_t ignored_events;
    size_t output_fault_events;
    size_t output_fault_failures;
    uint16_t active_output_mask;
    uint16_t locked_output_mask;
} svc_event_dispatcher_result_t;

svc_event_dispatcher_result_t svc_event_dispatcher_drain(
    svc_event_bus_t *event_bus,
    svc_output_manager_t *output_manager);
