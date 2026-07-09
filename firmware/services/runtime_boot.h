#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "config_acceptance.h"
#include "config_store.h"
#include "event_bus.h"
#include "output_manager.h"
#include "system_safety.h"

typedef enum {
    SVC_RUNTIME_BOOT_OK = 0,
    SVC_RUNTIME_BOOT_INVALID_ARGUMENT,
    SVC_RUNTIME_BOOT_REJECTED_CONFIG,
    SVC_RUNTIME_BOOT_INIT_FAILED
} svc_runtime_boot_status_t;

typedef struct {
    svc_runtime_boot_status_t status;
    svc_config_acceptance_result_t acceptance;
    bool event_bus_initialized;
    bool output_manager_initialized;
    bool system_safety_initialized;
    uint16_t active_output_mask;
    uint16_t locked_output_mask;
} svc_runtime_boot_result_t;

typedef struct {
    svc_event_bus_t event_bus;
    svc_output_manager_t output_manager;
    svc_system_safety_t system_safety;
    bool initialized;
} svc_runtime_t;

typedef enum {
    SVC_RUNTIME_STORE_BOOT_OK = 0,
    SVC_RUNTIME_STORE_BOOT_INVALID_ARGUMENT,
    SVC_RUNTIME_STORE_BOOT_LOAD_FAILED,
    SVC_RUNTIME_STORE_BOOT_BOOT_FAILED
} svc_runtime_store_boot_status_t;

typedef struct {
    svc_runtime_store_boot_status_t status;
    svc_config_store_load_result_t store;
    svc_runtime_boot_result_t boot;
} svc_runtime_store_boot_result_t;

svc_runtime_boot_result_t svc_runtime_boot(
    svc_runtime_t *runtime,
    const svc_device_config_t *config,
    const svc_hardware_capability_t *capability);

svc_runtime_store_boot_result_t svc_runtime_boot_from_store(
    svc_runtime_t *runtime,
    const svc_config_record_t *slot_a,
    const svc_config_record_t *slot_b,
    const svc_device_config_t *fallback_config,
    const svc_hardware_capability_t *capability,
    svc_device_config_t *loaded_config);
