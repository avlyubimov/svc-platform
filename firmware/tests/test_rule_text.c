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

static void test_parse_ambient_condition(void)
{
    svc_rule_condition_t condition = {0};

    const svc_rule_text_status_t status = svc_rule_text_parse_condition(
        "ambient_night == true",
        &condition);

    assert(status == SVC_RULE_TEXT_OK);
    assert(condition.type == SVC_RULE_CONDITION_AMBIENT_NIGHT);
    assert(condition.expected);
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

static void test_reject_noncanonical_pwm_values(void)
{
    svc_rule_action_t action = {0};

    assert(svc_rule_text_parse_action(
        "FOG_LEFT.pwm = 001",
        &action) == SVC_RULE_TEXT_INVALID_ACTION_VALUE);
    assert(svc_rule_text_parse_action(
        "FOG_LEFT.pwm = +1",
        &action) == SVC_RULE_TEXT_INVALID_ACTION_VALUE);
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

static void test_compile_rule_rejects_invalid_condition_without_buffer_write(void)
{
    const char *conditions[] = {
        "engine_running == true",
        "wheel_speed == true"
    };
    svc_rule_condition_t condition_buffer[2] = {
        {SVC_RULE_CONDITION_AMBIENT_DAY, true},
        {SVC_RULE_CONDITION_AMBIENT_NIGHT, false}
    };
    svc_rule_t rule = {0};

    const svc_rule_text_status_t compile_status = svc_rule_text_compile_rule(
        conditions,
        2U,
        "FOG_LEFT.pwm = 40",
        condition_buffer,
        2U,
        &rule);

    assert(compile_status == SVC_RULE_TEXT_UNKNOWN_CONDITION);
    assert(condition_buffer[0].type == SVC_RULE_CONDITION_AMBIENT_DAY);
    assert(condition_buffer[0].expected);
    assert(condition_buffer[1].type == SVC_RULE_CONDITION_AMBIENT_NIGHT);
    assert(!condition_buffer[1].expected);
    assert(rule.condition_count == 0U);
}

static void test_compile_rule_set_from_multiple_actions_and_execute(void)
{
    const char *conditions[] = {
        "engine_running == true",
        "high_beam == true"
    };
    const char *actions[] = {
        "FOG_LEFT.pwm = 40",
        "FOG_RIGHT.pwm = 70"
    };
    svc_rule_condition_t condition_buffer[2] = {0};
    svc_rule_t rules[2] = {0};
    size_t compiled_rule_count = 0U;

    const svc_rule_text_status_t compile_status = svc_rule_text_compile_rule_set(
        conditions,
        2U,
        actions,
        2U,
        condition_buffer,
        2U,
        rules,
        2U,
        &compiled_rule_count);

    assert(compile_status == SVC_RULE_TEXT_OK);
    assert(compiled_rule_count == 2U);
    assert(rules[0].conditions == condition_buffer);
    assert(rules[1].conditions == condition_buffer);
    assert(rules[0].condition_count == 2U);
    assert(rules[1].action.role == OUT_ROLE_FOG_RIGHT);
    assert(rules[1].action.pwm_duty_percent == 70U);

    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_ENGINE_STARTED, SVC_OUTPUT_OUT1, 1U});
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U});

    svc_output_manager_t manager = {0};
    assert(svc_output_manager_init(&manager, &svc_default_config));

    const svc_rule_engine_run_result_t result = svc_rule_engine_evaluate_rules(
        &svc_default_config,
        &manager,
        &state,
        rules,
        compiled_rule_count,
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_OK);
    assert(result.applied_actions == 2U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 40U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT4) == 70U);
}

static void test_compile_rule_set_rejects_action_overflow(void)
{
    const char *conditions[] = {
        "engine_running == true"
    };
    const char *actions[] = {
        "FOG_LEFT.pwm = 40",
        "FOG_RIGHT.pwm = 70"
    };
    svc_rule_condition_t condition_buffer[1] = {0};
    svc_rule_t rules[1] = {0};
    size_t compiled_rule_count = 99U;

    const svc_rule_text_status_t compile_status = svc_rule_text_compile_rule_set(
        conditions,
        1U,
        actions,
        2U,
        condition_buffer,
        1U,
        rules,
        1U,
        &compiled_rule_count);

    assert(compile_status == SVC_RULE_TEXT_TOO_MANY_ACTIONS);
    assert(compiled_rule_count == 0U);
}

static void test_compile_rule_set_rejects_invalid_action(void)
{
    const char *conditions[] = {
        "engine_running == true"
    };
    const char *actions[] = {
        "FOG_LEFT.pwm = 40",
        "FOG_RIGHT.pwm = 101"
    };
    svc_rule_condition_t condition_buffer[1] = {0};
    svc_rule_t rules[2] = {0};
    rules[0].condition_count = 99U;
    rules[0].action.role = OUT_ROLE_CHIGEE;
    rules[1].condition_count = 88U;
    rules[1].action.role = OUT_ROLE_DVR;
    size_t compiled_rule_count = 99U;

    const svc_rule_text_status_t compile_status = svc_rule_text_compile_rule_set(
        conditions,
        1U,
        actions,
        2U,
        condition_buffer,
        1U,
        rules,
        2U,
        &compiled_rule_count);

    assert(compile_status == SVC_RULE_TEXT_INVALID_ACTION_VALUE);
    assert(compiled_rule_count == 0U);
    assert(rules[0].condition_count == 99U);
    assert(rules[0].action.role == OUT_ROLE_CHIGEE);
    assert(rules[1].condition_count == 88U);
    assert(rules[1].action.role == OUT_ROLE_DVR);
    assert(condition_buffer[0].type == SVC_RULE_CONDITION_ENGINE_RUNNING);
}

static void test_compile_rule_set_rejects_invalid_action_without_condition_write(void)
{
    const char *conditions[] = {
        "engine_running == true"
    };
    const char *actions[] = {
        "FOG_LEFT.pwm = 40",
        "FOG_RIGHT.pwm = 101"
    };
    svc_rule_condition_t condition_buffer[1] = {
        {SVC_RULE_CONDITION_AMBIENT_DUSK, true}
    };
    svc_rule_t rules[2] = {0};
    size_t compiled_rule_count = 99U;

    const svc_rule_text_status_t compile_status = svc_rule_text_compile_rule_set(
        conditions,
        1U,
        actions,
        2U,
        condition_buffer,
        1U,
        rules,
        2U,
        &compiled_rule_count);

    assert(compile_status == SVC_RULE_TEXT_INVALID_ACTION_VALUE);
    assert(compiled_rule_count == 0U);
    assert(condition_buffer[0].type == SVC_RULE_CONDITION_AMBIENT_DUSK);
    assert(condition_buffer[0].expected);
}

int main(void)
{
    test_parse_true_condition();
    test_parse_false_condition();
    test_parse_ambient_condition();
    test_reject_unknown_condition();
    test_parse_positive_pwm_as_enable_action();
    test_parse_zero_pwm_as_disable_action();
    test_reject_unknown_action_role();
    test_reject_invalid_pwm_value();
    test_reject_noncanonical_pwm_values();
    test_compile_rule_from_text_and_execute();
    test_compile_rule_rejects_condition_overflow();
    test_compile_rule_rejects_invalid_condition_without_buffer_write();
    test_compile_rule_set_from_multiple_actions_and_execute();
    test_compile_rule_set_rejects_action_overflow();
    test_compile_rule_set_rejects_invalid_action();
    test_compile_rule_set_rejects_invalid_action_without_condition_write();
    return 0;
}
