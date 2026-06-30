#include <assert.h>
#include <stdbool.h>

#include "svc_config.h"
#include "thermal_service.h"

static svc_thermal_monitor_t initialized_monitor(void)
{
    svc_thermal_monitor_t monitor = {0};
    svc_thermal_monitor_init(&monitor);
    return monitor;
}

static uint8_t mask_for(svc_thermal_zone_t zone)
{
    return (uint8_t)(1U << (uint8_t)zone);
}

static void test_default_thermal_config_is_valid(void)
{
    assert(svc_thermal_config_is_valid(&svc_default_config));
}

static void test_allow_below_warn(void)
{
    svc_thermal_monitor_t monitor = initialized_monitor();
    const svc_thermal_result_t result = svc_thermal_update_zone(
        &monitor,
        &svc_default_config.thermal[SVC_THERMAL_ZONE_PCB],
        SVC_THERMAL_ZONE_PCB,
        SVC_DEFAULT_THERMAL_WARN_C - 1,
        true);

    assert(result.action == SVC_THERMAL_ACTION_ALLOW);
    assert(result.telemetry_valid);
}

static void test_derate_at_warn(void)
{
    svc_thermal_monitor_t monitor = initialized_monitor();
    const svc_thermal_result_t result = svc_thermal_update_zone(
        &monitor,
        &svc_default_config.thermal[SVC_THERMAL_ZONE_PWR_A],
        SVC_THERMAL_ZONE_PWR_A,
        SVC_DEFAULT_THERMAL_WARN_C,
        true);

    assert(result.action == SVC_THERMAL_ACTION_DERATE);
    assert(result.derate_zone_mask == mask_for(SVC_THERMAL_ZONE_PWR_A));
}

static void test_cutoff_latches_until_recovery(void)
{
    svc_thermal_monitor_t monitor = initialized_monitor();
    const svc_thermal_zone_config_t *config = &svc_default_config.thermal[SVC_THERMAL_ZONE_PWR_A];

    assert(svc_thermal_update_zone(&monitor, config, SVC_THERMAL_ZONE_PWR_A, SVC_DEFAULT_THERMAL_CUTOFF_C, true).action == SVC_THERMAL_ACTION_CUTOFF);
    assert((monitor.cutoff_latched_mask & mask_for(SVC_THERMAL_ZONE_PWR_A)) != 0U);

    const svc_thermal_result_t held = svc_thermal_update_zone(
        &monitor,
        config,
        SVC_THERMAL_ZONE_PWR_A,
        SVC_DEFAULT_THERMAL_WARN_C - 1,
        true);
    assert(held.action == SVC_THERMAL_ACTION_CUTOFF);

    const svc_thermal_result_t recovered = svc_thermal_update_zone(
        &monitor,
        config,
        SVC_THERMAL_ZONE_PWR_A,
        SVC_DEFAULT_THERMAL_RECOVERY_C,
        true);
    assert(recovered.action == SVC_THERMAL_ACTION_ALLOW);
    assert((monitor.cutoff_latched_mask & mask_for(SVC_THERMAL_ZONE_PWR_A)) == 0U);
}

static void test_invalid_telemetry_forces_cutoff(void)
{
    svc_thermal_monitor_t monitor = initialized_monitor();
    const svc_thermal_result_t result = svc_thermal_update_zone(
        &monitor,
        &svc_default_config.thermal[SVC_THERMAL_ZONE_PWR_B],
        SVC_THERMAL_ZONE_PWR_B,
        25,
        false);

    assert(result.action == SVC_THERMAL_ACTION_CUTOFF);
    assert(!result.telemetry_valid);
    assert(result.cutoff_zone_mask == mask_for(SVC_THERMAL_ZONE_PWR_B));
}

static void test_telemetry_aggregate_reports_worst_action(void)
{
    svc_thermal_monitor_t monitor = initialized_monitor();
    svc_telemetry_snapshot_t telemetry = {0};
    svc_telemetry_snapshot_init(&telemetry);
    assert(svc_telemetry_update_thermal(&telemetry, SVC_THERMAL_ZONE_PCB, 25, true, 100U));
    assert(svc_telemetry_update_thermal(&telemetry, SVC_THERMAL_ZONE_PWR_A, SVC_DEFAULT_THERMAL_WARN_C, true, 100U));
    assert(svc_telemetry_update_thermal(&telemetry, SVC_THERMAL_ZONE_PWR_B, SVC_DEFAULT_THERMAL_CUTOFF_C, true, 100U));

    const svc_thermal_result_t result = svc_thermal_update_from_telemetry(
        &monitor,
        &svc_default_config,
        &telemetry,
        100U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(result.action == SVC_THERMAL_ACTION_CUTOFF);
    assert(result.derate_zone_mask == mask_for(SVC_THERMAL_ZONE_PWR_A));
    assert(result.cutoff_zone_mask == mask_for(SVC_THERMAL_ZONE_PWR_B));
}

static void test_stale_thermal_telemetry_forces_cutoff(void)
{
    svc_thermal_monitor_t monitor = initialized_monitor();
    svc_telemetry_snapshot_t telemetry = {0};
    svc_telemetry_snapshot_init(&telemetry);
    assert(svc_telemetry_update_thermal(&telemetry, SVC_THERMAL_ZONE_PCB, 25, true, 100U));
    assert(svc_telemetry_update_thermal(&telemetry, SVC_THERMAL_ZONE_PWR_A, 25, true, 100U));
    assert(svc_telemetry_update_thermal(&telemetry, SVC_THERMAL_ZONE_PWR_B, 25, true, 100U));

    const svc_thermal_result_t result = svc_thermal_update_from_telemetry(
        &monitor,
        &svc_default_config,
        &telemetry,
        1200U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(result.action == SVC_THERMAL_ACTION_CUTOFF);
    assert(!result.telemetry_valid);
    assert(result.cutoff_zone_mask == (
        mask_for(SVC_THERMAL_ZONE_PCB) |
        mask_for(SVC_THERMAL_ZONE_PWR_A) |
        mask_for(SVC_THERMAL_ZONE_PWR_B)));
}

int main(void)
{
    test_default_thermal_config_is_valid();
    test_allow_below_warn();
    test_derate_at_warn();
    test_cutoff_latches_until_recovery();
    test_invalid_telemetry_forces_cutoff();
    test_telemetry_aggregate_reports_worst_action();
    test_stale_thermal_telemetry_forces_cutoff();
    return 0;
}
