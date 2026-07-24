#include "mcuboot_control.h"

#include <errno.h>
#include <zephyr/dfu/mcuboot.h>

int svc_e73_request_test_boot(void)
{
    return boot_request_upgrade(BOOT_UPGRADE_TEST);
}

int svc_e73_confirm_running_image(bool health_checks_passed)
{
    if (!health_checks_passed) {
        return -EPERM;
    }

    return boot_write_img_confirmed();
}
