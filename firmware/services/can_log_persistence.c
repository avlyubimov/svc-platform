#include "can_log_persistence.h"

#include <string.h>

#define SVC_CAN_LOG_RECORD_TYPE_RX 1U
#define SVC_CAN_LOG_RECORD_CRC_OFFSET 36U

static void increment_counter(uint32_t *counter)
{
    if (*counter < UINT32_MAX) {
        ++(*counter);
    }
}

static void put_u32(uint8_t *destination, uint32_t value)
{
    for (size_t index = 0U; index < 4U; ++index) {
        destination[index] = (uint8_t)(value >> (index * 8U));
    }
}

static void put_u64(uint8_t *destination, uint64_t value)
{
    for (size_t index = 0U; index < 8U; ++index) {
        destination[index] = (uint8_t)(value >> (index * 8U));
    }
}

static uint32_t get_u32(const uint8_t *source)
{
    uint32_t value = 0U;
    for (size_t index = 0U; index < 4U; ++index) {
        value |= (uint32_t)source[index] << (index * 8U);
    }
    return value;
}

static uint64_t get_u64(const uint8_t *source)
{
    uint64_t value = 0U;
    for (size_t index = 0U; index < 8U; ++index) {
        value |= (uint64_t)source[index] << (index * 8U);
    }
    return value;
}

static uint32_t crc32(const uint8_t *data, size_t size)
{
    uint32_t crc = UINT32_MAX;
    for (size_t index = 0U; index < size; ++index) {
        crc ^= data[index];
        for (uint8_t bit = 0U; bit < 8U; ++bit) {
            const uint32_t mask = (uint32_t)(-(int32_t)(crc & 1U));
            crc = (crc >> 1U) ^ (0xEDB88320U & mask);
        }
    }
    return ~crc;
}

static void encode_record(
    const svc_can_frame_t *frame,
    uint64_t sequence,
    uint8_t record[SVC_CAN_LOG_RECORD_SIZE])
{
    memset(record, 0, SVC_CAN_LOG_RECORD_SIZE);
    record[0] = 'S';
    record[1] = 'V';
    record[2] = 'C';
    record[3] = 'L';
    record[4] = SVC_CAN_LOG_RECORD_FORMAT_VERSION;
    record[5] = SVC_CAN_LOG_RECORD_TYPE_RX;
    record[6] = (uint8_t)frame->port;
    record[7] = frame->extended_id ? 1U : 0U;
    put_u64(&record[8], sequence);
    put_u32(&record[16], frame->timestamp_ms);
    put_u32(&record[20], frame->id);
    record[24] = frame->dlc;
    memcpy(&record[25], frame->data, frame->dlc);
    put_u32(&record[SVC_CAN_LOG_RECORD_CRC_OFFSET], crc32(record, SVC_CAN_LOG_RECORD_CRC_OFFSET));
}

void svc_can_log_persistence_init(
    svc_can_log_persistence_t *persistence,
    svc_can_log_storage_backend_t backend,
    uint64_t initial_sequence)
{
    if (persistence == NULL) {
        return;
    }
    *persistence = (svc_can_log_persistence_t){
        .backend = backend,
        .next_sequence = initial_sequence,
    };
}

svc_can_log_persist_status_t svc_can_log_persist_can1(
    svc_can_log_persistence_t *persistence,
    svc_can1_log_queue_t *queue,
    size_t max_records,
    size_t *persisted_records)
{
    if (persisted_records != NULL) {
        *persisted_records = 0U;
    }
    if (persistence == NULL || queue == NULL) {
        return SVC_CAN_LOG_PERSIST_INVALID_ARGUMENT;
    }
    if (persistence->backend.write == NULL || persistence->backend.sync == NULL) {
        return SVC_CAN_LOG_PERSIST_BACKEND_UNAVAILABLE;
    }
    if (max_records == 0U) {
        return SVC_CAN_LOG_PERSIST_NO_DATA;
    }

    const size_t queued_count = svc_can1_log_queue_count(queue);
    const size_t selected_count = max_records < queued_count ? max_records : queued_count;
    if (selected_count == 0U) {
        return SVC_CAN_LOG_PERSIST_NO_DATA;
    }

    for (size_t output_index = 0U; output_index < selected_count; ++output_index) {
        svc_can_frame_t frame = {0};
        uint8_t record[SVC_CAN_LOG_RECORD_SIZE] = {0U};
        if (!svc_can1_log_queue_peek(queue, output_index, &frame)) {
            return SVC_CAN_LOG_PERSIST_INVALID_ARGUMENT;
        }
        encode_record(&frame, persistence->next_sequence + output_index, record);
        if (persistence->backend.write(
                persistence->backend.context,
                record,
                sizeof(record)) != sizeof(record)) {
            increment_counter(&persistence->write_failure_count);
            return SVC_CAN_LOG_PERSIST_WRITE_FAILED;
        }
    }
    if (!persistence->backend.sync(persistence->backend.context)) {
        increment_counter(&persistence->sync_failure_count);
        return SVC_CAN_LOG_PERSIST_SYNC_FAILED;
    }

    if (!svc_can1_log_queue_consume(queue, selected_count)) {
        return SVC_CAN_LOG_PERSIST_INVALID_ARGUMENT;
    }
    persistence->next_sequence += selected_count;
    for (size_t index = 0U; index < selected_count; ++index) {
        increment_counter(&persistence->persisted_can1_count);
    }
    if (persisted_records != NULL) {
        *persisted_records = selected_count;
    }
    return SVC_CAN_LOG_PERSIST_OK;
}

bool svc_can_log_record_decode(
    const uint8_t record[SVC_CAN_LOG_RECORD_SIZE],
    svc_can_frame_t *frame,
    uint64_t *sequence)
{
    if (record == NULL || frame == NULL || sequence == NULL ||
        record[0] != 'S' || record[1] != 'V' || record[2] != 'C' || record[3] != 'L' ||
        record[4] != SVC_CAN_LOG_RECORD_FORMAT_VERSION ||
        record[5] != SVC_CAN_LOG_RECORD_TYPE_RX ||
        record[6] != (uint8_t)SVC_CAN_PORT_CAN1_VEHICLE ||
        record[24] > SVC_CAN_FRAME_MAX_DATA_LEN ||
        get_u32(&record[SVC_CAN_LOG_RECORD_CRC_OFFSET]) != crc32(record, SVC_CAN_LOG_RECORD_CRC_OFFSET)) {
        return false;
    }

    *sequence = get_u64(&record[8]);
    *frame = (svc_can_frame_t){
        .port = SVC_CAN_PORT_CAN1_VEHICLE,
        .id = get_u32(&record[20]),
        .dlc = record[24],
        .timestamp_ms = get_u32(&record[16]),
        .extended_id = (record[7] & 1U) != 0U,
    };
    memcpy(frame->data, &record[25], frame->dlc);
    return true;
}
