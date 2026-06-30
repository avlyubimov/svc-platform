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

Current host tests cover the PB-100 board-level power budget service.
