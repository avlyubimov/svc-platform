#include <assert.h>

#include "output_manager.h"
#include "rule_text.h"
#include "svc_config.h"

static void test_parse_true_condition(void)
{
    svc_rule_condition_t condition = {0};

    const svc_rule_text_status_t status = svc_rule_text_parse_condition(
        "engine_running == true",
        &condition);

    assert(status == SVC_RULE_TEXT_OK);
    assert(condition.type == SVC_RULE_CONDITION_ENGINE_RUNNING);
    assert(condition.expected);
}

static void test_parse_false_condition(void)
{
    svc_rule_condition_t condition = {0};

    const svc_rule_text_status_t status = svc_rule_text_parse_condition(
        "left_indicator == false",
        &condition);

    assert(status == SVC_RULE_TEXT_OK);
    assert(condition.type == SVC_RULE_CONDITION_LEFT_INDICATOR);
    assert(!condition.expected);
}

static void test_reject_unknown_condition(void)
{
    svc_rule_condition_t condition = {0};

    const svc_rule_text_status_t status = svc_rule_text_parse_condition(
        "wheel_speed == true",
        &condition);

    assert(status == SVC_RULE_TEXT_UNKNOWN_CONDITION);
}

static void test_parse_positive_pwm_as_enable_action(void)
{
    svc_rule_action_t action = {0};

    const svc_rule_text_status_t status = svc_rule_text_parse_action(
        "FOG_LEFT.pwm = 100",
        &action);

    assert(status == SVC_RULE_TEXT_OK);
    assert(action.type == SVC_RULE_ACTION_ENABLE_ROLE);
    assert(action.role == OUT_ROLE_FOG_LEFT);
    assert(action.pwm_duty_percent == 100U);
}

static void test_parse_zero_pwm_as_disable_action(void)
{
    svc_rule_action_t action = {0};

    const svc_rule_text_status_t status = svc_rule_text_parse_action(
        "FOG_LEFT.pwm = 0",
        &action);

    assert(status == SVC_RULE_TEXT_OK);
    assert(action.type == SVC_RULE_ACTION_DISABLE_ROLE);
    assert(action.role == OUT_ROLE_FOG_LEFT);
    assert(action.pwm_duty_percent == 0U);
}

static void test_reject_unknown_action_role(void)
{
    svc_rule_action_t action = {0};

    const svc_rule_text_status_t status = svc_rule_text_parse_action(
        "UNKNOWN.pwm = 100",
        &action);

    assert(status == SVC_RULE_TEXT_UNKNOWN_ROLE);
}

static void test_reject_invalid_pwm_value(void)
{
    svc_rule_action_t action = {0};

    const svc_rule_text_status_t status = svc_rule_text_parse_action(
        "FOG_LEFT.pwm = 101",
        &action);

    assert(status == SVC_RULE_TEXT_INVALID_ACTION_VALUE);
}

static void test_compile_rule_from_text_and_execute(void)
{
    const char *conditions[] = {
        "engine_running == true",
        "high_beam == true"
    };
    svc_rule_condition_t condition_buffer[2] = {0};
    svc_rule_t rule = {0};

    const svc_rule_text_status_t compile_status = svc_rule_text_compile_rule(
        conditions,
        2U,
        "FOG_LEFT.pwm = 40",
        condition_buffer,
        2U,
        &rule);

    assert(compile_status == SVC_RULE_TEXT_OK);
    assert(rule.condition_count == 2U);
    assert(rule.action.type == SVC_RULE_ACTION_ENABLE_ROLE);
    assert(rule.action.role == OUT_ROLE_FOG_LEFT);
    assert(rule.action.pwm_duty_percent == 40U);

    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_ENGINE_STARTED, SVC_OUTPUT_OUT1, 1U});
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U});

    svc_output_manager_t manager = {0};
    assert(svc_output_manager_init(&manager, &svc_default_config));

    const svc_rule_engine_result_t result = svc_rule_engine_evaluate_rule(
        &svc_default_config,
        &manager,
        &state,
        &rule,
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_OK);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 40U);
}

static void test_compile_rule_rejects_condition_overflow(void)
{
    const char *conditions[] = {
        "engine_running == true",
        "high_beam == true"
    };
    svc_rule_condition_t condition_buffer[1] = {0};
    svc_rule_t rule = {0};

    const svc_rule_text_status_t compile_status = svc_rule_text_compile_rule(
        conditions,
        2U,
        "FOG_LEFT.pwm = 40",
        condition_buffer,
        1U,
        &rule);

    assert(compile_status == SVC_RULE_TEXT_TOO_MANY_CONDITIONS);
}

int main(void)
{
    test_parse_true_condition();
    test_parse_false_condition();
    test_reject_unknown_condition();
    test_parse_positive_pwm_as_enable_action();
    test_parse_zero_pwm_as_disable_action();
    test_reject_unknown_action_role();
    test_reject_invalid_pwm_value();
    test_compile_rule_from_text_and_execute();
    test_compile_rule_rejects_condition_overflow();
    return 0;
}
