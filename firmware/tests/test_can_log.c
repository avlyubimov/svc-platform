#include <assert.h>
#include <stddef.h>
#include <string.h>

#include "can_log.h"
#include "can_log_fatfs.h"
#include "can_log_persistence.h"
#include "can_log_queue.h"
#include "can_log_task.h"

#define FAT_MOCK_FILE_COUNT 4U
#define FAT_MOCK_FILE_CAPACITY 512U

typedef struct {
    uint32_t session_id;
    uint8_t bytes[FAT_MOCK_FILE_CAPACITY];
    size_t size;
    uint64_t reserved_size;
    bool exists;
} fat_mock_file_t;

typedef struct {
    fat_mock_file_t files[FAT_MOCK_FILE_COUNT];
    fat_mock_file_t *current;
    size_t mount_count;
    size_t open_count;
    size_t sync_count;
    size_t close_count;
    size_t truncate_count;
    size_t preallocate_count;
    bool fail_next_sync;
    bool fail_next_close;
} fat_mock_t;

static bool fat_mount(void *context)
{
    fat_mock_t *fat = context;
    ++fat->mount_count;
    return true;
}

static bool fat_find_latest_session(
    void *context,
    uint32_t first_session_id,
    bool *found,
    uint32_t *latest_session_id)
{
    fat_mock_t *fat = context;
    *found = false;
    *latest_session_id = first_session_id;
    for (size_t index = 0U; index < FAT_MOCK_FILE_COUNT; ++index) {
        if (fat->files[index].exists &&
            fat->files[index].session_id >= first_session_id &&
            (!*found || fat->files[index].session_id > *latest_session_id)) {
            *found = true;
            *latest_session_id = fat->files[index].session_id;
        }
    }
    return true;
}

static bool fat_open_session(
    void *context,
    uint32_t session_id,
    bool *created,
    uint64_t *logical_size)
{
    fat_mock_t *fat = context;
    ++fat->open_count;
    for (size_t index = 0U; index < FAT_MOCK_FILE_COUNT; ++index) {
        if (fat->files[index].exists && fat->files[index].session_id == session_id) {
            fat->current = &fat->files[index];
            *created = false;
            *logical_size = fat->current->size;
            return true;
        }
    }
    for (size_t index = 0U; index < FAT_MOCK_FILE_COUNT; ++index) {
        if (!fat->files[index].exists) {
            fat->files[index].exists = true;
            fat->files[index].session_id = session_id;
            fat->current = &fat->files[index];
            *created = true;
            *logical_size = 0U;
            return true;
        }
    }
    return false;
}

static size_t fat_read_at(void *context, uint64_t offset, uint8_t *data, size_t size)
{
    fat_mock_t *fat = context;
    if (fat->current == NULL || offset > fat->current->size ||
        size > fat->current->size - (size_t)offset) {
        return 0U;
    }
    memcpy(data, &fat->current->bytes[offset], size);
    return size;
}

static size_t fat_append(void *context, const uint8_t *data, size_t size)
{
    fat_mock_t *fat = context;
    if (fat->current == NULL || size > sizeof(fat->current->bytes) - fat->current->size) {
        return 0U;
    }
    memcpy(&fat->current->bytes[fat->current->size], data, size);
    fat->current->size += size;
    return size;
}

static bool fat_sync(void *context)
{
    fat_mock_t *fat = context;
    ++fat->sync_count;
    if (fat->fail_next_sync) {
        fat->fail_next_sync = false;
        return false;
    }
    return fat->current != NULL;
}

static bool fat_preallocate(void *context, uint64_t target_size)
{
    fat_mock_t *fat = context;
    if (fat->current == NULL || target_size > FAT_MOCK_FILE_CAPACITY) {
        return false;
    }
    ++fat->preallocate_count;
    fat->current->reserved_size = target_size;
    return true;
}

static bool fat_truncate(void *context, uint64_t logical_size)
{
    fat_mock_t *fat = context;
    if (fat->current == NULL || logical_size > fat->current->size) {
        return false;
    }
    ++fat->truncate_count;
    fat->current->size = (size_t)logical_size;
    return true;
}

