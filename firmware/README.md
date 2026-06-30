# Firmware

Target architecture:
- FreeRTOS
- drivers
- event bus
- services
- plugins
- rule engine
- logger
- BLE/USB API

No direct feature-to-hardware coupling. Use Output Manager and role mapping.

## Host validation

Run from `firmware/`:

```bash
make test
```

The firmware Makefile treats `core/*.h` and `services/*.h` as host-test
prerequisites, so interface changes force test binary rebuilds.

Current host tests cover:

- PB-100 board-level power budget service.
- Output Manager safe default-off, enable/disable, budget denial, telemetry
  denial, and fault lockout behavior.
- Battery protection warning, cutoff latch, recovery, and invalid telemetry
  behavior.
- Event Bus FIFO order, overflow rejection, and empty-pop behavior.
- Event Dispatcher output overcurrent/fault handling through Output Manager.
- CAN1 listen-only TX denial and CAN2 expansion TX allowance.
- System Safety Coordinator integration between battery cutoff, Event Bus, and
  Output Manager output shutdown.
