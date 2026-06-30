#pragma once

#include <stdbool.h>

typedef enum {
    SVC_CAN_PORT_CAN1_VEHICLE = 0,
    SVC_CAN_PORT_CAN2_EXPANSION
} svc_can_port_t;

typedef enum {
    SVC_CAN_TX_DENY = 0,
    SVC_CAN_TX_ALLOW
} svc_can_tx_decision_t;

typedef struct {
    svc_can_tx_decision_t decision;
    bool tx_disabled_status;
    bool listen_only_required;
} svc_can_safety_result_t;

svc_can_safety_result_t svc_can_safety_evaluate_tx(
    svc_can_port_t port,
    bool tx_disabled_status);