static bool fat_close(void *context)
{
    fat_mock_t *fat = context;
    ++fat->close_count;
    if (fat->fail_next_close) {
        fat->fail_next_close = false;
        return false;
    }
    fat->current = NULL;
    return true;
}

static svc_can_log_fatfs_port_t fat_port_for(fat_mock_t *fat)
{
    return (svc_can_log_fatfs_port_t){
        .context = fat,
        .mount = fat_mount,
        .find_latest_session = fat_find_latest_session,
        .open_session = fat_open_session,
        .read_at = fat_read_at,
        .append = fat_append,
        .sync = fat_sync,
        .preallocate = fat_preallocate,
        .truncate = fat_truncate,
        .close = fat_close,
    };
}

static svc_can_log_fatfs_config_t fat_config(
    uint32_t session_id,
    uint64_t rotation_bytes)
{
    return (svc_can_log_fatfs_config_t){
        .session_id = session_id,
        .started_us = 1234567890123ULL,
        .rotation_bytes = rotation_bytes,
        .preallocation_bytes = rotation_bytes,
        .can_bitrate = 500000U,
        .session_reason = SVC_CAN_LOG_SESSION_REASON_IGNITION_WAKE,
        .hardware_version = "LB-100-REV1",
        .firmware_version = "0.4.0-dev",
        .board_serial = "LB1-EVT-00001",
    };
}

typedef struct {
    uint8_t bytes[SVC_CAN_LOG_RECORD_SIZE * SVC_CAN_LOG_CAPACITY];
    size_t size;
    size_t write_limit;
    size_t sync_count;
    bool sync_result;
    svc_can1_log_queue_t *inject_queue;
    svc_can_frame_t injected_frames[2];
    bool inject_during_write;
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
    if (storage->inject_during_write && storage->inject_queue != NULL) {
        storage->inject_during_write = false;
        assert(svc_can1_log_queue_push_isr(
                   storage->inject_queue,
                   &storage->injected_frames[0]) == SVC_CAN1_LOG_QUEUE_OK);
        assert(svc_can1_log_queue_push_isr(
                   storage->inject_queue,
                   &storage->injected_frames[1]) == SVC_CAN1_LOG_QUEUE_OK);
    }
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
        .timestamp_us = 0x100000000ULL + id,
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

static void test_persists_can1_queue_without_mutating_diagnostic_log(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    const svc_can_frame_t first = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x123U, 0xA0U);
    const svc_can_frame_t can2 = frame_for(SVC_CAN_PORT_CAN2_EXPANSION, 0x456U, 0xB0U);
    svc_can_frame_t second = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x18DAF110U, 0xC0U);
    second.extended_id = true;
    assert(svc_can_log_append_rx(&log, &first) == SVC_CAN_LOG_OK);
    assert(svc_can_log_append_rx(&log, &can2) == SVC_CAN_LOG_OK);
    assert(svc_can_log_append_rx(&log, &second) == SVC_CAN_LOG_OK);
    assert(svc_can1_log_queue_push_isr(&queue, &first) == SVC_CAN1_LOG_QUEUE_OK);
    assert(svc_can1_log_queue_push_isr(&queue, &second) == SVC_CAN1_LOG_QUEUE_OK);

    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE,
        .sync_result = true,
    };
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 1000U);
    size_t persisted = 0U;
    assert(svc_can_log_persist_can1(&persistence, &queue, 8U, &persisted) == SVC_CAN_LOG_PERSIST_OK);
    assert(persisted == 2U);
    assert(storage.size == 2U * SVC_CAN_LOG_RECORD_SIZE);
    assert(storage.sync_count == 1U);
    assert(persistence.next_sequence == 1002U);
    assert(persistence.persisted_can1_count == 2U);
    assert(svc_can1_log_queue_count(&queue) == 0U);
    assert(svc_can_log_count(&log) == 3U);

    svc_can_frame_t retained = {0};
    assert(svc_can_log_get(&log, 1U, &retained));
    assert(retained.port == SVC_CAN_PORT_CAN2_EXPANSION);
    assert(retained.id == 0x456U);

    svc_can_frame_t decoded = {0};
    uint64_t sequence = 0U;
    assert(svc_can_log_record_decode(&storage.bytes[0], &decoded, &sequence));
    assert(sequence == 1000U);
    assert(decoded.id == first.id);
    assert(decoded.data[0] == 0xA0U);
    assert(decoded.timestamp_us == first.timestamp_us);
    assert(svc_can_log_record_decode(&storage.bytes[SVC_CAN_LOG_RECORD_SIZE], &decoded, &sequence));
    assert(sequence == 1001U);
    assert(decoded.id == second.id);
    assert(decoded.extended_id);
}

