#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "can_log.h"

#define SVC_CAN_LOG_RECORD_SIZE 40U
#define SVC_CAN_LOG_RECORD_FORMAT_VERSION 1U

typedef size_t (*svc_can_log_storage_write_fn)(
    void *context,
    const uint8_t *data,
    size_t size);

typedef bool (*svc_can_log_storage_sync_fn)(void *context);

typedef struct {
    void *context;
    svc_can_log_storage_write_fn write;
    svc_can_log_storage_sync_fn sync;
} svc_can_log_storage_backend_t;

typedef enum {
    SVC_CAN_LOG_PERSIST_OK = 0,
    SVC_CAN_LOG_PERSIST_NO_DATA,
    SVC_CAN_LOG_PERSIST_INVALID_ARGUMENT,
    SVC_CAN_LOG_PERSIST_BACKEND_UNAVAILABLE,
    SVC_CAN_LOG_PERSIST_WRITE_FAILED,
    SVC_CAN_LOG_PERSIST_SYNC_FAILED
} svc_can_log_persist_status_t;

typedef struct {
    svc_can_log_storage_backend_t backend;
    uint64_t next_sequence;
    uint32_t persisted_can1_count;
    uint32_t write_failure_count;
    uint32_t sync_failure_count;
} svc_can_log_persistence_t;

void svc_can_log_persistence_init(
    svc_can_log_persistence_t *persistence,
    svc_can_log_storage_backend_t backend,
    uint64_t initial_sequence);

svc_can_log_persist_status_t svc_can_log_persist_can1(
    svc_can_log_persistence_t *persistence,
    svc_can_log_t *log,
    size_t max_records,
    size_t *persisted_records);

bool svc_can_log_record_decode(
    const uint8_t record[SVC_CAN_LOG_RECORD_SIZE],
    svc_can_frame_t *frame,
    uint64_t *sequence);
