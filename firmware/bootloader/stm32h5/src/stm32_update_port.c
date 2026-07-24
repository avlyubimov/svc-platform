#include "stm32_update_port.h"

#include <stddef.h>

void svc_stm32_update_port_init(
    svc_stm32_update_port_t *port,
    svc_stm32_stage_write_fn stage_write,
    void *stage_context)
{
    if (port == NULL) {
        return;
    }

    svc_update_transfer_init(&port->transfer);
    port->stage_write = stage_write;
    port->stage_context = stage_context;
}

bool svc_stm32_update_port_begin(
    svc_stm32_update_port_t *port,
    uint32_t transfer_id,
    uint32_t total_size)
{
    return port != NULL &&
           port->stage_write != NULL &&
           svc_update_begin(
               &port->transfer,
               SVC_UPDATE_TARGET_STM32_MAIN,
               SVC_UPDATE_HW_LB100_REV1,
               SVC_UPDATE_PROTOCOL_V1,
               transfer_id,
               total_size);
}

svc_update_chunk_result_t svc_stm32_update_port_stage_chunk(
    svc_stm32_update_port_t *port,
    uint32_t transfer_id,
    uint32_t sequence,
    uint32_t offset,
    const uint8_t *payload,
    uint16_t payload_length,
    uint32_t payload_crc32)
{
    if (port == NULL ||
        port->stage_write == NULL ||
        payload == NULL ||
        port->transfer.state != SVC_UPDATE_RECEIVING ||
        transfer_id != port->transfer.transfer_id) {
        return SVC_UPDATE_CHUNK_INVALID;
    }

    if (svc_update_crc32(payload, payload_length) != payload_crc32) {
        return SVC_UPDATE_CHUNK_CORRUPT;
    }

    if (port->transfer.has_last_chunk &&
        sequence == port->transfer.last_sequence &&
        offset == port->transfer.last_offset &&
        payload_length == port->transfer.last_length &&
        payload_crc32 == port->transfer.last_crc32) {
        return SVC_UPDATE_CHUNK_DUPLICATE;
    }

    if (sequence != port->transfer.next_sequence ||
        offset != port->transfer.committed_offset) {
        return SVC_UPDATE_CHUNK_RETRY;
    }

    if (!port->stage_write(
            port->stage_context,
            offset,
            payload,
            payload_length)) {
        return SVC_UPDATE_CHUNK_RETRY;
    }

    return svc_update_accept_chunk(
        &port->transfer,
        transfer_id,
        sequence,
        offset,
        payload,
        payload_length,
        payload_crc32);
}
