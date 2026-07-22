#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdatomic.h>

#include "can_log.h"

#if ATOMIC_INT_LOCK_FREE != 2
#error "CAN1 ISR queue requires always-lock-free unsigned-int atomics"
#endif

/* One slot remains empty so head == tail has an unambiguous meaning. */
#define SVC_CAN1_LOG_QUEUE_CAPACITY 128U

typedef enum {
    SVC_CAN1_LOG_QUEUE_OK = 0,
    SVC_CAN1_LOG_QUEUE_FULL,
    SVC_CAN1_LOG_QUEUE_INVALID_ARGUMENT,
    SVC_CAN1_LOG_QUEUE_INVALID_FRAME
} svc_can1_log_queue_status_t;

typedef struct {
    svc_can_frame_t frames[SVC_CAN1_LOG_QUEUE_CAPACITY];
    atomic_uint_least32_t head;
    atomic_uint_least32_t tail;
    atomic_uint_least32_t dropped_count;
} svc_can1_log_queue_t;

void svc_can1_log_queue_init(svc_can1_log_queue_t *queue);

/* Single-producer entry point. It is bounded and never calls storage code. */
svc_can1_log_queue_status_t svc_can1_log_queue_push_isr(
    svc_can1_log_queue_t *queue,
    const svc_can_frame_t *frame);

/* Single-consumer logger-task API. Peeked slots stay immutable until consume. */
bool svc_can1_log_queue_peek(
    const svc_can1_log_queue_t *queue,
    size_t offset,
    svc_can_frame_t *frame);

bool svc_can1_log_queue_consume(svc_can1_log_queue_t *queue, size_t count);

size_t svc_can1_log_queue_count(const svc_can1_log_queue_t *queue);
uint32_t svc_can1_log_queue_dropped_count(const svc_can1_log_queue_t *queue);
