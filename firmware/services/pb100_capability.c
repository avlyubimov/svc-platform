#include "pb100_capability.h"

const svc_hardware_capability_t svc_pb100_hardware_capability = {
    .output_count = SVC_OUTPUT_COUNT,
    .main_fuse_limit_ma = 50000U,
    .board_continuous_limit_ma = 40000U,
    .default_total_current_limit_ma = 40000U,
    .outputs_default_off = true,
    .configuration_required_for_roles = true,
    .can1_read_only_default = true,
    .can1_tx_route_dnp_open = true,
    .can1_tx_requires_future_adr = true,
    .can1_hardware_action_required_for_tx = true,
    .outputs = {
        {SVC_OUTPUT_OUT1, 15U, 12000U, true, true},
        {SVC_OUTPUT_OUT2, 20U, 18000U, false, true},
        {SVC_OUTPUT_OUT3, 10U, 8000U, true, true},
        {SVC_OUTPUT_OUT4, 10U, 8000U, true, true},
        {SVC_OUTPUT_OUT5, 5U, 4000U, true, true},
        {SVC_OUTPUT_OUT6, 10U, 8000U, true, true},
        {SVC_OUTPUT_OUT7, 10U, 8000U, true, true},
        {SVC_OUTPUT_OUT8, 5U, 4000U, true, true},
        {SVC_OUTPUT_OUT9, 5U, 4000U, true, true},
        {SVC_OUTPUT_OUT10, 10U, 8000U, true, true}
    }
};
