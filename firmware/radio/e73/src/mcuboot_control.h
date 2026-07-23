#pragma once

#include <stdbool.h>

int svc_e73_request_test_boot(void);

int svc_e73_confirm_running_image(bool health_checks_passed);
