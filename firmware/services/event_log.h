#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "event_bus.h"

#define SVC_EVENT_LOG_CAPACITY 64U

typedef struct {
    svc_event_t event;
    uint32_t timestamp_ms;
} svc_event_log_entry_t;

typedef struct {
    svc_event_log_entry_t entries[SVC_EVENT_LOG_CAPACITY];
    size_t start;
    size_t count;
    uint32_t dropped_count;
} svc_event_log_t;

void svc_event_log_init(svc_event_log_t *log);
void svc_event_log_append(
    svc_event_log_t *log,
    svc_event_t event,
    uint32_t timestamp_ms);
bool svc_event_log_get(
    const svc_event_log_t *log,
    size_t index,
    svc_event_log_entry_t *entry);
size_t svc_event_log_count(const svc_event_log_t *log);
uint32_t svc_event_log_dropped_count(const svc_event_log_t *log);
