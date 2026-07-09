#include "rule_condition.h"

#include <stddef.h>

void svc_rule_state_init(svc_rule_state_t *state)
{
    if (state == NULL) {
        return;
    }

    state->engine_running = false;
    state->high_beam = false;
    state->left_indicator = false;
    state->ambient_day = false;
    state->ambient_dusk = false;
    state->ambient_night = false;
}

static void set_ambient_light_state(svc_rule_state_t *state, bool day, bool dusk, bool night)
{
    state->ambient_day = day;
    state->ambient_dusk = dusk;
    state->ambient_night = night;
}

void svc_rule_state_apply_event(svc_rule_state_t *state, svc_event_t event)
{
    if (state == NULL) {
        return;
    }

    switch (event.type) {
    case SVC_EVENT_ENGINE_STARTED:
        state->engine_running = true;
        break;
    case SVC_EVENT_ENGINE_STOPPED:
        state->engine_running = false;
        break;
    case SVC_EVENT_HIGH_BEAM_ON:
        state->high_beam = true;
        break;
    case SVC_EVENT_HIGH_BEAM_OFF:
        state->high_beam = false;
        break;
    case SVC_EVENT_LEFT_INDICATOR_ON:
        state->left_indicator = true;
        break;
    case SVC_EVENT_LEFT_INDICATOR_OFF:
        state->left_indicator = false;
        break;
    case SVC_EVENT_AMBIENT_LIGHT_DAY:
        set_ambient_light_state(state, true, false, false);
        break;
    case SVC_EVENT_AMBIENT_LIGHT_DUSK:
        set_ambient_light_state(state, false, true, false);
        break;
    case SVC_EVENT_AMBIENT_LIGHT_NIGHT:
        set_ambient_light_state(state, false, false, true);
        break;
    default:
        break;
    }
}

bool svc_rule_condition_matches(
    const svc_rule_state_t *state,
    svc_rule_condition_t condition)
{
    if (state == NULL) {
        return false;
    }

    bool actual = false;
    switch (condition.type) {
    case SVC_RULE_CONDITION_ENGINE_RUNNING:
        actual = state->engine_running;
        break;
    case SVC_RULE_CONDITION_HIGH_BEAM:
        actual = state->high_beam;
        break;
    case SVC_RULE_CONDITION_LEFT_INDICATOR:
        actual = state->left_indicator;
        break;
    case SVC_RULE_CONDITION_AMBIENT_DAY:
        actual = state->ambient_day;
        break;
    case SVC_RULE_CONDITION_AMBIENT_DUSK:
        actual = state->ambient_dusk;
        break;
    case SVC_RULE_CONDITION_AMBIENT_NIGHT:
        actual = state->ambient_night;
        break;
    default:
        return false;
    }

    return actual == condition.expected;
}

bool svc_rule_conditions_match_all(
    const svc_rule_state_t *state,
    const svc_rule_condition_t *conditions,
    size_t condition_count)
{
    if (condition_count == 0U) {
        return state != NULL;
    }
    if (state == NULL || conditions == NULL) {
        return false;
    }

    for (size_t condition_index = 0U; condition_index < condition_count; ++condition_index) {
        if (!svc_rule_condition_matches(state, conditions[condition_index])) {
            return false;
        }
    }
    return true;
}
