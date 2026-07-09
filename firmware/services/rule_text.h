#pragma once

#include <stddef.h>

#include "rule_engine.h"

typedef enum {
    SVC_RULE_TEXT_OK = 0,
    SVC_RULE_TEXT_INVALID_ARGUMENT,
    SVC_RULE_TEXT_UNKNOWN_CONDITION,
    SVC_RULE_TEXT_UNKNOWN_ROLE,
    SVC_RULE_TEXT_INVALID_ACTION_VALUE,
    SVC_RULE_TEXT_UNSUPPORTED_ACTION,
    SVC_RULE_TEXT_TOO_MANY_CONDITIONS,
    SVC_RULE_TEXT_TOO_MANY_ACTIONS
} svc_rule_text_status_t;

svc_rule_text_status_t svc_rule_text_parse_condition(
    const char *text,
    svc_rule_condition_t *condition);

svc_rule_text_status_t svc_rule_text_parse_action(
    const char *text,
    svc_rule_action_t *action);

svc_rule_text_status_t svc_rule_text_compile_rule(
    const char *const *condition_texts,
    size_t condition_count,
    const char *action_text,
    svc_rule_condition_t *condition_buffer,
    size_t condition_capacity,
    svc_rule_t *rule);

svc_rule_text_status_t svc_rule_text_compile_rule_set(
    const char *const *condition_texts,
    size_t condition_count,
    const char *const *action_texts,
    size_t action_count,
    svc_rule_condition_t *condition_buffer,
    size_t condition_capacity,
    svc_rule_t *rule_buffer,
    size_t rule_capacity,
    size_t *compiled_rule_count);
