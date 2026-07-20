#include <assert.h>
#include <stddef.h>

#include "config_store.h"
#include "svc_config.h"

static void test_builds_and_validates_config_record(void)
{
    svc_config_record_t record = {0};

    assert(svc_config_store_build_record(&svc_default_config, 7U, &record) == SVC_CONFIG_STORE_OK);
    assert(record.magic == SVC_CONFIG_STORE_MAGIC);
    assert(record.format_version == SVC_CONFIG_STORE_FORMAT_VERSION);
    assert(record.sequence == 7U);
    assert(svc_config_store_validate_record(&record) == SVC_CONFIG_STORE_OK);
}

static void test_rejects_checksum_corruption(void)
{
    svc_config_record_t record = {0};
    assert(svc_config_store_build_record(&svc_default_config, 1U, &record) == SVC_CONFIG_STORE_OK);

    record.config.outputs[0].current_limit_ma += 1U;

    assert(svc_config_store_validate_record(&record) == SVC_CONFIG_STORE_INVALID_CHECKSUM);
}

static void test_rejects_reserved_field_corruption(void)
{
    svc_config_record_t record = {0};
    assert(svc_config_store_build_record(&svc_default_config, 1U, &record) == SVC_CONFIG_STORE_OK);

    record.reserved = 1U;

    assert(svc_config_store_validate_record(&record) == SVC_CONFIG_STORE_INVALID_RESERVED);
}

static void test_rejects_telemetry_checksum_corruption(void)
{
    svc_config_record_t record = {0};
    assert(svc_config_store_build_record(&svc_default_config, 1U, &record) == SVC_CONFIG_STORE_OK);

    record.config.telemetry.thermal[SVC_THERMAL_ZONE_PCB].plausible_max_c += 1;

    assert(svc_config_store_validate_record(&record) == SVC_CONFIG_STORE_INVALID_CHECKSUM);
}

static void test_selects_newest_valid_slot(void)
{
    svc_config_record_t older_record = {0};
    svc_config_record_t newer_record = {0};
    svc_device_config_t newer_config = svc_default_config;
    newer_config.power_budget.total_current_limit_ma = 39000U;

    assert(svc_config_store_build_record(&svc_default_config, 3U, &older_record) == SVC_CONFIG_STORE_OK);
    assert(svc_config_store_build_record(&newer_config, 4U, &newer_record) == SVC_CONFIG_STORE_OK);

    svc_device_config_t loaded_config = {0};
    const svc_config_store_load_result_t result = svc_config_store_load_latest(
        &older_record,
        &newer_record,
        &svc_default_config,
        &loaded_config);

    assert(result.status == SVC_CONFIG_STORE_LOAD_OK);
    assert(result.source == SVC_CONFIG_STORE_SOURCE_SLOT_B);
    assert(result.sequence == 4U);
    assert(loaded_config.power_budget.total_current_limit_ma == 39000U);
}

static void test_fallback_default_when_slots_are_invalid(void)
{
    svc_config_record_t bad_record = {0};
    bad_record.magic = SVC_CONFIG_STORE_MAGIC;

    svc_device_config_t loaded_config = {0};
    const svc_config_store_load_result_t result = svc_config_store_load_latest(
        &bad_record,
        NULL,
        &svc_default_config,
        &loaded_config);

    assert(result.status == SVC_CONFIG_STORE_LOAD_FALLBACK_DEFAULT);
    assert(result.source == SVC_CONFIG_STORE_SOURCE_FALLBACK_DEFAULT);
    assert(loaded_config.power_budget.total_current_limit_ma == SVC_DEFAULT_TOTAL_CURRENT_LIMIT_MA);
}

static void test_persisted_config_survives_default_change(void)
{
    svc_device_config_t user_config = svc_default_config;
    user_config.battery.warn_mv = 12100U;
    user_config.battery.recovery_mv = 12500U;
    svc_config_record_t user_record = {0};
    assert(svc_config_store_build_record(&user_config, 9U, &user_record) == SVC_CONFIG_STORE_OK);

    svc_device_config_t new_firmware_default = svc_default_config;
    new_firmware_default.battery.warn_mv = 12200U;
    new_firmware_default.battery.recovery_mv = 12600U;

    svc_device_config_t loaded_config = {0};
    const svc_config_store_load_result_t result = svc_config_store_load_latest(
        &user_record,
        NULL,
        &new_firmware_default,
        &loaded_config);

    assert(result.status == SVC_CONFIG_STORE_LOAD_OK);
    assert(result.source == SVC_CONFIG_STORE_SOURCE_SLOT_A);
    assert(loaded_config.battery.warn_mv == 12100U);
    assert(loaded_config.battery.recovery_mv == 12500U);
}

static void test_no_valid_config_when_slots_and_fallback_invalid(void)
{
    svc_device_config_t invalid_fallback = svc_default_config;
    invalid_fallback.outputs[0].role = OUT_ROLE_COUNT;
    svc_device_config_t loaded_config = svc_default_config;

    const svc_config_store_load_result_t result = svc_config_store_load_latest(
        NULL,
        NULL,
        &invalid_fallback,
        &loaded_config);

    assert(result.status == SVC_CONFIG_STORE_LOAD_NO_VALID_CONFIG);
    assert(result.source == SVC_CONFIG_STORE_SOURCE_NONE);
    assert(loaded_config.power_budget.total_current_limit_ma == 0U);
}

int main(void)
{
    test_builds_and_validates_config_record();
    test_rejects_checksum_corruption();
    test_rejects_reserved_field_corruption();
    test_rejects_telemetry_checksum_corruption();
    test_selects_newest_valid_slot();
    test_fallback_default_when_slots_are_invalid();
    test_persisted_config_survives_default_change();
    test_no_valid_config_when_slots_and_fallback_invalid();
    return 0;
}
