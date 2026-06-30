#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#include "output_manager.h"
#include "rule_engine.h"
#include "svc_config.h"

static uint16_t mask_for(svc_output_id_t output_id)
{
    return (uint16_t)(1U << (uint8_t)output_id);
}

static svc_output_manager_t initialized_output_manager(const svc_device_config_t *config)
{
    svc_output_manager_t manager = {0};
    assert(svc_output_manager_init(&manager, config));
    return manager;
}

static void test_enable_role_uses_config_mapping(void)
{
    svc_output_manager_t manager = initialized_output_manager(&svc_default_config);

    const svc_rule_engine_result_t result = svc_rule_engine_apply_action(
        &svc_default_config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_LEFT, 100U},
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_OK);
    assert(result.role_result.output_id == SVC_OUTPUT_OUT3);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT3)) != 0U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 100U);
}

static void test_disable_role_uses_config_mapping(void)
{
    svc_output_manager_t manager = initialized_output_manager(&svc_default_config);
    assert(svc_rule_engine_apply_action(
        &svc_default_config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_LEFT, 100U},
        1000U,
        true).status == SVC_RULE_ENGINE_OK);

    const svc_rule_engine_result_t result = svc_rule_engine_apply_action(
        &svc_default_config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_DISABLE_ROLE, OUT_ROLE_FOG_LEFT, 0U},
        0U,
        true);

    assert(result.status == SVC_RULE_ENGINE_OK);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT3)) == 0U);
}

static void test_ambiguous_role_is_denied(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[0].role = OUT_ROLE_FOG_LEFT;
    svc_output_manager_t manager = initialized_output_manager(&config);

    const svc_rule_engine_result_t result = svc_rule_engine_apply_action(
        &config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_LEFT, 100U},
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_DENY_ROLE_AMBIGUOUS);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

static void test_missing_role_is_denied(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[7].role = OUT_ROLE_SPARE;
    svc_output_manager_t manager = initialized_output_manager(&config);

    const svc_rule_engine_result_t result = svc_rule_engine_apply_action(
        &config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_DVR, 100U},
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_DENY_ROLE_NOT_FOUND);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

static void test_output_manager_denial_is_reported(void)
{
    svc_output_manager_t manager = initialized_output_manager(&svc_default_config);

    const svc_rule_engine_result_t result = svc_rule_engine_apply_action(
        &svc_default_config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_CIGARETTE_SOCKET, 100U},
        30000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_DENY_OUTPUT_MANAGER);
    assert(result.output_result.status == SVC_OUTPUT_MANAGER_DENY_BUDGET);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

static void test_pwm_role_action_preserves_duty_cycle(void)
{
    svc_output_manager_t manager = initialized_output_manager(&svc_default_config);

    const svc_rule_engine_result_t result = svc_rule_engine_apply_action(
        &svc_default_config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_LEFT, 40U},
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_OK);
    assert(result.output_result.pwm_duty_percent == 40U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 40U);
}

static void test_pwm_role_action_denies_non_pwm_output(void)
{
    svc_output_manager_t manager = initialized_output_manager(&svc_default_config);

    const svc_rule_engine_result_t result = svc_rule_engine_apply_action(
        &svc_default_config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_CIGARETTE_SOCKET, 40U},
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_DENY_OUTPUT_MANAGER);
    assert(result.output_result.status == SVC_OUTPUT_MANAGER_DENY_PWM_NOT_ALLOWED);
}

static void test_matching_rule_applies_role_action(void)
{
    svc_output_manager_t manager = initialized_output_manager(&svc_default_config);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_ENGINE_STARTED, SVC_OUTPUT_OUT1, 1U});
    svc_rule_state_apply_event(&state, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 1U});

    const svc_rule_condition_t conditions[] = {
        {SVC_RULE_CONDITION_ENGINE_RUNNING, true},
        {SVC_RULE_CONDITION_HIGH_BEAM, true}
    };
    const svc_rule_t rule = {
        .conditions = conditions,
        .condition_count = sizeof(conditions) / sizeof(conditions[0]),
        .action = {SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_LEFT, 100U}
    };

    const svc_rule_engine_result_t result = svc_rule_engine_evaluate_rule(
        &svc_default_config,
        &manager,
        &state,
        &rule,
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_OK);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT3)) != 0U);
}

static void test_unmatched_rule_is_skipped_without_output_change(void)
{
    svc_output_manager_t manager = initialized_output_manager(&svc_default_config);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);

    const svc_rule_condition_t conditions[] = {
        {SVC_RULE_CONDITION_ENGINE_RUNNING, true},
        {SVC_RULE_CONDITION_HIGH_BEAM, true}
    };
    const svc_rule_t rule = {
        .conditions = conditions,
        .condition_count = sizeof(conditions) / sizeof(conditions[0]),
        .action = {SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_LEFT, 100U}
    };

    const svc_rule_engine_result_t result = svc_rule_engine_evaluate_rule(
        &svc_default_config,
        &manager,
        &state,
        &rule,
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_SKIPPED_CONDITIONS);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

static void test_null_rule_is_denied(void)
{
    svc_output_manager_t manager = initialized_output_manager(&svc_default_config);
    svc_rule_state_t state = {0};
    svc_rule_state_init(&state);

    const svc_rule_engine_result_t result = svc_rule_engine_evaluate_rule(
        &svc_default_config,
        &manager,
        &state,
        NULL,
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_DENY_INVALID_ARGUMENT);
}

int main(void)
{
    test_enable_role_uses_config_mapping();
    test_disable_role_uses_config_mapping();
    test_ambiguous_role_is_denied();
    test_missing_role_is_denied();
    test_output_manager_denial_is_reported();
    test_pwm_role_action_preserves_duty_cycle();
    test_pwm_role_action_denies_non_pwm_output();
    test_matching_rule_applies_role_action();
    test_unmatched_rule_is_skipped_without_output_change();
    test_null_rule_is_denied();
    return 0;
}
