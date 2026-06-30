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

Current host tests cover:

- PB-100 board-level power budget service.
- Output Manager safe default-off, enable/disable, budget denial, telemetry
  denial, and fault lockout behavior.
- Battery protection warning, cutoff latch, recovery, and invalid telemetry
  behavior.
- Event Bus FIFO order, overflow rejection, and empty-pop behavior.
