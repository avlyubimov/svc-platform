#include <assert.h>
#include <stddef.h>

#include "can_log.h"

static svc_can_frame_t frame_for(
    svc_can_port_t port,
    uint32_t id,
    uint8_t first_byte)
{
    return (svc_can_frame_t){
        .port = port,
        .id = id,
        .dlc = 2U,
        .data = {first_byte, (uint8_t)(first_byte + 1U)},
        .timestamp_ms = id,
        .extended_id = false
    };
}

static void test_logs_can1_rx_frame_without_tx_path(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x123U, 0xABU);

    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);
    assert(svc_can_log_count(&log) == 1U);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN1_VEHICLE) == 1U);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN2_EXPANSION) == 0U);

    svc_can_frame_t read_frame = {0};
    assert(svc_can_log_get(&log, 0U, &read_frame));
    assert(read_frame.port == SVC_CAN_PORT_CAN1_VEHICLE);
    assert(read_frame.id == 0x123U);
    assert(read_frame.dlc == 2U);
    assert(read_frame.data[0] == 0xABU);
}

static void test_logs_can2_rx_frame_separately(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN2_EXPANSION, 0x321U, 1U);

    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);

    assert(svc_can_log_count(&log) == 1U);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN1_VEHICLE) == 0U);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN2_EXPANSION) == 1U);
}

static void test_rejects_invalid_dlc(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x123U, 0U);
    frame.dlc = SVC_CAN_FRAME_MAX_DATA_LEN + 1U;

    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_INVALID_DLC);
    assert(svc_can_log_count(&log) == 0U);
}

static void test_rejects_invalid_port(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    svc_can_frame_t frame = frame_for((svc_can_port_t)99, 0x123U, 0U);

    assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_INVALID_PORT);
    assert(svc_can_log_count(&log) == 0U);
}

static void test_ring_buffer_overwrites_oldest_frame(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);

    for (size_t index = 0U; index < SVC_CAN_LOG_CAPACITY + 3U; ++index) {
        const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, (uint32_t)index, (uint8_t)index);
        assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);
    }

    assert(svc_can_log_count(&log) == SVC_CAN_LOG_CAPACITY);
    assert(svc_can_log_dropped_count(&log) == 3U);

    svc_can_frame_t first_retained = {0};
    assert(svc_can_log_get(&log, 0U, &first_retained));
    assert(first_retained.id == 3U);
}

static void test_diagnostic_counts_saturate_on_overflow(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);

    for (size_t index = 0U; index < SVC_CAN_LOG_CAPACITY; ++index) {
        const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, (uint32_t)index, (uint8_t)index);
        assert(svc_can_log_append_rx(&log, &frame) == SVC_CAN_LOG_OK);
    }

    log.dropped_count = UINT32_MAX;
    log.can1_rx_count = UINT32_MAX;
    log.can2_rx_count = UINT32_MAX;

    const svc_can_frame_t can1_frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 100U, 1U);
    const svc_can_frame_t can2_frame = frame_for(SVC_CAN_PORT_CAN2_EXPANSION, 101U, 2U);
    assert(svc_can_log_append_rx(&log, &can1_frame) == SVC_CAN_LOG_OK);
    assert(svc_can_log_append_rx(&log, &can2_frame) == SVC_CAN_LOG_OK);

    assert(svc_can_log_dropped_count(&log) == UINT32_MAX);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN1_VEHICLE) == UINT32_MAX);
    assert(svc_can_log_port_count(&log, SVC_CAN_PORT_CAN2_EXPANSION) == UINT32_MAX);
}

static void test_null_inputs_fail_safe(void)
{
    svc_can_log_t log = {0};
    svc_can_log_init(&log);
    const svc_can_frame_t frame = frame_for(SVC_CAN_PORT_CAN1_VEHICLE, 0x123U, 0U);

    assert(svc_can_log_append_rx(NULL, &frame) == SVC_CAN_LOG_INVALID_ARGUMENT);
    assert(svc_can_log_append_rx(&log, NULL) == SVC_CAN_LOG_INVALID_ARGUMENT);
    assert(svc_can_log_count(NULL) == 0U);
    assert(svc_can_log_dropped_count(NULL) == 0U);
    assert(svc_can_log_port_count(NULL, SVC_CAN_PORT_CAN1_VEHICLE) == 0U);
}

int main(void)
{
    test_logs_can1_rx_frame_without_tx_path();
    test_logs_can2_rx_frame_separately();
    test_rejects_invalid_dlc();
    test_rejects_invalid_port();
    test_ring_buffer_overwrites_oldest_frame();
    test_diagnostic_counts_saturate_on_overflow();
    test_null_inputs_fail_safe();
    return 0;
}
