#pragma once

#include <stddef.h>

#include "svc_config.h"

typedef enum {
    SVC_ROLE_RESOLVER_OK = 0,
    SVC_ROLE_RESOLVER_INVALID_CONFIG,
    SVC_ROLE_RESOLVER_INVALID_ROLE,
    SVC_ROLE_RESOLVER_NOT_FOUND,
    SVC_ROLE_RESOLVER_AMBIGUOUS
} svc_role_resolver_status_t;

typedef struct {
    svc_role_resolver_status_t status;
    svc_output_id_t output_id;
    size_t match_count;
} svc_role_resolver_result_t;

svc_role_resolver_result_t svc_role_resolver_find_output(
    const svc_device_config_t *config,
    output_role_t role);