static void test_write_failure_retains_frames_for_retry(void)
{
    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x321U, 0x10U);
    assert(svc_can1_log_queue_push_isr(&queue, &frame) == SVC_CAN1_LOG_QUEUE_OK);
    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE - 1U,
        .sync_result = true,
    };
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 9U);

    assert(svc_can_log_persist_can1(&persistence, &queue, 1U, NULL) == SVC_CAN_LOG_PERSIST_WRITE_FAILED);
    assert(svc_can1_log_queue_count(&queue) == 1U);
    assert(persistence.next_sequence == 9U);
    assert(persistence.write_failure_count == 1U);
    assert(storage.sync_count == 0U);
}

static void test_sync_failure_retains_frames_for_retry(void)
{
    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x654U, 0x20U);
    assert(svc_can1_log_queue_push_isr(&queue, &frame) == SVC_CAN1_LOG_QUEUE_OK);
    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE,
        .sync_result = false,
    };
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 12U);

    assert(svc_can_log_persist_can1(&persistence, &queue, 1U, NULL) == SVC_CAN_LOG_PERSIST_SYNC_FAILED);
    assert(svc_can1_log_queue_count(&queue) == 1U);
    assert(persistence.next_sequence == 12U);
    assert(persistence.sync_failure_count == 1U);
}

static void test_record_crc_rejects_corruption(void)
{
    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x7FFU, 0x30U);
    assert(svc_can1_log_queue_push_isr(&queue, &frame) == SVC_CAN1_LOG_QUEUE_OK);
    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE,
        .sync_result = true,
    };
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 0U);
    assert(svc_can_log_persist_can1(&persistence, &queue, 1U, NULL) == SVC_CAN_LOG_PERSIST_OK);
    storage.bytes[25] ^= 0x01U;

    svc_can_frame_t decoded = {0};
    uint64_t sequence = 0U;
    assert(!svc_can_log_record_decode(storage.bytes, &decoded, &sequence));
}

static void test_persistence_empty_and_invalid_backends_fail_safe(void)
{
    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(
        &persistence,
        (svc_can_log_storage_backend_t){0},
        0U);
    assert(svc_can_log_persist_can1(&persistence, &queue, 1U, NULL) == SVC_CAN_LOG_PERSIST_BACKEND_UNAVAILABLE);

    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE,
        .sync_result = true,
    };
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 0U);
    assert(svc_can_log_persist_can1(&persistence, &queue, 1U, NULL) == SVC_CAN_LOG_PERSIST_NO_DATA);
    assert(svc_can_log_persist_can1(NULL, &queue, 1U, NULL) == SVC_CAN_LOG_PERSIST_INVALID_ARGUMENT);
    assert(svc_can_log_persist_can1(&persistence, NULL, 1U, NULL) == SVC_CAN_LOG_PERSIST_INVALID_ARGUMENT);
}

