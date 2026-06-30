# Event Bus

No direct calls such as CAN -> Fog.

Correct flow:

```text
CAN Manager -> Event Bus -> Rule Engine -> Output Manager
```

Example events:
- EVENT_ENGINE_STARTED
- EVENT_ENGINE_STOPPED
- EVENT_HIGH_BEAM_ON
- EVENT_LEFT_INDICATOR_ON
- EVENT_LOW_BATTERY
- EVENT_OUTPUT_OVERCURRENT

Initial host-testable implementation:

- `firmware/services/event_bus.h`
- `firmware/services/event_bus.c`
- `firmware/tests/test_event_bus.c`
