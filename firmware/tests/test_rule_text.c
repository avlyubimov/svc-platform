#include <assert.h>

#include "rule_text.h"

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

int main(void)
{
    test_parse_true_condition();
    test_parse_false_condition();
    test_reject_unknown_condition();
    test_parse_positive_pwm_as_enable_action();
    test_parse_zero_pwm_as_disable_action();
    test_reject_unknown_action_role();
    test_reject_invalid_pwm_value();
    return 0;
}
