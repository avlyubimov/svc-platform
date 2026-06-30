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

## Host-testable implementation

- `firmware/services/rule_engine.h`
- `firmware/services/rule_engine.c`
- `firmware/tests/test_rule_engine.c`

Rule condition state is implemented in:

- `firmware/services/rule_condition.h`
- `firmware/services/rule_condition.c`
- `firmware/tests/test_rule_condition.c`
