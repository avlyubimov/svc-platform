# Rule Event Bridge

The Rule Event Bridge connects Event Bus state-change events to the Rule Engine
condition state.

## Responsibilities

- Drain queued events during the rule-processing phase.
- Apply only rule-condition events to `svc_rule_state_t`.
- Retain non-rule events on the Event Bus so safety and diagnostic dispatchers
  can still process them.
- Avoid any direct GPIO, PWM, CAN TX, or output-state control.

## Supported condition events

- `SVC_EVENT_ENGINE_STARTED`
- `SVC_EVENT_ENGINE_STOPPED`
- `SVC_EVENT_HIGH_BEAM_ON`
- `SVC_EVENT_HIGH_BEAM_OFF`
- `SVC_EVENT_LEFT_INDICATOR_ON`
- `SVC_EVENT_LEFT_INDICATOR_OFF`
- `SVC_EVENT_AMBIENT_LIGHT_DAY`
- `SVC_EVENT_AMBIENT_LIGHT_DUSK`
- `SVC_EVENT_AMBIENT_LIGHT_NIGHT`

CAN-derived events therefore flow through this path:

```text
CAN RX -> CAN Event Decode -> Event Bus -> Rule Event Bridge
       -> Rule condition state -> Rule Engine -> Output Manager
```

Fault events stay queued for the Event Dispatcher:

```text
Fault Monitor -> Event Bus -> Rule Event Bridge retains event
              -> Event Dispatcher -> Output Manager fault path
```

## Host-testable implementation

- `firmware/services/rule_event_bridge.h`
- `firmware/services/rule_event_bridge.c`
- `firmware/tests/test_rule_event_bridge.c`
