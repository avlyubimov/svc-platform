#include "can_log_queue.h"

#include <limits.h>

static uint_least32_t next_index(uint_least32_t index)
{
    return (index + 1U) % SVC_CAN1_LOG_QUEUE_CAPACITY;
}

static void increment_drop_counter(atomic_uint_least32_t *counter)
{
    uint_least32_t current = atomic_load_explicit(counter, memory_order_relaxed);
    while (current < UINT32_MAX &&
           !atomic_compare_exchange_weak_explicit(
               counter,
               &current,
               current + 1U,
               memory_order_relaxed,
               memory_order_relaxed)) {
    }
}

void svc_can1_log_queue_init(svc_can1_log_queue_t *queue)
{
    if (queue == NULL) {
        return;
    }
    atomic_init(&queue->head, 0U);
    atomic_init(&queue->tail, 0U);
    atomic_init(&queue->dropped_count, 0U);
}

svc_can1_log_queue_status_t svc_can1_log_queue_push_isr(
    svc_can1_log_queue_t *queue,
    const svc_can_frame_t *frame)
{
    if (queue == NULL || frame == NULL) {
        return SVC_CAN1_LOG_QUEUE_INVALID_ARGUMENT;
    }
    if (frame->port != SVC_CAN_PORT_CAN1_VEHICLE ||
        frame->dlc > SVC_CAN_FRAME_MAX_DATA_LEN) {
        return SVC_CAN1_LOG_QUEUE_INVALID_FRAME;
    }

    const uint_least32_t head = atomic_load_explicit(&queue->head, memory_order_relaxed);
    const uint_least32_t next = next_index(head);
    const uint_least32_t tail = atomic_load_explicit(&queue->tail, memory_order_acquire);
    if (next == tail) {
        increment_drop_counter(&queue->dropped_count);
        return SVC_CAN1_LOG_QUEUE_FULL;
    }

    queue->frames[head] = *frame;
    atomic_store_explicit(&queue->head, next, memory_order_release);
    return SVC_CAN1_LOG_QUEUE_OK;
}

size_t svc_can1_log_queue_count(const svc_can1_log_queue_t *queue)
{
    if (queue == NULL) {
        return 0U;
    }
    const uint_least32_t head = atomic_load_explicit(&queue->head, memory_order_acquire);
    const uint_least32_t tail = atomic_load_explicit(&queue->tail, memory_order_relaxed);
    return head >= tail
        ? (size_t)(head - tail)
        : (size_t)(SVC_CAN1_LOG_QUEUE_CAPACITY - tail + head);
}

bool svc_can1_log_queue_peek(
    const svc_can1_log_queue_t *queue,
    size_t offset,
    svc_can_frame_t *frame)
{
    if (queue == NULL || frame == NULL || offset >= svc_can1_log_queue_count(queue)) {
        return false;
    }
    const uint_least32_t tail = atomic_load_explicit(&queue->tail, memory_order_relaxed);
    const size_t index = (tail + offset) % SVC_CAN1_LOG_QUEUE_CAPACITY;
    *frame = queue->frames[index];
    return true;
}

bool svc_can1_log_queue_consume(svc_can1_log_queue_t *queue, size_t count)
{
    if (queue == NULL || count > svc_can1_log_queue_count(queue)) {
        return false;
    }
    const uint_least32_t tail = atomic_load_explicit(&queue->tail, memory_order_relaxed);
    const uint_least32_t next = (tail + count) % SVC_CAN1_LOG_QUEUE_CAPACITY;
    atomic_store_explicit(&queue->tail, next, memory_order_release);
    return true;
}

uint32_t svc_can1_log_queue_dropped_count(const svc_can1_log_queue_t *queue)
{
    if (queue == NULL) {
        return 0U;
    }
    const uint_least32_t value =
        atomic_load_explicit(&queue->dropped_count, memory_order_relaxed);
    return value > UINT32_MAX ? UINT32_MAX : (uint32_t)value;
}