static void test_isr_append_during_sync_batch_cannot_replace_consumed_frames(void)
{
    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    const svc_can_frame_t first = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x101U, 1U);
    const svc_can_frame_t second = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x102U, 2U);
    const svc_can_frame_t third = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x103U, 3U);
    const svc_can_frame_t fourth = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x104U, 4U);
    assert(svc_can1_log_queue_push_isr(&queue, &first) == SVC_CAN1_LOG_QUEUE_OK);
    assert(svc_can1_log_queue_push_isr(&queue, &second) == SVC_CAN1_LOG_QUEUE_OK);

    storage_mock_t storage = {
        .write_limit = SVC_CAN_LOG_RECORD_SIZE,
        .sync_result = true,
        .inject_queue = &queue,
        .injected_frames = {third, fourth},
        .inject_during_write = true,
    };
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(&persistence, backend_for(&storage), 50U);
    assert(svc_can_log_persist_can1(&persistence, &queue, 2U, NULL) == SVC_CAN_LOG_PERSIST_OK);

    assert(svc_can1_log_queue_count(&queue) == 2U);
    svc_can_frame_t retained = {0};
    assert(svc_can1_log_queue_peek(&queue, 0U, &retained));
    assert(retained.id == third.id);
    assert(svc_can1_log_queue_peek(&queue, 1U, &retained));
    assert(retained.id == fourth.id);

    svc_can_frame_t decoded = {0};
    uint64_t sequence = 0U;
    assert(svc_can_log_record_decode(storage.bytes, &decoded, &sequence));
    assert(decoded.id == first.id && sequence == 50U);
    assert(svc_can_log_record_decode(
        &storage.bytes[SVC_CAN_LOG_RECORD_SIZE],
        &decoded,
        &sequence));
    assert(decoded.id == second.id && sequence == 51U);
}

static void test_can1_queue_is_bounded_and_rejects_other_ports(void)
{
    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    const svc_can_frame_t can2 = frame_for(SVC_CAN_PORT_CAN2_EXPANSION, 1U, 1U);
    assert(svc_can1_log_queue_push_isr(&queue, &can2) == SVC_CAN1_LOG_QUEUE_INVALID_FRAME);

    for (size_t index = 0U; index + 1U < SVC_CAN1_LOG_QUEUE_CAPACITY; ++index) {
        const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, (uint32_t)index, 0U);
        assert(svc_can1_log_queue_push_isr(&queue, &frame) == SVC_CAN1_LOG_QUEUE_OK);
    }
    const svc_can_frame_t overflow = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 999U, 0U);
    assert(svc_can1_log_queue_push_isr(&queue, &overflow) == SVC_CAN1_LOG_QUEUE_FULL);
    assert(svc_can1_log_queue_count(&queue) == SVC_CAN1_LOG_QUEUE_CAPACITY - 1U);
    assert(svc_can1_log_queue_dropped_count(&queue) == 1U);
}

static void test_fatfs_adapter_writes_header_preallocates_and_rotates(void)
{
    fat_mock_t fat = {0};
    svc_can_log_fatfs_t adapter = {0};
    const svc_can_log_fatfs_config_t config = fat_config(
        7U,
        SVC_CAN_LOG_SESSION_HEADER_SIZE + 2U * SVC_CAN_LOG_RECORD_SIZE);
    assert(svc_can_log_fatfs_start(
               &adapter,
               fat_port_for(&fat),
               config,
               100U) == SVC_CAN_LOG_FATFS_OK);
    assert(fat.files[0].size == SVC_CAN_LOG_SESSION_HEADER_SIZE);
    assert(memcmp(fat.files[0].bytes, "SVCS", 4U) == 0);
    assert(fat.files[0].bytes[4] == SVC_CAN_LOG_SESSION_FORMAT_VERSION);
    assert(fat.files[0].bytes[5] ==
        (uint8_t)SVC_CAN_LOG_SESSION_REASON_IGNITION_WAKE);
    assert(memcmp(&fat.files[0].bytes[44], "LB-100-REV1", 11U) == 0);
    assert(memcmp(&fat.files[0].bytes[60], "0.4.0-dev", 9U) == 0);
    assert(memcmp(&fat.files[0].bytes[84], "LB1-EVT-00001", 13U) == 0);
    assert(fat.files[0].reserved_size == config.preallocation_bytes);

    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    for (uint32_t index = 0U; index < 3U; ++index) {
        const svc_can_frame_t frame = frame_for(
            SVC_CAN_PORT_CAN1_VEHICLE,
            0x200U + index,
            (uint8_t)index);
        assert(svc_can1_log_queue_push_isr(&queue, &frame) == SVC_CAN1_LOG_QUEUE_OK);
    }
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(
        &persistence,
        svc_can_log_fatfs_backend(&adapter),
        adapter.next_sequence);
    assert(svc_can_log_persist_can1(&persistence, &queue, 3U, NULL) == SVC_CAN_LOG_PERSIST_OK);
    assert(adapter.rotation_count == 1U);
    assert(adapter.active_session_id == 8U);
    assert(fat.files[0].size == config.rotation_bytes);
    assert(fat.files[1].size == SVC_CAN_LOG_SESSION_HEADER_SIZE + SVC_CAN_LOG_RECORD_SIZE);
    assert(memcmp(fat.files[1].bytes, "SVCS", 4U) == 0);
    assert(adapter.next_sequence == 103U);
    assert(svc_can_log_fatfs_stop(&adapter));

    svc_can_log_fatfs_t rebooted = {0};
    assert(svc_can_log_fatfs_start(
               &rebooted,
               fat_port_for(&fat),
               config,
               0U) == SVC_CAN_LOG_FATFS_OK);
    assert(rebooted.active_session_id == 8U);
    assert(rebooted.recovered_record_count == 1U);
    assert(rebooted.next_sequence == 103U);
    assert(svc_can_log_fatfs_stop(&rebooted));
}

