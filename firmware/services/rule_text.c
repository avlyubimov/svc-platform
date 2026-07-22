#include "rule_text.h"

#include <stdbool.h>
#include <stddef.h>
#include <string.h>

typedef struct {
    const char *name;
    svc_rule_condition_type_t type;
} condition_name_t;

typedef struct {
    const char *name;
    output_role_t role;
} role_name_t;

static const condition_name_t CONDITION_NAMES[] = {
    {"engine_running", SVC_RULE_CONDITION_ENGINE_RUNNING},
    {"high_beam", SVC_RULE_CONDITION_HIGH_BEAM},
    {"left_indicator", SVC_RULE_CONDITION_LEFT_INDICATOR},
    {"ambient_day", SVC_RULE_CONDITION_AMBIENT_DAY},
    {"ambient_dusk", SVC_RULE_CONDITION_AMBIENT_DUSK},
    {"ambient_night", SVC_RULE_CONDITION_AMBIENT_NIGHT}
};

static const role_name_t ROLE_NAMES[] = {
    {"USB", OUT_ROLE_USB},
    {"CIGARETTE_SOCKET", OUT_ROLE_CIGARETTE_SOCKET},
    {"FOG_LEFT", OUT_ROLE_FOG_LEFT},
    {"FOG_RIGHT", OUT_ROLE_FOG_RIGHT},
    {"CHIGEE", OUT_ROLE_CHIGEE},
    {"HEATED_SEAT_RIDER", OUT_ROLE_HEATED_SEAT_RIDER},
    {"HEATED_SEAT_PASSENGER", OUT_ROLE_HEATED_SEAT_PASSENGER},
    {"DVR", OUT_ROLE_DVR},
    {"AUX_BRAKE", OUT_ROLE_AUX_BRAKE},
    {"SPARE", OUT_ROLE_SPARE},
    {"CIGARETTE_COMPRESSOR", OUT_ROLE_CIGARETTE_COMPRESSOR},
    {"HIGH_CURRENT_RESERVE", OUT_ROLE_HIGH_CURRENT_RESERVE},
    {"FOG_PRIMARY_LEFT", OUT_ROLE_FOG_PRIMARY_LEFT},
    {"FOG_PRIMARY_RIGHT", OUT_ROLE_FOG_PRIMARY_RIGHT},
    {"LOW_CURRENT_RESERVE_1", OUT_ROLE_LOW_CURRENT_RESERVE_1},
    {"FOG_SECONDARY_LEFT", OUT_ROLE_FOG_SECONDARY_LEFT},
    {"FOG_SECONDARY_RIGHT", OUT_ROLE_FOG_SECONDARY_RIGHT},
    {"LOW_CURRENT_RESERVE_2", OUT_ROLE_LOW_CURRENT_RESERVE_2},
    {"LOW_CURRENT_RESERVE_3", OUT_ROLE_LOW_CURRENT_RESERVE_3},
    {"MEDIUM_CURRENT_RESERVE", OUT_ROLE_MEDIUM_CURRENT_RESERVE}
};

static bool parse_bool_literal(const char *text, bool *value)
{
    if (strcmp(text, "true") == 0) {
        *value = true;
        return true;
    }
    if (strcmp(text, "false") == 0) {
        *value = false;
        return true;
    }
    return false;
}

static bool parse_role_name(const char *name, size_t name_length, output_role_t *role)
{
    for (size_t role_index = 0U; role_index < sizeof(ROLE_NAMES) / sizeof(ROLE_NAMES[0]); ++role_index) {
        if (strlen(ROLE_NAMES[role_index].name) != name_length) {
            continue;
        }
        if (strncmp(ROLE_NAMES[role_index].name, name, name_length) != 0) {
            continue;
        }
        *role = ROLE_NAMES[role_index].role;
        return true;
    }
    return false;
}

