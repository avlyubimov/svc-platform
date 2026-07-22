#pragma once

#include <stddef.h>
#include <stdint.h>

#include "can_log_fatfs.h"
#include "can_log_queue.h"

typedef enum {
    SVC_CAN_LOG_TASK_IDLE = 0,
    SVC_CAN_LOG_TASK_FLUSHED,
    SVC_CAN_LOG_TASK_RETRY_LATER,
    SVC_CAN_LOG_TASK_INVALID_ARGUMENT
} svc_can_log_task_status_t;

typedef struct {
    svc_can1_log_queue_t *queue;
    svc_can_log_persistence_t persistence;
    size_t batch_records;
    uint32_t successful_batch_count;
    uint32_t retry_count;
} svc_can_log_task_t;

bool svc_can_log_task_init(
    svc_can_log_task_t *task,
    svc_can1_log_queue_t *queue,
    svc_can_log_fatfs_t *adapter,
    size_t batch_records);

/* Called only from the single logger task; never from a CAN receive ISR. */
svc_can_log_task_status_t svc_can_log_task_run_once(
    svc_can_log_task_t *task,
    size_t *persisted_records);
