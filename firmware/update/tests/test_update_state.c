#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "update_state.h"

static svc_ota_admission_t allowed_admission(void)
{
    return (svc_ota_admission_t){
        .speed_centi_kph = 0,
        .speed_valid = true,
        .speed_stale = false,
        .engine_running = false,
        .engine_state_valid = true,
        .engine_state_stale = false,
        .outputs_all_off = true,
        .no_critical_fault = true,
        .battery_mv = 12600U,
        .battery_min_mv = 11800U,
        .battery_max_mv = 14800U,
        .battery_valid = true,
        .battery_stale = false,
        .board_temperature_c = 40,
        .board_temperature_min_c = -20,
        .board_temperature_max_c = 85,
        .board_temperature_valid = true,
        .board_temperature_stale = false,
        .link_stable = true,
        .file_complete = true,
        .sha256_valid = true,
        .signature_valid = true,
        .hardware_compatible = true,
        .protocol_compatible = true,
        .bootloader_compatible = true
    };
}

static void test_rejects_protocol_and_hardware_mismatch(void)
{
    svc_update_transfer_t transfer;
    svc_update_transfer_init(&transfer);

    assert(!svc_update_begin(
        &transfer,
        SVC_UPDATE_TARGET_STM32_MAIN,
        SVC_UPDATE_HW_LB100_REV1,
        2U,
        1U,
        10U));
    assert(!svc_update_begin(
        &transfer,
        SVC_UPDATE_TARGET_STM32_MAIN,
        SVC_UPDATE_HW_UNSUPPORTED,
        SVC_UPDATE_PROTOCOL_V1,
        1U,
        10U));
}

static void test_chunk_retry_corruption_interrupt_and_resume(void)
{
    const uint8_t first_payload[] = {1U, 2U, 3U};
    const uint8_t second_payload[] = {4U, 5U};
    svc_update_transfer_t transfer;
    svc_update_transfer_init(&transfer);
    assert(svc_update_begin(
        &transfer,
        SVC_UPDATE_TARGET_STM32_MAIN,
        SVC_UPDATE_HW_LB100_REV1,
        SVC_UPDATE_PROTOCOL_V1,
        77U,
        5U));

    assert(svc_update_accept_chunk(
        &transfer,
        77U,
        0U,
        0U,
        first_payload,
        sizeof(first_payload),
        0U) == SVC_UPDATE_CHUNK_CORRUPT);
    assert(transfer.committed_offset == 0U);

    const uint32_t first_crc = svc_update_crc32(first_payload, sizeof(first_payload));
    assert(svc_update_accept_chunk(
        &transfer,
        77U,
        1U,
        0U,
        first_payload,
        sizeof(first_payload),
        first_crc) == SVC_UPDATE_CHUNK_RETRY);
    assert(svc_update_accept_chunk(
        &transfer,
        77U,
        0U,
        0U,
        first_payload,
        sizeof(first_payload),
        first_crc) == SVC_UPDATE_CHUNK_ACCEPTED);
    assert(svc_update_accept_chunk(
        &transfer,
        77U,
        0U,
        0U,
        first_payload,
        sizeof(first_payload),
        first_crc) == SVC_UPDATE_CHUNK_DUPLICATE);
    assert(transfer.committed_offset == 3U);

    assert(svc_update_interrupt(&transfer));
    assert(!svc_update_resume(
        &transfer,
        SVC_UPDATE_TARGET_E73_RADIO,
        SVC_UPDATE_HW_LB100_REV1,
        SVC_UPDATE_PROTOCOL_V1,
        77U,
        5U));
    assert(svc_update_resume(
        &transfer,
        SVC_UPDATE_TARGET_STM32_MAIN,
        SVC_UPDATE_HW_LB100_REV1,
        SVC_UPDATE_PROTOCOL_V1,
        77U,
        5U));

    assert(svc_update_accept_chunk(
        &transfer,
        77U,
        1U,
        3U,
        second_payload,
        sizeof(second_payload),
        svc_update_crc32(second_payload, sizeof(second_payload))) ==
        SVC_UPDATE_CHUNK_ACCEPTED);
}

