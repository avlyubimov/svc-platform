#include "role_resolver.h"

#include "config_validator.h"

static svc_role_resolver_result_t make_result(
    svc_role_resolver_status_t status,
    svc_output_id_t output_id,
    size_t match_count)
{
    return (svc_role_resolver_result_t){
        .status = status,
        .output_id = output_id,
        .match_count = match_count
    };
}

svc_role_resolver_result_t svc_role_resolver_find_output(
    const svc_device_config_t *config,
    output_role_t role)
{
    if (svc_config_validate_device(config).status != SVC_CONFIG_OK) {
        return make_result(SVC_ROLE_RESOLVER_INVALID_CONFIG, SVC_OUTPUT_OUT1, 0U);
    }
    if (role == OUT_ROLE_NONE || !svc_output_role_is_valid(role)) {
        return make_result(SVC_ROLE_RESOLVER_INVALID_ROLE, SVC_OUTPUT_OUT1, 0U);
    }

    svc_output_id_t matched_output = SVC_OUTPUT_OUT1;
    size_t match_count = 0U;
    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        if (config->outputs[output_index].role != role) {
            continue;
        }
        matched_output = config->outputs[output_index].id;
        ++match_count;
    }

    if (match_count == 0U) {
        return make_result(SVC_ROLE_RESOLVER_NOT_FOUND, SVC_OUTPUT_OUT1, match_count);
    }
    if (match_count > 1U) {
        return make_result(SVC_ROLE_RESOLVER_AMBIGUOUS, matched_output, match_count);
    }
    return make_result(SVC_ROLE_RESOLVER_OK, matched_output, match_count);
}
