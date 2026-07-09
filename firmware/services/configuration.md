# Configuration Validation

Firmware uses `svc_device_config_t` as the in-memory configuration contract.
Accessory roles are data fields in that configuration, not hardware or firmware
channel constants.

## Initial validation

- Battery thresholds must be valid.
- Thermal thresholds must satisfy `recovery_c < warn_c < cutoff_c`.
- Power budget and output electrical limits must be valid.
- Output IDs must remain contiguous `OUT1`..`OUT10`.
- Output roles must be known enum values.
- `OUT_ROLE_NONE` is valid for unused channels.
- `firmware/configs/config-example.json` must match the C default config values.

The validator does not require a specific role to live on a specific physical
output. Vehicle profiles may remap roles as long as the electrical limits remain
valid.

## Host-testable implementation

- `firmware/services/config_validator.h`
- `firmware/services/config_validator.c`
- `firmware/services/config_store.h`
- `firmware/services/config_store.c`
- `firmware/services/config_update.h`
- `firmware/services/config_update.c`
- `firmware/tests/test_config_validator.c`
- `firmware/tests/test_config_store.c`
- `firmware/tests/test_config_update.c`

Repository-level JSON validation:

- `firmware/configs/svc-config.schema.json`
- `tools/validate_config.py`

The repository validator checks that schema role/output/priority enums and rule
string patterns stay in sync with firmware enums and the supported rule grammar.
It also checks that `config-example.json` stays aligned with `svc_default_config`,
that current JSON rule strings fit the limited firmware rule text grammar, that
every `then[]` has at least one action, that rule actions resolve to one
configured role mapping, and that partial PWM actions target PWM-capable outputs.
The example fog-light rules use the ambient day/dusk/night conditions supported
by firmware rather than hard-coding physical output channels.

Configuration persistence is defined by `firmware/services/config-store.md`.
Persisted records are versioned, checksummed, and selected from two slots before
falling back to compiled defaults. Firmware updates must not erase or silently
prefer new defaults over a valid persisted user configuration.
New persisted records must be prepared through `svc_config_update_prepare_record()`
so the configuration is accepted against the target hardware capability before a
record can be written by a storage backend.

## Hardware capability manifests

Hardware capabilities are separate from vehicle role mapping. PB-100 capabilities
are tracked in `firmware/configs/hardware/pb-100-capabilities.json`.

The manifest describes generic `OUT1`..`OUT10` electrical capability, telemetry,
power-budget limits, and CAN1 safety defaults. It must not contain accessory role
names. `tools/validate_config.py` checks it against the PB-100 output matrix,
current/thermal telemetry maps, `config-example.json`, and the CAN1 DNP/open
read-only policy.

Firmware consumes capabilities through a role-free service boundary:

- `firmware/services/config_acceptance.h`
- `firmware/services/config_acceptance.c`
- `firmware/services/hardware_capability.h`
- `firmware/services/hardware_capability.c`
- `firmware/services/pb100_capability.h`
- `firmware/services/pb100_capability.c`
- `firmware/tests/test_config_acceptance.c`
- `firmware/tests/test_hardware_capability.c`

The service validates generic output count, per-output electrical limits, PWM
capability, safe default-off state, total-current budget, and CAN1 read-only
policy. It intentionally does not inspect accessory roles; role mapping remains
configuration and vehicle-profile data.

`svc_pb100_hardware_capability` is the compiled PB-100 Rev.1 baseline used by
host tests. `tools/validate_config.py` checks it against
`firmware/configs/hardware/pb-100-capabilities.json` so firmware and JSON
capability contracts do not drift.

Startup acceptance must call `svc_config_accept_for_hardware()` before a loaded
configuration is used by safety services. This composes general configuration
validation with the discovered board capability contract and reports whether a
failure is invalid configuration, invalid hardware capability data, or a valid
configuration exceeding the connected board limits.
