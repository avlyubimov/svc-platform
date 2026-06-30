#pragma once

#include "rule_engine.h"

typedef enum {
    SVC_RULE_TEXT_OK = 0,
    SVC_RULE_TEXT_INVALID_ARGUMENT,
    SVC_RULE_TEXT_UNKNOWN_CONDITION,
    SVC_RULE_TEXT_UNKNOWN_ROLE,
    SVC_RULE_TEXT_INVALID_ACTION_VALUE,
    SVC_RULE_TEXT_UNSUPPORTED_ACTION
} svc_rule_text_status_t;

svc_rule_text_status_t svc_rule_text_parse_condition(
    const char *text,
    svc_rule_condition_t *condition);

svc_rule_text_status_t svc_rule_text_parse_action(
    const char *text,
    svc_rule_action_t *action);
