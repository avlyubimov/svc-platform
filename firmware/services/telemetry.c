#include "telemetry.h"

#include <stddef.h>

static bool output_id_is_valid(svc_output_id_t output_id)
{
    return output_id >= SVC_OUTPUT_OUT1 && output_id <= SVC_OUTPUT_OUT10;
}

static bool timestamp_is_fresh(uint32_t updated_ms, uint32_t now_ms, uint32_t stale_after_ms)
{
    return (now_ms - updated_ms) <= stale_after_ms;
}

void svc_telemetry_snapshot_init(svc_telemetry_snapshot_t *snapshot)
{
    if (snapshot == NULL) {
        return;
    }

    snapshot->battery_mv = 0U;
    snapshot->total_current_ma = 0U;
    snapshot->battery_updated_ms = 0U;
    snapshot->total_current_updated_ms = 0U;
    snapshot->battery_valid = false;
    snapshot->total_current_valid = false;

    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        snapshot->output_current_ma[output_index] = 0U;
        snapshot->output_current_updated_ms[output_index] = 0U;
        snapshot->output_current_valid[output_index] = false;
    }
}

void svc_telemetry_update_battery(
    svc_telemetry_snapshot_t *snapshot,
    uint16_t battery_mv,
    bool valid,
    uint32_t now_ms)
{
    if (snapshot == NULL) {
        return;
    }

    snapshot->battery_mv = battery_mv;
    snapshot->battery_valid = valid;
    snapshot->battery_updated_ms = now_ms;
}

void svc_telemetry_update_total_current(
    svc_telemetry_snapshot_t *snapshot,
    uint32_t total_current_ma,
    bool valid,
    uint32_t now_ms)
{
    if (snapshot == NULL) {
        return;
    }

    snapshot->total_current_ma = total_current_ma;
    snapshot->total_current_valid = valid;
    snapshot->total_current_updated_ms = now_ms;
}

bool svc_telemetry_update_output_current(
    svc_telemetry_snapshot_t *snapshot,
    svc_output_id_t output_id,
    uint32_t output_current_ma,
    bool valid,
    uint32_t now_ms)
{
    if (snapshot == NULL || !output_id_is_valid(output_id)) {
        return false;
    }

    const uint8_t output_index = (uint8_t)output_id;
    snapshot->output_current_ma[output_index] = output_current_ma;
    snapshot->output_current_valid[output_index] = valid;
    snapshot->output_current_updated_ms[output_index] = now_ms;
    return true;
}

bool svc_telemetry_battery_is_valid(
    const svc_telemetry_snapshot_t *snapshot,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    return snapshot != NULL &&
           snapshot->battery_valid &&
           timestamp_is_fresh(snapshot->battery_updated_ms, now_ms, stale_after_ms);
}

bool svc_telemetry_total_current_is_valid(
    const svc_telemetry_snapshot_t *snapshot,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    return snapshot != NULL &&
           snapshot->total_current_valid &&
           timestamp_is_fresh(snapshot->total_current_updated_ms, now_ms, stale_after_ms);
}

bool svc_telemetry_output_current_is_valid(
    const svc_telemetry_snapshot_t *snapshot,
    svc_output_id_t output_id,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    if (snapshot == NULL || !output_id_is_valid(output_id)) {
        return false;
    }

    const uint8_t output_index = (uint8_t)output_id;
    return snapshot->output_current_valid[output_index] &&
           timestamp_is_fresh(snapshot->output_current_updated_ms[output_index], now_ms, stale_after_ms);
}

svc_telemetry_power_budget_input_t svc_telemetry_power_budget_input(
    const svc_telemetry_snapshot_t *snapshot,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    if (snapshot == NULL) {
        return (svc_telemetry_power_budget_input_t){0U, false};
    }

    return (svc_telemetry_power_budget_input_t){
        .measured_total_current_ma = snapshot->total_current_ma,
        .telemetry_valid = svc_telemetry_total_current_is_valid(snapshot, now_ms, stale_after_ms)
    };
}

svc_telemetry_battery_input_t svc_telemetry_battery_input(
    const svc_telemetry_snapshot_t *snapshot,
    uint32_t now_ms,
    uint32_t stale_after_ms)
{
    if (snapshot == NULL) {
        return (svc_telemetry_battery_input_t){0U, false};
    }

    return (svc_telemetry_battery_input_t){
        .measured_battery_mv = snapshot->battery_mv,
        .telemetry_valid = svc_telemetry_battery_is_valid(snapshot, now_ms, stale_after_ms)
    };
}
