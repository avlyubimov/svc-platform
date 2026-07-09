#include <assert.h>
#include <stdbool.h>
#include <stddef.h>

#include "rule_condition.h"

static void test_init_clears_state(void)
{
    svc_rule_state_t state = {
        .engine_running = true,
        .high_beam = true,
        .left_indicator = true,
        .ambient_day = true,
        .ambient_dusk = true,
        .ambient_night = true
    };

    svc_rule_state_init(&state);

    assert(!state.engine_running);
    assert(!state.high_beam);
    assert(!state.left_indicator);
    assert(!state.ambient_day);
    assert(!state.ambient_dusk);
    assert(!state.ambient_night);
}

static void test_events_update_rule_state(void)
{
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);

    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_ENGINE_STARTED, SVC_OUTPUT_OUT1, 1U});
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U});
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_LEFT_INDICATOR_ON, SVC_OUTPUT_OUT1, 1U});

    assert(state.engine_running);
    assert(state.high_beam);
    assert(state.left_indicator);

    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_ENGINE_STOPPED, SVC_OUTPUT_OUT1, 0U});
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_HIGH_BEAM_OFF, SVC_OUTPUT_OUT1, 0U});
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_LEFT_INDICATOR_OFF, SVC_OUTPUT_OUT1, 0U});

    assert(!state.engine_running);
    assert(!state.high_beam);
    assert(!state.left_indicator);
}

static void test_ambient_events_update_exclusive_rule_state(void)
{
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);

    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_AMBIENT_LIGHT_DAY, SVC_OUTPUT_OUT1, 10000U});

    assert(state.ambient_day);
    assert(!state.ambient_dusk);
    assert(!state.ambient_night);

    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_AMBIENT_LIGHT_DUSK, SVC_OUTPUT_OUT1, 3000U});

    assert(!state.ambient_day);
    assert(state.ambient_dusk);
    assert(!state.ambient_night);

    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_AMBIENT_LIGHT_NIGHT, SVC_OUTPUT_OUT1, 1000U});

    assert(!state.ambient_day);
    assert(!state.ambient_dusk);
    assert(state.ambient_night);
}

static void test_non_rule_events_are_ignored(void)
{
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);

    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_OUTPUT_FAULT, SVC_OUTPUT_OUT3, 1U});

    assert(!state.engine_running);
    assert(!state.high_beam);
    assert(!state.left_indicator);
    assert(!state.ambient_day);
    assert(!state.ambient_dusk);
    assert(!state.ambient_night);
}

static void test_single_condition_matches_expected_state(void)
{
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U});

    assert(svc_rule_condition_matches(
        &state,
        (svc_rule_condition_t){SVC_RULE_CONDITION_HIGH_BEAM, true}));
    assert(!svc_rule_condition_matches(
        &state,
        (svc_rule_condition_t){SVC_RULE_CONDITION_HIGH_BEAM, false}));
}

static void test_ambient_condition_matches_expected_state(void)
{
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_AMBIENT_LIGHT_DUSK, SVC_OUTPUT_OUT1, 3000U});

    assert(svc_rule_condition_matches(
        &state,
        (svc_rule_condition_t){SVC_RULE_CONDITION_AMBIENT_DUSK, true}));
    assert(svc_rule_condition_matches(
        &state,
        (svc_rule_condition_t){SVC_RULE_CONDITION_AMBIENT_DAY, false}));
    assert(!svc_rule_condition_matches(
        &state,
        (svc_rule_condition_t){SVC_RULE_CONDITION_AMBIENT_NIGHT, true}));
}

static void test_all_conditions_must_match(void)
{
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_ENGINE_STARTED, SVC_OUTPUT_OUT1, 1U});
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U});

    const svc_rule_condition_t matching_conditions[] = {
        {SVC_RULE_CONDITION_ENGINE_RUNNING, true},
        {SVC_RULE_CONDITION_HIGH_BEAM, true},
        {SVC_RULE_CONDITION_LEFT_INDICATOR, false}
    };
    const svc_rule_condition_t failing_conditions[] = {
        {SVC_RULE_CONDITION_ENGINE_RUNNING, true},
        {SVC_RULE_CONDITION_LEFT_INDICATOR, true}
    };

    assert(svc_rule_conditions_match_all(
        &state,
        matching_conditions,
        sizeof(matching_conditions) / sizeof(matching_conditions[0])));
    assert(!svc_rule_conditions_match_all(
        &state,
        failing_conditions,
        sizeof(failing_conditions) / sizeof(failing_conditions[0])));
}

int main(void)
{
    test_init_clears_state();
    test_events_update_rule_state();
    test_ambient_events_update_exclusive_rule_state();
    test_non_rule_events_are_ignored();
    test_single_condition_matches_expected_state();
    test_ambient_condition_matches_expected_state();
    test_all_conditions_must_match();
    return 0;
}
