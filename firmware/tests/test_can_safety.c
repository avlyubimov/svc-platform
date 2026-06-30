#include <assert.h>
#include <stdbool.h>

#include "can_safety.h"

static void test_can1_tx_is_denied_when_disabled_status_true(void)
{
    const svc_can_safety_result_t result = svc_can_safety_evaluate_tx(
        SVC_CAN_PORT_CAN1_VEHICLE,
        true);

    assert(result.decision == SVC_CAN_TX_DENY);
    assert(result.tx_disabled_status);
    assert(result.listen_only_required);
}

static void test_can1_tx_is_denied_when_disabled_status_false(void)
{
    const svc_can_safety_result_t result = svc_can_safety_evaluate_tx(
        SVC_CAN_PORT_CAN1_VEHICLE,
        false);

    assert(result.decision == SVC_CAN_TX_DENY);
    assert(!result.tx_disabled_status);
    assert(result.listen_only_required);
}

static void test_can2_tx_is_allowed_for_expansion(void)
{
    const svc_can_safety_result_t result = svc_can_safety_evaluate_tx(
        SVC_CAN_PORT_CAN2_EXPANSION,
        false);

    assert(result.decision == SVC_CAN_TX_ALLOW);
    assert(!result.listen_only_required);
}

int main(void)
{
    test_can1_tx_is_denied_when_disabled_status_true();
    test_can1_tx_is_denied_when_disabled_status_false();
    test_can2_tx_is_allowed_for_expansion();
    return 0;
}
