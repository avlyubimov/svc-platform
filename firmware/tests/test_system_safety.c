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

    const svc_system_safety_result_t result = svc_system_safety_update_battery(
        &safety,
        &manager,
        &bus,
        11700U,
        true);

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

    const svc_system_safety_result_t result = svc_system_safety_update_battery(
        &safety,
        &manager,
        &bus,
        11700U,
        true);

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
    assert(svc_system_safety_update_battery(&safety, &manager, &bus, 11700U, true).battery.action == SVC_BATTERY_ACTION_CUTOFF);

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

int main(void)
{
    test_warn_publishes_event_without_disabling_outputs();
    test_cutoff_disables_active_outputs_and_publishes_event();
    test_invalid_telemetry_forces_cutoff();
    test_event_publish_failure_still_disables_outputs();
    test_recovery_does_not_reenable_outputs();
    test_uninitialized_safety_fails_safe();
    test_stale_telemetry_forces_cutoff();
    return 0;
}
