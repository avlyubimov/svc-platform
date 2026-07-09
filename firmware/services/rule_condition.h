#pragma once

#include <stdbool.h>
#include <stddef.h>

#include "event_bus.h"

typedef enum {
    SVC_RULE_CONDITION_ENGINE_RUNNING = 0,
    SVC_RULE_CONDITION_HIGH_BEAM,
    SVC_RULE_CONDITION_LEFT_INDICATOR,
    SVC_RULE_CONDITION_AMBIENT_DAY,
    SVC_RULE_CONDITION_AMBIENT_DUSK,
    SVC_RULE_CONDITION_AMBIENT_NIGHT
} svc_rule_condition_type_t;

typedef struct {
    bool engine_running;
    bool high_beam;
    bool left_indicator;
    bool ambient_day;
    bool ambient_dusk;
    bool ambient_night;
} svc_rule_state_t;

typedef struct {
    svc_rule_condition_type_t type;
    bool expected;
} svc_rule_condition_t;

void svc_rule_state_init(svc_rule_state_t *state);
void svc_rule_state_apply_event(svc_rule_state_t *state, svc_event_t event);
bool svc_rule_condition_matches(
    const svc_rule_state_t *state,
    svc_rule_condition_t condition);
bool svc_rule_conditions_match_all(
    const svc_rule_state_t *state,
    const svc_rule_condition_t *conditions,
    size_t condition_count);
