#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "event_bus.h"
#include "output_manager.h"
#include "svc_config.h"
#include "system_safety.h"
#include "telemetry.h"

static uint16_t mask_for(svc_output_id_t output_id)
{
    return (uint16_t)(1U << (uint8_t)output_id);
}

static svc_output_manager_t initialized_output_manager(void)
{
    svc_output_manager_t manager = {0};
    assert(svc_output_manager_init(&manager, &svc_default_config));
    return manager;
}

static svc_system_safety_t initialized_safety(void)
{
    svc_system_safety_t safety = {0};
    assert(svc_system_safety_init(&safety, &svc_default_config));
    return safety;
}

static svc_system_safety_result_t update_battery_below_cutoff_after_shutdown_delay(
    svc_system_safety_t *safety,
    svc_output_manager_t *manager,
    svc_event_bus_t *bus,
    uint16_t measured_mv)
{
    svc_telemetry_snapshot_t telemetry = {0};
    svc_telemetry_snapshot_init(&telemetry);
    svc_telemetry_update_battery(&telemetry, 12600U, true, 0U);
    assert(svc_system_safety_update_from_telemetry(
        safety,
        manager,
        bus,
        &telemetry,
        0U,
        SVC_TELEMETRY_DEFAULT_STALE_MS).battery.action == SVC_BATTERY_ACTION_ALLOW);

    const uint32_t cutoff_time_ms = (uint32_t)SVC_DEFAULT_BATTERY_SHUTDOWN_DELAY_S * 1000U;
    svc_telemetry_update_battery(&telemetry, measured_mv, true, cutoff_time_ms);
    return svc_system_safety_update_from_telemetry(
        safety,
        manager,
        bus,
        &telemetry,
        cutoff_time_ms,
        SVC_TELEMETRY_DEFAULT_STALE_MS);
}

static void test_warn_publishes_event_without_disabling_outputs(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_safety_result_t result = svc_system_safety_update_battery(
        &safety,
        &manager,
        &bus,
        11900U,
        true);

    assert(result.battery.action == SVC_BATTERY_ACTION_WARN);
    assert(result.event_publish_attempted);
    assert(result.event_published);
    assert(result.disabled_output_mask == 0U);
    assert((result.active_output_mask & mask_for(SVC_OUTPUT_OUT9)) != 0U);
    assert(svc_event_bus_count(&bus) == 1U);

    svc_event_t event = {0};
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_LOW_BATTERY_WARN);
    assert(event.value == 11900U);
}

static void test_cutoff_disables_active_outputs_and_publishes_event(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT5, 5000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_safety_result_t result = update_battery_below_cutoff_after_shutdown_delay(
        &safety,
        &manager,
        &bus,
        11700U);

    const uint16_t expected_disabled_mask = mask_for(SVC_OUTPUT_OUT5) | mask_for(SVC_OUTPUT_OUT9);
    assert(result.battery.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(result.battery.cutoff_latched);
    assert(result.event_publish_attempted);
    assert(result.event_published);
    assert(result.disabled_output_mask == expected_disabled_mask);
    assert(result.active_output_mask == 0U);
    assert(svc_output_manager_active_mask(&manager) == 0U);

    svc_event_t event = {0};
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_LOW_BATTERY_CUTOFF);
    assert(event.value == 11700U);
}