static void test_hash_signature_and_incomplete_file_fail(void)
{
    const uint8_t payload[] = {1U, 2U};
    svc_update_transfer_t transfer;

    svc_update_transfer_init(&transfer);
    assert(svc_update_begin(
        &transfer,
        SVC_UPDATE_TARGET_E73_RADIO,
        SVC_UPDATE_HW_LB100_REV1,
        SVC_UPDATE_PROTOCOL_V1,
        1U,
        3U));
    assert(svc_update_accept_chunk(
        &transfer,
        1U,
        0U,
        0U,
        payload,
        sizeof(payload),
        svc_update_crc32(payload, sizeof(payload))) == SVC_UPDATE_CHUNK_ACCEPTED);
    assert(!svc_update_finish_transfer(&transfer, true, true));
    assert(transfer.state == SVC_UPDATE_FAILED);

    svc_update_transfer_init(&transfer);
    assert(svc_update_begin(
        &transfer,
        SVC_UPDATE_TARGET_E73_RADIO,
        SVC_UPDATE_HW_LB100_REV1,
        SVC_UPDATE_PROTOCOL_V1,
        2U,
        2U));
    assert(svc_update_accept_chunk(
        &transfer,
        2U,
        0U,
        0U,
        payload,
        sizeof(payload),
        svc_update_crc32(payload, sizeof(payload))) == SVC_UPDATE_CHUNK_ACCEPTED);
    assert(!svc_update_finish_transfer(&transfer, false, true));
    assert(transfer.state == SVC_UPDATE_FAILED);

    svc_update_transfer_init(&transfer);
    assert(svc_update_begin(
        &transfer,
        SVC_UPDATE_TARGET_E73_RADIO,
        SVC_UPDATE_HW_LB100_REV1,
        SVC_UPDATE_PROTOCOL_V1,
        3U,
        2U));
    assert(svc_update_accept_chunk(
        &transfer,
        3U,
        0U,
        0U,
        payload,
        sizeof(payload),
        svc_update_crc32(payload, sizeof(payload))) == SVC_UPDATE_CHUNK_ACCEPTED);
    assert(!svc_update_finish_transfer(&transfer, true, false));
    assert(transfer.state == SVC_UPDATE_FAILED);
}

static void test_ota_admission_reports_specific_reason(void)
{
    svc_ota_admission_t admission = allowed_admission();
    assert(svc_ota_check_admission(&admission) == SVC_OTA_ALLOWED);

    admission.speed_stale = true;
    assert(svc_ota_check_admission(&admission) == SVC_OTA_DENY_VEHICLE_MOVING);
    admission.speed_stale = false;
    admission.engine_running = true;
    assert(svc_ota_check_admission(&admission) == SVC_OTA_DENY_ENGINE_RUNNING);
    admission.engine_running = false;
    admission.outputs_all_off = false;
    assert(svc_ota_check_admission(&admission) == SVC_OTA_DENY_OUTPUTS_ACTIVE);
    admission.outputs_all_off = true;
    admission.battery_mv = 11000U;
    assert(svc_ota_check_admission(&admission) == SVC_OTA_DENY_BATTERY_OUT_OF_RANGE);
    admission.battery_mv = 12600U;
    admission.board_temperature_c = 100;
    assert(svc_ota_check_admission(&admission) ==
           SVC_OTA_DENY_TEMPERATURE_OUT_OF_RANGE);
    admission.board_temperature_c = 40;
    admission.link_stable = false;
    assert(svc_ota_check_admission(&admission) == SVC_OTA_DENY_LINK_UNSTABLE);
}

static void test_power_loss_before_confirmation_rolls_back(void)
{
    const uint8_t payload[] = {1U};
    svc_update_transfer_t transfer;
    svc_update_transfer_init(&transfer);
    assert(svc_update_begin(
        &transfer,
        SVC_UPDATE_TARGET_STM32_MAIN,
        SVC_UPDATE_HW_LB100_REV1,
        SVC_UPDATE_PROTOCOL_V1,
        5U,
        1U));
    assert(svc_update_accept_chunk(
        &transfer,
        5U,
        0U,
        0U,
        payload,
        sizeof(payload),
        svc_update_crc32(payload, sizeof(payload))) == SVC_UPDATE_CHUNK_ACCEPTED);
    assert(svc_update_finish_transfer(&transfer, true, true));

    const svc_ota_admission_t admission = allowed_admission();
    assert(svc_update_request_test_boot(&transfer, &admission));
    assert(svc_update_enter_test_boot(&transfer));
    assert(svc_update_after_reset(&transfer));
    assert(transfer.state == SVC_UPDATE_ROLLBACK);
    assert(svc_update_complete_rollback(&transfer));
    assert(transfer.state == SVC_UPDATE_ROLLED_BACK);
}

static void test_confirmed_boot_does_not_rollback(void)
{
    svc_update_transfer_t transfer = {
        .state = SVC_UPDATE_TESTING
    };
    assert(svc_update_confirm(&transfer));
    assert(svc_update_after_reset(&transfer));
    assert(transfer.state == SVC_UPDATE_CONFIRMED);
}

static void test_e73_and_stm32_version_compatibility(void)
{
    const svc_update_version_t version_0_1_0 = {0U, 1U, 0U};
    const svc_update_version_t version_0_2_0 = {0U, 2U, 0U};

    assert(svc_update_versions_compatible(
        1U,
        1U,
        1U,
        version_0_2_0,
        version_0_1_0,
        version_0_2_0,
        version_0_1_0));
    assert(!svc_update_versions_compatible(
        1U,
        1U,
        2U,
        version_0_2_0,
        version_0_1_0,
        version_0_2_0,
        version_0_1_0));
    assert(!svc_update_versions_compatible(
        1U,
        1U,
        1U,
        version_0_1_0,
        version_0_2_0,
        version_0_2_0,
        version_0_1_0));
}

int main(void)
{
    test_rejects_protocol_and_hardware_mismatch();
    test_chunk_retry_corruption_interrupt_and_resume();
    test_hash_signature_and_incomplete_file_fail();
    test_ota_admission_reports_specific_reason();
    test_power_loss_before_confirmation_rolls_back();
    test_confirmed_boot_does_not_rollback();
    test_e73_and_stm32_version_compatibility();
    return 0;
}
