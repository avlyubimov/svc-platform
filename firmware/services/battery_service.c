#include "battery_service.h"

#include <stddef.h>

static uint16_t saturating_add_u16(uint16_t left, uint16_t right)
{
    const uint32_t sum = (uint32_t)left + right;
    return sum > UINT16_MAX ? UINT16_MAX : (uint16_t)sum;
}

bool svc_battery_config_is_valid(const svc_battery_config_t *config)
{
    if (config == NULL) {
        return false;
    }
    if (config->cutoff_mv == 0U || config->warn_mv == 0U || config->recovery_mv == 0U) {
        return false;
    }
    if (config->cutoff_mv >= config->warn_mv) {
        return false;
    }
    if (config->warn_mv > config->recovery_mv) {
        return false;
    }
    return config->shutdown_delay_s > 0U;
}

void svc_battery_monitor_init(svc_battery_monitor_t *monitor)
{
    if (monitor == NULL) {
        return;
    }
    monitor->cutoff_latched = false;
    monitor->undervoltage_duration_s = 0U;
}

svc_battery_result_t svc_battery_update(
    svc_battery_monitor_t *monitor,
    const svc_battery_config_t *config,
    uint16_t measured_mv,
    bool telemetry_valid)
{
    return svc_battery_update_elapsed_s(
        monitor,
        config,
        measured_mv,
        telemetry_valid,
        1U);
}

svc_battery_result_t svc_battery_update_elapsed_s(
    svc_battery_monitor_t *monitor,
    const svc_battery_config_t *config,
    uint16_t measured_mv,
    bool telemetry_valid,
    uint16_t elapsed_s)
{
    svc_battery_result_t result = {
        .action = SVC_BATTERY_ACTION_CUTOFF,
        .measured_mv = measured_mv,
        .telemetry_valid = telemetry_valid,
        .cutoff_latched = true,
        .undervoltage_duration_s = 0U
    };

    if (monitor == NULL || !svc_battery_config_is_valid(config)) {
        return result;
    }

    if (!telemetry_valid) {
        monitor->cutoff_latched = true;
        monitor->undervoltage_duration_s = 0U;
        result.cutoff_latched = monitor->cutoff_latched;
        result.undervoltage_duration_s = monitor->undervoltage_duration_s;
        return result;
    }

    if (measured_mv <= config->cutoff_mv) {
        const uint16_t counted_elapsed_s = elapsed_s == 0U ? 1U : elapsed_s;
        monitor->undervoltage_duration_s = saturating_add_u16(
            monitor->undervoltage_duration_s,
            counted_elapsed_s);
        if (monitor->undervoltage_duration_s >= config->shutdown_delay_s) {
            monitor->cutoff_latched = true;
        }
        result.cutoff_latched = monitor->cutoff_latched;
        result.undervoltage_duration_s = monitor->undervoltage_duration_s;
        if (!monitor->cutoff_latched) {
            result.action = SVC_BATTERY_ACTION_WARN;
        }
        return result;
    }

    monitor->undervoltage_duration_s = 0U;
    if (monitor->cutoff_latched) {
        if (measured_mv >= config->recovery_mv) {
            monitor->cutoff_latched = false;
        } else {
            result.cutoff_latched = monitor->cutoff_latched;
            result.undervoltage_duration_s = monitor->undervoltage_duration_s;
            return result;
        }
    }

    result.cutoff_latched = monitor->cutoff_latched;
    result.undervoltage_duration_s = monitor->undervoltage_duration_s;
    if (measured_mv < config->warn_mv) {
        result.action = SVC_BATTERY_ACTION_WARN;
        return result;
    }

    result.action = SVC_BATTERY_ACTION_ALLOW;
    return result;
}
