#include "update_state.h"

#include <limits.h>
#include <stddef.h>

static int version_compare(svc_update_version_t left, svc_update_version_t right)
{
    if (left.major != right.major) {
        return left.major < right.major ? -1 : 1;
    }
    if (left.minor != right.minor) {
        return left.minor < right.minor ? -1 : 1;
    }
    if (left.patch != right.patch) {
        return left.patch < right.patch ? -1 : 1;
    }
    return 0;
}

void svc_update_transfer_init(svc_update_transfer_t *transfer)
{
    if (transfer == NULL) {
        return;
    }

    *transfer = (svc_update_transfer_t){
        .state = SVC_UPDATE_IDLE,
        .hardware = SVC_UPDATE_HW_UNSUPPORTED
    };
}

bool svc_update_begin(
    svc_update_transfer_t *transfer,
    svc_update_target_t target,
    svc_update_hardware_t hardware,
    uint16_t protocol_version,
    uint32_t transfer_id,
    uint32_t total_size)
{
    if (transfer == NULL ||
        transfer->state != SVC_UPDATE_IDLE ||
        target > SVC_UPDATE_TARGET_STM32_MAIN ||
        hardware != SVC_UPDATE_HW_LB100_REV1 ||
        protocol_version != SVC_UPDATE_PROTOCOL_V1 ||
        total_size == 0U) {
        return false;
    }

    *transfer = (svc_update_transfer_t){
        .state = SVC_UPDATE_RECEIVING,
        .target = target,
        .hardware = hardware,
        .transfer_id = transfer_id,
        .total_size = total_size,
        .protocol_version = protocol_version
    };
    return true;
}

svc_update_chunk_result_t svc_update_accept_chunk(
    svc_update_transfer_t *transfer,
    uint32_t transfer_id,
    uint32_t sequence,
    uint32_t offset,
    const uint8_t *payload,
    uint16_t payload_length,
    uint32_t payload_crc32)
{
    if (transfer == NULL ||
        transfer->state != SVC_UPDATE_RECEIVING ||
        transfer_id != transfer->transfer_id ||
        payload == NULL ||
        payload_length == 0U ||
        payload_length > SVC_UPDATE_MAX_CHUNK_SIZE) {
        return SVC_UPDATE_CHUNK_INVALID;
    }

    const uint32_t calculated_crc32 = svc_update_crc32(payload, payload_length);
    if (calculated_crc32 != payload_crc32) {
        return SVC_UPDATE_CHUNK_CORRUPT;
    }

    if (transfer->has_last_chunk &&
        sequence == transfer->last_sequence &&
        offset == transfer->last_offset &&
        payload_length == transfer->last_length &&
        payload_crc32 == transfer->last_crc32) {
        return SVC_UPDATE_CHUNK_DUPLICATE;
    }

    if (sequence != transfer->next_sequence ||
        offset != transfer->committed_offset) {
        return SVC_UPDATE_CHUNK_RETRY;
    }

    if (offset > transfer->total_size ||
        payload_length > transfer->total_size - offset) {
        return SVC_UPDATE_CHUNK_INVALID;
    }

    transfer->last_sequence = sequence;
    transfer->last_offset = offset;
    transfer->last_crc32 = payload_crc32;
    transfer->last_length = payload_length;
    transfer->has_last_chunk = true;
    transfer->committed_offset += payload_length;
    transfer->next_sequence += 1U;
    return SVC_UPDATE_CHUNK_ACCEPTED;
}

bool svc_update_interrupt(svc_update_transfer_t *transfer)
{
    if (transfer == NULL || transfer->state != SVC_UPDATE_RECEIVING) {
        return false;
    }

    transfer->state = SVC_UPDATE_INTERRUPTED;
    return true;
}

bool svc_update_resume(
    svc_update_transfer_t *transfer,
    svc_update_target_t target,
    svc_update_hardware_t hardware,
    uint16_t protocol_version,
    uint32_t transfer_id,
    uint32_t total_size)
{
    if (transfer == NULL ||
        transfer->state != SVC_UPDATE_INTERRUPTED ||
        target != transfer->target ||
        hardware != transfer->hardware ||
        protocol_version != transfer->protocol_version ||
        transfer_id != transfer->transfer_id ||
        total_size != transfer->total_size) {
        return false;
    }

    transfer->state = SVC_UPDATE_RECEIVING;
    return true;
}

bool svc_update_finish_transfer(
    svc_update_transfer_t *transfer,
    bool sha256_valid,
    bool signature_valid)
{
    if (transfer == NULL || transfer->state != SVC_UPDATE_RECEIVING) {
        return false;
    }

    transfer->sha256_valid = sha256_valid;
    transfer->signature_valid = signature_valid;
    if (transfer->committed_offset != transfer->total_size ||
        !sha256_valid ||
        !signature_valid) {
        transfer->state = SVC_UPDATE_FAILED;
        return false;
    }

    transfer->state = SVC_UPDATE_VERIFIED;
    return true;
}

