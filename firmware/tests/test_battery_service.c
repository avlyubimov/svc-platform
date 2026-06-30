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

static void test_cutoff_latches_below_cutoff(void)
{
    svc_battery_monitor_t monitor = initialized_monitor();
    const svc_battery_result_t cutoff_result = svc_battery_update(
        &monitor,
        &svc_default_config.battery,
        11700U,
        true);

    assert(cutoff_result.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(cutoff_result.cutoff_latched);

    const svc_battery_result_t held_result = svc_battery_update(
        &monitor,
        &svc_default_config.battery,
        12100U,
        true);

    assert(held_result.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(held_result.cutoff_latched);
}

static void test_recovery_clears_cutoff_latch(void)
{
    svc_battery_monitor_t monitor = initialized_monitor();
    assert(svc_battery_update(&monitor, &svc_default_config.battery, 11700U, true).action == SVC_BATTERY_ACTION_CUTOFF);

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
    test_cutoff_latches_below_cutoff();
    test_recovery_clears_cutoff_latch();
    test_invalid_telemetry_forces_cutoff();
    return 0;
}
