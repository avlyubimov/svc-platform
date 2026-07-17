#include "config_store.h"

#include <stddef.h>

#include "config_validator.h"

#define SVC_CONFIG_STORE_FNV_OFFSET 2166136261U
#define SVC_CONFIG_STORE_FNV_PRIME 16777619U

static uint32_t mix_byte(uint32_t checksum, uint8_t value)
{
    return (checksum ^ value) * SVC_CONFIG_STORE_FNV_PRIME;
}

static uint32_t mix_u32(uint32_t checksum, uint32_t value)
{
    checksum = mix_byte(checksum, (uint8_t)(value & 0xFFU));
    checksum = mix_byte(checksum, (uint8_t)((value >> 8U) & 0xFFU));
    checksum = mix_byte(checksum, (uint8_t)((value >> 16U) & 0xFFU));
    return mix_byte(checksum, (uint8_t)((value >> 24U) & 0xFFU));
}

static uint32_t mix_i32(uint32_t checksum, int32_t value)
{
    return mix_u32(checksum, (uint32_t)value);
}

static uint32_t config_checksum(const svc_device_config_t *config, uint32_t sequence)
{
    uint32_t checksum = SVC_CONFIG_STORE_FNV_OFFSET;
    checksum = mix_u32(checksum, SVC_CONFIG_STORE_MAGIC);
    checksum = mix_u32(checksum, SVC_CONFIG_STORE_FORMAT_VERSION);
    checksum = mix_u32(checksum, sequence);

    checksum = mix_u32(checksum, config->battery.warn_mv);
    checksum = mix_u32(checksum, config->battery.cutoff_mv);
    checksum = mix_u32(checksum, config->battery.recovery_mv);
    checksum = mix_u32(checksum, config->battery.shutdown_delay_s);

    for (size_t zone_index = 0U; zone_index < SVC_THERMAL_ZONE_COUNT; ++zone_index) {
        checksum = mix_i32(checksum, config->thermal[zone_index].warn_c);
        checksum = mix_i32(checksum, config->thermal[zone_index].cutoff_c);
        checksum = mix_i32(checksum, config->thermal[zone_index].recovery_c);
    }

    checksum = mix_u32(checksum, config->power_budget.total_current_limit_ma);
    for (size_t priority_index = 0U; priority_index < 3U; ++priority_index) {
        checksum = mix_u32(checksum, (uint32_t)config->power_budget.shed_order[priority_index]);
    }

    checksum = mix_u32(checksum, config->telemetry.total_current.shunt_microohm);
    checksum = mix_u32(checksum, config->telemetry.total_current.monitor_range_uv);
    checksum = mix_i32(checksum, config->telemetry.total_current.zero_offset_ma);
    checksum = mix_u32(checksum, config->telemetry.total_current.gain_ppm);
    checksum = mix_u32(checksum, config->telemetry.total_current.stale_timeout_ms);
    checksum = mix_u32(checksum, config->telemetry.total_current.plausible_max_ma);
    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        const svc_output_current_telemetry_config_t *output_current =
            &config->telemetry.output_current[output_index];
        checksum = mix_u32(checksum, output_current->range_ma);
        checksum = mix_i32(checksum, output_current->zero_offset_ma);
        checksum = mix_u32(checksum, output_current->gain_ppm);
        checksum = mix_u32(checksum, output_current->stale_timeout_ms);
        checksum = mix_u32(checksum, output_current->plausible_max_ma);
    }

    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        const svc_output_config_t *output = &config->outputs[output_index];
        checksum = mix_u32(checksum, (uint32_t)output->id);
        checksum = mix_u32(checksum, (uint32_t)output->role);
        checksum = mix_u32(checksum, output->fuse_limit_a);
        checksum = mix_u32(checksum, output->current_limit_ma);
        checksum = mix_u32(checksum, output->pwm_allowed ? 1U : 0U);
        checksum = mix_u32(checksum, (uint32_t)output->priority);
    }

    return checksum;
}

