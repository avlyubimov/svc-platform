#include "thermal_service.h"

#include <stddef.h>

static bool thermal_zone_is_valid(svc_thermal_zone_t zone)
{
    return zone >= SVC_THERMAL_ZONE_PCB && zone <= SVC_THERMAL_ZONE_PWR_B;
}

static uint8_t zone_mask(svc_thermal_zone_t zone)
{
    return (uint8_t)(1U << (uint8_t)zone);
}

static svc_thermal_result_t make_result(
    svc_thermal_action_t action,
    uint8_t derate_zone_mask,
    uint8_t cutoff_zone_mask,
    bool telemetry_valid)
{
    return (svc_thermal_result_t){
        .action = action,
        .derate_zone_mask = derate_zone_mask,
        .cutoff_zone_mask = cutoff_zone_mask,
        .telemetry_valid = telemetry_valid
    };
}

static svc_thermal_action_t worst_action(svc_thermal_action_t left, svc_thermal_action_t right)
{
    return left > right ? left : right;
}

bool svc_thermal_zone_config_is_valid(const svc_thermal_zone_config_t *config)
{
    if (config == NULL) {
        return false;
    }
    return config->recovery_c < config->warn_c &&
           config->warn_c < config->cutoff_c;
}

bool svc_thermal_config_is_valid(const svc_device_config_t *config)
{
    if (config == NULL) {
        return false;
    }
    for (size_t zone_index = 0U; zone_index < SVC_THERMAL_ZONE_COUNT; ++zone_index) {
        if (!svc_thermal_zone_config_is_valid(&config->thermal[zone_index])) {
            return false;
        }
    }
    return true;
}

void svc_thermal_monitor_init(svc_thermal_monitor_t *monitor)
{
    if (monitor == NULL) {
        return;
    }
    monitor->cutoff_latched_mask = 0U;
}

svc_thermal_result_t svc_thermal_update_zone(
    svc_thermal_monitor_t *monitor,
    const svc_thermal_zone_config_t *config,
    svc_thermal_zone_t zone,
    int16_t measured_c,
    bool telemetry_valid)
{
    if (monitor == NULL || !svc_thermal_zone_config_is_valid(config) || !thermal_zone_is_valid(zone)) {
        return make_result(SVC_THERMAL_ACTION_CUTOFF, 0U, thermal_zone_is_valid(zone) ? zone_mask(zone) : 0U, false);
    }

    const uint8_t mask = zone_mask(zone);
    if (!telemetry_valid) {
        monitor->cutoff_latched_mask |= mask;
        return make_result(SVC_THERMAL_ACTION_CUTOFF, 0U, mask, false);
    }

    if (measured_c >= config->cutoff_c) {
        monitor->cutoff_latched_mask |= mask;
        return make_result(SVC_THERMAL_ACTION_CUTOFF, 0U, mask, true);
    }

    if ((monitor->cutoff_latched_mask & mask) != 0U) {
        if (measured_c <= config->recovery_c) {
            monitor->cutoff_latched_mask &= (uint8_t)~mask;
        } else {
            return make_result(SVC_THERMAL_ACTION_CUTOFF, 0U, mask, true);
        }
    }

    if (measured_c >= config->warn_c) {
        return make_result(SVC_THERMAL_ACTION_DERATE, mask, 0U, true);
    }

    return make_result(SVC_THERMAL_ACTION_ALLOW, 0U, 0U, true);
}

svc_thermal_result_t svc_thermal_update_from_telemetry(
    svc_thermal_monitor_t *monitor,
    const svc_device_config_t *config,
    const svc_telemetry_snapshot_t *telemetry,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    if (monitor == NULL || !svc_thermal_config_is_valid(config)) {
        return make_result(SVC_THERMAL_ACTION_CUTOFF, 0U, 0U, false);
    }

    svc_thermal_result_t aggregate = make_result(SVC_THERMAL_ACTION_ALLOW, 0U, 0U, true);
    for (size_t zone_index = 0U; zone_index < SVC_THERMAL_ZONE_COUNT; ++zone_index) {
        const svc_thermal_zone_t zone = (svc_thermal_zone_t)zone_index;
        const svc_telemetry_thermal_input_t input = svc_telemetry_thermal_input(
            telemetry,
            zone,
            now_ms,
            stale_after_ms);
        const svc_thermal_result_t zone_result = svc_thermal_update_zone(
            monitor,
            &config->thermal[zone_index],
            zone,
            input.measured_temperature_c,
            input.telemetry_valid);

        aggregate.action = worst_action(aggregate.action, zone_result.action);
        aggregate.derate_zone_mask |= zone_result.derate_zone_mask;
        aggregate.cutoff_zone_mask |= zone_result.cutoff_zone_mask;
        aggregate.telemetry_valid = aggregate.telemetry_valid && zone_result.telemetry_valid;
    }

    return aggregate;
}
