#include <assert.h>
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
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_LEFT},
        1000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_OK);
    assert(result.role_result.output_id == SVC_OUTPUT_OUT3);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT3)) != 0U);
}

static void test_disable_role_uses_config_mapping(void)
{
    svc_output_manager_t manager = initialized_output_manager(&svc_default_config);
    assert(svc_rule_engine_apply_action(
        &svc_default_config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_LEFT},
        1000U,
        true).status == SVC_RULE_ENGINE_OK);

    const svc_rule_engine_result_t result = svc_rule_engine_apply_action(
        &svc_default_config,
        &manager,
        (svc_rule_action_t){SVC_RULE_ACTION_DISABLE_ROLE, OUT_ROLE_FOG_LEFT},
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
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_FOG_LEFT},
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
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_DVR},
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
        (svc_rule_action_t){SVC_RULE_ACTION_ENABLE_ROLE, OUT_ROLE_CIGARETTE_SOCKET},
        30000U,
        true);

    assert(result.status == SVC_RULE_ENGINE_DENY_OUTPUT_MANAGER);
    assert(result.output_result.status == SVC_OUTPUT_MANAGER_DENY_BUDGET);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

int main(void)
{
    test_enable_role_uses_config_mapping();
    test_disable_role_uses_config_mapping();
    test_ambiguous_role_is_denied();
    test_missing_role_is_denied();
    test_output_manager_denial_is_reported();
    return 0;
}
