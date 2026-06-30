#include "battery_service.h"

#include <stddef.h>

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
}

svc_battery_result_t svc_battery_update(
    svc_battery_monitor_t *monitor,
    const svc_battery_config_t *config,
    uint16_t measured_mv,
    bool telemetry_valid)
{
    svc_battery_result_t result = {
        .action = SVC_BATTERY_ACTION_CUTOFF,
        .measured_mv = measured_mv,
        .telemetry_valid = telemetry_valid,
        .cutoff_latched = true
    };

    if (monitor == NULL || !svc_battery_config_is_valid(config)) {
        return result;
    }

    if (!telemetry_valid) {
        monitor->cutoff_latched = true;
        result.cutoff_latched = monitor->cutoff_latched;
        return result;
    }

    if (measured_mv <= config->cutoff_mv) {
        monitor->cutoff_latched = true;
        result.cutoff_latched = monitor->cutoff_latched;
        return result;
    }

    if (monitor->cutoff_latched) {
        if (measured_mv >= config->recovery_mv) {
            monitor->cutoff_latched = false;
        } else {
            result.cutoff_latched = monitor->cutoff_latched;
            return result;
        }
    }

    result.cutoff_latched = monitor->cutoff_latched;
    if (measured_mv < config->warn_mv) {
        result.action = SVC_BATTERY_ACTION_WARN;
        return result;
    }

    result.action = SVC_BATTERY_ACTION_ALLOW;
    return result;
}
