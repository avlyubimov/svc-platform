#include <assert.h>
#include <stdbool.h>

#include "manual_fog_control.h"
#include "svc_config.h"

static const svc_manual_fog_safety_t SAFE = {
    .configuration_valid = true,
    .faults_clear = true,
    .voltage_permits = true,
    .current_permits = true,
    .thermal_permits = true
};

static svc_manual_fog_result_t update(
    svc_manual_fog_control_t *control,
    bool pair_a_high,
    bool pair_b_high,
    uint32_t now_ms)
{
    return svc_manual_fog_control_update(control, pair_a_high, pair_b_high, now_ms, SAFE);
}

static void settle(
    svc_manual_fog_control_t *control,
    bool pair_a_high,
    bool pair_b_high,
    uint32_t start_ms)
{
    update(control, pair_a_high, pair_b_high, start_ms);
    update(control, pair_a_high, pair_b_high, start_ms + SVC_DEFAULT_FOG_DEBOUNCE_MS);
}

static void init_released(svc_manual_fog_control_t *control)
{
    assert(svc_manual_fog_control_init(control, &svc_default_config.manual_fog, true, true, 0U));
}

static void test_button_a_controls_only_first_pair(void)
{
    svc_manual_fog_control_t control;
    init_released(&control);
    settle(&control, false, true, 10U);

    const svc_manual_fog_result_t result = update(&control, false, true, 61U);
    assert(result.pair_a_channel_1_requested);
    assert(!result.pair_b_channel_1_requested);
    assert(!result.pair_b_channel_2_requested);
}

static void test_button_b_controls_only_second_pair(void)
{
    svc_manual_fog_control_t control;
    init_released(&control);
    settle(&control, true, false, 10U);

    const svc_manual_fog_result_t result = update(&control, true, false, 61U);
    assert(result.pair_b_channel_1_requested);
    assert(!result.pair_a_channel_1_requested);
    assert(!result.pair_a_channel_2_requested);
}

static void test_both_pairs_and_simultaneous_press(void)
{
    svc_manual_fog_control_t control;
    init_released(&control);
    settle(&control, false, false, 10U);

    svc_manual_fog_result_t result = update(&control, false, false, 61U);
    assert(result.pair_a_channel_1_requested);
    assert(result.pair_b_channel_1_requested);

    result = update(&control, false, false, 60U + SVC_DEFAULT_FOG_CHANNEL_DELAY_MS);
    assert(result.pair_a_channel_2_requested);
    assert(result.pair_b_channel_2_requested);
}

static void test_each_pair_starts_channels_sequentially(void)
{
    svc_manual_fog_control_t control;
    init_released(&control);
    settle(&control, false, true, 10U);

    svc_manual_fog_result_t result = update(&control, false, true, 60U);
    assert(result.pair_a_channel_1_requested);
    assert(!result.pair_a_channel_2_requested);

    result = update(&control, false, true, 60U + SVC_DEFAULT_FOG_CHANNEL_DELAY_MS);
    assert(result.pair_a_channel_2_requested);
}

static void test_pair_off_disables_both_channels_same_update(void)
{
    svc_manual_fog_control_t control;
    init_released(&control);
    settle(&control, false, true, 10U);
    update(&control, false, true, 300U);
    settle(&control, true, true, 310U);
    settle(&control, false, true, 400U);

    const svc_manual_fog_result_t result = update(&control, false, true, 451U);
    assert(!result.pair_a_request_on);
    assert(!result.pair_a_channel_1_requested);
    assert(!result.pair_a_channel_2_requested);
}

static void test_contact_bounce_does_not_toggle(void)
{
    svc_manual_fog_control_t control;
    init_released(&control);
    update(&control, false, true, 10U);
    update(&control, true, true, 20U);
    update(&control, false, true, 30U);
    update(&control, true, true, 40U);

    const svc_manual_fog_result_t result = update(&control, true, true, 100U);
    assert(!result.pair_a_request_on);
}

