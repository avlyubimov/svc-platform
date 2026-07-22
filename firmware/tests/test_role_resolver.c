#include <assert.h>

#include "role_resolver.h"
#include "svc_config.h"

static void test_default_config_resolves_role_to_output(void)
{
    const svc_role_resolver_result_t result = svc_role_resolver_find_output(
        &svc_default_config,
        OUT_ROLE_FOG_PRIMARY_LEFT);

    assert(result.status == SVC_ROLE_RESOLVER_OK);
    assert(result.output_id == SVC_OUTPUT_OUT3);
    assert(result.match_count == 1U);
}

static void test_none_role_is_not_actionable(void)
{
    const svc_role_resolver_result_t result = svc_role_resolver_find_output(
        &svc_default_config,
        OUT_ROLE_NONE);

    assert(result.status == SVC_ROLE_RESOLVER_INVALID_ROLE);
}

static void test_missing_role_is_reported(void)
{
    svc_device_config_t config = svc_default_config;
    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        if (config.outputs[output_index].role == OUT_ROLE_LOW_CURRENT_RESERVE_2) {
            config.outputs[output_index].role = OUT_ROLE_SPARE;
        }
    }

    const svc_role_resolver_result_t result = svc_role_resolver_find_output(
        &config,
        OUT_ROLE_LOW_CURRENT_RESERVE_2);

    assert(result.status == SVC_ROLE_RESOLVER_NOT_FOUND);
    assert(result.match_count == 0U);
}

static void test_ambiguous_role_is_reported(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[0].role = OUT_ROLE_FOG_PRIMARY_LEFT;

    const svc_role_resolver_result_t result = svc_role_resolver_find_output(
        &config,
        OUT_ROLE_FOG_PRIMARY_LEFT);

    assert(result.status == SVC_ROLE_RESOLVER_AMBIGUOUS);
    assert(result.match_count == 2U);
}

static void test_invalid_config_is_reported(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[0].role = OUT_ROLE_COUNT;

    const svc_role_resolver_result_t result = svc_role_resolver_find_output(
        &config,
        OUT_ROLE_HIGH_CURRENT_RESERVE);

    assert(result.status == SVC_ROLE_RESOLVER_INVALID_CONFIG);
}

int main(void)
{
    test_default_config_resolves_role_to_output();
    test_none_role_is_not_actionable();
    test_missing_role_is_reported();
    test_ambiguous_role_is_reported();
    test_invalid_config_is_reported();
    return 0;
}
