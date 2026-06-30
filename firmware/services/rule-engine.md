# Rule Engine

The Rule Engine consumes role-based actions and applies them through the Output
Manager. It does not write GPIO/PWM hardware and does not hard-code output
numbers.

## Initial skeleton

- Track event-derived condition state for engine running, high beam, and left
  indicator.
- Evaluate condition lists with all-conditions-must-match semantics.
- Evaluate an in-memory rule and skip it when conditions do not match.
- Enable a configured role through role resolution.
- Disable a configured role through role resolution.
- Deny missing or ambiguous role mappings.
- Preserve Output Manager budget, telemetry, lockout, and invalid-config
  denials.

The current implementation is an in-memory rule runner. Full JSON rule parsing
will be added after the core safety path is stable.

## Initial text grammar

Supported condition strings:

- `engine_running == true|false`
- `high_beam == true|false`
- `left_indicator == true|false`

Supported action strings:

- `ROLE.pwm = 0..100`

`0` maps to a disable-role action. Any positive PWM value maps to an enable-role
action with that duty-cycle request. Output Manager enforces whether the target
output allows partial PWM.

## Host-testable implementation

- `firmware/services/rule_engine.h`
- `firmware/services/rule_engine.c`
- `firmware/tests/test_rule_engine.c`

Rule condition state is implemented in:

- `firmware/services/rule_condition.h`
- `firmware/services/rule_condition.c`
- `firmware/tests/test_rule_condition.c`

Rule text parsing is implemented in:

- `firmware/services/rule_text.h`
- `firmware/services/rule_text.c`
- `firmware/tests/test_rule_text.c`
