# Rule Engine

The Rule Engine consumes role-based actions and applies them through the Output
Manager. It does not write GPIO/PWM hardware and does not hard-code output
numbers.

## Initial skeleton

- Track event-derived condition state for engine running, high beam, and left
  indicator.
- Track event-derived ambient light state for day, dusk, and night fog-light
  rules.
- Accept condition state updates from the Rule Event Bridge, which drains
  matching Event Bus events without controlling outputs.
- Evaluate condition lists with all-conditions-must-match semantics.
- Evaluate an in-memory rule and skip it when conditions do not match.
- Evaluate ordered rule sets so multiple configured actions can be represented
  as multiple `svc_rule_t` entries with shared conditions.
- Enable a configured role through role resolution.
- Disable a configured role through role resolution.
- Deny missing or ambiguous role mappings.
- Preserve Output Manager budget, telemetry, lockout, and invalid-config
  denials.

The current implementation is an in-memory rule runner. Full JSON rule parsing
will be added after the core safety path is stable. Configuration entries with
multiple `then` actions can be represented by multiple `svc_rule_t` entries that
share the same condition array and execute in order.

## Initial text grammar

Supported condition strings:

- `engine_running == true|false`
- `high_beam == true|false`
- `left_indicator == true|false`
- `ambient_day == true|false`
- `ambient_dusk == true|false`
- `ambient_night == true|false`

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

The parser can also compile condition/action strings into an in-memory
`svc_rule_t` using caller-provided condition storage, so embedded code can avoid
dynamic allocation.

`svc_rule_text_compile_rule_set()` compiles one condition list plus multiple
action strings into an ordered `svc_rule_t` array using caller-provided rule and
condition buffers. This maps the JSON `then[]` shape to the rule-set runner
without dynamic allocation.

`svc_rule_engine_evaluate_rule_with_telemetry()` reads total-current validity
from Telemetry Snapshot before applying a matching rule, so stale current data
denies new output starts through the Output Manager budget path.

`svc_rule_engine_evaluate_rules()` and
`svc_rule_engine_evaluate_rules_with_telemetry()` evaluate ordered rule arrays,
continue past skipped conditions, and stop on the first denied action while
reporting the failed rule index.

Rule Runtime composes the event bridge, fault dispatcher, and ordered rule
runner into the intended firmware step:

- `firmware/services/rule_runtime.h`
- `firmware/services/rule_runtime.c`
- `firmware/tests/test_rule_runtime.c`