svc_config_store_status_t svc_config_store_build_record(
    const svc_device_config_t *config,
    uint32_t sequence,
    svc_config_record_t *record)
{
    if (config == NULL || record == NULL) {
        return SVC_CONFIG_STORE_INVALID_NULL;
    }
    if (svc_config_validate_device(config).status != SVC_CONFIG_OK) {
        *record = (svc_config_record_t){0};
        return SVC_CONFIG_STORE_INVALID_CONFIG;
    }

    *record = (svc_config_record_t){
        .magic = SVC_CONFIG_STORE_MAGIC,
        .format_version = SVC_CONFIG_STORE_FORMAT_VERSION,
        .reserved = 0U,
        .sequence = sequence,
        .config = *config,
        .checksum = config_checksum(config, sequence)
    };
    return SVC_CONFIG_STORE_OK;
}

svc_config_store_status_t svc_config_store_validate_record(
    const svc_config_record_t *record)
{
    if (record == NULL) {
        return SVC_CONFIG_STORE_INVALID_NULL;
    }
    if (record->magic != SVC_CONFIG_STORE_MAGIC) {
        return SVC_CONFIG_STORE_INVALID_MAGIC;
    }
    if (record->format_version != SVC_CONFIG_STORE_FORMAT_VERSION) {
        return SVC_CONFIG_STORE_INVALID_VERSION;
    }
    if (record->checksum != config_checksum(&record->config, record->sequence)) {
        return SVC_CONFIG_STORE_INVALID_CHECKSUM;
    }
    if (svc_config_validate_device(&record->config).status != SVC_CONFIG_OK) {
        return SVC_CONFIG_STORE_INVALID_CONFIG;
    }
    return SVC_CONFIG_STORE_OK;
}

static bool record_is_valid(
    const svc_config_record_t *record,
    svc_config_store_status_t *status)
{
    *status = svc_config_store_validate_record(record);
    return *status == SVC_CONFIG_STORE_OK;
}

static svc_config_store_load_result_t make_load_result(
    svc_config_store_load_status_t status,
    svc_config_store_source_t source,
    svc_config_store_status_t slot_a_status,
    svc_config_store_status_t slot_b_status,
    uint32_t sequence)
{
    return (svc_config_store_load_result_t){
        .status = status,
        .source = source,
        .slot_a_status = slot_a_status,
        .slot_b_status = slot_b_status,
        .sequence = sequence
    };
}

svc_config_store_load_result_t svc_config_store_load_latest(
    const svc_config_record_t *slot_a,
    const svc_config_record_t *slot_b,
    const svc_device_config_t *fallback_config,
    svc_device_config_t *loaded_config)
{
    if (loaded_config == NULL) {
        return make_load_result(
            SVC_CONFIG_STORE_LOAD_INVALID_ARGUMENT,
            SVC_CONFIG_STORE_SOURCE_NONE,
            SVC_CONFIG_STORE_INVALID_NULL,
            SVC_CONFIG_STORE_INVALID_NULL,
            0U);
    }

    svc_config_store_status_t slot_a_status = SVC_CONFIG_STORE_INVALID_NULL;
    svc_config_store_status_t slot_b_status = SVC_CONFIG_STORE_INVALID_NULL;
    const bool slot_a_valid = record_is_valid(slot_a, &slot_a_status);
    const bool slot_b_valid = record_is_valid(slot_b, &slot_b_status);

    if (slot_a_valid && (!slot_b_valid || slot_a->sequence >= slot_b->sequence)) {
        *loaded_config = slot_a->config;
        return make_load_result(
            SVC_CONFIG_STORE_LOAD_OK,
            SVC_CONFIG_STORE_SOURCE_SLOT_A,
            slot_a_status,
            slot_b_status,
            slot_a->sequence);
    }
    if (slot_b_valid) {
        *loaded_config = slot_b->config;
        return make_load_result(
            SVC_CONFIG_STORE_LOAD_OK,
            SVC_CONFIG_STORE_SOURCE_SLOT_B,
            slot_a_status,
            slot_b_status,
            slot_b->sequence);
    }
    if (fallback_config != NULL &&
        svc_config_validate_device(fallback_config).status == SVC_CONFIG_OK) {
        *loaded_config = *fallback_config;
        return make_load_result(
            SVC_CONFIG_STORE_LOAD_FALLBACK_DEFAULT,
            SVC_CONFIG_STORE_SOURCE_FALLBACK_DEFAULT,
            slot_a_status,
            slot_b_status,
            0U);
    }

    *loaded_config = (svc_device_config_t){0};
    return make_load_result(
        SVC_CONFIG_STORE_LOAD_NO_VALID_CONFIG,
        SVC_CONFIG_STORE_SOURCE_NONE,
        slot_a_status,
        slot_b_status,
        0U);
}
