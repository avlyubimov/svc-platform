#include "can_log_task.h"

#include <limits.h>

static void increment_counter(uint32_t *counter)
{
    if (*counter < UINT32_MAX) {
        ++(*counter);
    }
}

bool svc_can_log_task_init(
    svc_can_log_task_t *task,
    svc_can1_log_queue_t *queue,
    svc_can_log_fatfs_t *adapter,
    size_t batch_records)
{
    if (task == NULL || queue == NULL || adapter == NULL ||
        !adapter->active || batch_records == 0U) {
        return false;
    }
    *task = (svc_can_log_task_t){
        .queue = queue,
        .adapter = adapter,
        .batch_records = batch_records,
    };
    svc_can_log_persistence_init(
        &task->persistence,
        svc_can_log_fatfs_backend(adapter),
        adapter->next_sequence);
    return true;
}

svc_can_log_task_status_t svc_can_log_task_run_once(
    svc_can_log_task_t *task,
    size_t *persisted_records)
{
    if (persisted_records != NULL) {
        *persisted_records = 0U;
    }
    if (task == NULL || task->queue == NULL || task->batch_records == 0U) {
        return SVC_CAN_LOG_TASK_INVALID_ARGUMENT;
    }
    const svc_can_log_persist_status_t status = svc_can_log_persist_can1(
        &task->persistence,
        task->queue,
        task->batch_records,
        persisted_records);
    if (status == SVC_CAN_LOG_PERSIST_NO_DATA) {
        return SVC_CAN_LOG_TASK_IDLE;
    }
    if (status == SVC_CAN_LOG_PERSIST_OK) {
        increment_counter(&task->successful_batch_count);
        return SVC_CAN_LOG_TASK_FLUSHED;
    }
    increment_counter(&task->retry_count);
    return SVC_CAN_LOG_TASK_RETRY_LATER;
}

svc_can_log_fatfs_status_t svc_can_log_task_restart_storage(
    svc_can_log_task_t *task)
{
    if (task == NULL || task->adapter == NULL || task->queue == NULL) {
        return SVC_CAN_LOG_FATFS_INVALID_ARGUMENT;
    }
    const svc_can_log_fatfs_status_t status = svc_can_log_fatfs_restart(
        task->adapter,
        task->persistence.next_sequence);
    if (status != SVC_CAN_LOG_FATFS_OK) {
        return status;
    }
    svc_can_log_persistence_init(
        &task->persistence,
        svc_can_log_fatfs_backend(task->adapter),
        task->adapter->next_sequence);
    increment_counter(&task->storage_restart_count);
    return SVC_CAN_LOG_FATFS_OK;
}