svc_ota_denial_t svc_ota_check_admission(const svc_ota_admission_t *admission)
{
    if (admission == NULL) {
        return SVC_OTA_DENY_FILE_INCOMPLETE;
    }
    if (!admission->speed_valid ||
        admission->speed_stale ||
        admission->speed_centi_kph != 0) {
        return SVC_OTA_DENY_VEHICLE_MOVING;
    }
    if (!admission->engine_state_valid ||
        admission->engine_state_stale ||
        admission->engine_running) {
        return SVC_OTA_DENY_ENGINE_RUNNING;
    }
    if (!admission->outputs_all_off) {
        return SVC_OTA_DENY_OUTPUTS_ACTIVE;
    }
    if (!admission->no_critical_fault) {
        return SVC_OTA_DENY_CRITICAL_FAULT;
    }
    if (!admission->battery_valid ||
        admission->battery_stale ||
        admission->battery_min_mv > admission->battery_max_mv ||
        admission->battery_mv < admission->battery_min_mv ||
        admission->battery_mv > admission->battery_max_mv) {
        return SVC_OTA_DENY_BATTERY_OUT_OF_RANGE;
    }
    if (!admission->board_temperature_valid ||
        admission->board_temperature_stale ||
        admission->board_temperature_min_c > admission->board_temperature_max_c ||
        admission->board_temperature_c < admission->board_temperature_min_c ||
        admission->board_temperature_c > admission->board_temperature_max_c) {
        return SVC_OTA_DENY_TEMPERATURE_OUT_OF_RANGE;
    }
    if (!admission->link_stable) {
        return SVC_OTA_DENY_LINK_UNSTABLE;
    }
    if (!admission->file_complete) {
        return SVC_OTA_DENY_FILE_INCOMPLETE;
    }
    if (!admission->sha256_valid) {
        return SVC_OTA_DENY_HASH_MISMATCH;
    }
    if (!admission->signature_valid) {
        return SVC_OTA_DENY_SIGNATURE_INVALID;
    }
    if (!admission->hardware_compatible) {
        return SVC_OTA_DENY_HARDWARE_MISMATCH;
    }
    if (!admission->protocol_compatible) {
        return SVC_OTA_DENY_PROTOCOL_INCOMPATIBLE;
    }
    if (!admission->bootloader_compatible) {
        return SVC_OTA_DENY_BOOTLOADER_TOO_OLD;
    }
    return SVC_OTA_ALLOWED;
}

bool svc_update_request_test_boot(
    svc_update_transfer_t *transfer,
    const svc_ota_admission_t *admission)
{
    if (transfer == NULL ||
        transfer->state != SVC_UPDATE_VERIFIED ||
        svc_ota_check_admission(admission) != SVC_OTA_ALLOWED) {
        return false;
    }

    transfer->state = SVC_UPDATE_PENDING_TEST_BOOT;
    return true;
}

bool svc_update_enter_test_boot(svc_update_transfer_t *transfer)
{
    if (transfer == NULL || transfer->state != SVC_UPDATE_PENDING_TEST_BOOT) {
        return false;
    }

    transfer->state = SVC_UPDATE_TESTING;
    return true;
}

bool svc_update_confirm(svc_update_transfer_t *transfer)
{
    if (transfer == NULL || transfer->state != SVC_UPDATE_TESTING) {
        return false;
    }

    transfer->state = SVC_UPDATE_CONFIRMED;
    return true;
}

bool svc_update_boot_failed(svc_update_transfer_t *transfer)
{
    if (transfer == NULL ||
        (transfer->state != SVC_UPDATE_TESTING &&
         transfer->state != SVC_UPDATE_PENDING_TEST_BOOT)) {
        return false;
    }

    transfer->state = SVC_UPDATE_ROLLBACK;
    return true;
}

bool svc_update_after_reset(svc_update_transfer_t *transfer)
{
    if (transfer == NULL) {
        return false;
    }

    if (transfer->state == SVC_UPDATE_TESTING) {
        transfer->state = SVC_UPDATE_ROLLBACK;
        return true;
    }

    return transfer->state == SVC_UPDATE_CONFIRMED ||
           transfer->state == SVC_UPDATE_ROLLBACK ||
           transfer->state == SVC_UPDATE_ROLLED_BACK;
}

bool svc_update_complete_rollback(svc_update_transfer_t *transfer)
{
    if (transfer == NULL || transfer->state != SVC_UPDATE_ROLLBACK) {
        return false;
    }

    transfer->state = SVC_UPDATE_ROLLED_BACK;
    return true;
}

bool svc_update_versions_compatible(
    uint16_t manifest_protocol,
    uint16_t e73_protocol,
    uint16_t stm32_protocol,
    svc_update_version_t e73_version,
    svc_update_version_t minimum_e73_version,
    svc_update_version_t stm32_version,
    svc_update_version_t minimum_stm32_version)
{
    return manifest_protocol == SVC_UPDATE_PROTOCOL_V1 &&
           e73_protocol == manifest_protocol &&
           stm32_protocol == manifest_protocol &&
           version_compare(e73_version, minimum_e73_version) >= 0 &&
           version_compare(stm32_version, minimum_stm32_version) >= 0;
}

uint32_t svc_update_crc32(const uint8_t *data, size_t length)
{
    if (data == NULL && length != 0U) {
        return 0U;
    }

    uint32_t crc = UINT32_MAX;
    for (size_t data_index = 0U; data_index < length; ++data_index) {
        crc ^= data[data_index];
        for (uint8_t bit_index = 0U; bit_index < 8U; ++bit_index) {
            const uint32_t mask = (uint32_t)-(int32_t)(crc & 1U);
            crc = (crc >> 1U) ^ (0xEDB88320U & mask);
        }
    }
    return ~crc;
}
