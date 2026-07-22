#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "can_log_persistence.h"

#define SVC_CAN_LOG_SESSION_HEADER_SIZE 128U
#define SVC_CAN_LOG_SESSION_FORMAT_VERSION 2U
#define SVC_CAN_LOG_HARDWARE_VERSION_SIZE 16U
#define SVC_CAN_LOG_FIRMWARE_VERSION_SIZE 24U
#define SVC_CAN_LOG_BOARD_SERIAL_SIZE 24U

typedef enum {
    SVC_CAN_LOG_SESSION_REASON_BOOT = 1,
    SVC_CAN_LOG_SESSION_REASON_IGNITION_WAKE,
    SVC_CAN_LOG_SESSION_REASON_MANUAL,
    SVC_CAN_LOG_SESSION_REASON_STORAGE_RECOVERY,
    SVC_CAN_LOG_SESSION_REASON_DIAGNOSTIC
} svc_can_log_session_reason_t;

/*
 * Thin port over FatFs/microSD primitives. The platform binding maps these
 * callbacks to f_mount/directory scan/f_open/f_read/f_write/f_sync/
 * f_expand/f_truncate.
 * preallocate must reserve storage without changing the logical file length.
 * find_latest_session searches IDs at or above first_session_id so reboot can
 * reopen the newest rotated file.
 */
typedef struct {
    void *context;
    bool (*mount)(void *context);
    bool (*find_latest_session)(
        void *context,
        uint32_t first_session_id,
        bool *found,
        uint32_t *latest_session_id);
    bool (*open_session)(
        void *context,
        uint32_t session_id,
        bool *created,
        uint64_t *logical_size);
    size_t (*read_at)(void *context, uint64_t offset, uint8_t *data, size_t size);
    size_t (*append)(void *context, const uint8_t *data, size_t size);
    bool (*sync)(void *context);
    bool (*preallocate)(void *context, uint64_t target_size);
    bool (*truncate)(void *context, uint64_t logical_size);
    bool (*close)(void *context);
} svc_can_log_fatfs_port_t;

typedef struct {
    uint32_t session_id;
    uint64_t started_us;
    uint64_t rotation_bytes;
    uint64_t preallocation_bytes;
    uint32_t can_bitrate;
    svc_can_log_session_reason_t session_reason;
    char hardware_version[SVC_CAN_LOG_HARDWARE_VERSION_SIZE];
    char firmware_version[SVC_CAN_LOG_FIRMWARE_VERSION_SIZE];
    char board_serial[SVC_CAN_LOG_BOARD_SERIAL_SIZE];
} svc_can_log_fatfs_config_t;

typedef enum {
    SVC_CAN_LOG_FATFS_OK = 0,
    SVC_CAN_LOG_FATFS_INVALID_ARGUMENT,
    SVC_CAN_LOG_FATFS_PORT_UNAVAILABLE,
    SVC_CAN_LOG_FATFS_MOUNT_FAILED,
    SVC_CAN_LOG_FATFS_OPEN_FAILED,
    SVC_CAN_LOG_FATFS_HEADER_INVALID,
    SVC_CAN_LOG_FATFS_IO_FAILED,
    SVC_CAN_LOG_FATFS_PREALLOCATE_FAILED,
    SVC_CAN_LOG_FATFS_RECOVERY_FAILED
} svc_can_log_fatfs_status_t;

typedef struct {
    svc_can_log_fatfs_port_t port;
    svc_can_log_fatfs_config_t config;
    uint64_t logical_size;
    uint64_t next_sequence;
    uint32_t active_session_id;
    uint32_t recovered_record_count;
    uint32_t rotation_count;
    uint32_t recovery_truncate_count;
    uint32_t format_rollover_count;
    uint32_t restart_count;
    uint32_t sync_failure_count;
    uint32_t close_failure_count;
    bool active;
    bool handle_open;
} svc_can_log_fatfs_t;

svc_can_log_fatfs_status_t svc_can_log_fatfs_start(
    svc_can_log_fatfs_t *adapter,
    svc_can_log_fatfs_port_t port,
    svc_can_log_fatfs_config_t config,
    uint64_t initial_sequence);

svc_can_log_storage_backend_t svc_can_log_fatfs_backend(svc_can_log_fatfs_t *adapter);

bool svc_can_log_fatfs_stop(svc_can_log_fatfs_t *adapter);

svc_can_log_fatfs_status_t svc_can_log_fatfs_restart(
    svc_can_log_fatfs_t *adapter,
    uint64_t initial_sequence);
