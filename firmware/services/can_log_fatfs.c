#include "can_log_fatfs.h"

#include <limits.h>
#include <string.h>

#define SVC_CAN_LOG_HEADER_REASON_OFFSET 5U
#define SVC_CAN_LOG_HEADER_BITRATE_OFFSET 12U
#define SVC_CAN_LOG_HEADER_STARTED_US_OFFSET 16U
#define SVC_CAN_LOG_HEADER_INITIAL_SEQUENCE_OFFSET 24U
#define SVC_CAN_LOG_HEADER_ROTATION_OFFSET 32U
#define SVC_CAN_LOG_HEADER_RECORD_SIZE_OFFSET 40U
#define SVC_CAN_LOG_HEADER_HARDWARE_VERSION_OFFSET 44U
#define SVC_CAN_LOG_HEADER_FIRMWARE_VERSION_OFFSET 60U
#define SVC_CAN_LOG_HEADER_BOARD_SERIAL_OFFSET 84U
#define SVC_CAN_LOG_SESSION_CRC_OFFSET 124U

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

static void increment_counter(uint32_t *counter)
{
    if (*counter < UINT32_MAX) {
        ++(*counter);
    }
}

static uint32_t saturating_add(uint32_t first, uint32_t second)
{
    return UINT32_MAX - first < second ? UINT32_MAX : first + second;
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

static bool string_field_is_valid(const char *value, size_t capacity)
{
    return value != NULL && value[0] != '\0' &&
           memchr(value, '\0', capacity) != NULL;
}

static bool session_reason_is_valid(svc_can_log_session_reason_t reason)
{
    return reason >= SVC_CAN_LOG_SESSION_REASON_BOOT &&
           reason <= SVC_CAN_LOG_SESSION_REASON_DIAGNOSTIC;
}

static bool config_is_valid(const svc_can_log_fatfs_config_t *config)
{
    return config != NULL &&
           config->rotation_bytes >=
               SVC_CAN_LOG_SESSION_HEADER_SIZE + SVC_CAN_LOG_RECORD_SIZE &&
           config->preallocation_bytes >= SVC_CAN_LOG_SESSION_HEADER_SIZE &&
           config->can_bitrate != 0U &&
           session_reason_is_valid(config->session_reason) &&
           string_field_is_valid(
               config->hardware_version,
               sizeof(config->hardware_version)) &&
           string_field_is_valid(
               config->firmware_version,
               sizeof(config->firmware_version)) &&
           string_field_is_valid(config->board_serial, sizeof(config->board_serial));
}

static void encode_string_field(
    uint8_t *destination,
    size_t capacity,
    const char *value)
{
    size_t length = 0U;
    while (length < capacity && value[length] != '\0') {
        ++length;
    }
    memset(destination, 0, capacity);
    memcpy(destination, value, length);
}

static bool encoded_string_matches(
    const uint8_t *encoded,
    size_t capacity,
    const char *expected)
{
    size_t index = 0U;
    while (index < capacity && expected[index] != '\0') {
        if (encoded[index] != (uint8_t)expected[index]) {
            return false;
        }
        ++index;
    }
    if (index == capacity) {
        return false;
    }
    while (index < capacity) {
        if (encoded[index] != 0U) {
            return false;
        }
        ++index;
    }
    return true;
}

static void encode_header(
    uint8_t header[SVC_CAN_LOG_SESSION_HEADER_SIZE],
    const svc_can_log_fatfs_config_t *config,
    uint32_t session_id,
    uint64_t initial_sequence)
{
    memset(header, 0, SVC_CAN_LOG_SESSION_HEADER_SIZE);
    header[0] = 'S';
    header[1] = 'V';
    header[2] = 'C';
    header[3] = 'S';
    header[4] = SVC_CAN_LOG_SESSION_FORMAT_VERSION;
    header[SVC_CAN_LOG_HEADER_REASON_OFFSET] = (uint8_t)config->session_reason;
    put_u16(&header[6], SVC_CAN_LOG_SESSION_HEADER_SIZE);
    put_u32(&header[8], session_id);
    put_u32(&header[SVC_CAN_LOG_HEADER_BITRATE_OFFSET], config->can_bitrate);
    put_u64(&header[SVC_CAN_LOG_HEADER_STARTED_US_OFFSET], config->started_us);
    put_u64(
        &header[SVC_CAN_LOG_HEADER_INITIAL_SEQUENCE_OFFSET],
        initial_sequence);
    put_u64(&header[SVC_CAN_LOG_HEADER_ROTATION_OFFSET], config->rotation_bytes);
    put_u32(&header[SVC_CAN_LOG_HEADER_RECORD_SIZE_OFFSET], SVC_CAN_LOG_RECORD_SIZE);
    encode_string_field(
        &header[SVC_CAN_LOG_HEADER_HARDWARE_VERSION_OFFSET],
        SVC_CAN_LOG_HARDWARE_VERSION_SIZE,
        config->hardware_version);
    encode_string_field(
        &header[SVC_CAN_LOG_HEADER_FIRMWARE_VERSION_OFFSET],
        SVC_CAN_LOG_FIRMWARE_VERSION_SIZE,
        config->firmware_version);
    encode_string_field(
        &header[SVC_CAN_LOG_HEADER_BOARD_SERIAL_OFFSET],
        SVC_CAN_LOG_BOARD_SERIAL_SIZE,
        config->board_serial);
    put_u32(
        &header[SVC_CAN_LOG_SESSION_CRC_OFFSET],
        crc32(header, SVC_CAN_LOG_SESSION_CRC_OFFSET));
}

static bool decode_header(
    const uint8_t header[SVC_CAN_LOG_SESSION_HEADER_SIZE],
    const svc_can_log_fatfs_config_t *config,
    uint32_t expected_session_id,
    uint64_t *initial_sequence)
{
    if (header[0] != 'S' || header[1] != 'V' ||
        header[2] != 'C' || header[3] != 'S' ||
        header[4] != SVC_CAN_LOG_SESSION_FORMAT_VERSION ||
        header[SVC_CAN_LOG_HEADER_REASON_OFFSET] !=
            (uint8_t)config->session_reason ||
        get_u16(&header[6]) != SVC_CAN_LOG_SESSION_HEADER_SIZE ||
        get_u32(&header[8]) != expected_session_id ||
        get_u32(&header[SVC_CAN_LOG_HEADER_BITRATE_OFFSET]) !=
            config->can_bitrate ||
        get_u64(&header[SVC_CAN_LOG_HEADER_ROTATION_OFFSET]) !=
            config->rotation_bytes ||
        get_u32(&header[SVC_CAN_LOG_HEADER_RECORD_SIZE_OFFSET]) !=
            SVC_CAN_LOG_RECORD_SIZE ||
        !encoded_string_matches(
            &header[SVC_CAN_LOG_HEADER_HARDWARE_VERSION_OFFSET],
            SVC_CAN_LOG_HARDWARE_VERSION_SIZE,
            config->hardware_version) ||
        !encoded_string_matches(
            &header[SVC_CAN_LOG_HEADER_FIRMWARE_VERSION_OFFSET],
            SVC_CAN_LOG_FIRMWARE_VERSION_SIZE,
            config->firmware_version) ||
        !encoded_string_matches(
            &header[SVC_CAN_LOG_HEADER_BOARD_SERIAL_OFFSET],
            SVC_CAN_LOG_BOARD_SERIAL_SIZE,
            config->board_serial) ||
        get_u32(&header[SVC_CAN_LOG_SESSION_CRC_OFFSET]) !=
            crc32(header, SVC_CAN_LOG_SESSION_CRC_OFFSET)) {
        return false;
    }
    *initial_sequence = get_u64(
        &header[SVC_CAN_LOG_HEADER_INITIAL_SEQUENCE_OFFSET]);
    return true;
}

static bool port_is_complete(const svc_can_log_fatfs_port_t *port)
{
    return port != NULL && port->mount != NULL &&
           port->find_latest_session != NULL && port->open_session != NULL &&
           port->read_at != NULL && port->append != NULL &&
           port->sync != NULL && port->preallocate != NULL &&
           port->truncate != NULL && port->close != NULL;
}

static bool close_current(svc_can_log_fatfs_t *adapter, bool attempt_sync)
{
    if (!adapter->handle_open) {
        adapter->active = false;
        return true;
    }

    bool sync_ok = true;
    if (attempt_sync) {
        sync_ok = adapter->port.sync(adapter->port.context);
        if (!sync_ok) {
            increment_counter(&adapter->sync_failure_count);
        }
    }
    const bool close_ok = adapter->port.close(adapter->port.context);
    if (!close_ok) {
        increment_counter(&adapter->close_failure_count);
    }
    adapter->active = false;
    adapter->handle_open = !close_ok;
    return sync_ok && close_ok;
}

static bool open_session(
    svc_can_log_fatfs_t *adapter,
    uint32_t session_id,
    bool *created,
    uint64_t *file_size)
{
    if (!adapter->port.open_session(
            adapter->port.context,
            session_id,
            created,
            file_size)) {
        return false;
    }
    adapter->active_session_id = session_id;
    adapter->handle_open = true;
    return true;
}

static svc_can_log_fatfs_status_t prepare_new_session(
    svc_can_log_fatfs_t *adapter,
    uint32_t session_id,
    uint64_t initial_sequence)
{
    uint8_t header[SVC_CAN_LOG_SESSION_HEADER_SIZE] = {0U};
    encode_header(header, &adapter->config, session_id, initial_sequence);
    if (adapter->port.append(adapter->port.context, header, sizeof(header)) !=
        sizeof(header)) {
        return SVC_CAN_LOG_FATFS_IO_FAILED;
    }
    if (!adapter->port.sync(adapter->port.context)) {
        increment_counter(&adapter->sync_failure_count);
        return SVC_CAN_LOG_FATFS_IO_FAILED;
    }
    const uint64_t reserve =
        adapter->config.preallocation_bytes < adapter->config.rotation_bytes
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
        adapter->port.read_at(
            adapter->port.context,
            0U,
            header,
            sizeof(header)) != sizeof(header)) {
        return SVC_CAN_LOG_FATFS_HEADER_INVALID;
    }
    uint64_t next_sequence = 0U;
    if (!decode_header(
            header,
            &adapter->config,
            adapter->active_session_id,
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
        increment_counter(&recovered);
    }

    if (valid_size != file_size) {
        const bool truncate_ok = adapter->port.truncate(
            adapter->port.context,
            valid_size);
        const bool sync_ok = adapter->port.sync(adapter->port.context);
        if (!sync_ok) {
            increment_counter(&adapter->sync_failure_count);
        }
        if (!truncate_ok || !sync_ok) {
            return SVC_CAN_LOG_FATFS_RECOVERY_FAILED;
        }
        increment_counter(&adapter->recovery_truncate_count);
    }
    adapter->logical_size = valid_size;
    adapter->next_sequence = next_sequence;
    adapter->recovered_record_count = recovered;
    adapter->active = true;
    return SVC_CAN_LOG_FATFS_OK;
}

static svc_can_log_fatfs_status_t create_rollover_after_invalid_header(
    svc_can_log_fatfs_t *adapter,
    uint64_t initial_sequence)
{
    const uint32_t previous_session_id = adapter->active_session_id;
    if (!close_current(adapter, false) || previous_session_id == UINT32_MAX) {
        return SVC_CAN_LOG_FATFS_HEADER_INVALID;
    }
    const uint32_t next_session_id = previous_session_id + 1U;
    bool created = false;
    uint64_t file_size = 0U;
    if (!open_session(
            adapter,
            next_session_id,
            &created,
            &file_size) ||
        !created || file_size != 0U) {
        (void)close_current(adapter, false);
        return SVC_CAN_LOG_FATFS_OPEN_FAILED;
    }
    const svc_can_log_fatfs_status_t status = prepare_new_session(
        adapter,
        next_session_id,
        initial_sequence);
    if (status != SVC_CAN_LOG_FATFS_OK) {
        (void)close_current(adapter, false);
        return status;
    }
    increment_counter(&adapter->format_rollover_count);
    return SVC_CAN_LOG_FATFS_OK;
}

svc_can_log_fatfs_status_t svc_can_log_fatfs_start(
    svc_can_log_fatfs_t *adapter,
    svc_can_log_fatfs_port_t port,
    svc_can_log_fatfs_config_t config,
    uint64_t initial_sequence)
{
    if (adapter == NULL || !config_is_valid(&config)) {
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
    bool created = false;
    uint64_t file_size = 0U;
    if (!open_session(
            adapter,
            selected_session_id,
            &created,
            &file_size) ||
        (found && created)) {
        (void)close_current(adapter, false);
        return SVC_CAN_LOG_FATFS_OPEN_FAILED;
    }
    if (created || file_size == 0U) {
        const svc_can_log_fatfs_status_t status = prepare_new_session(
            adapter,
            selected_session_id,
            initial_sequence);
        if (status != SVC_CAN_LOG_FATFS_OK) {
            (void)close_current(adapter, false);
        }
        return status;
    }

    const svc_can_log_fatfs_status_t recovery_status = recover_session(
        adapter,
        file_size);
    if (recovery_status == SVC_CAN_LOG_FATFS_OK) {
        return recovery_status;
    }
    if (recovery_status == SVC_CAN_LOG_FATFS_HEADER_INVALID) {
        return create_rollover_after_invalid_header(adapter, initial_sequence);
    }
    (void)close_current(adapter, false);
    return recovery_status;
}

static bool rotate_session(svc_can_log_fatfs_t *adapter, uint64_t initial_sequence)
{
    const uint32_t previous_session_id = adapter->active_session_id;
    const bool session_id_available = previous_session_id < UINT32_MAX;
    const bool closed = close_current(adapter, true);
    if (!closed || !session_id_available) {
        return false;
    }

    const uint32_t next_session = previous_session_id + 1U;
    bool created = false;
    uint64_t file_size = 0U;
    if (!open_session(
            adapter,
            next_session,
            &created,
            &file_size) ||
        !created || file_size != 0U) {
        (void)close_current(adapter, false);
        return false;
    }
    if (prepare_new_session(adapter, next_session, initial_sequence) !=
        SVC_CAN_LOG_FATFS_OK) {
        (void)close_current(adapter, false);
        return false;
    }
    increment_counter(&adapter->rotation_count);
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
        const bool truncate_ok = adapter->port.truncate(
            adapter->port.context,
            adapter->logical_size);
        const bool sync_ok = adapter->port.sync(adapter->port.context);
        if (!sync_ok) {
            increment_counter(&adapter->sync_failure_count);
        }
        if (!truncate_ok || !sync_ok) {
            adapter->active = false;
        }
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
    if (adapter == NULL || !adapter->active) {
        return false;
    }
    const bool result = adapter->port.sync(adapter->port.context);
    if (!result) {
        increment_counter(&adapter->sync_failure_count);
        adapter->active = false;
    }
    return result;
}

svc_can_log_storage_backend_t svc_can_log_fatfs_backend(
    svc_can_log_fatfs_t *adapter)
{
    return (svc_can_log_storage_backend_t){
        .context = adapter,
        .write = storage_write,
        .sync = storage_sync,
    };
}

bool svc_can_log_fatfs_stop(svc_can_log_fatfs_t *adapter)
{
    if (adapter == NULL || (!adapter->active && !adapter->handle_open)) {
        return false;
    }
    return close_current(adapter, adapter->active);
}

svc_can_log_fatfs_status_t svc_can_log_fatfs_restart(
    svc_can_log_fatfs_t *adapter,
    uint64_t initial_sequence)
{
    if (adapter == NULL || !port_is_complete(&adapter->port) ||
        !config_is_valid(&adapter->config)) {
        return SVC_CAN_LOG_FATFS_INVALID_ARGUMENT;
    }

    const svc_can_log_fatfs_port_t port = adapter->port;
    const svc_can_log_fatfs_config_t config = adapter->config;
    const uint32_t old_rotation_count = adapter->rotation_count;
    const uint32_t old_recovery_truncate_count =
        adapter->recovery_truncate_count;
    const uint32_t old_format_rollover_count = adapter->format_rollover_count;
    const uint32_t old_restart_count = adapter->restart_count;
    (void)close_current(adapter, adapter->active);
    const uint32_t old_sync_failure_count = adapter->sync_failure_count;
    const uint32_t old_close_failure_count = adapter->close_failure_count;

    svc_can_log_fatfs_t reopened = {0};
    const svc_can_log_fatfs_status_t status = svc_can_log_fatfs_start(
        &reopened,
        port,
        config,
        initial_sequence);
    if (status != SVC_CAN_LOG_FATFS_OK) {
        adapter->active = false;
        return status;
    }
    reopened.rotation_count = saturating_add(
        old_rotation_count,
        reopened.rotation_count);
    reopened.recovery_truncate_count = saturating_add(
        old_recovery_truncate_count,
        reopened.recovery_truncate_count);
    reopened.format_rollover_count = saturating_add(
        old_format_rollover_count,
        reopened.format_rollover_count);
    reopened.restart_count = old_restart_count;
    increment_counter(&reopened.restart_count);
    reopened.sync_failure_count = saturating_add(
        old_sync_failure_count,
        reopened.sync_failure_count);
    reopened.close_failure_count = saturating_add(
        old_close_failure_count,
        reopened.close_failure_count);
    *adapter = reopened;
    return SVC_CAN_LOG_FATFS_OK;
}
