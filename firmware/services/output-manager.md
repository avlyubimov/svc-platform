# Output Manager

The Output Manager is the only firmware service allowed to apply physical output
state changes.

## Responsibilities

- Map configured roles to generic outputs.
- Enforce per-channel current limits.
- Enforce board-level current budget.
- Apply priority-based load shedding.
- Keep outputs off during boot, reset, update, and fault recovery.
- Convert rule-engine actions into hardware driver commands.

## Prohibited behavior

- CAN Manager must not directly control outputs.
- Rule Engine must not write GPIO/PWM hardware directly.
- Accessory roles must not be hard-coded to output numbers in firmware.

## Initial safety policy

- All outputs default off.
- Invalid device configuration keeps outputs off.
- Board over-budget state refuses new loads before shedding active loads.
- Lower-priority loads shed before higher-priority loads.
- Battery cutoff shutdown is applied through the System Safety Coordinator, not
  by feature code directly manipulating outputs.
- Output overcurrent and fault events are applied through the Event Dispatcher,
  then the Output Manager fault path.
- Rule actions resolve roles first and then call the Output Manager by generic
  output ID.

Initial host-testable implementation:

- `firmware/services/output_manager.h`
- `firmware/services/output_manager.c`
- `firmware/tests/test_output_manager.c`

Device configuration validation is provided by:

- `firmware/services/config_validator.h`
- `firmware/services/config_validator.c`
- `firmware/tests/test_config_validator.c`

Role-based action execution is provided by:

- `firmware/services/role_resolver.h`
- `firmware/services/rule_engine.h`
