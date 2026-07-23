#pragma once

#include <stddef.h>
#include <stdint.h>

#include "update_state.h"

typedef bool (*svc_stm32_stage_write_fn)(
    void *context,
    uint32_t offset,
    const uint8_t *data,
    size_t length);

typedef struct {
    svc_update_transfer_t transfer;
    svc_stm32_stage_write_fn stage_write;
    void *stage_context;
} svc_stm32_update_port_t;

void svc_stm32_update_port_init(
    svc_stm32_update_port_t *port,
    svc_stm32_stage_write_fn stage_write,
    void *stage_context);

bool svc_stm32_update_port_begin(
    svc_stm32_update_port_t *port,
    uint32_t transfer_id,
    uint32_t total_size);

svc_update_chunk_result_t svc_stm32_update_port_stage_chunk(
    svc_stm32_update_port_t *port,
    uint32_t transfer_id,
    uint32_t sequence,
    uint32_t offset,
    const uint8_t *payload,
    uint16_t payload_length,
    uint32_t payload_crc32);
