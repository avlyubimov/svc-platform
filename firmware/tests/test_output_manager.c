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
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT9) == 0U);
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
    assert(result.pwm_duty_percent == 100U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT9) == 100U);
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

static void test_enable_sheds_lower_priority_load_before_denial(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT2, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 19000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_output_manager_result_t result = svc_output_manager_request_enable(
        &manager,
        SVC_OUTPUT_OUT1,
        35000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_OK);
    assert(result.shed_output_mask == mask_for(SVC_OUTPUT_OUT2));
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT2)) == 0U);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT1)) != 0U);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT9)) != 0U);
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
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT9) == 0U);
}

static void test_fault_locks_output_off(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_apply_fault(&manager, SVC_OUTPUT_OUT9).status == SVC_OUTPUT_MANAGER_OK);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT9)) == 0U);
    assert((svc_output_manager_locked_mask(&manager) & mask_for(SVC_OUTPUT_OUT9)) != 0U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT9) == 0U);

    const svc_output_manager_result_t result = svc_output_manager_request_enable(
        &manager,
        SVC_OUTPUT_OUT9,
        1000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_DENY_LOCKED_OUT);
}

static void test_pwm_request_sets_duty_and_active_mask(void)
{
    svc_output_manager_t manager = initialized_manager();
    const svc_output_manager_result_t result = svc_output_manager_request_pwm(
        &manager,
        SVC_OUTPUT_OUT3,
        40U,
        1000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_OK);
    assert(result.pwm_duty_percent == 40U);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT3)) != 0U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 40U);
}

static void test_zero_pwm_request_disables_output(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_pwm(&manager, SVC_OUTPUT_OUT3, 40U, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_output_manager_result_t result = svc_output_manager_request_pwm(
        &manager,
        SVC_OUTPUT_OUT3,
        0U,
        0U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_OK);
    assert(result.pwm_duty_percent == 0U);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT3)) == 0U);
}

static void test_partial_pwm_is_denied_when_not_allowed(void)
{
    svc_output_manager_t manager = initialized_manager();
    const svc_output_manager_result_t result = svc_output_manager_request_pwm(
        &manager,
        SVC_OUTPUT_OUT2,
        40U,
        1000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_DENY_PWM_NOT_ALLOWED);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

static void test_invalid_pwm_is_denied(void)
{
    svc_output_manager_t manager = initialized_manager();
    const svc_output_manager_result_t result = svc_output_manager_request_pwm(
        &manager,
        SVC_OUTPUT_OUT3,
        101U,
        1000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_DENY_INVALID_PWM);
    assert(svc_output_manager_active_mask(&manager) == 0U);
}

static void test_pwm_increase_requires_valid_telemetry(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_pwm(&manager, SVC_OUTPUT_OUT3, 40U, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_output_manager_result_t result = svc_output_manager_request_pwm(
        &manager,
        SVC_OUTPUT_OUT3,
        100U,
        1000U,
        false);

    assert(result.status == SVC_OUTPUT_MANAGER_DENY_BUDGET);
    assert(result.budget_decision == SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 40U);
}

static void test_pwm_increase_rechecks_total_budget(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_pwm(&manager, SVC_OUTPUT_OUT3, 40U, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_output_manager_result_t result = svc_output_manager_request_pwm(
        &manager,
        SVC_OUTPUT_OUT3,
        100U,
        39000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_DENY_BUDGET);
    assert(result.budget_decision == SVC_POWER_BUDGET_DENY_TOTAL_LIMIT);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 40U);
}

static void test_pwm_increase_denies_projected_current_overflow(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_pwm(&manager, SVC_OUTPUT_OUT3, 40U, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_output_manager_result_t result = svc_output_manager_request_pwm(
        &manager,
        SVC_OUTPUT_OUT3,
        100U,
        UINT32_MAX - 1000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_DENY_BUDGET);
    assert(result.budget_decision == SVC_POWER_BUDGET_DENY_TOTAL_LIMIT);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 40U);
}

static void test_pwm_decrease_is_allowed_without_fresh_telemetry(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_pwm(&manager, SVC_OUTPUT_OUT3, 80U, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_output_manager_result_t result = svc_output_manager_request_pwm(
        &manager,
        SVC_OUTPUT_OUT3,
        40U,
        0U,
        false);

    assert(result.status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 40U);
}

static void test_runtime_budget_enforcement_sheds_configured_priority_order(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT2, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT3, 19000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 27000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_output_manager_result_t result = svc_output_manager_enforce_budget(
        &manager,
        45000U,
        true);

    assert(result.status == SVC_OUTPUT_MANAGER_OK);
    assert(result.shed_output_mask == mask_for(SVC_OUTPUT_OUT2));
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT2)) == 0U);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT3)) != 0U);
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT9)) != 0U);
}

static void test_thermal_derate_reduces_pwm_and_sheds_non_pwm_low_priority(void)
{
    svc_output_manager_t manager = initialized_manager();
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT2, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT3, 19000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_output_manager_result_t result = svc_output_manager_apply_thermal_derate(
        &manager,
        50U);

    assert(result.status == SVC_OUTPUT_MANAGER_OK);
    assert(result.shed_output_mask == mask_for(SVC_OUTPUT_OUT2));
    assert(result.derated_output_mask == mask_for(SVC_OUTPUT_OUT3));
    assert((svc_output_manager_active_mask(&manager) & mask_for(SVC_OUTPUT_OUT2)) == 0U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT3) == 50U);
}

int main(void)
{
    test_init_keeps_all_outputs_off();
    test_enable_inside_budget_sets_active_mask();
    test_enable_over_budget_is_denied();
    test_enable_sheds_lower_priority_load_before_denial();
    test_invalid_telemetry_is_denied();
    test_disable_clears_active_output();
    test_fault_locks_output_off();
    test_pwm_request_sets_duty_and_active_mask();
    test_zero_pwm_request_disables_output();
    test_partial_pwm_is_denied_when_not_allowed();
    test_invalid_pwm_is_denied();
    test_pwm_increase_requires_valid_telemetry();
    test_pwm_increase_rechecks_total_budget();
    test_pwm_increase_denies_projected_current_overflow();
    test_pwm_decrease_is_allowed_without_fresh_telemetry();
    test_runtime_budget_enforcement_sheds_configured_priority_order();
    test_thermal_derate_reduces_pwm_and_sheds_non_pwm_low_priority();
    return 0;
}
