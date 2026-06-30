# Event Bus

No direct calls such as CAN -> Fog.

Correct flow:

```text
CAN Manager -> Event Bus -> Rule Engine -> Output Manager
```

Example events:
- `SVC_EVENT_ENGINE_STARTED`
- `SVC_EVENT_ENGINE_STOPPED`
- `SVC_EVENT_HIGH_BEAM_ON`
- `SVC_EVENT_LEFT_INDICATOR_ON`
- `SVC_EVENT_LOW_BATTERY_WARN`
- `SVC_EVENT_LOW_BATTERY_CUTOFF`
- `SVC_EVENT_OUTPUT_OVERCURRENT`

For non-output events, `output_id` is ignored and `value` carries the event
payload, such as measured battery millivolts.

Initial host-testable implementation:

- `firmware/services/event_bus.h`
- `firmware/services/event_bus.c`
- `firmware/tests/test_event_bus.c`