static void test_stuck_a_does_not_block_b(void)
{
    svc_manual_fog_control_t control;
    init_released(&control);
    settle(&control, false, true, 10U);
    settle(&control, false, false, 100U);

    const svc_manual_fog_result_t result = update(
        &control,
        false,
        false,
        60U + SVC_DEFAULT_FOG_STUCK_TIMEOUT_MS);
    assert(result.pair_a_stuck_fault);
    assert(!result.pair_a_channel_1_requested);
    assert(result.pair_b_channel_1_requested);
    assert(!result.pair_b_stuck_fault);
}

static void test_boot_and_reset_clear_requests(void)
{
    svc_manual_fog_control_t control;
    assert(svc_manual_fog_control_init(&control, &svc_default_config.manual_fog, false, false, 0U));
    svc_manual_fog_result_t result = update(&control, false, false, 100U);
    assert(!result.pair_a_request_on);
    assert(!result.pair_b_request_on);

    init_released(&control);
    settle(&control, false, false, 10U);
    assert(svc_manual_fog_control_init(&control, &svc_default_config.manual_fog, true, true, 500U));
    result = update(&control, true, true, 600U);
    assert(!result.pair_a_request_on);
    assert(!result.pair_b_request_on);
}

static void test_safety_denials_clear_requests(void)
{
    svc_manual_fog_safety_t safety = SAFE;
    svc_manual_fog_control_t control;
    init_released(&control);
    settle(&control, false, false, 10U);

    safety.voltage_permits = false;
    svc_manual_fog_result_t result = svc_manual_fog_control_update(&control, false, false, 100U, safety);
    assert(!result.pair_a_request_on && !result.pair_b_request_on);

    settle(&control, true, true, 110U);
    settle(&control, false, false, 200U);
    safety = SAFE;
    safety.current_permits = false;
    result = svc_manual_fog_control_update(&control, false, false, 300U, safety);
    assert(!result.pair_a_request_on && !result.pair_b_request_on);

    settle(&control, true, true, 310U);
    settle(&control, false, false, 400U);
    safety = SAFE;
    safety.thermal_permits = false;
    result = svc_manual_fog_control_update(&control, false, false, 500U, safety);
    assert(!result.pair_a_request_on && !result.pair_b_request_on);
}

static void test_fault_clear_does_not_restore_request(void)
{
    svc_manual_fog_control_t control;
    init_released(&control);
    settle(&control, false, true, 10U);

    svc_manual_fog_safety_t safety = SAFE;
    safety.faults_clear = false;
    svc_manual_fog_result_t result = svc_manual_fog_control_update(&control, false, true, 100U, safety);
    assert(!result.pair_a_request_on);

    result = update(&control, false, true, 200U);
    assert(!result.pair_a_request_on);
}

static void test_maintained_mode_follows_contact_after_safe_boot(void)
{
    svc_manual_fog_config_t config = svc_default_config.manual_fog;
    config.pair_a.behavior = SVC_MANUAL_INPUT_MAINTAINED;
    svc_manual_fog_control_t control;
    assert(svc_manual_fog_control_init(&control, &config, true, true, 0U));

    settle(&control, false, true, 10U);
    svc_manual_fog_result_t result = update(&control, false, true, 61U);
    assert(result.pair_a_request_on);

    settle(&control, true, true, 100U);
    result = update(&control, true, true, 151U);
    assert(!result.pair_a_request_on);
}

int main(void)
{
    test_button_a_controls_only_first_pair();
    test_button_b_controls_only_second_pair();
    test_both_pairs_and_simultaneous_press();
    test_each_pair_starts_channels_sequentially();
    test_pair_off_disables_both_channels_same_update();
    test_contact_bounce_does_not_toggle();
    test_stuck_a_does_not_block_b();
    test_boot_and_reset_clear_requests();
    test_safety_denials_clear_requests();
    test_fault_clear_does_not_restore_request();
    test_maintained_mode_follows_contact_after_safe_boot();
    return 0;
}
