# Event Log

Event Log is a fixed-size diagnostic ring buffer for firmware events.

## Initial behavior

- Store event payloads with timestamps.
- Preserve chronological reads from oldest to newest retained entry.
- Keep the latest entries when capacity is exceeded.
- Count dropped entries on overwrite and saturate the diagnostic drop counter.
- Avoid dynamic allocation.

## Host-testable implementation

- `firmware/services/event_log.h`
- `firmware/services/event_log.c`
- `firmware/tests/test_event_log.c`
