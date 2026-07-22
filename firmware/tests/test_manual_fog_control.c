#include <assert.h>
#include <stdbool.h>

#include "manual_fog_control.h"
#include "svc_config.h"

static svc_manual_fog_result_t update(
    svc_manual_fog_control_t *control,
    bool input_high,
    uint32_t now_ms)
{
    return svc_manual_fog_control_update(control, input_high, now_ms, true, true, true);
}

static void press_and_debounce(svc_manual_fog_control_t *control, uint32_t start_ms)
{
    update(control, false, start_ms);
    update(control, false, start_ms + SVC_DEFAULT_FOG_DEBOUNCE_MS);
}

static void release_and_debounce(svc_manual_fog_control_t *control, uint32_t start_ms)
{
    update(control, true, start_ms);
    update(control, true, start_ms + SVC_DEFAULT_FOG_DEBOUNCE_MS);
}

static void test_boot_is_off_and_held_button_is_not_accepted(void)
{
    svc_manual_fog_control_t control;
    assert(svc_manual_fog_control_init(&control, &svc_default_config.manual_fog, false, 0U));

    const svc_manual_fog_result_t result = update(&control, false, 100U);

    assert(!result.request_on);
    assert(!result.primary_pair_requested);
    assert(!result.secondary_pair_requested);
}

static void test_short_press_toggles_and_delays_second_pair(void)
{
    svc_manual_fog_control_t control;
    assert(svc_manual_fog_control_init(&control, &svc_default_config.manual_fog, true, 0U));

    press_and_debounce(&control, 10U);
    svc_manual_fog_result_t result = update(&control, false, 61U);
    assert(result.request_on);
    assert(result.primary_pair_requested);
    assert(!result.secondary_pair_requested);

    result = update(&control, false, 310U);
    assert(result.secondary_pair_requested);

    release_and_debounce(&control, 320U);
    press_and_debounce(&control, 400U);
    result = update(&control, false, 451U);
    assert(!result.request_on);
    assert(!result.primary_pair_requested);
    assert(!result.secondary_pair_requested);
}

static void test_fault_or_voltage_denial_clears_request(void)
{
    svc_manual_fog_control_t control;
    assert(svc_manual_fog_control_init(&control, &svc_default_config.manual_fog, true, 0U));
    press_and_debounce(&control, 10U);

    const svc_manual_fog_result_t result =
        svc_manual_fog_control_update(&control, false, 100U, true, false, true);

    assert(!result.request_on);
    assert(!result.primary_pair_requested);
}

static void test_stuck_button_faults_safe_off_until_release(void)
{
    svc_manual_fog_control_t control;
    assert(svc_manual_fog_control_init(&control, &svc_default_config.manual_fog, true, 0U));
    press_and_debounce(&control, 10U);

    svc_manual_fog_result_t result =
        update(&control, false, 60U + SVC_DEFAULT_FOG_STUCK_TIMEOUT_MS);
    assert(result.stuck_fault);
    assert(!result.request_on);

    release_and_debounce(&control, 30100U);
    result = update(&control, true, 30151U);
    assert(!result.stuck_fault);
}

int main(void)
{
    test_boot_is_off_and_held_button_is_not_accepted();
    test_short_press_toggles_and_delays_second_pair();
    test_fault_or_voltage_denial_clears_request();
    test_stuck_button_faults_safe_off_until_release();
    return 0;
}
