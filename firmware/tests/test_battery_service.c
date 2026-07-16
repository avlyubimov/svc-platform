#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "battery_service.h"
#include "svc_config.h"

static svc_battery_monitor_t initialized_monitor(void)
{
    svc_battery_monitor_t monitor = {0};
    svc_battery_monitor_init(&monitor);
    return monitor;
}

static void test_default_battery_config_is_valid(void)
{
    assert(svc_battery_config_is_valid(&svc_default_config.battery));
}

static void test_allows_voltage_above_warn(void)
{
    svc_battery_monitor_t monitor = initialized_monitor();
    const svc_battery_result_t result = svc_battery_update(
        &monitor,
        &svc_default_config.battery,
        12600U,
        true);

    assert(result.action == SVC_BATTERY_ACTION_ALLOW);
    assert(!result.cutoff_latched);
}

static void test_warns_below_warn_threshold(void)
{
    svc_battery_monitor_t monitor = initialized_monitor();
    const svc_battery_result_t result = svc_battery_update(
        &monitor,
        &svc_default_config.battery,
        11900U,
        true);

    assert(result.action == SVC_BATTERY_ACTION_WARN);
    assert(!result.cutoff_latched);
}

static void test_below_cutoff_warns_until_shutdown_delay(void)
{
    svc_battery_monitor_t monitor = initialized_monitor();
    svc_battery_config_t config = svc_default_config.battery;
    config.shutdown_delay_s = 3U;

    const svc_battery_result_t delayed_result = svc_battery_update_elapsed_s(
        &monitor,
        &config,
        11700U,
        true,
        1U);

    assert(delayed_result.action == SVC_BATTERY_ACTION_WARN);
    assert(delayed_result.undervoltage_duration_s == 1U);
    assert(!delayed_result.cutoff_latched);
}

static void test_cutoff_latches_after_shutdown_delay(void)
{
    svc_battery_monitor_t monitor = initialized_monitor();
    svc_battery_config_t config = svc_default_config.battery;
    config.shutdown_delay_s = 3U;
    assert(svc_battery_update_elapsed_s(&monitor, &config, 11700U, true, 1U).action == SVC_BATTERY_ACTION_WARN);

    const svc_battery_result_t cutoff_result = svc_battery_update_elapsed_s(
        &monitor,
        &config,
        11700U,
        true,
        2U);

    assert(cutoff_result.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(cutoff_result.cutoff_latched);
    assert(cutoff_result.undervoltage_duration_s == 3U);

    const svc_battery_result_t held_result = svc_battery_update_elapsed_s(
        &monitor,
        &config,
        12100U,
        true,
        1U);

    assert(held_result.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(held_result.cutoff_latched);
}

static void test_recovery_clears_cutoff_latch(void)
{
    svc_battery_monitor_t monitor = initialized_monitor();
    assert(svc_battery_update_elapsed_s(
        &monitor,
        &svc_default_config.battery,
        11700U,
        true,
        SVC_DEFAULT_BATTERY_SHUTDOWN_DELAY_S).action == SVC_BATTERY_ACTION_CUTOFF);

    const svc_battery_result_t result = svc_battery_update(
        &monitor,
        &svc_default_config.battery,
        12500U,
        true);

    assert(result.action == SVC_BATTERY_ACTION_ALLOW);
    assert(!result.cutoff_latched);
}

static void test_invalid_telemetry_forces_cutoff(void)
{
    svc_battery_monitor_t monitor = initialized_monitor();
    const svc_battery_result_t result = svc_battery_update(
        &monitor,
        &svc_default_config.battery,
        12600U,
        false);

    assert(result.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(result.cutoff_latched);
}

int main(void)
{
    test_default_battery_config_is_valid();
    test_allows_voltage_above_warn();
    test_warns_below_warn_threshold();
    test_below_cutoff_warns_until_shutdown_delay();
    test_cutoff_latches_after_shutdown_delay();
    test_recovery_clears_cutoff_latch();
    test_invalid_telemetry_forces_cutoff();
    return 0;
}
