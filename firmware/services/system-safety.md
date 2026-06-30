# System Safety Coordinator

The System Safety Coordinator ties independent safety services together without
letting feature code bypass the Output Manager.

## Initial responsibilities

- Run battery protection updates.
- Publish low-battery warning and cutoff events on state transitions.
- Disable all active outputs through the Output Manager on battery cutoff.
- Disable all active outputs through the Output Manager on thermal cutoff.
- Treat invalid battery telemetry as cutoff.
- Treat invalid or stale thermal telemetry as cutoff.
- Keep outputs off after recovery; recovery permits future requests but does not
  restore prior output state automatically.

## Fail-safe behavior

Battery cutoff has priority over event logging. If the Event Bus is full or not
available, the coordinator still disables active outputs.

## Host-testable implementation

- `firmware/services/system_safety.h`
- `firmware/services/system_safety.c`
- `firmware/tests/test_system_safety.c`

Battery telemetry validity/staleness is provided by:

- `firmware/services/telemetry.h`
- `firmware/services/telemetry.c`
- `firmware/tests/test_telemetry.c`

`svc_system_safety_update_from_telemetry()` converts stale or invalid battery
telemetry into the same cutoff path as invalid raw telemetry.

Thermal safety uses `svc_system_safety_update_thermal_from_telemetry()` to
publish thermal derate/cutoff events and to shut down active outputs on thermal
cutoff. Thermal recovery does not automatically re-enable previous loads.