static void test_fatfs_adapter_recovers_torn_tail_after_power_loss(void)
{
    fat_mock_t fat = {0};
    svc_can_log_fatfs_t first_boot = {0};
    const svc_can_log_fatfs_config_t config = fat_config(21U, 400U);
    assert(svc_can_log_fatfs_start(
               &first_boot,
               fat_port_for(&fat),
               config,
               500U) == SVC_CAN_LOG_FATFS_OK);

    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    for (uint32_t index = 0U; index < 2U; ++index) {
        const svc_can_frame_t frame = frame_for(
            SVC_CAN_PORT_CAN1_VEHICLE,
            0x300U + index,
            (uint8_t)index);
        assert(svc_can1_log_queue_push_isr(&queue, &frame) == SVC_CAN1_LOG_QUEUE_OK);
    }
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(
        &persistence,
        svc_can_log_fatfs_backend(&first_boot),
        first_boot.next_sequence);
    assert(svc_can_log_persist_can1(&persistence, &queue, 2U, NULL) == SVC_CAN_LOG_PERSIST_OK);

    const uint8_t torn_record[7] = {
        'S', 'V', 'C', 'L', SVC_CAN_LOG_RECORD_FORMAT_VERSION, 1U, 0U};
    assert(fat_append(&fat, torn_record, sizeof(torn_record)) == sizeof(torn_record));
    fat.current = NULL; /* Simulated reset: no orderly sync/close. */

    svc_can_log_fatfs_t recovered = {0};
    assert(svc_can_log_fatfs_start(
               &recovered,
               fat_port_for(&fat),
               config,
               0U) == SVC_CAN_LOG_FATFS_OK);
    assert(recovered.recovered_record_count == 2U);
    assert(recovered.recovery_truncate_count == 1U);
    assert(recovered.logical_size ==
        SVC_CAN_LOG_SESSION_HEADER_SIZE + 2U * SVC_CAN_LOG_RECORD_SIZE);
    assert(recovered.next_sequence == 502U);
    assert(fat.truncate_count == 1U);
    assert(svc_can_log_fatfs_stop(&recovered));
}

static void test_logger_task_owns_queue_consumption(void)
{
    fat_mock_t fat = {0};
    svc_can_log_fatfs_t adapter = {0};
    const svc_can_log_fatfs_config_t config = fat_config(30U, 400U);
    assert(svc_can_log_fatfs_start(
               &adapter,
               fat_port_for(&fat),
               config,
               10U) == SVC_CAN_LOG_FATFS_OK);
    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    svc_can_log_task_t task = {0};
    assert(svc_can_log_task_init(&task, &queue, &adapter, 4U));
    assert(svc_can_log_task_run_once(&task, NULL) == SVC_CAN_LOG_TASK_IDLE);

    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x555U, 5U);
    assert(svc_can1_log_queue_push_isr(&queue, &frame) == SVC_CAN1_LOG_QUEUE_OK);
    size_t persisted = 0U;
    assert(svc_can_log_task_run_once(&task, &persisted) == SVC_CAN_LOG_TASK_FLUSHED);
    assert(persisted == 1U);
    assert(task.successful_batch_count == 1U);
    assert(svc_can1_log_queue_count(&queue) == 0U);
    assert(svc_can_log_fatfs_stop(&adapter));
}

