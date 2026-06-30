# System Safety Coordinator

The System Safety Coordinator ties independent safety services together without
letting feature code bypass the Output Manager.

## Initial responsibilities

- Run battery protection updates.
- Publish low-battery warning and cutoff events on state transitions.
- Disable all active outputs through the Output Manager on battery cutoff.
- Treat invalid battery telemetry as cutoff.
- Keep outputs off after recovery; recovery permits future requests but does not
  restore prior output state automatically.

## Fail-safe behavior

Battery cutoff has priority over event logging. If the Event Bus is full or not
available, the coordinator still disables active outputs.

## Host-testable implementation

- `firmware/services/system_safety.h`
- `firmware/services/system_safety.c`
- `firmware/tests/test_system_safety.c`
