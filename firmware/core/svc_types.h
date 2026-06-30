#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef enum {
    SVC_STATE_BOOT,
    SVC_STATE_STANDBY,
    SVC_STATE_ACTIVE,
    SVC_STATE_DELAY_OFF,
    SVC_STATE_FAULT,
    SVC_STATE_SERVICE
} svc_state_t;

typedef enum {
    OUT_ROLE_NONE,
    OUT_ROLE_USB,
    OUT_ROLE_CIGARETTE_SOCKET,
    OUT_ROLE_FOG_LEFT,
    OUT_ROLE_FOG_RIGHT,
    OUT_ROLE_CHIGEE,
    OUT_ROLE_HEATED_SEAT_RIDER,
    OUT_ROLE_HEATED_SEAT_PASSENGER,
    OUT_ROLE_DVR,
    OUT_ROLE_AUX_BRAKE,
    OUT_ROLE_SPARE,
    OUT_ROLE_COUNT
} output_role_t;
