#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "stm32_update_port.h"

typedef struct {
    uint8_t bytes[8];
    bool fail_write;
    size_t writes;
} fake_flash_t;

static bool fake_stage_write(
    void *context,
    uint32_t offset,
    const uint8_t *data,
    size_t length)
{
    fake_flash_t *flash = context;
    if (flash == NULL ||
        flash->fail_write ||
        offset > sizeof(flash->bytes) ||
        length > sizeof(flash->bytes) - offset) {
        return false;
    }

    memcpy(&flash->bytes[offset], data, length);
    flash->writes += 1U;
    return true;
}

static void test_failed_flash_write_is_not_committed(void)
{
    const uint8_t payload[] = {1U, 2U, 3U};
    fake_flash_t flash = {
        .fail_write = true
    };
    svc_stm32_update_port_t port;
    svc_stm32_update_port_init(&port, fake_stage_write, &flash);
    assert(svc_stm32_update_port_begin(&port, 4U, sizeof(payload)));

    const uint32_t crc32 = svc_update_crc32(payload, sizeof(payload));
    assert(svc_stm32_update_port_stage_chunk(
        &port,
        4U,
        0U,
        0U,
        payload,
        sizeof(payload),
        crc32) == SVC_UPDATE_CHUNK_RETRY);
    assert(port.transfer.committed_offset == 0U);

    flash.fail_write = false;
    assert(svc_stm32_update_port_stage_chunk(
        &port,
        4U,
        0U,
        0U,
        payload,
        sizeof(payload),
        crc32) == SVC_UPDATE_CHUNK_ACCEPTED);
    assert(port.transfer.committed_offset == sizeof(payload));
    assert(flash.writes == 1U);
}

int main(void)
{
    test_failed_flash_write_is_not_committed();
    return 0;
}
