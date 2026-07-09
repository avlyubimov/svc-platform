# Configuration Store

Configuration Store defines the firmware-side persistence contract for user
configuration records. It is storage-backend neutral: future flash, FRAM, SD, or
service-tool drivers provide bytes, while this service validates records and
selects the active configuration.

## Initial responsibilities

- Build versioned configuration records with sequence numbers.
- Validate magic, format version, checksum, and configuration contents.
- Select the newest valid record from two slots.
- Fall back to compiled defaults only when no valid persisted record exists.
- Keep persisted user configuration preferred across firmware default changes.

## Safety contract

Invalid records are rejected before runtime boot. If both slots and fallback
configuration are invalid, no configuration is loaded.

## Host-testable implementation

- `firmware/services/config_store.h`
- `firmware/services/config_store.c`
- `firmware/tests/test_config_store.c`
