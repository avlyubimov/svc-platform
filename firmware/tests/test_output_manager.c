#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "output_manager.h"
#include "svc_config.h"

static uint16_t mask_for(svc_output_id_t output_id)
{
    return (uint16_t)(1U << (uint8_t)output_id);
}

static svc_output_manager_t initialized_manager(void)
{
    svc_output_manager_t manager = {0};
    assert(svc_output_manager_init(&manager, &svc_default_config));
    return manager;
}

static void test_init_keeps_all_outputs_off(void)
{
    const svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_active_mask(&manager) == 0U);
    assert(svc_output_manager_locked_mask(&manager) == 0U);
}

static void test_enable_inside_budget_sets_active_mask(void)
{
    svc_output_manager_t manager = initialized_manager();
    const svc_output_manager_result_t result = svc_output_manager_request_enable(
        &manager,
        SVC_OUTPUT_OUT9,
        30000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_OK);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT9)) != 0U);
}

static void test_enable_over_budget_is_denied(void)
{
    svc_output_manager_t manager = initialized_manager();
    const svc_output_manager_result_t result = svc_output_manager_request_enable(
        &manager,
        SVC_OUTPUT_OUT2,
        30000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_DENY_BUDGET);
    assert(result.budget_decision == SVC_POWER_BUDGET_DENY_TOTAL_LIMIT);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

static void test_invalid_telemetry_is_denied(void)
{
    svc_output_manager_t manager = initialized_manager();
    const svc_output_manager_result_t result = svc_output_manager_request_enable(
        &manager,
        SVC_OUTPUT_OUT1,
        0U,
        false);

    assert(result.status == SVC_OUTPUT_MANAGER_DENY_BUDGET);
    assert(result.budget_decision == SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

static void test_disable_clears_active_output(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_request_disable(&manager, SVC_OUTPUT_OUT9).status == SVC_OUTPUT_MANAGER_OK);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT9)) == 0U);
}

static void test_fault_locks_output_off(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_apply_fault(&manager, SVC_OUTPUT_OUT9).status == SVC_OUTPUT_MANAGER_OK);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT9)) == 0U);
    assert((svc_output_manager_locked_mask(&manager) & mask_for(SVC_OUTPUT_OUT9)) != 0U);

    const svc_output_manager_result_t result = svc_output_manager_request_enable(
        &manager,
        SVC_OUTPUT_OUT9,
        1000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_DENY_LOCKED_OUT);
}

int main(void)
{
    test_init_keeps_all_outputs_off();
    test_enable_inside_budget_sets_active_mask();
    test_enable_over_budget_is_denied();
    test_invalid_telemetry_is_denied();
    test_disable_clears_active_output();
    test_fault_locks_output_off();
    return 0;
}