static void test_stop_closes_even_when_sync_fails(void)
{
    fat_mock_t fat = {0};
    svc_can_log_fatfs_t adapter = {0};
    const svc_can_log_fatfs_config_t config = fat_config(40U, 400U);
    assert(svc_can_log_fatfs_start(
               &adapter,
               fat_port_for(&fat),
               config,
               0U) == SVC_CAN_LOG_FATFS_OK);

    fat.fail_next_sync = true;
    assert(!svc_can_log_fatfs_stop(&adapter));
    assert(fat.sync_count == 2U); /* Header sync plus stop sync. */
    assert(fat.close_count == 1U);
    assert(fat.current == NULL);
    assert(adapter.sync_failure_count == 1U);
    assert(!adapter.active);
    assert(!adapter.handle_open);
}

static void test_session_identity_fields_are_mandatory(void)
{
    fat_mock_t fat = {0};
    svc_can_log_fatfs_t adapter = {0};
    svc_can_log_fatfs_config_t config = fat_config(45U, 400U);
    config.board_serial[0] = '\0';
    assert(svc_can_log_fatfs_start(
               &adapter,
               fat_port_for(&fat),
               config,
               0U) == SVC_CAN_LOG_FATFS_INVALID_ARGUMENT);
    assert(fat.mount_count == 0U);
    assert(!adapter.active);
}

static void test_rotation_closes_even_when_sync_fails(void)
{
    fat_mock_t fat = {0};
    svc_can_log_fatfs_t adapter = {0};
    const svc_can_log_fatfs_config_t config = fat_config(
        50U,
        SVC_CAN_LOG_SESSION_HEADER_SIZE + SVC_CAN_LOG_RECORD_SIZE);
    assert(svc_can_log_fatfs_start(
               &adapter,
               fat_port_for(&fat),
               config,
               10U) == SVC_CAN_LOG_FATFS_OK);

    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    const svc_can_frame_t first = frame_for(
        SVC_CAN_PORT_CAN1_VEHICLE,
        0x501U,
        1U);
    const svc_can_frame_t second = frame_for(
        SVC_CAN_PORT_CAN1_VEHICLE,
        0x502U,
        2U);
    assert(svc_can1_log_queue_push_isr(&queue, &first) ==
        SVC_CAN1_LOG_QUEUE_OK);
    assert(svc_can1_log_queue_push_isr(&queue, &second) ==
        SVC_CAN1_LOG_QUEUE_OK);
    svc_can_log_persistence_t persistence = {0};
    svc_can_log_persistence_init(
        &persistence,
        svc_can_log_fatfs_backend(&adapter),
        10U);
    fat.fail_next_sync = true;
    assert(svc_can_log_persist_can1(&persistence, &queue, 2U, NULL) ==
        SVC_CAN_LOG_PERSIST_WRITE_FAILED);
    assert(fat.close_count == 1U);
    assert(fat.current == NULL);
    assert(!adapter.active);
    assert(!adapter.handle_open);
    assert(svc_can1_log_queue_count(&queue) == 2U);
}

