#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "can_safety.h"

#define SVC_CAN_FRAME_MAX_DATA_LEN 8U
#define SVC_CAN_LOG_CAPACITY 32U

typedef enum {
    SVC_CAN_LOG_OK = 0,
    SVC_CAN_LOG_INVALID_ARGUMENT,
    SVC_CAN_LOG_INVALID_PORT,
    SVC_CAN_LOG_INVALID_DLC
} svc_can_log_status_t;

typedef struct {
    svc_can_port_t port;
    uint32_t id;
    uint8_t dlc;
    uint8_t data[SVC_CAN_FRAME_MAX_DATA_LEN];
    uint32_t timestamp_ms;
    bool extended_id;
} svc_can_frame_t;

typedef struct {
    svc_can_frame_t frames[SVC_CAN_LOG_CAPACITY];
    size_t start;
    size_t count;
    uint32_t dropped_count;
    uint32_t can1_rx_count;
    uint32_t can2_rx_count;
} svc_can_log_t;

void svc_can_log_init(svc_can_log_t *log);

svc_can_log_status_t svc_can_log_append_rx(
    svc_can_log_t *log,
    const svc_can_frame_t *frame);

bool svc_can_log_get(
    const svc_can_log_t *log,
    size_t index,
    svc_can_frame_t *frame);

size_t svc_can_log_count(const svc_can_log_t *log);
uint32_t svc_can_log_dropped_count(const svc_can_log_t *log);
uint32_t svc_can_log_port_count(const svc_can_log_t *log, svc_can_port_t port);
