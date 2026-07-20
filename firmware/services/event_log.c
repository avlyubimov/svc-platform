#include "event_log.h"

#include <stdint.h>

void svc_event_log_init(svc_event_log_t *log)
{
    if (log == NULL) {
        return;
    }

    log->start = 0U;
    log->count = 0U;
    log->dropped_count = 0U;
}

void svc_event_log_append(
    svc_event_log_t *log,
    svc_event_t event,
    uint32_t timestamp_ms)
{
    if (log == NULL) {
        return;
    }

    size_t write_index = (log->start + log->count) % SVC_EVENT_LOG_CAPACITY;
    if (log->count == SVC_EVENT_LOG_CAPACITY) {
        write_index = log->start;
        log->start = (log->start + 1U) % SVC_EVENT_LOG_CAPACITY;
        if (log->dropped_count < UINT32_MAX) {
            ++log->dropped_count;
        }
    } else {
        ++log->count;
    }

    log->entries[write_index] = (svc_event_log_entry_t){
        .event = event,
        .timestamp_ms = timestamp_ms
    };
}

bool svc_event_log_get(
    const svc_event_log_t *log,
    size_t index,
    svc_event_log_entry_t *entry)
{
    if (log == NULL || entry == NULL || index >= log->count) {
        return false;
    }

    const size_t read_index = (log->start + index) % SVC_EVENT_LOG_CAPACITY;
    *entry = log->entries[read_index];
    return true;
}

size_t svc_event_log_count(const svc_event_log_t *log)
{
    return log == NULL ? 0U : log->count;
}

uint32_t svc_event_log_dropped_count(const svc_event_log_t *log)
{
    return log == NULL ? 0U : log->dropped_count;
}
