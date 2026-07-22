#include <assert.h>
#include <stddef.h>
#include <string.h>

#include "can_log.h"
#include "can_log_persistence.h"

typedef struct {
    uint8_t bytes[SVC_CAN_LOG_RECORD_SIZE * SVC_CAN_LOG_CAPACITY];
    size_t size;
    size_t write_limit;
    size_t sync_count;
    bool sync_result;
} storage_mock_t;

static size_t storage_write(void *context, const uint8_t *data, size_t size)
{
    storage_mock_t *storage = context;
    size_t accepted = size;
    if (storage->write_limit < accepted) {
        accepted = storage->write_limit;
    }
    if (accepted > sizeof(storage->bytes) - storage->size) {
        accepted = sizeof(storage->bytes) - storage->size;
    }
    memcpy(&storage->bytes[storage->size], data, accepted);
    storage->size += accepted;
    return accepted;
}

static bool storage_sync(void *context)
{
    storage_mock_t *storage = context;
    ++storage->sync_count;
    return storage->sync_result;
}

static svc_can_log_storage_backend_t backend_for(storage_mock_t *storage)
{
    return (svc_can_log_storage_backend_t){
        .context = storage,
        .write = storage_write,
        .sync = storage_sync,
    };
}

static svc_can_frame_t frame_for(
    svc_can_port_t port,
    uint32_t id,
    uint8_t first_byte)
{
    return (svc_can_frame_t){
        .port = port,
        .id = id,
        .dlc = 2U,
        .data = {first_byte, (uint8_t)(first_byte + 1U)},
        .timestamp_ms = id,
        .extended_id = false
    };
}

static void test_logs_can1_rx_frame_without_tx_path(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x123U, 0xABU);

    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);
    assert(svc_can_log_count(&log) == 1U);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN1_VEHICLE) == 1U);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN2_EXPANSION) == 0U);

    svc_can_frame_t read_frame = {0};
    assert(svc_can_log_get(&log, 0U, &read_frame));
    assert(read_frame.port == SVC_CAN_PORT_CAN1_VEHICLE);
    assert(read_frame.id == 0x123U);
    assert(read_frame.dlc == 2U);
    assert(read_frame.data[0] == 0xABU);
}

static void test_logs_can2_rx_frame_separately(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN2_EXPANSION, 0x321U, 1U);

    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);

    assert(svc_can_log_count(&log) == 1U);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN1_VEHICLE) == 0U);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN2_EXPANSION) == 1U);
}

static void test_rejects_invalid_dlc(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x123U, 0U);
    frame.dlc = SVC_CAN_FRAME_MAX_DATA_LEN + 1U;

    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_INVALID_DLC);
    assert(svc_can_log_count(&log) == 0U);
}

static void test_rejects_invalid_port(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    svc_can_frame_t frame = frame_for((svc_can_port_t)99, 0x123U, 0U);

    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_INVALID_PORT);
    assert(svc_can_log_count(&log) == 0U);
}

static void test_ring_buffer_overwrites_oldest_frame(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);

    for (size_t index = 0U; index < SVC_CAN_LOG_CAPACITY + 3U; ++index) {
        const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, (uint32_t)index, (uint8_t)index);
        assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);
    }

    assert(svc_can_log_count(&log) == SVC_CAN_LOG_CAPACITY);
    assert(svc_can_log_dropped_count(&log) == 3U);

    svc_can_frame_t first_retained = {0};
    assert(svc_can_log_get(&log, 0U, &first_retained));
    assert(first_retained.id == 3U);
}

static void test_diagnostic_counts_saturate_on_overflow(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);

    for (size_t index = 0U; index < SVC_CAN_LOG_CAPACITY; ++index) {
        const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, (uint32_t)index, (uint8_t)index);
        assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);
    }

    log.dropped_count = UINT32_MAX;
    log.can1_rx_count = UINT32_MAX;
    log.can2_rx_count = UINT32_MAX;

    const svc_can_frame_t can1_frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 100U, 1U);
    const svc_can_frame_t can2_frame = frame_for(SVC_CAN_PORT_CAN2_EXPANSION, 101U, 2U);
    assert(svc_can_log_append_rx(&log, &can1_frame) == SVC_CAN_LOG_OK);
    assert(svc_can_log_append_rx(&log, &can2_frame) == SVC_CAN_LOG_OK);

    assert(svc_can_log_dropped_count(&log) == UINT32_MAX);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN1_VEHICLE) == UINT32_MAX);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN2_EXPANSION) == UINT32_MAX);
}

static void test_null_inputs_fail_safe(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x123U, 0U);

    assert(svc_can_log_append_rx(NULL, &frame) == SVC_CAN_LOG_INVALID_ARGUMENT);
    assert(svc_can_log_append_rx(&log, NULL) == SVC_CAN_LOG_INVALID_ARGUMENT);
    assert(svc_can_log_count(NULL) == 0U);
    assert(svc_can_log_dropped_count(NULL) == 0U);
    assert(svc_can_log_port_count(NULL, SVC_CAN_PORT_CAN1_VEHICLE) == 0U);
}

