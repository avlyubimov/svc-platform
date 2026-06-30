#include "can_safety.h"

svc_can_safety_result_t svc_can_safety_evaluate_tx(
    svc_can_port_t port,
    bool tx_disabled_status)
{
    svc_can_safety_result_t result = {
        .decision = SVC_CAN_TX_DENY,
        .tx_disabled_status = tx_disabled_status,
        .listen_only_required = true
    };

    if (port == SVC_CAN_PORT_CAN2_EXPANSION) {
        result.decision = SVC_CAN_TX_ALLOW;
        result.listen_only_required = false;
        return result;
    }

    return result;
}
