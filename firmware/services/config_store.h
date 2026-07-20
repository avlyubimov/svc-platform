#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "svc_config.h"

#define SVC_CONFIG_STORE_MAGIC 0x53564343U
#define SVC_CONFIG_STORE_FORMAT_VERSION 1U

typedef enum {
    SVC_CONFIG_STORE_OK = 0,
    SVC_CONFIG_STORE_INVALID_NULL,
    SVC_CONFIG_STORE_INVALID_MAGIC,
    SVC_CONFIG_STORE_INVALID_VERSION,
    SVC_CONFIG_STORE_INVALID_RESERVED,
    SVC_CONFIG_STORE_INVALID_CHECKSUM,
    SVC_CONFIG_STORE_INVALID_CONFIG
} svc_config_store_status_t;

typedef enum {
    SVC_CONFIG_STORE_SOURCE_NONE = 0,
    SVC_CONFIG_STORE_SOURCE_SLOT_A,
    SVC_CONFIG_STORE_SOURCE_SLOT_B,
    SVC_CONFIG_STORE_SOURCE_FALLBACK_DEFAULT
} svc_config_store_source_t;

typedef enum {
    SVC_CONFIG_STORE_LOAD_OK = 0,
    SVC_CONFIG_STORE_LOAD_FALLBACK_DEFAULT,
    SVC_CONFIG_STORE_LOAD_INVALID_ARGUMENT,
    SVC_CONFIG_STORE_LOAD_NO_VALID_CONFIG
} svc_config_store_load_status_t;

typedef struct {
    uint32_t magic;
    uint16_t format_version;
    uint16_t reserved;
    uint32_t sequence;
    svc_device_config_t config;
    uint32_t checksum;
} svc_config_record_t;

typedef struct {
    svc_config_store_load_status_t status;
    svc_config_store_source_t source;
    svc_config_store_status_t slot_a_status;
    svc_config_store_status_t slot_b_status;
    uint32_t sequence;
} svc_config_store_load_result_t;

svc_config_store_status_t svc_config_store_build_record(
    const svc_device_config_t *config,
    uint32_t sequence,
    svc_config_record_t *record);

svc_config_store_status_t svc_config_store_validate_record(
    const svc_config_record_t *record);

svc_config_store_load_result_t svc_config_store_load_latest(
    const svc_config_record_t *slot_a,
    const svc_config_record_t *slot_b,
    const svc_device_config_t *fallback_config,
    svc_device_config_t *loaded_config);