static void test_persists_only_can1_and_retains_can2(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t first = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x123U, 0xA0U);
    const svc_can_frame_t can2 = frame_for(SVC_CAN_PORT_CAN2_EXPANSION, 0x456U, 0xB0U);
    svc_can_frame_t second = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x18DAF110U, 0xC0U);
    second.extended_id = true;
    assert(svc_can_log_append_rx(&log, &first) == SVC_CAN_LOG_OK);
    assert(svc_can_log_append_rx(&log, &can2) == SVC_CAN_LOG_OK);
    assert(svc_can_log_append_rx(&log, &second) == SVC_CAN_LOG_OK);

    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE,
        .sync_result = true,
    };
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 1000U);
    size_t persisted = 0U;
    assert(svc_can_log_persist_can1(&persistence, &log, 8U, &persisted) == SVC_CAN_LOG_PERSIST_OK);
    assert(persisted == 2U);
    assert(storage.size == 2U * SVC_CAN_LOG_RECORD_SIZE);
    assert(storage.sync_count == 1U);
    assert(persistence.next_sequence == 1002U);
    assert(persistence.persisted_can1_count == 2U);
    assert(svc_can_log_count(&log) == 1U);

    svc_can_frame_t retained = {0};
    assert(svc_can_log_get(&log, 0U, &retained));
    assert(retained.port == SVC_CAN_PORT_CAN2_EXPANSION);
    assert(retained.id == 0x456U);

    svc_can_frame_t decoded = {0};
    uint64_t sequence = 0U;
    assert(svc_can_log_record_decode(&storage.bytes[0], &decoded, &sequence));
    assert(sequence == 1000U);
    assert(decoded.id == first.id);
    assert(decoded.data[0] == 0xA0U);
    assert(svc_can_log_record_decode(&storage.bytes[SVC_CAN_LOG_RECORD_SIZE], &decoded, &sequence));
    assert(sequence == 1001U);
    assert(decoded.id == second.id);
    assert(decoded.extended_id);
}

static void test_write_failure_retains_frames_for_retry(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x321U, 0x10U);
    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);
    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE - 1U,
        .sync_result = true,
    };
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 9U);

    assert(svc_can_log_persist_can1(&persistence, &log, 1U, NULL) == SVC_CAN_LOG_PERSIST_WRITE_FAILED);
    assert(svc_can_log_count(&log) == 1U);
    assert(persistence.next_sequence == 9U);
    assert(persistence.write_failure_count == 1U);
    assert(storage.sync_count == 0U);
}

static void test_sync_failure_retains_frames_for_retry(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x654U, 0x20U);
    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);
    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE,
        .sync_result = false,
    };
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 12U);

    assert(svc_can_log_persist_can1(&persistence, &log, 1U, NULL) == SVC_CAN_LOG_PERSIST_SYNC_FAILED);
    assert(svc_can_log_count(&log) == 1U);
    assert(persistence.next_sequence == 12U);
    assert(persistence.sync_failure_count == 1U);
}

static void test_record_crc_rejects_corruption(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x7FFU, 0x30U);
    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);
    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE,
        .sync_result = true,
    };
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 0U);
    assert(svc_can_log_persist_can1(&persistence, &log, 1U, NULL) == SVC_CAN_LOG_PERSIST_OK);
    storage.bytes[25] ^= 0x01U;

    svc_can_frame_t decoded = {0};
    uint64_t sequence = 0U;
    assert(!svc_can_log_record_decode(storage.bytes, &decoded, &sequence));
}

static void test_persistence_empty_and_invalid_backends_fail_safe(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(
        &persistence,
        (svc_can_log_storage_backend_t){0},
        0U);
    assert(svc_can_log_persist_can1(&persistence, &log, 1U, NULL) == SVC_CAN_LOG_PERSIST_BACKEND_UNAVAILABLE);

    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE,
        .sync_result = true,
    };
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 0U);
    assert(svc_can_log_persist_can1(&persistence, &log, 1U, NULL) == SVC_CAN_LOG_PERSIST_NO_DATA);
    assert(svc_can_log_persist_can1(NULL, &log, 1U, NULL) == SVC_CAN_LOG_PERSIST_INVALID_ARGUMENT);
    assert(svc_can_log_persist_can1(&persistence, NULL, 1U, NULL) == SVC_CAN_LOG_PERSIST_INVALID_ARGUMENT);
}

int main(void)
{
    test_logs_can1_rx_frame_without_tx_path();
    test_logs_can2_rx_frame_separately();
    test_rejects_invalid_dlc();
    test_rejects_invalid_port();
    test_ring_buffer_overwrites_oldest_frame();
    test_diagnostic_counts_saturate_on_overflow();
    test_null_inputs_fail_safe();
    test_persists_only_can1_and_retains_can2();
    test_write_failure_retains_frames_for_retry();
    test_sync_failure_retains_frames_for_retry();
    test_record_crc_rejects_corruption();
    test_persistence_empty_and_invalid_backends_fail_safe();
    return 0;
}
