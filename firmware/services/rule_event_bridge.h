#pragma once

#include <stddef.h>

#include "event_bus.h"
#include "rule_condition.h"

typedef struct {
    size_t processed_events;
    size_t condition_events;
    size_t retained_events;
    size_t retain_failures;
} svc_rule_event_bridge_result_t;

svc_rule_event_bridge_result_t svc_rule_event_bridge_drain(
    svc_event_bus_t *event_bus,
    svc_rule_state_t *rule_state);
