#include "can_log.h"

#include <stddef.h>

static bool port_is_valid(svc_can_port_t port)
{
    return port == SVC_CAN_PORT_CAN1_VEHICLE ||
           port == SVC_CAN_PORT_CAN2_EXPANSION;
}

void svc_can_log_init(svc_can_log_t *log)
{
    if (log == NULL) {
        return;
    }

    log->start = 0U;
    log->count = 0U;
    log->dropped_count = 0U;
    log->can1_rx_count = 0U;
    log->can2_rx_count = 0U;
}

svc_can_log_status_t svc_can_log_append_rx(
    svc_can_log_t *log,
    const svc_can_frame_t *frame)
{
    if (log == NULL || frame == NULL) {
        return SVC_CAN_LOG_INVALID_ARGUMENT;
    }
    if (!port_is_valid(frame->port)) {
        return SVC_CAN_LOG_INVALID_PORT;
    }
    if (frame->dlc > SVC_CAN_FRAME_MAX_DATA_LEN) {
        return SVC_CAN_LOG_INVALID_DLC;
    }

    size_t write_index = (log->start + log->count) % SVC_CAN_LOG_CAPACITY;
    if (log->count == SVC_CAN_LOG_CAPACITY) {
        write_index = log->start;
        log->start = (log->start + 1U) % SVC_CAN_LOG_CAPACITY;
        ++log->dropped_count;
    } else {
        ++log->count;
    }

    log->frames[write_index] = *frame;
    if (frame->port == SVC_CAN_PORT_CAN1_VEHICLE) {
        ++log->can1_rx_count;
    } else {
        ++log->can2_rx_count;
    }

    return SVC_CAN_LOG_OK;
}

bool svc_can_log_get(
    const svc_can_log_t *log,
    size_t index,
    svc_can_frame_t *frame)
{
    if (log == NULL || frame == NULL || index >= log->count) {
        return false;
    }

    const size_t read_index = (log->start + index) % SVC_CAN_LOG_CAPACITY;
    *frame = log->frames[read_index];
    return true;
}

size_t svc_can_log_count(const svc_can_log_t *log)
{
    return log == NULL ? 0U : log->count;
}

uint32_t svc_can_log_dropped_count(const svc_can_log_t *log)
{
    return log == NULL ? 0U : log->dropped_count;
}

uint32_t svc_can_log_port_count(const svc_can_log_t *log, svc_can_port_t port)
{
    if (log == NULL || !port_is_valid(port)) {
        return 0U;
    }
    return port == SVC_CAN_PORT_CAN1_VEHICLE
        ? log->can1_rx_count
        : log->can2_rx_count;
}
