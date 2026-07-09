#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "can_log.h"
#include "event_bus.h"

#define SVC_CAN_DECODE_EVENT_RULE_INDEX_NONE ((size_t)-1)

typedef struct {
    svc_can_port_t port;
    uint32_t id;
    uint32_t id_mask;
    uint8_t byte_index;
    uint8_t bit_mask;
    bool active_when_nonzero;
    svc_event_type_t event_on_active;
    svc_event_type_t event_on_inactive;
    bool initialized;
    bool last_active;
} svc_can_event_rule_t;

typedef enum {
    SVC_CAN_DECODE_OK = 0,
    SVC_CAN_DECODE_INVALID_ARGUMENT,
    SVC_CAN_DECODE_INVALID_FRAME,
    SVC_CAN_DECODE_NO_MATCH,
    SVC_CAN_DECODE_EVENT_UNCHANGED,
    SVC_CAN_DECODE_EVENT_PUBLISHED,
    SVC_CAN_DECODE_EVENT_DROPPED
} svc_can_decode_status_t;

typedef struct {
    svc_can_decode_status_t status;
    size_t rule_index;
    svc_event_type_t event_type;
    bool active;
} svc_can_decode_result_t;

svc_can_decode_result_t svc_can_decode_frame_to_event(
    svc_can_event_rule_t *rules,
    size_t rule_count,
    const svc_can_frame_t *frame,
    svc_event_bus_t *event_bus);
