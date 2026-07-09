# Event Dispatcher

The Event Dispatcher drains the Event Bus and applies safety-relevant events
through existing services.

## Initial responsibilities

- Consume events in FIFO order.
- Apply `SVC_EVENT_OUTPUT_OVERCURRENT` through the Output Manager fault path.
- Apply `SVC_EVENT_OUTPUT_FAULT` through the Output Manager fault path.
- Ignore non-fault events that remain after the Rule Event Bridge has retained
  safety/diagnostic events and consumed rule-condition events.
- Preserve queued events if required dependencies are missing.

## Safety contract

The dispatcher does not write GPIO or PWM hardware. Output state changes still go
through the Output Manager, which keeps the single hardware-control boundary
intact.

## Host-testable implementation

- `firmware/services/event_dispatcher.h`
- `firmware/services/event_dispatcher.c`
- `firmware/tests/test_event_dispatcher.c`
