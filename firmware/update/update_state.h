#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define SVC_UPDATE_PROTOCOL_V1 1U
#define SVC_UPDATE_MAX_CHUNK_SIZE 512U

typedef enum {
    SVC_UPDATE_TARGET_E73_RADIO = 0,
    SVC_UPDATE_TARGET_STM32_MAIN
} svc_update_target_t;

typedef enum {
    SVC_UPDATE_HW_LB100_REV1 = 0,
    SVC_UPDATE_HW_UNSUPPORTED
} svc_update_hardware_t;

typedef enum {
    SVC_UPDATE_IDLE = 0,
    SVC_UPDATE_RECEIVING,
    SVC_UPDATE_INTERRUPTED,
    SVC_UPDATE_VERIFIED,
    SVC_UPDATE_PENDING_TEST_BOOT,
    SVC_UPDATE_TESTING,
    SVC_UPDATE_CONFIRMED,
    SVC_UPDATE_ROLLBACK,
    SVC_UPDATE_ROLLED_BACK,
    SVC_UPDATE_FAILED
} svc_update_state_t;

typedef enum {
    SVC_UPDATE_CHUNK_ACCEPTED = 0,
    SVC_UPDATE_CHUNK_DUPLICATE,
    SVC_UPDATE_CHUNK_RETRY,
    SVC_UPDATE_CHUNK_CORRUPT,
    SVC_UPDATE_CHUNK_INVALID
} svc_update_chunk_result_t;

typedef enum {
    SVC_OTA_ALLOWED = 0,
    SVC_OTA_DENY_VEHICLE_MOVING,
    SVC_OTA_DENY_ENGINE_RUNNING,
    SVC_OTA_DENY_OUTPUTS_ACTIVE,
    SVC_OTA_DENY_CRITICAL_FAULT,
    SVC_OTA_DENY_BATTERY_OUT_OF_RANGE,
    SVC_OTA_DENY_TEMPERATURE_OUT_OF_RANGE,
    SVC_OTA_DENY_LINK_UNSTABLE,
    SVC_OTA_DENY_FILE_INCOMPLETE,
    SVC_OTA_DENY_HASH_MISMATCH,
    SVC_OTA_DENY_SIGNATURE_INVALID,
    SVC_OTA_DENY_HARDWARE_MISMATCH,
    SVC_OTA_DENY_PROTOCOL_INCOMPATIBLE,
    SVC_OTA_DENY_BOOTLOADER_TOO_OLD
} svc_ota_denial_t;

typedef struct {
    uint16_t major;
    uint16_t minor;
    uint16_t patch;
} svc_update_version_t;

typedef struct {
    svc_update_state_t state;
    svc_update_target_t target;
    svc_update_hardware_t hardware;
    uint32_t transfer_id;
    uint32_t total_size;
    uint32_t committed_offset;
    uint32_t next_sequence;
    uint32_t last_sequence;
    uint32_t last_offset;
    uint32_t last_crc32;
    uint16_t last_length;
    uint16_t protocol_version;
    bool has_last_chunk;
    bool sha256_valid;
    bool signature_valid;
} svc_update_transfer_t;

typedef struct {
    int32_t speed_centi_kph;
    bool speed_valid;
    bool speed_stale;
    bool engine_running;
    bool engine_state_valid;
    bool engine_state_stale;
    bool outputs_all_off;
    bool no_critical_fault;
    uint16_t battery_mv;
    uint16_t battery_min_mv;
    uint16_t battery_max_mv;
    bool battery_valid;
    bool battery_stale;
    int16_t board_temperature_c;
    int16_t board_temperature_min_c;
    int16_t board_temperature_max_c;
    bool board_temperature_valid;
    bool board_temperature_stale;
    bool link_stable;
    bool file_complete;
    bool sha256_valid;
    bool signature_valid;
    bool hardware_compatible;
    bool protocol_compatible;
    bool bootloader_compatible;
} svc_ota_admission_t;

void svc_update_transfer_init(svc_update_transfer_t *transfer);

bool svc_update_begin(
    svc_update_transfer_t *transfer,
    svc_update_target_t target,
    svc_update_hardware_t hardware,
    uint16_t protocol_version,
    uint32_t transfer_id,
    uint32_t total_size);

svc_update_chunk_result_t svc_update_accept_chunk(
    svc_update_transfer_t *transfer,
    uint32_t transfer_id,
    uint32_t sequence,
    uint32_t offset,
    const uint8_t *payload,
    uint16_t payload_length,
    uint32_t payload_crc32);

bool svc_update_interrupt(svc_update_transfer_t *transfer);

bool svc_update_resume(
    svc_update_transfer_t *transfer,
    svc_update_target_t target,
    svc_update_hardware_t hardware,
    uint16_t protocol_version,
    uint32_t transfer_id,
    uint32_t total_size);

bool svc_update_finish_transfer(
    svc_update_transfer_t *transfer,
    bool sha256_valid,
    bool signature_valid);

svc_ota_denial_t svc_ota_check_admission(const svc_ota_admission_t *admission);

bool svc_update_request_test_boot(
    svc_update_transfer_t *transfer,
    const svc_ota_admission_t *admission);

bool svc_update_enter_test_boot(svc_update_transfer_t *transfer);

bool svc_update_confirm(svc_update_transfer_t *transfer);

bool svc_update_boot_failed(svc_update_transfer_t *transfer);

bool svc_update_after_reset(svc_update_transfer_t *transfer);

bool svc_update_complete_rollback(svc_update_transfer_t *transfer);

bool svc_update_versions_compatible(
    uint16_t manifest_protocol,
    uint16_t e73_protocol,
    uint16_t stm32_protocol,
    svc_update_version_t e73_version,
    svc_update_version_t minimum_e73_version,
    svc_update_version_t stm32_version,
    svc_update_version_t minimum_stm32_version);

uint32_t svc_update_crc32(const uint8_t *data, size_t length);
