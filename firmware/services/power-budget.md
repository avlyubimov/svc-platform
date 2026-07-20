# Power Budget Service

The Power Budget Service protects PB-100 from over-subscription.

## Inputs

- Configured total-current limit.
- Per-output configured current limits.
- Per-output priority.
- Measured total input current.
- Measured or estimated per-output current.
- Output fault and thermal state.

## Outputs

- Budget-available decision for requested output starts.
- Load-shed requests ordered by configured priority.
- Over-budget events for logging and diagnostics.
- Runtime enforcement input to the Output Manager/System Safety loop so active
  loads are shed instead of only refusing future starts.

Initial host-testable implementation:

- `firmware/services/power_budget.h`
- `firmware/services/power_budget.c`
- `firmware/tests/test_power_budget.c`

## Defaults

- Total-current limit: 40 A.
- Shed order: priority C, then B, then A.

## Safety behavior

If telemetry is missing or invalid, the service must choose the safer state:
deny new high-current loads. In the System Safety runtime enforcement path,
invalid or stale total-current telemetry disables active outputs until
diagnostics are valid again.

When telemetry is valid and measured total current exceeds the configured board
limit, active outputs are shed in `shed_order` priority order until the
configured limit is reached or no active loads remain.
Projected-current calculations saturate on unsigned overflow and deny the
request instead of allowing wrapped values.

Telemetry validity/staleness is provided by:

- `firmware/services/telemetry.h`
- `firmware/services/telemetry.c`
- `firmware/tests/test_telemetry.c`
