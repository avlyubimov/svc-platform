cmake_minimum_required(VERSION 3.20)
project(svc_stm32_update_scaffold C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

add_library(svc_stm32_update STATIC
    src/stm32_update_port.c
    ../../update/update_state.c
)
target_include_directories(svc_stm32_update PUBLIC
    src
    ../../update
)
target_compile_options(svc_stm32_update PRIVATE
    -Wall
    -Wextra
    -Werror
)

add_executable(test_stm32_update_port
    tests/test_stm32_update_port.c
)
target_link_libraries(test_stm32_update_port PRIVATE svc_stm32_update)
target_compile_options(test_stm32_update_port PRIVATE
    -Wall
    -Wextra
    -Werror
)

enable_testing()
add_test(NAME stm32_update_port COMMAND test_stm32_update_port)
