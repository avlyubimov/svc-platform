#include "can_log_fatfs.h"

#include <limits.h>
#include <string.h>

#define SVC_CAN_LOG_SESSION_CRC_OFFSET 60U

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

static void put_u16(uint8_t *destination, uint16_t value)
{
    destination[0] = (uint8_t)value;
    destination[1] = (uint8_t)(value >> 8U);
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

static uint16_t get_u16(const uint8_t *source)
{
    return (uint16_t)((uint16_t)source[0] | ((uint16_t)source[1] << 8U));
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

static void encode_header(
    uint8_t header[SVC_CAN_LOG_SESSION_HEADER_SIZE],
    uint32_t session_id,
    uint64_t started_ms,
    uint64_t initial_sequence,
    uint64_t rotation_bytes)
{
    memset(header, 0, SVC_CAN_LOG_SESSION_HEADER_SIZE);
    header[0] = 'S';
    header[1] = 'V';
    header[2] = 'C';
    header[3] = 'S';
    header[4] = SVC_CAN_LOG_SESSION_FORMAT_VERSION;
    put_u16(&header[6], SVC_CAN_LOG_SESSION_HEADER_SIZE);
    put_u32(&header[8], session_id);
    put_u64(&header[12], started_ms);
    put_u64(&header[20], initial_sequence);
    put_u32(&header[28], SVC_CAN_LOG_RECORD_SIZE);
    put_u64(&header[32], rotation_bytes);
    put_u32(
        &header[SVC_CAN_LOG_SESSION_CRC_OFFSET],
        crc32(header, SVC_CAN_LOG_SESSION_CRC_OFFSET));
}

static bool decode_header(
    const uint8_t header[SVC_CAN_LOG_SESSION_HEADER_SIZE],
    uint32_t expected_session_id,
    uint64_t expected_rotation_bytes,
    uint64_t *initial_sequence)
{
    if (header[0] != 'S' || header[1] != 'V' || header[2] != 'C' || header[3] != 'S' ||
        header[4] != SVC_CAN_LOG_SESSION_FORMAT_VERSION ||
        get_u16(&header[6]) != SVC_CAN_LOG_SESSION_HEADER_SIZE ||
        get_u32(&header[8]) != expected_session_id ||
        get_u32(&header[28]) != SVC_CAN_LOG_RECORD_SIZE ||
        get_u64(&header[32]) != expected_rotation_bytes ||
        get_u32(&header[SVC_CAN_LOG_SESSION_CRC_OFFSET]) !=
            crc32(header, SVC_CAN_LOG_SESSION_CRC_OFFSET)) {
        return false;
    }
    *initial_sequence = get_u64(&header[20]);
    return true;
}

static bool port_is_complete(const svc_can_log_fatfs_port_t *port)
{
    return port->mount != NULL && port->find_latest_session != NULL &&
           port->open_session != NULL &&
           port->read_at != NULL && port->append != NULL &&
           port->sync != NULL && port->preallocate != NULL &&
           port->truncate != NULL && port->close != NULL;
}

static svc_can_log_fatfs_status_t prepare_new_session(
    svc_can_log_fatfs_t *adapter,
    uint32_t session_id,
    uint64_t initial_sequence)
{
    uint8_t header[SVC_CAN_LOG_SESSION_HEADER_SIZE] = {0U};
    encode_header(
        header,
        session_id,
        adapter->config.started_ms,
        initial_sequence,
        adapter->config.rotation_bytes);
    if (adapter->port.append(adapter->port.context, header, sizeof(header)) != sizeof(header) ||
        !adapter->port.sync(adapter->port.context)) {
        return SVC_CAN_LOG_FATFS_IO_FAILED;
    }
    const uint64_t reserve = adapter->config.preallocation_bytes < adapter->config.rotation_bytes
        ? adapter->config.preallocation_bytes
        : adapter->config.rotation_bytes;
    if (reserve > SVC_CAN_LOG_SESSION_HEADER_SIZE &&
        !adapter->port.preallocate(adapter->port.context, reserve)) {
        return SVC_CAN_LOG_FATFS_PREALLOCATE_FAILED;
    }
    adapter->active_session_id = session_id;
    adapter->logical_size = SVC_CAN_LOG_SESSION_HEADER_SIZE;
    adapter->next_sequence = initial_sequence;
    adapter->active = true;
    return SVC_CAN_LOG_FATFS_OK;
}

static svc_can_log_fatfs_status_t recover_session(
    svc_can_log_fatfs_t *adapter,
    uint64_t file_size)
{
    uint8_t header[SVC_CAN_LOG_SESSION_HEADER_SIZE] = {0U};
    if (file_size < sizeof(header) ||
        adapter->port.read_at(adapter->port.context, 0U, header, sizeof(header)) != sizeof(header)) {
        return SVC_CAN_LOG_FATFS_HEADER_INVALID;
    }
    uint64_t next_sequence = 0U;
    if (!decode_header(
            header,
            adapter->active_session_id,
            adapter->config.rotation_bytes,
            &next_sequence)) {
        return SVC_CAN_LOG_FATFS_HEADER_INVALID;
    }

    uint64_t valid_size = SVC_CAN_LOG_SESSION_HEADER_SIZE;
    uint32_t recovered = 0U;
    while (file_size - valid_size >= SVC_CAN_LOG_RECORD_SIZE) {
        uint8_t record[SVC_CAN_LOG_RECORD_SIZE] = {0U};
        svc_can_frame_t frame = {0};
        uint64_t sequence = 0U;
        if (adapter->port.read_at(
                adapter->port.context,
                valid_size,
                record,
                sizeof(record)) != sizeof(record) ||
            !svc_can_log_record_decode(record, &frame, &sequence)) {
            break;
        }
        if (sequence >= next_sequence && sequence < UINT64_MAX) {
            next_sequence = sequence + 1U;
        }
        valid_size += SVC_CAN_LOG_RECORD_SIZE;
        if (recovered < UINT32_MAX) {
            ++recovered;
        }
    }

    if (valid_size != file_size) {
        if (!adapter->port.truncate(adapter->port.context, valid_size) ||
            !adapter->port.sync(adapter->port.context)) {
            return SVC_CAN_LOG_FATFS_RECOVERY_FAILED;
        }
        ++adapter->recovery_truncate_count;
    }
    adapter->logical_size = valid_size;
    adapter->next_sequence = next_sequence;
    adapter->recovered_record_count = recovered;
    adapter->active = true;
    return SVC_CAN_LOG_FATFS_OK;
}

svc_can_log_fatfs_status_t svc_can_log_fatfs_start(
    svc_can_log_fatfs_t *adapter,
    svc_can_log_fatfs_port_t port,
    svc_can_log_fatfs_config_t config,
    uint64_t initial_sequence)
{
    if (adapter == NULL ||
        config.rotation_bytes < SVC_CAN_LOG_SESSION_HEADER_SIZE + SVC_CAN_LOG_RECORD_SIZE ||
        config.preallocation_bytes < SVC_CAN_LOG_SESSION_HEADER_SIZE) {
        return SVC_CAN_LOG_FATFS_INVALID_ARGUMENT;
    }
    if (!port_is_complete(&port)) {
        return SVC_CAN_LOG_FATFS_PORT_UNAVAILABLE;
    }
    *adapter = (svc_can_log_fatfs_t){
        .port = port,
        .config = config,
        .active_session_id = config.session_id,
    };
    if (!port.mount(port.context)) {
        return SVC_CAN_LOG_FATFS_MOUNT_FAILED;
    }
    bool found = false;
    uint32_t selected_session_id = config.session_id;
    if (!port.find_latest_session(
            port.context,
            config.session_id,
            &found,
            &selected_session_id) ||
        (found && selected_session_id < config.session_id)) {
        return SVC_CAN_LOG_FATFS_OPEN_FAILED;
    }
    if (!found) {
        selected_session_id = config.session_id;
    }
    adapter->active_session_id = selected_session_id;
    bool created = false;
    uint64_t file_size = 0U;
    if (!port.open_session(
            port.context,
            selected_session_id,
            &created,
            &file_size) ||
        (found && created)) {
        return SVC_CAN_LOG_FATFS_OPEN_FAILED;
    }
    if (created || file_size == 0U) {
        return prepare_new_session(adapter, selected_session_id, initial_sequence);
    }
    return recover_session(adapter, file_size);
}

static bool rotate_session(svc_can_log_fatfs_t *adapter, uint64_t initial_sequence)
{
    if (!adapter->port.sync(adapter->port.context) ||
        !adapter->port.close(adapter->port.context) ||
        adapter->active_session_id == UINT32_MAX) {
        /* The handle state is no longer trustworthy after a failed close. */
        adapter->active = false;
        return false;
    }
    const uint32_t next_session = adapter->active_session_id + 1U;
    bool created = false;
    uint64_t file_size = 0U;
    if (!adapter->port.open_session(
            adapter->port.context,
            next_session,
            &created,
            &file_size) ||
        !created || file_size != 0U ||
        prepare_new_session(adapter, next_session, initial_sequence) != SVC_CAN_LOG_FATFS_OK) {
        adapter->active = false;
        return false;
    }
    ++adapter->rotation_count;
    return true;
}

static size_t storage_write(void *context, const uint8_t *data, size_t size)
{
    svc_can_log_fatfs_t *adapter = context;
    svc_can_frame_t frame = {0};
    uint64_t sequence = 0U;
    if (adapter == NULL || !adapter->active || data == NULL ||
        size != SVC_CAN_LOG_RECORD_SIZE ||
        !svc_can_log_record_decode(data, &frame, &sequence)) {
        return 0U;
    }
    if (adapter->logical_size + size > adapter->config.rotation_bytes &&
        !rotate_session(adapter, sequence)) {
        return 0U;
    }
    if (adapter->port.append(adapter->port.context, data, size) != size) {
        (void)adapter->port.truncate(adapter->port.context, adapter->logical_size);
        (void)adapter->port.sync(adapter->port.context);
        return 0U;
    }
    adapter->logical_size += size;
    if (sequence >= adapter->next_sequence && sequence < UINT64_MAX) {
        adapter->next_sequence = sequence + 1U;
    }
    return size;
}

static bool storage_sync(void *context)
{
    svc_can_log_fatfs_t *adapter = context;
    return adapter != NULL && adapter->active &&
           adapter->port.sync(adapter->port.context);
}

svc_can_log_storage_backend_t svc_can_log_fatfs_backend(svc_can_log_fatfs_t *adapter)
{
    return (svc_can_log_storage_backend_t){
        .context = adapter,
        .write = storage_write,
        .sync = storage_sync,
    };
}

bool svc_can_log_fatfs_stop(svc_can_log_fatfs_t *adapter)
{
    if (adapter == NULL || !adapter->active) {
        return false;
    }
    const bool result = adapter->port.sync(adapter->port.context) &&
        adapter->port.close(adapter->port.context);
    adapter->active = false;
    return result;
}
