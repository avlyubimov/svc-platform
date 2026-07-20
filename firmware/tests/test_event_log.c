#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#include "event_log.h"

static void test_init_starts_empty(void)
{
    svc_event_log_t log = {0};
    svc_event_log_init(&log);

    assert(svc_event_log_count(&log) == 0U);
    assert(svc_event_log_dropped_count(&log) == 0U);
}

static void test_append_and_get_preserve_order(void)
{
    svc_event_log_t log = {0};
    svc_event_log_init(&log);

    svc_event_log_append(&log, (svc_event_t){SVC_EVENT_ENGINE_STARTED, SVC_OUTPUT_OUT1, 1U}, 100U);
    svc_event_log_append(&log, (svc_event_t){SVC_EVENT_HIGH_BEAM_ON, SVC_OUTPUT_OUT1, 2U}, 200U);

    assert(svc_event_log_count(&log) == 2U);

    svc_event_log_entry_t entry = {0};
    assert(svc_event_log_get(&log, 0U, &entry));
    assert(entry.event.type == SVC_EVENT_ENGINE_STARTED);
    assert(entry.event.value == 1U);
    assert(entry.timestamp_ms == 100U);

    assert(svc_event_log_get(&log, 1U, &entry));
    assert(entry.event.type == SVC_EVENT_HIGH_BEAM_ON);
    assert(entry.event.value == 2U);
    assert(entry.timestamp_ms == 200U);
}

static void test_overflow_keeps_latest_events(void)
{
    svc_event_log_t log = {0};
    svc_event_log_init(&log);

    for (size_t event_index = 0U; event_index < SVC_EVENT_LOG_CAPACITY + 2U; ++event_index) {
        svc_event_log_append(
            &log,
            (svc_event_t){SVC_EVENT_OUTPUT_STATE_CHANGED, SVC_OUTPUT_OUT1, (uint32_t)event_index},
            (uint32_t)(1000U + event_index));
    }

    assert(svc_event_log_count(&log) == SVC_EVENT_LOG_CAPACITY);
    assert(svc_event_log_dropped_count(&log) == 2U);

    svc_event_log_entry_t first = {0};
    svc_event_log_entry_t last = {0};
    assert(svc_event_log_get(&log, 0U, &first));
    assert(svc_event_log_get(&log, SVC_EVENT_LOG_CAPACITY - 1U, &last));
    assert(first.event.value == 2U);
    assert(last.event.value == SVC_EVENT_LOG_CAPACITY + 1U);
}

static void test_drop_count_saturates_on_overflow(void)
{
    svc_event_log_t log = {0};
    svc_event_log_init(&log);

    for (size_t event_index = 0U; event_index < SVC_EVENT_LOG_CAPACITY; ++event_index) {
        svc_event_log_append(
            &log,
            (svc_event_t){SVC_EVENT_OUTPUT_STATE_CHANGED, SVC_OUTPUT_OUT1, (uint32_t)event_index},
            (uint32_t)event_index);
    }

    log.dropped_count = UINT32_MAX;
    svc_event_log_append(
        &log,
        (svc_event_t){SVC_EVENT_OUTPUT_STATE_CHANGED, SVC_OUTPUT_OUT1, 99U},
        99U);

    assert(svc_event_log_count(&log) == SVC_EVENT_LOG_CAPACITY);
    assert(svc_event_log_dropped_count(&log) == UINT32_MAX);
}

static void test_get_rejects_invalid_index(void)
{
    svc_event_log_t log = {0};
    svc_event_log_init(&log);

    svc_event_log_entry_t entry = {0};
    assert(!svc_event_log_get(&log, 0U, &entry));
}

int main(void)
{
    test_init_starts_empty();
    test_append_and_get_preserve_order();
    test_overflow_keeps_latest_events();
    test_drop_count_saturates_on_overflow();
    test_get_rejects_invalid_index();
    return 0;
}
