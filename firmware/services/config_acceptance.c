#include "config_acceptance.h"

static bool hardware_status_is_capability_fault(svc_hardware_capability_status_t status)
{
    return status == SVC_HARDWARE_CAPABILITY_INVALID_NULL ||
           status == SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_COUNT ||
           status == SVC_HARDWARE_CAPABILITY_INVALID_POWER_BUDGET ||
           status == SVC_HARDWARE_CAPABILITY_INVALID_SAFE_DEFAULT ||
           status == SVC_HARDWARE_CAPABILITY_INVALID_CAN1_POLICY ||
           status == SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_ID ||
           status == SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_LIMIT;
}

static svc_config_acceptance_result_t make_result(
    svc_config_acceptance_status_t status,
    svc_config_status_t config_status,
    svc_hardware_capability_status_t hardware_status,
    size_t output_index)
{
    return (svc_config_acceptance_result_t){
        .status = status,
        .config_status = config_status,
        .hardware_status = hardware_status,
        .output_index = output_index
    };
}

svc_config_acceptance_result_t svc_config_accept_for_hardware(
    const svc_device_config_t *config,
    const svc_hardware_capability_t *capability)
{
    const svc_config_validation_result_t config_result =
        svc_config_validate_device(config);
    if (config_result.status != SVC_CONFIG_OK) {
        return make_result(
            SVC_CONFIG_ACCEPTANCE_INVALID_DEVICE_CONFIG,
            config_result.status,
            SVC_HARDWARE_CAPABILITY_OK,
            config_result.output_index);
    }

    const svc_hardware_capability_result_t hardware_result =
        svc_hardware_capability_validate_config(capability, config);
    if (hardware_result.status == SVC_HARDWARE_CAPABILITY_OK) {
        return make_result(
            SVC_CONFIG_ACCEPTANCE_OK,
            SVC_CONFIG_OK,
            SVC_HARDWARE_CAPABILITY_OK,
            SVC_CONFIG_OUTPUT_INDEX_NONE);
    }

    return make_result(
        hardware_status_is_capability_fault(hardware_result.status)
            ? SVC_CONFIG_ACCEPTANCE_INVALID_HARDWARE_CAPABILITY
            : SVC_CONFIG_ACCEPTANCE_CONFIG_EXCEEDS_HARDWARE,
        SVC_CONFIG_OK,
        hardware_result.status,
        hardware_result.output_index);
}
