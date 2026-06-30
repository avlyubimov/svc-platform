#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "svc_types.h"

#define SVC_OUTPUT_COUNT 10U
#define SVC_DEFAULT_TOTAL_CURRENT_LIMIT_MA 40000U
#define SVC_DEFAULT_BATTERY_WARN_MV 12000U
#define SVC_DEFAULT_BATTERY_CUTOFF_MV 11800U
#define SVC_DEFAULT_BATTERY_RECOVERY_MV 12400U
#define SVC_DEFAULT_BATTERY_SHUTDOWN_DELAY_S 30U

typedef enum {
    SVC_OUTPUT_OUT1 = 0,
    SVC_OUTPUT_OUT2,
    SVC_OUTPUT_OUT3,
    SVC_OUTPUT_OUT4,
    SVC_OUTPUT_OUT5,
    SVC_OUTPUT_OUT6,
    SVC_OUTPUT_OUT7,
    SVC_OUTPUT_OUT8,
    SVC_OUTPUT_OUT9,
    SVC_OUTPUT_OUT10
} svc_output_id_t;

typedef enum {
    SVC_PRIORITY_A = 0,
    SVC_PRIORITY_B,
    SVC_PRIORITY_C
} svc_load_priority_t;

typedef struct {
    svc_output_id_t id;
    output_role_t role;
    uint16_t fuse_limit_a;
    uint16_t current_limit_ma;
    bool pwm_allowed;
    svc_load_priority_t priority;
} svc_output_config_t;

typedef struct {
    uint32_t total_current_limit_ma;
    svc_load_priority_t shed_order[3];
} svc_power_budget_config_t;

typedef struct {
    uint16_t warn_mv;
    uint16_t cutoff_mv;
    uint16_t recovery_mv;
    uint16_t shutdown_delay_s;
} svc_battery_config_t;

typedef struct {
    svc_battery_config_t battery;
    svc_power_budget_config_t power_budget;
    svc_output_config_t outputs[SVC_OUTPUT_COUNT];
} svc_device_config_t;

extern const svc_device_config_t svc_default_config;
