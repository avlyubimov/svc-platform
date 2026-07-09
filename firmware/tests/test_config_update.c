#include <assert.h>
#include <stddef.h>

#include "config_update.h"
#include "pb100_capability.h"
#include "svc_config.h"

static void test_prepare_record_accepts_default_config(void)
{
    svc_config_record_t record = {0};

    const svc_config_update_result_t result = svc_config_update_prepare_record(
        &svc_default_config,
        &svc_pb100_hardware_capability,
        10U,
        &record);

    assert(result.status == SVC_CONFIG_UPDATE_OK);
    assert(result.acceptance.status == SVC_CONFIG_ACCEPTANCE_OK);
    assert(result.store_status == SVC_CONFIG_STORE_OK);
    assert(record.sequence == 10U);
    assert(svc_config_store_validate_record(&record) == SVC_CONFIG_STORE_OK);
}

static void test_prepare_record_rejects_config_exceeding_hardware(void)
{
    svc_device_config_t config = svc_default_config;
    config.outputs[0].current_limit_ma = 13000U;
    svc_config_record_t record = {0};

    const svc_config_update_result_t result = svc_config_update_prepare_record(
        &config,
        &svc_pb100_hardware_capability,
        11U,
        &record);

    assert(result.status == SVC_CONFIG_UPDATE_REJECTED);
    assert(result.acceptance.status == SVC_CONFIG_ACCEPTANCE_CONFIG_EXCEEDS_HARDWARE);
    assert(result.acceptance.hardware_status == SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_OUTPUT_CAPABILITY);
    assert(result.store_status == SVC_CONFIG_STORE_INVALID_CONFIG);
    assert(record.magic == 0U);
}

static void test_prepare_record_rejects_invalid_hardware_capability(void)
{
    svc_hardware_capability_t capability = svc_pb100_hardware_capability;
    capability.can1_hardware_action_required_for_tx = false;
    svc_config_record_t record = {0};

    const svc_config_update_result_t result = svc_config_update_prepare_record(
        &svc_default_config,
        &capability,
        12U,
        &record);

    assert(result.status == SVC_CONFIG_UPDATE_REJECTED);
    assert(result.acceptance.status == SVC_CONFIG_ACCEPTANCE_INVALID_HARDWARE_CAPABILITY);
    assert(result.acceptance.hardware_status == SVC_HARDWARE_CAPABILITY_INVALID_CAN1_POLICY);
    assert(record.magic == 0U);
}

static void test_prepare_record_handles_null_record(void)
{
    const svc_config_update_result_t result = svc_config_update_prepare_record(
        &svc_default_config,
        &svc_pb100_hardware_capability,
        13U,
        NULL);

    assert(result.status == SVC_CONFIG_UPDATE_INVALID_ARGUMENT);
    assert(result.store_status == SVC_CONFIG_STORE_INVALID_NULL);
}

int main(void)
{
    test_prepare_record_accepts_default_config();
    test_prepare_record_rejects_config_exceeding_hardware();
    test_prepare_record_rejects_invalid_hardware_capability();
    test_prepare_record_handles_null_record();
    return 0;
}
