#include "rule_engine.h"

#include <stddef.h>

static svc_rule_engine_result_t make_result(
    svc_rule_engine_status_t status,
    svc_role_resolver_result_t role_result,
    svc_output_manager_result_t output_result)
{
    return (svc_rule_engine_result_t){
        .status = status,
        .role_result = role_result,
        .output_result = output_result
    };
}

static svc_rule_engine_status_t status_for_role_result(svc_role_resolver_status_t status)
{
    if (status == SVC_ROLE_RESOLVER_INVALID_CONFIG) {
        return SVC_RULE_ENGINE_DENY_INVALID_CONFIG;
    }
    if (status == SVC_ROLE_RESOLVER_NOT_FOUND || status == SVC_ROLE_RESOLVER_INVALID_ROLE) {
        return SVC_RULE_ENGINE_DENY_ROLE_NOT_FOUND;
    }
    if (status == SVC_ROLE_RESOLVER_AMBIGUOUS) {
        return SVC_RULE_ENGINE_DENY_ROLE_AMBIGUOUS;
    }
    return SVC_RULE_ENGINE_DENY_INVALID_ARGUMENT;
}

svc_rule_engine_result_t svc_rule_engine_apply_action(
    const svc_device_config_t *config,
    svc_output_manager_t *output_manager,
    svc_rule_action_t action,
    uint32_t measured_total_current_ma,
    bool telemetry_valid)
{
    const svc_role_resolver_result_t role_result = svc_role_resolver_find_output(
        config,
        action.role);
    if (role_result.status != SVC_ROLE_RESOLVER_OK) {
        return make_result(
            status_for_role_result(role_result.status),
            role_result,
            (svc_output_manager_result_t){0});
    }
    if (output_manager == NULL) {
        return make_result(
            SVC_RULE_ENGINE_DENY_INVALID_ARGUMENT,
            role_result,
            (svc_output_manager_result_t){0});
    }

    svc_output_manager_result_t output_result = {0};
    if (action.type == SVC_RULE_ACTION_ENABLE_ROLE) {
        const uint8_t duty_percent = action.pwm_duty_percent == 0U ? 100U : action.pwm_duty_percent;
        output_result = svc_output_manager_request_pwm(
            output_manager,
            role_result.output_id,
            duty_percent,
            measured_total_current_ma,
            telemetry_valid);
    } else if (action.type == SVC_RULE_ACTION_DISABLE_ROLE) {
        output_result = svc_output_manager_request_pwm(
            output_manager,
            role_result.output_id,
            0U,
            measured_total_current_ma,
            telemetry_valid);
    } else {
        return make_result(
            SVC_RULE_ENGINE_DENY_INVALID_ARGUMENT,
            role_result,
            output_result);
    }

    if (output_result.status != SVC_OUTPUT_MANAGER_OK) {
        return make_result(SVC_RULE_ENGINE_DENY_OUTPUT_MANAGER, role_result, output_result);
    }
    return make_result(SVC_RULE_ENGINE_OK, role_result, output_result);
}

svc_rule_engine_result_t svc_rule_engine_evaluate_rule(
    const svc_device_config_t *config,
    svc_output_manager_t *output_manager,
    const svc_rule_state_t *state,
    const svc_rule_t *rule,
    uint32_t measured_total_current_ma,
    bool telemetry_valid)
{
    if (rule == NULL || state == NULL) {
        return make_result(
            SVC_RULE_ENGINE_DENY_INVALID_ARGUMENT,
            (svc_role_resolver_result_t){0},
            (svc_output_manager_result_t){0});
    }
    if (!svc_rule_conditions_match_all(state, rule->conditions, rule->condition_count)) {
        return make_result(
            SVC_RULE_ENGINE_SKIPPED_CONDITIONS,
            (svc_role_resolver_result_t){0},
            (svc_output_manager_result_t){0});
    }

    return svc_rule_engine_apply_action(
        config,
        output_manager,
        rule->action,
        measured_total_current_ma,
        telemetry_valid);
}
