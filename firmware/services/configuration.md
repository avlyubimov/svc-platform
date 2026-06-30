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
- `firmware/tests/test_config_validator.c`

Repository-level JSON validation:

- `firmware/configs/svc-config.schema.json`
- `tools/validate_config.py`

The repository validator checks that schema role/output/priority enums stay in
sync with firmware enums and that `config-example.json` stays aligned with
`svc_default_config`. It also checks that current JSON rule strings fit the
limited firmware rule text grammar.

## Hardware capability manifests

Hardware capabilities are separate from vehicle role mapping. PB-100 capabilities
are tracked in `firmware/configs/hardware/pb-100-capabilities.json`.

The manifest describes generic `OUT1`..`OUT10` electrical capability, telemetry,
power-budget limits, and CAN1 safety defaults. It must not contain accessory role
names. `tools/validate_config.py` checks it against the PB-100 output matrix,
current/thermal telemetry maps, `config-example.json`, and the CAN1 DNP/open
read-only policy.
