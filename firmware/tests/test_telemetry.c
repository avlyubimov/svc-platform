#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "telemetry.h"

static void test_init_marks_all_measurements_invalid(void)
{
    svc_telemetry_snapshot_t snapshot = {0};
    svc_telemetry_snapshot_init(&snapshot);

    assert(!svc_telemetry_battery_is_valid(&snapshot, 0U, SVC_TELEMETRY_DEFAULT_STALE_MS));
    assert(!svc_telemetry_total_current_is_valid(&snapshot, 0U, SVC_TELEMETRY_DEFAULT_STALE_MS));
    assert(!svc_telemetry_output_current_is_valid(&snapshot, SVC_OUTPUT_OUT1, 0U, SVC_TELEMETRY_DEFAULT_STALE_MS));
}

static void test_battery_validity_expires_after_stale_window(void)
{
    svc_telemetry_snapshot_t snapshot = {0};
    svc_telemetry_snapshot_init(&snapshot);
    svc_telemetry_update_battery(&snapshot, 12600U, true, 100U);

    assert(svc_telemetry_battery_is_valid(&snapshot, 1099U, SVC_TELEMETRY_DEFAULT_STALE_MS));
    assert(!svc_telemetry_battery_is_valid(&snapshot, 1101U, SVC_TELEMETRY_DEFAULT_STALE_MS));

    const svc_telemetry_battery_input_t input = svc_telemetry_battery_input(
        &snapshot,
        1101U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);
    assert(input.measured_battery_mv == 12600U);
    assert(!input.telemetry_valid);
}

static void test_invalid_battery_sample_fails_validity_even_when_fresh(void)
{
    svc_telemetry_snapshot_t snapshot = {0};
    svc_telemetry_snapshot_init(&snapshot);
    svc_telemetry_update_battery(&snapshot, 12600U, false, 100U);

    assert(!svc_telemetry_battery_is_valid(&snapshot, 100U, SVC_TELEMETRY_DEFAULT_STALE_MS));
}

static void test_total_current_power_budget_input(void)
{
    svc_telemetry_snapshot_t snapshot = {0};
    svc_telemetry_snapshot_init(&snapshot);
    svc_telemetry_update_total_current(&snapshot, 12000U, true, 500U);

    const svc_telemetry_power_budget_input_t input = svc_telemetry_power_budget_input(
        &snapshot,
        600U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(input.measured_total_current_ma == 12000U);
    assert(input.telemetry_valid);
}

static void test_output_current_validity_and_invalid_output(void)
{
    svc_telemetry_snapshot_t snapshot = {0};
    svc_telemetry_snapshot_init(&snapshot);

    assert(svc_telemetry_update_output_current(&snapshot, SVC_OUTPUT_OUT3, 4000U, true, 100U));
    assert(svc_telemetry_output_current_is_valid(&snapshot, SVC_OUTPUT_OUT3, 100U, SVC_TELEMETRY_DEFAULT_STALE_MS));
    assert(snapshot.output_current_ma[SVC_OUTPUT_OUT3] == 4000U);

    assert(!svc_telemetry_update_output_current(&snapshot, (svc_output_id_t)SVC_OUTPUT_COUNT, 1U, true, 100U));
    assert(!svc_telemetry_output_current_is_valid(&snapshot, (svc_output_id_t)SVC_OUTPUT_COUNT, 100U, SVC_TELEMETRY_DEFAULT_STALE_MS));
}

static void test_thermal_validity_and_stale_input(void)
{
    svc_telemetry_snapshot_t snapshot = {0};
    svc_telemetry_snapshot_init(&snapshot);

    assert(svc_telemetry_update_thermal(&snapshot, SVC_THERMAL_ZONE_PWR_A, 85, true, 100U));
    assert(svc_telemetry_thermal_is_valid(&snapshot, SVC_THERMAL_ZONE_PWR_A, 100U, SVC_TELEMETRY_DEFAULT_STALE_MS));

    const svc_telemetry_thermal_input_t fresh = svc_telemetry_thermal_input(
        &snapshot,
        SVC_THERMAL_ZONE_PWR_A,
        100U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);
    assert(fresh.measured_temperature_c == 85);
    assert(fresh.telemetry_valid);

    const svc_telemetry_thermal_input_t stale = svc_telemetry_thermal_input(
        &snapshot,
        SVC_THERMAL_ZONE_PWR_A,
        1200U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);
    assert(stale.measured_temperature_c == 85);
    assert(!stale.telemetry_valid);
}

int main(void)
{
    test_init_marks_all_measurements_invalid();
    test_battery_validity_expires_after_stale_window();
    test_invalid_battery_sample_fails_validity_even_when_fresh();
    test_total_current_power_budget_input();
    test_output_current_validity_and_invalid_output();
    test_thermal_validity_and_stale_input();
    return 0;
}
