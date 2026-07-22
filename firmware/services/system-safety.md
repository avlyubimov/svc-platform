# System Safety Coordinator

The System Safety Coordinator ties independent safety services together without
letting feature code bypass the Output Manager.

## Initial responsibilities

- Run battery protection updates.
- Publish low-battery warning and cutoff events on state transitions.
- Disable all active outputs through the Output Manager on battery cutoff.
- Apply `battery.shutdown_delay_s` before low-voltage cutoff when battery
  telemetry remains continuously below the cutoff threshold.
- Convert telemetry update elapsed time with overflow-safe ceiling arithmetic so
  long intervals cannot shorten the low-voltage cutoff delay.
- Run total-current budget enforcement from telemetry and shed active loads
  through the Output Manager when measured current exceeds the configured limit.
- Treat invalid or stale total-current telemetry as a safe fault that disables
  active outputs through the Output Manager.
- Publish power-budget shedding events when runtime enforcement disables loads.
- Retry a dropped power-budget shedding event until the Event Bus accepts it.
- Apply thermal derating through the Output Manager at thermal warning.
- Disable all active outputs through the Output Manager on thermal cutoff.
- Treat invalid battery telemetry as cutoff.
- Treat invalid or stale thermal telemetry as cutoff.
- Keep outputs off after recovery; recovery permits future requests but does not
  restore prior output state automatically.
- Accept `FOG_A_SW_IN` and `FOG_B_SW_IN` only through
  `manual_fog_control`; each input has independent debounce, stuck-input,
  boot-off and pair-delay processing and produces a request rather than direct
  GPIO control. Invalid configuration, a fault or denied voltage clears both
  requests.
- Preserve shedding order from configuration: the secondary fog pair uses
  priority C, the primary pair priority B and remaining reference loads priority
  A. A critical voltage condition still disables every managed output.
- Treat `C36_BIDIRECTIONAL` as an external unmanaged branch. Firmware may warn
  about low battery or inadequate generator margin but cannot claim to disable
  C36.

## Fail-safe behavior

Battery cutoff has priority over event logging. If the Event Bus is full or not
available, the coordinator still disables active outputs.

## Host-testable implementation

- `firmware/services/system_safety.h`
- `firmware/services/system_safety.c`
- `firmware/tests/test_system_safety.c`
- `firmware/services/manual_fog_control.h`
- `firmware/services/manual_fog_control.c`
- `firmware/tests/test_manual_fog_control.c`

Startup sequencing is handled by:

- `firmware/services/runtime_boot.h`
- `firmware/services/runtime_boot.c`
- `firmware/tests/test_runtime_boot.c`

Battery telemetry validity/staleness is provided by:

- `firmware/services/telemetry.h`
- `firmware/services/telemetry.c`
- `firmware/tests/test_telemetry.c`

`svc_system_safety_update_from_telemetry()` converts stale or invalid battery
telemetry into the same cutoff path as invalid raw telemetry.

Thermal safety uses `svc_system_safety_update_thermal_from_telemetry()` to
publish thermal derate/cutoff events, reduce PWM-capable outputs to
`SVC_THERMAL_DERATE_PWM_MAX_PERCENT` during derate, disable non-PWM
low-priority loads, and shut down active outputs on thermal cutoff. Thermal
recovery does not automatically re-enable previous loads.
