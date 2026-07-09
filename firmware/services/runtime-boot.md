# Runtime Boot

Runtime Boot is the firmware startup boundary between loaded configuration,
discovered hardware capability, and safety services.

## Initial responsibilities

- Initialize the Event Bus.
- Load the newest valid persisted configuration when booting from configuration
  store slots.
- Run configuration acceptance against the discovered hardware capability.
- Initialize Output Manager and System Safety only after acceptance succeeds.
- Keep all outputs off when acceptance fails.
- Report whether boot failed because of invalid arguments, rejected
  configuration/capability, or internal service initialization.

## Safety contract

Boot does not enable any output. A rejected configuration leaves the runtime
uninitialized with an empty Event Bus and zero active or locked outputs.
When booting from store, the caller owns the loaded configuration storage and
must keep it alive for the runtime lifetime.

## Host-testable implementation

- `firmware/services/runtime_boot.h`
- `firmware/services/runtime_boot.c`
- `firmware/tests/test_runtime_boot.c`