static bool parse_pwm_percent(const char *text, uint8_t *pwm_duty_percent)
{
    if (text == NULL || text[0] == '\0') {
        return false;
    }
    if (text[0] == '0') {
        if (text[1] != '\0') {
            return false;
        }
        *pwm_duty_percent = 0U;
        return true;
    }

    unsigned int value = 0U;
    for (size_t index = 0U; text[index] != '\0'; ++index) {
        if (text[index] < '0' || text[index] > '9') {
            return false;
        }
        value = value * 10U + (unsigned int)(text[index] - '0');
        if (value > 100U) {
            return false;
        }
    }

    *pwm_duty_percent = (uint8_t)value;
    return true;
}

svc_rule_text_status_t svc_rule_text_parse_condition(
    const char *text,
    svc_rule_condition_t *condition)
{
    if (text == NULL || condition == NULL) {
        return SVC_RULE_TEXT_INVALID_ARGUMENT;
    }

    const char *operator = " == ";
    const char *operator_position = strstr(text, operator);
    if (operator_position == NULL) {
        return SVC_RULE_TEXT_UNKNOWN_CONDITION;
    }

    const size_t name_length = (size_t)(operator_position - text);
    const char *bool_text = operator_position + strlen(operator);
    bool expected = false;
    if (!parse_bool_literal(bool_text, &expected)) {
        return SVC_RULE_TEXT_UNKNOWN_CONDITION;
    }

    for (size_t condition_index = 0U; condition_index < sizeof(CONDITION_NAMES) / sizeof(CONDITION_NAMES[0]); ++condition_index) {
        if (strlen(CONDITION_NAMES[condition_index].name) != name_length) {
            continue;
        }
        if (strncmp(CONDITION_NAMES[condition_index].name, text, name_length) != 0) {
            continue;
        }
        condition->type = CONDITION_NAMES[condition_index].type;
        condition->expected = expected;
        return SVC_RULE_TEXT_OK;
    }

    return SVC_RULE_TEXT_UNKNOWN_CONDITION;
}

svc_rule_text_status_t svc_rule_text_parse_action(
    const char *text,
    svc_rule_action_t *action)
{
    if (text == NULL || action == NULL) {
        return SVC_RULE_TEXT_INVALID_ARGUMENT;
    }

    const char *property = ".pwm = ";
    const char *property_position = strstr(text, property);
    if (property_position == NULL) {
        return SVC_RULE_TEXT_UNSUPPORTED_ACTION;
    }

    output_role_t role = OUT_ROLE_NONE;
    const size_t role_name_length = (size_t)(property_position - text);
    if (!parse_role_name(text, role_name_length, &role)) {
        return SVC_RULE_TEXT_UNKNOWN_ROLE;
    }

    const char *value_text = property_position + strlen(property);
    uint8_t pwm_value = 0U;
    if (!parse_pwm_percent(value_text, &pwm_value)) {
        return SVC_RULE_TEXT_INVALID_ACTION_VALUE;
    }

    action->role = role;
    action->pwm_duty_percent = pwm_value;
    action->type = pwm_value == 0U ? SVC_RULE_ACTION_DISABLE_ROLE : SVC_RULE_ACTION_ENABLE_ROLE;
    return SVC_RULE_TEXT_OK;
}

static svc_rule_text_status_t validate_condition_texts(
    const char *const *condition_texts,
    size_t condition_count)
{
    for (size_t condition_index = 0U; condition_index < condition_count; ++condition_index) {
        svc_rule_condition_t condition = {0};
        const svc_rule_text_status_t status = svc_rule_text_parse_condition(
            condition_texts[condition_index],
            &condition);
        if (status != SVC_RULE_TEXT_OK) {
            return status;
        }
    }
    return SVC_RULE_TEXT_OK;
}

static svc_rule_text_status_t write_condition_texts(
    const char *const *condition_texts,
    size_t condition_count,
    svc_rule_condition_t *condition_buffer)
{
    for (size_t condition_index = 0U; condition_index < condition_count; ++condition_index) {
        const svc_rule_text_status_t status = svc_rule_text_parse_condition(
            condition_texts[condition_index],
            &condition_buffer[condition_index]);
        if (status != SVC_RULE_TEXT_OK) {
            return status;
        }
    }
    return SVC_RULE_TEXT_OK;
}

