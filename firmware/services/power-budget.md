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

Initial host-testable implementation:

- `firmware/services/power_budget.h`
- `firmware/services/power_budget.c`
- `firmware/tests/test_power_budget.c`

## Defaults

- Total-current limit: 40 A.
- Shed order: priority C, then B, then A.

## Safety behavior

If telemetry is missing or invalid, the service must choose the safer state:
deny new high-current loads and keep affected outputs off until diagnostics are
valid again.
