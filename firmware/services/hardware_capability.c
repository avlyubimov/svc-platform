#include "hardware_capability.h"

static svc_hardware_capability_result_t make_result(
    svc_hardware_capability_status_t status,
    size_t output_index)
{
    return (svc_hardware_capability_result_t){
        .status = status,
        .output_index = output_index
    };
}

static bool output_capability_limits_are_valid(const svc_output_capability_t *output)
{
    return output->max_fuse_a > 0U &&
           output->max_current_ma > 0U &&
           (uint32_t)output->max_current_ma <= (uint32_t)output->max_fuse_a * 1000U;
}

svc_hardware_capability_result_t svc_hardware_capability_validate(
    const svc_hardware_capability_t *capability)
{
    if (capability == NULL) {
        return make_result(
            SVC_HARDWARE_CAPABILITY_INVALID_NULL,
            SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
    }
    if (capability->output_count != SVC_OUTPUT_COUNT) {
        return make_result(
            SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_COUNT,
            SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
    }
    if (capability->main_fuse_limit_ma == 0U ||
        capability->board_continuous_limit_ma == 0U ||
        capability->default_total_current_limit_ma == 0U ||
        capability->board_continuous_limit_ma > capability->main_fuse_limit_ma ||
        capability->default_total_current_limit_ma > capability->board_continuous_limit_ma) {
        return make_result(
            SVC_HARDWARE_CAPABILITY_INVALID_POWER_BUDGET,
            SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
    }
    if (!capability->outputs_default_off || !capability->configuration_required_for_roles) {
        return make_result(
            SVC_HARDWARE_CAPABILITY_INVALID_SAFE_DEFAULT,
            SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
    }
    if (!capability->can1_read_only_default ||
        !capability->can1_tx_route_dnp_open ||
        !capability->can1_tx_requires_future_adr ||
        !capability->can1_hardware_action_required_for_tx) {
        return make_result(
            SVC_HARDWARE_CAPABILITY_INVALID_CAN1_POLICY,
            SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
    }

    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        const svc_output_capability_t *output = &capability->outputs[output_index];
        if (output->id != (svc_output_id_t)output_index) {
            return make_result(
                SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_ID,
                output_index);
        }
        if (!output->safe_default_off) {
            return make_result(
                SVC_HARDWARE_CAPABILITY_INVALID_SAFE_DEFAULT,
                output_index);
        }
        if (!output_capability_limits_are_valid(output)) {
            return make_result(
                SVC_HARDWARE_CAPABILITY_INVALID_OUTPUT_LIMIT,
                output_index);
        }
    }

    return make_result(
        SVC_HARDWARE_CAPABILITY_OK,
        SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
}

svc_hardware_capability_result_t svc_hardware_capability_validate_config(
    const svc_hardware_capability_t *capability,
    const svc_device_config_t *config)
{
    const svc_hardware_capability_result_t capability_result =
        svc_hardware_capability_validate(capability);
    if (capability_result.status != SVC_HARDWARE_CAPABILITY_OK) {
        return capability_result;
    }
    if (config == NULL) {
        return make_result(
            SVC_HARDWARE_CAPABILITY_INVALID_CONFIG_NULL,
            SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
    }
    if (config->power_budget.total_current_limit_ma > capability->default_total_current_limit_ma ||
        config->power_budget.total_current_limit_ma > capability->board_continuous_limit_ma) {
        return make_result(
            SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_POWER_BUDGET,
            SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
    }

    for (size_t output_index = 0U; output_index < SVC_OUTPUT_COUNT; ++output_index) {
        const svc_output_config_t *configured_output = &config->outputs[output_index];
        const svc_output_capability_t *capable_output = &capability->outputs[output_index];
        if (configured_output->id != capable_output->id) {
            return make_result(
                SVC_HARDWARE_CAPABILITY_CONFIG_OUTPUT_MISMATCH,
                output_index);
        }
        if (configured_output->fuse_limit_a > capable_output->max_fuse_a ||
            configured_output->current_limit_ma > capable_output->max_current_ma) {
            return make_result(
                SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_OUTPUT_CAPABILITY,
                output_index);
        }
        if (configured_output->pwm_allowed && !capable_output->pwm_supported) {
            return make_result(
                SVC_HARDWARE_CAPABILITY_CONFIG_REQUIRES_PWM,
                output_index);
        }
    }

    return make_result(
        SVC_HARDWARE_CAPABILITY_OK,
        SVC_HARDWARE_CAPABILITY_OUTPUT_INDEX_NONE);
}