static void test_logger_restarts_and_reopens_after_card_failure(void)
{
    fat_mock_t fat = {0};
    svc_can_log_fatfs_t adapter = {0};
    const svc_can_log_fatfs_config_t config = fat_config(60U, 400U);
    assert(svc_can_log_fatfs_start(
               &adapter,
               fat_port_for(&fat),
               config,
               100U) == SVC_CAN_LOG_FATFS_OK);
    svc_can1_log_queue_t queue = {0};
    svc_can1_log_queue_init(&queue);
    svc_can_log_task_t task = {0};
    assert(svc_can_log_task_init(&task, &queue, &adapter, 4U));
    const svc_can_frame_t frame = frame_for(
        SVC_CAN_PORT_CAN1_VEHICLE,
        0x601U,
        6U);
    assert(svc_can1_log_queue_push_isr(&queue, &frame) ==
        SVC_CAN1_LOG_QUEUE_OK);

    fat.fail_next_sync = true;
    assert(svc_can_log_task_run_once(&task, NULL) ==
        SVC_CAN_LOG_TASK_RETRY_LATER);
    assert(!adapter.active);
    assert(adapter.handle_open);
    assert(svc_can1_log_queue_count(&queue) == 1U);

    assert(svc_can_log_task_restart_storage(&task) == SVC_CAN_LOG_FATFS_OK);
    assert(adapter.active);
    assert(adapter.restart_count == 1U);
    assert(task.storage_restart_count == 1U);
    assert(task.persistence.next_sequence == 101U);
    assert(fat.mount_count == 2U);
    assert(fat.open_count == 2U);
    assert(fat.close_count == 1U);

    assert(svc_can_log_task_run_once(&task, NULL) ==
        SVC_CAN_LOG_TASK_FLUSHED);
    assert(svc_can1_log_queue_count(&queue) == 0U);
    assert(task.persistence.next_sequence == 102U);
    assert(svc_can_log_fatfs_stop(&adapter));
}

static void test_restart_retries_a_failed_close_before_reopen(void)
{
    fat_mock_t fat = {0};
    svc_can_log_fatfs_t adapter = {0};
    const svc_can_log_fatfs_config_t config = fat_config(70U, 400U);
    assert(svc_can_log_fatfs_start(
               &adapter,
               fat_port_for(&fat),
               config,
               0U) == SVC_CAN_LOG_FATFS_OK);
    fat.fail_next_close = true;
    assert(!svc_can_log_fatfs_stop(&adapter));
    assert(adapter.handle_open);
    assert(adapter.close_failure_count == 1U);

    assert(svc_can_log_fatfs_restart(&adapter, 0U) ==
        SVC_CAN_LOG_FATFS_OK);
    assert(adapter.active);
    assert(adapter.restart_count == 1U);
    assert(adapter.close_failure_count == 1U);
    assert(fat.close_count == 2U);
    assert(svc_can_log_fatfs_stop(&adapter));
}

static void test_old_or_mismatched_header_rolls_to_new_session(void)
{
    fat_mock_t fat = {0};
    fat.files[0].exists = true;
    fat.files[0].session_id = 80U;
    fat.files[0].size = 64U;
    memcpy(fat.files[0].bytes, "SVCS", 4U);
    fat.files[0].bytes[4] = 1U;

    svc_can_log_fatfs_t adapter = {0};
    const svc_can_log_fatfs_config_t config = fat_config(80U, 400U);
    assert(svc_can_log_fatfs_start(
               &adapter,
               fat_port_for(&fat),
               config,
               900U) == SVC_CAN_LOG_FATFS_OK);
    assert(adapter.active_session_id == 81U);
    assert(adapter.format_rollover_count == 1U);
    assert(fat.files[0].size == 64U);
    assert(fat.files[1].size == SVC_CAN_LOG_SESSION_HEADER_SIZE);
    assert(fat.files[1].bytes[4] == SVC_CAN_LOG_SESSION_FORMAT_VERSION);
    assert(svc_can_log_fatfs_stop(&adapter));
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
    test_persists_can1_queue_without_mutating_diagnostic_log();
    test_write_failure_retains_frames_for_retry();
    test_sync_failure_retains_frames_for_retry();
    test_record_crc_rejects_corruption();
    test_persistence_empty_and_invalid_backends_fail_safe();
    test_isr_append_during_sync_batch_cannot_replace_consumed_frames();
    test_can1_queue_is_bounded_and_rejects_other_ports();
    test_fatfs_adapter_writes_header_preallocates_and_rotates();
    test_fatfs_adapter_recovers_torn_tail_after_power_loss();
    test_logger_task_owns_queue_consumption();
    test_stop_closes_even_when_sync_fails();
    test_session_identity_fields_are_mandatory();
    test_rotation_closes_even_when_sync_fails();
    test_logger_restarts_and_reopens_after_card_failure();
    test_restart_retries_a_failed_close_before_reopen();
    test_old_or_mismatched_header_rolls_to_new_session();
    return 0;
}
