#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "output_manager.h"
#include "rule_condition.h"
#include "role_resolver.h"
#include "svc_config.h"

typedef enum {
    SVC_RULE_ACTION_ENABLE_ROLE = 0,
    SVC_RULE_ACTION_DISABLE_ROLE
} svc_rule_action_type_t;

typedef enum {
    SVC_RULE_ENGINE_OK = 0,
    SVC_RULE_ENGINE_SKIPPED_CONDITIONS,
    SVC_RULE_ENGINE_DENY_INVALID_ARGUMENT,
    SVC_RULE_ENGINE_DENY_INVALID_CONFIG,
    SVC_RULE_ENGINE_DENY_ROLE_NOT_FOUND,
    SVC_RULE_ENGINE_DENY_ROLE_AMBIGUOUS,
    SVC_RULE_ENGINE_DENY_OUTPUT_MANAGER
} svc_rule_engine_status_t;

typedef struct {
    svc_rule_action_type_t type;
    output_role_t role;
} svc_rule_action_t;

typedef struct {
    const svc_rule_condition_t *conditions;
    size_t condition_count;
    svc_rule_action_t action;
} svc_rule_t;

typedef struct {
    svc_rule_engine_status_t status;
    svc_role_resolver_result_t role_result;
    svc_output_manager_result_t output_result;
} svc_rule_engine_result_t;

svc_rule_engine_result_t svc_rule_engine_apply_action(
    const svc_device_config_t *config,
    svc_output_manager_t *output_manager,
    svc_rule_action_t action,
    uint32_t measured_total_current_ma,
    bool telemetry_valid);

svc_rule_engine_result_t svc_rule_engine_evaluate_rule(
    const svc_device_config_t *config,
    svc_output_manager_t *output_manager,
    const svc_rule_state_t *state,
    const svc_rule_t *rule,
    uint32_t measured_total_current_ma,
    bool telemetry_valid);