static svc_rule_text_status_t validate_action_texts(
    const char *const *action_texts,
    size_t action_count)
{
    for (size_t action_index = 0U; action_index < action_count; ++action_index) {
        svc_rule_action_t action = {0};
        const svc_rule_text_status_t status = svc_rule_text_parse_action(
            action_texts[action_index],
            &action);
        if (status != SVC_RULE_TEXT_OK) {
            return status;
        }
    }
    return SVC_RULE_TEXT_OK;
}

svc_rule_text_status_t svc_rule_text_compile_rule(
    const char *const *condition_texts,
    size_t condition_count,
    const char *action_text,
    svc_rule_condition_t *condition_buffer,
    size_t condition_capacity,
    svc_rule_t *rule)
{
    if (rule == NULL || action_text == NULL) {
        return SVC_RULE_TEXT_INVALID_ARGUMENT;
    }
    if (condition_count > condition_capacity) {
        return SVC_RULE_TEXT_TOO_MANY_CONDITIONS;
    }
    if (condition_count > 0U && (condition_texts == NULL || condition_buffer == NULL)) {
        return SVC_RULE_TEXT_INVALID_ARGUMENT;
    }

    svc_rule_text_status_t status = validate_condition_texts(
        condition_texts,
        condition_count);
    if (status != SVC_RULE_TEXT_OK) {
        return status;
    }

    svc_rule_action_t action = {0};
    const svc_rule_text_status_t action_status = svc_rule_text_parse_action(action_text, &action);
    if (action_status != SVC_RULE_TEXT_OK) {
        return action_status;
    }

    status = write_condition_texts(
        condition_texts,
        condition_count,
        condition_buffer);
    if (status != SVC_RULE_TEXT_OK) {
        return status;
    }

    rule->conditions = condition_buffer;
    rule->condition_count = condition_count;
    rule->action = action;
    return SVC_RULE_TEXT_OK;
}

svc_rule_text_status_t svc_rule_text_compile_rule_set(
    const char *const *condition_texts,
    size_t condition_count,
    const char *const *action_texts,
    size_t action_count,
    svc_rule_condition_t *condition_buffer,
    size_t condition_capacity,
    svc_rule_t *rule_buffer,
    size_t rule_capacity,
    size_t *compiled_rule_count)
{
    if (compiled_rule_count != NULL) {
        *compiled_rule_count = 0U;
    }
    if (action_count == 0U || action_texts == NULL || rule_buffer == NULL) {
        return SVC_RULE_TEXT_INVALID_ARGUMENT;
    }
    if (condition_count > condition_capacity) {
        return SVC_RULE_TEXT_TOO_MANY_CONDITIONS;
    }
    if (action_count > rule_capacity) {
        return SVC_RULE_TEXT_TOO_MANY_ACTIONS;
    }
    if (condition_count > 0U && (condition_texts == NULL || condition_buffer == NULL)) {
        return SVC_RULE_TEXT_INVALID_ARGUMENT;
    }

    svc_rule_text_status_t status = validate_condition_texts(
        condition_texts,
        condition_count);
    if (status != SVC_RULE_TEXT_OK) {
        return status;
    }

    status = validate_action_texts(action_texts, action_count);
    if (status != SVC_RULE_TEXT_OK) {
        return status;
    }

    status = write_condition_texts(
        condition_texts,
        condition_count,
        condition_buffer);
    if (status != SVC_RULE_TEXT_OK) {
        return status;
    }

    for (size_t action_index = 0U; action_index < action_count; ++action_index) {
        svc_rule_action_t action = {0};
        const svc_rule_text_status_t status = svc_rule_text_parse_action(
            action_texts[action_index],
            &action);
        if (status != SVC_RULE_TEXT_OK) {
            return status;
        }

        rule_buffer[action_index].conditions = condition_count == 0U ? NULL : condition_buffer;
        rule_buffer[action_index].condition_count = condition_count;
        rule_buffer[action_index].action = action;
    }

    if (compiled_rule_count != NULL) {
        *compiled_rule_count = action_count;
    }
    return SVC_RULE_TEXT_OK;
}
