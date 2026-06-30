# Role Mapping

Physical outputs stay generic. Accessory roles are resolved from
`svc_device_config_t` at runtime before any output action is requested.

## Initial behavior

- Resolve a configured role to one generic output.
- Reject `OUT_ROLE_NONE` for actionable requests.
- Report missing roles.
- Report ambiguous roles instead of guessing.
- Reject invalid device configuration.

Role resolution does not encode any fixed relationship such as
`FOG_LEFT == OUT3`; the default config may map that today, but vehicle profiles
can change the mapping.

## Host-testable implementation

- `firmware/services/role_resolver.h`
- `firmware/services/role_resolver.c`
- `firmware/tests/test_role_resolver.c`
