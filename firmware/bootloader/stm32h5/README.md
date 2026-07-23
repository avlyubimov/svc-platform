# STM32H563 secure-update scaffold

This directory is an integration boundary, not a replacement bootloader.
STM32H563 production work must start from ST's OEMiRoT examples for
`NUCLEO-H563ZI`/the selected STM32CubeH5 release.

The host-buildable code proves:

- transport code writes only through an injected staging-slot interface;
- a failed staging write is never acknowledged;
- sequence, offset, and CRC checks are shared with the versioned update state
  machine;
- no phone or E73 decision can bypass STM32 admission.

## Host build

```bash
cmake -S firmware/bootloader/stm32h5 \
  -B build/stm32-update
cmake --build build/stm32-update
ctest --test-dir build/stm32-update --output-on-failure
```

This does not produce a deployable STM32 image. Target output remains blocked on
the accepted CubeH5 version, final flash layout, OEMiRoT provisioning, option
bytes, HAL/storage integration, watchdog integration, and production key
handling.

E73 forwards a candidate through the UART protocol in
`firmware/update/uart-update-v1.md`. STM32 writes and validates its own download
slot. A damaged STM32 boot chain is recovered through SWD/USB, not through E73.
