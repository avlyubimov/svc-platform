# Rule Runtime

Rule Runtime is the host-testable firmware step that connects queued events to
rule execution while preserving safety ordering.

## Processing order

1. Rule Event Bridge drains rule-condition events into `svc_rule_state_t` and
   retains unrelated events.
2. Event Dispatcher applies retained output fault events through Output Manager.
3. Rule Engine evaluates the ordered rule set against the updated condition
   state and current telemetry validity.

This order means output faults lock channels before rule actions can request new
output state. Rule Runtime does not write GPIO/PWM hardware directly; all output
state changes still go through Output Manager.

## Safety contract

- Invalid runtime dependencies do not consume queued events.
- Vehicle CAN remains receive-only; CAN-derived state enters through Event Bus.
- Role actions resolve through configuration, not hard-coded output numbers.
- Stale current telemetry denies matching output-start rules through the
  existing Output Manager budget path.

## Host-testable implementation

- `firmware/services/rule_runtime.h`
- `firmware/services/rule_runtime.c`
- `firmware/tests/test_rule_runtime.c`
