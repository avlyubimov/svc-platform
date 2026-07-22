#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "power_budget.h"
#include "svc_config.h"

static uint16_t mask_for(svc_output_id_t output_id)
{
    return (uint16_t)(1U << (uint8_t)output_id);
}

static void test_default_config_is_valid(void)
{
    assert(svc_power_budget_validate_config(&svc_default_config));
}

static void test_allows_output_inside_budget(void)
{
    const svc_power_budget_result_t result = svc_power_budget_can_enable_output(
        &svc_default_config,
        0U,
        SVC_OUTPUT_OUT9,
        30000U,
        true);

    assert(result.decision == SVC_POWER_BUDGET_ALLOW);
    assert(result.projected_total_current_ma == 34000U);
    assert(result.configured_limit_ma == 40000U);
}

static void test_denies_output_over_budget(void)
{
    const svc_power_budget_result_t result = svc_power_budget_can_enable_output(
        &svc_default_config,
        0U,
        SVC_OUTPUT_OUT2,
        30000U,
        true);

    assert(result.decision == SVC_POWER_BUDGET_DENY_TOTAL_LIMIT);
    assert(result.projected_total_current_ma == 48000U);
}

static void test_denies_projected_current_overflow(void)
{
    const svc_power_budget_result_t result = svc_power_budget_can_enable_output(
        &svc_default_config,
        0U,
        SVC_OUTPUT_OUT9,
        UINT32_MAX - 1000U,
        true);

    assert(result.decision == SVC_POWER_BUDGET_DENY_TOTAL_LIMIT);
    assert(result.projected_total_current_ma == UINT32_MAX);
}

static void test_denies_invalid_telemetry(void)
{
    const svc_power_budget_result_t result = svc_power_budget_can_enable_output(
        &svc_default_config,
        0U,
        SVC_OUTPUT_OUT1,
        0U,
        false);

    assert(result.decision == SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID);
}

static void test_denies_already_active_output(void)
{
    const svc_power_budget_result_t result = svc_power_budget_can_enable_output(
        &svc_default_config,
        mask_for(SVC_OUTPUT_OUT1),
        SVC_OUTPUT_OUT1,
        12000U,
        true);

    assert(result.decision == SVC_POWER_BUDGET_DENY_ALREADY_ACTIVE);
}

static void test_shed_order_uses_configured_priority_order(void)
{
    svc_output_id_t shed_outputs[4] = {SVC_OUTPUT_OUT1, SVC_OUTPUT_OUT1, SVC_OUTPUT_OUT1, SVC_OUTPUT_OUT1};
    const uint16_t active_mask =
        mask_for(SVC_OUTPUT_OUT2) |
        mask_for(SVC_OUTPUT_OUT3) |
        mask_for(SVC_OUTPUT_OUT5) |
        mask_for(SVC_OUTPUT_OUT9);

    const size_t shed_count = svc_power_budget_build_shed_list(
        &svc_default_config,
        active_mask,
        shed_outputs,
        4U);

    assert(shed_count == 4U);
    assert(shed_outputs[0] == SVC_OUTPUT_OUT3);
    assert(shed_outputs[1] == SVC_OUTPUT_OUT2);
    assert(shed_outputs[2] == SVC_OUTPUT_OUT5);
    assert(shed_outputs[3] == SVC_OUTPUT_OUT9);
}

int main(void)
{
    test_default_config_is_valid();
    test_allows_output_inside_budget();
    test_denies_output_over_budget();
    test_denies_projected_current_overflow();
    test_denies_invalid_telemetry();
    test_denies_already_active_output();
    test_shed_order_uses_configured_priority_order();
    return 0;
}