static void test_invalid_telemetry_forces_cutoff(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_safety_result_t result = svc_system_safety_update_battery(
        &safety,
        &manager,
        &bus,
        12600U,
        false);

    assert(result.battery.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(result.battery.cutoff_latched);
    assert(result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert(result.active_output_mask == 0U);
}

static void test_event_publish_failure_still_disables_outputs(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    for (size_t event_index = 0U; event_index < SVC_EVENT_BUS_CAPACITY; ++event_index) {
        assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_STATE_CHANGED, SVC_OUTPUT_OUT1, (uint32_t)event_index}));
    }
    assert(svc_event_bus_is_full(&bus));
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_safety_result_t result = update_battery_below_cutoff_after_shutdown_delay(
        &safety,
        &manager,
        &bus,
        11700U);

    assert(result.battery.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(result.event_publish_attempted);
    assert(!result.event_published);
    assert(result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert(result.active_output_mask == 0U);
}

static void test_recovery_does_not_reenable_outputs(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(update_battery_below_cutoff_after_shutdown_delay(&safety, &manager, &bus, 11700U).battery.action == SVC_BATTERY_ACTION_CUTOFF);

    const svc_system_safety_result_t result = svc_system_safety_update_battery(
        &safety,
        &manager,
        &bus,
        12500U,
        true);

    assert(result.battery.action == SVC_BATTERY_ACTION_ALLOW);
    assert(!result.battery.cutoff_latched);
    assert(result.disabled_output_mask == 0U);
    assert(result.active_output_mask == 0U);
}

static void test_uninitialized_safety_fails_safe(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = {0};
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_safety_result_t result = svc_system_safety_update_battery(
        &safety,
        &manager,
        &bus,
        12600U,
        true);

    assert(result.battery.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(result.battery.cutoff_latched);
    assert(result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert(result.active_output_mask == 0U);
}

static void test_stale_telemetry_forces_cutoff(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_telemetry_snapshot_t telemetry = {0};
    svc_telemetry_snapshot_init(&telemetry);
    svc_telemetry_update_battery(&telemetry, 12600U, true, 100U);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_safety_result_t result = svc_system_safety_update_from_telemetry(
        &safety,
        &manager,
        &bus,
        &telemetry,
        1200U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(result.battery.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(!result.battery.telemetry_valid);
    assert(result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert(result.active_output_mask == 0U);
}

static void test_battery_cutoff_waits_for_shutdown_delay(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_safety_result_t result = svc_system_safety_update_battery(
        &safety,
        &manager,
        &bus,
        11700U,
        true);

    assert(result.battery.action == SVC_BATTERY_ACTION_WARN);
    assert(!result.battery.cutoff_latched);
    assert(result.disabled_output_mask == 0U);
    assert((result.active_output_mask & mask_for(SVC_OUTPUT_OUT9)) != 0U);
}

static void test_large_battery_elapsed_interval_forces_cutoff_without_wrap(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_telemetry_snapshot_t telemetry = {0};
    svc_telemetry_snapshot_init(&telemetry);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    svc_telemetry_update_battery(&telemetry, 12600U, true, 0U);
    assert(svc_system_safety_update_from_telemetry(
        &safety,
        &manager,
        &bus,
        &telemetry,
        0U,
        SVC_TELEMETRY_DEFAULT_STALE_MS).battery.action == SVC_BATTERY_ACTION_ALLOW);

    svc_telemetry_update_battery(&telemetry, 11700U, true, UINT32_MAX);
    const svc_system_safety_result_t result = svc_system_safety_update_from_telemetry(
        &safety,
        &manager,
        &bus,
        &telemetry,
        UINT32_MAX,
        SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(result.battery.action == SVC_BATTERY_ACTION_CUTOFF);
    assert(result.battery.cutoff_latched);
    assert(result.battery.undervoltage_duration_s == UINT16_MAX);
    assert(result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert(result.active_output_mask == 0U);
}

static svc_telemetry_snapshot_t thermal_telemetry_all_at(int16_t temperature_c, uint32_t now_ms)
{
    svc_telemetry_snapshot_t telemetry = {0};
    svc_telemetry_snapshot_init(&telemetry);
    assert(svc_telemetry_update_thermal(&telemetry, SVC_THERMAL_ZONE_PCB, temperature_c, true, now_ms));
    assert(svc_telemetry_update_thermal(&telemetry, SVC_THERMAL_ZONE_PWR_A, temperature_c, true, now_ms));
    assert(svc_telemetry_update_thermal(&telemetry, SVC_THERMAL_ZONE_PWR_B, temperature_c, true, now_ms));
    return telemetry;
}

static void test_thermal_derate_publishes_event_without_disabling_outputs(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_telemetry_snapshot_t telemetry = thermal_telemetry_all_at(SVC_DEFAULT_THERMAL_WARN_C, 100U);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_thermal_safety_result_t result = svc_system_safety_update_thermal_from_telemetry(
        &safety,
        &manager,
        &bus,
        &telemetry,
        100U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(result.thermal.action == SVC_THERMAL_ACTION_DERATE);
    assert(result.event_publish_attempted);
    assert(result.event_published);
    assert(result.disabled_output_mask == 0U);
    assert(result.derated_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert((result.active_output_mask & mask_for(SVC_OUTPUT_OUT9)) != 0U);
    assert(svc_output_manager_pwm_duty_percent(&manager, SVC_OUTPUT_OUT9) == SVC_THERMAL_DERATE_PWM_MAX_PERCENT);

    svc_event_t event = {0};
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_THERMAL_DERATE);
}

static void test_runtime_power_budget_sheds_active_loads(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT2, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT3, 19000U, true).status == SVC_OUTPUT_MANAGER_OK);
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 27000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_power_budget_safety_result_t result = svc_system_safety_update_power_budget(
        &safety,
        &manager,
        &bus,
        45000U,
        true);

    assert(result.budget.status == SVC_OUTPUT_MANAGER_OK);
    assert(result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT3));
    assert((result.active_output_mask & mask_for(SVC_OUTPUT_OUT3)) == 0U);
    assert((result.active_output_mask & mask_for(SVC_OUTPUT_OUT2)) != 0U);
    assert((result.active_output_mask & mask_for(SVC_OUTPUT_OUT9)) != 0U);
    assert(result.event_publish_attempted);
    assert(result.event_published);

    svc_event_t event = {0};
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_POWER_BUDGET_SHED);
    assert(event.value == 45000U);
}

static void test_stale_power_budget_telemetry_disables_active_outputs(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_telemetry_snapshot_t telemetry = {0};
    svc_telemetry_snapshot_init(&telemetry);
    svc_telemetry_update_total_current(&telemetry, 12000U, true, 100U);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_power_budget_safety_result_t result =
        svc_system_safety_update_power_budget_from_telemetry(
            &safety,
            &manager,
            &bus,
            &telemetry,
            1200U,
            SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(result.budget.status == SVC_OUTPUT_MANAGER_DENY_BUDGET);
    assert(result.budget.budget_decision == SVC_POWER_BUDGET_DENY_TELEMETRY_INVALID);
    assert(result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert(result.active_output_mask == 0U);
    assert(result.event_publish_attempted);
    assert(result.event_published);

    svc_event_t event = {0};
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_POWER_BUDGET_SHED);
}

static void test_power_budget_shed_event_retries_after_bus_full(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);

    for (size_t event_index = 0U; event_index < SVC_EVENT_BUS_CAPACITY; ++event_index) {
        assert(svc_event_bus_publish(&bus, (svc_event_t){SVC_EVENT_OUTPUT_STATE_CHANGED, SVC_OUTPUT_OUT1, (uint32_t)event_index}));
    }
    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_power_budget_safety_result_t dropped_result = svc_system_safety_update_power_budget(
        &safety,
        &manager,
        &bus,
        12000U,
        false);

    assert(dropped_result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert(dropped_result.event_publish_attempted);
    assert(!dropped_result.event_published);
    assert(dropped_result.active_output_mask == 0U);

    svc_event_t event = {0};
    while (svc_event_bus_pop(&bus, &event)) {
    }

    const svc_system_power_budget_safety_result_t retry_result = svc_system_safety_update_power_budget(
        &safety,
        &manager,
        &bus,
        0U,
        false);

    assert(retry_result.disabled_output_mask == 0U);
    assert(retry_result.event_publish_attempted);
    assert(retry_result.event_published);
    assert(svc_event_bus_count(&bus) == 1U);
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_POWER_BUDGET_SHED);
    assert(event.value == 12000U);
}

static void test_thermal_cutoff_disables_active_outputs(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_telemetry_snapshot_t telemetry = thermal_telemetry_all_at(SVC_DEFAULT_THERMAL_CUTOFF_C, 100U);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_thermal_safety_result_t result = svc_system_safety_update_thermal_from_telemetry(
        &safety,
        &manager,
        &bus,
        &telemetry,
        100U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(result.thermal.action == SVC_THERMAL_ACTION_CUTOFF);
    assert(result.event_publish_attempted);
    assert(result.event_published);
    assert(result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert(result.active_output_mask == 0U);

    svc_event_t event = {0};
    assert(svc_event_bus_pop(&bus, &event));
    assert(event.type == SVC_EVENT_THERMAL_CUTOFF);
}

static void test_stale_thermal_telemetry_disables_active_outputs(void)
{
    svc_output_manager_t manager = initialized_output_manager();
    svc_system_safety_t safety = initialized_safety();
    svc_event_bus_t bus = {0};
    svc_event_bus_init(&bus);
    svc_telemetry_snapshot_t telemetry = thermal_telemetry_all_at(25, 100U);

    assert(svc_output_manager_request_enable(&manager, SVC_OUTPUT_OUT9, 1000U, true).status == SVC_OUTPUT_MANAGER_OK);

    const svc_system_thermal_safety_result_t result = svc_system_safety_update_thermal_from_telemetry(
        &safety,
        &manager,
        &bus,
        &telemetry,
        1200U,
        SVC_TELEMETRY_DEFAULT_STALE_MS);

    assert(result.thermal.action == SVC_THERMAL_ACTION_CUTOFF);
    assert(!result.thermal.telemetry_valid);
    assert(result.disabled_output_mask == mask_for(SVC_OUTPUT_OUT9));
    assert(result.active_output_mask == 0U);
}

int main(void)
{
    test_warn_publishes_event_without_disabling_outputs();
    test_cutoff_disables_active_outputs_and_publishes_event();
    test_invalid_telemetry_forces_cutoff();
    test_event_publish_failure_still_disables_outputs();
    test_recovery_does_not_reenable_outputs();
    test_uninitialized_safety_fails_safe();
    test_stale_telemetry_forces_cutoff();
    test_battery_cutoff_waits_for_shutdown_delay();
    test_large_battery_elapsed_interval_forces_cutoff_without_wrap();
    test_thermal_derate_publishes_event_without_disabling_outputs();
    test_thermal_cutoff_disables_active_outputs();
    test_stale_thermal_telemetry_disables_active_outputs();
    test_runtime_power_budget_sheds_active_loads();
    test_stale_power_budget_telemetry_disables_active_outputs();
    test_power_budget_shed_event_retries_after_bus_full();
    return 0;
}
