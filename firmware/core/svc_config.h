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
#define SVC_THERMAL_ZONE_COUNT 3U
#define SVC_DEFAULT_THERMAL_WARN_C 85
#define SVC_DEFAULT_THERMAL_CUTOFF_C 105
#define SVC_DEFAULT_THERMAL_RECOVERY_C 75
#define SVC_DEFAULT_TOTAL_CURRENT_SHUNT_UOHM 500U
#define SVC_DEFAULT_TOTAL_CURRENT_MONITOR_RANGE_UV 40960U
#define SVC_DEFAULT_TOTAL_CURRENT_ZERO_OFFSET_MA 0
#define SVC_DEFAULT_TOTAL_CURRENT_GAIN_PPM 1000000U
#define SVC_DEFAULT_TELEMETRY_STALE_TIMEOUT_MS 1000U
#define SVC_DEFAULT_TOTAL_CURRENT_PLAUSIBLE_MAX_MA 60000U
#define SVC_DEFAULT_OUTPUT_CURRENT_ZERO_OFFSET_MA 0
#define SVC_DEFAULT_OUTPUT_CURRENT_GAIN_PPM 1000000U
#define SVC_DEFAULT_OUTPUT_CURRENT_STALE_TIMEOUT_MS 1000U
#define SVC_DEFAULT_OUT1_CURRENT_RANGE_MA 20000U
#define SVC_DEFAULT_OUT2_CURRENT_RANGE_MA 30000U
#define SVC_DEFAULT_OUT3_CURRENT_RANGE_MA 15000U
#define SVC_DEFAULT_OUT4_CURRENT_RANGE_MA 15000U
#define SVC_DEFAULT_OUT5_CURRENT_RANGE_MA 8000U
#define SVC_DEFAULT_OUT6_CURRENT_RANGE_MA 15000U
#define SVC_DEFAULT_OUT7_CURRENT_RANGE_MA 15000U
#define SVC_DEFAULT_OUT8_CURRENT_RANGE_MA 8000U
#define SVC_DEFAULT_OUT9_CURRENT_RANGE_MA 8000U
#define SVC_DEFAULT_OUT10_CURRENT_RANGE_MA 15000U

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

typedef enum {
    SVC_THERMAL_ZONE_PCB = 0,
    SVC_THERMAL_ZONE_PWR_A,
    SVC_THERMAL_ZONE_PWR_B
} svc_thermal_zone_t;

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
    int16_t warn_c;
    int16_t cutoff_c;
    int16_t recovery_c;
} svc_thermal_zone_config_t;

typedef struct {
    uint16_t shunt_microohm;
    uint32_t monitor_range_uv;
    int32_t zero_offset_ma;
    uint32_t gain_ppm;
    uint32_t stale_timeout_ms;
    uint32_t plausible_max_ma;
} svc_total_current_telemetry_config_t;

typedef struct {
    uint32_t range_ma;
    int32_t zero_offset_ma;
    uint32_t gain_ppm;
    uint32_t stale_timeout_ms;
    uint32_t plausible_max_ma;
} svc_output_current_telemetry_config_t;

typedef struct {
    svc_total_current_telemetry_config_t total_current;
    svc_output_current_telemetry_config_t output_current[SVC_OUTPUT_COUNT];
} svc_telemetry_config_t;

typedef struct {
    svc_battery_config_t battery;
    svc_thermal_zone_config_t thermal[SVC_THERMAL_ZONE_COUNT];
    svc_power_budget_config_t power_budget;
    svc_telemetry_config_t telemetry;
    svc_output_config_t outputs[SVC_OUTPUT_COUNT];
} svc_device_config_t;

extern const svc_device_config_t svc_default_config;
