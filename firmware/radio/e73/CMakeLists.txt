cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(svc_e73_radio)

target_sources(app PRIVATE
    src/main.c
    src/ble_uart_bridge.c
    src/mcuboot_control.c
    src/telemetry_stub.c
    ../../update/update_state.c
)
target_include_directories(app PRIVATE
    src
    ../../update
)
