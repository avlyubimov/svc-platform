# Event Bus

No direct calls such as CAN -> Fog.

Correct flow:

```text
CAN Manager -> Event Bus -> Rule Engine -> Output Manager
Fault Monitor -> Event Bus -> Event Dispatcher -> Output Manager
```

Example events:
- `SVC_EVENT_ENGINE_STARTED`
- `SVC_EVENT_ENGINE_STOPPED`
- `SVC_EVENT_HIGH_BEAM_ON`
- `SVC_EVENT_LEFT_INDICATOR_ON`
- `SVC_EVENT_LOW_BATTERY_WARN`
- `SVC_EVENT_LOW_BATTERY_CUTOFF`
- `SVC_EVENT_THERMAL_DERATE`
- `SVC_EVENT_THERMAL_CUTOFF`
- `SVC_EVENT_OUTPUT_OVERCURRENT`

For non-output events, `output_id` is ignored and `value` carries the event
payload, such as measured battery millivolts.

Initial host-testable implementation:

- `firmware/services/event_bus.h`
- `firmware/services/event_bus.c`
- `firmware/tests/test_event_bus.c`

Fault event dispatch is implemented separately:

- `firmware/services/event_dispatcher.h`
- `firmware/services/event_dispatcher.c`
- `firmware/tests/test_event_dispatcher.c`

Rule condition state consumes selected events:

- `SVC_EVENT_ENGINE_STARTED`
- `SVC_EVENT_ENGINE_STOPPED`
- `SVC_EVENT_HIGH_BEAM_ON`
- `SVC_EVENT_HIGH_BEAM_OFF`
- `SVC_EVENT_LEFT_INDICATOR_ON`
- `SVC_EVENT_LEFT_INDICATOR_OFF`

The Rule Event Bridge owns draining those events into `svc_rule_state_t` while
retaining unrelated events on the Event Bus:

- `firmware/services/rule_event_bridge.h`
- `firmware/services/rule_event_bridge.c`
- `firmware/tests/test_rule_event_bridge.c`

Diagnostic logging is implemented separately:

- `firmware/services/event_log.h`
- `firmware/services/event_log.c`
- `firmware/tests/test_event_log.c`
