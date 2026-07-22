# CAN RX Log

CAN RX Log is the firmware receive-only capture boundary for CAN frames.

## Responsibilities

- Store received CAN1 and CAN2 frames in a fixed-size ring buffer.
- Track dropped frames when the ring buffer overwrites the oldest retained
  frame, saturating the diagnostic drop counter instead of wrapping it.
- Track CAN1 and CAN2 receive counts separately with saturating counters.
- Reject invalid ports and DLC values.
- Persist CAN1 receive frames to the mounted microSD log through a narrow,
  storage-backend-neutral append/sync interface.
- Keep CAN2 frames in RAM unless a later policy explicitly enables a separate
  persistent stream.

## microSD persistence contract

`can_log_persistence.c` converts each CAN1 RX frame into a fixed 40-byte
little-endian `SVCL` record. The record contains format/type bytes, a 64-bit
sequence, timestamp, CAN identifier, DLC, eight zero-padded data bytes and a
CRC-32 over the first 36 bytes. The platform microSD/FAT adapter owns mounting,
session file naming and preallocation; it supplies only `write` and `sync`
callbacks to this service.

The task-context flush routine writes a bounded batch and calls `sync` before
removing any CAN1 frames from RAM. Short writes and sync failures retain the
batch with the same sequence numbers for retry. A torn file may therefore end
with a partial record or duplicate retried sequence; offline readers must scan
for `SVCL`, reject bad CRCs and deduplicate equal sequence numbers. CAN receive
ISR code must only append to the RAM log. It must never call the microSD backend.

The caller serializes append/flush access (for example with the logger task
queue or a critical section), flushes before power-down, and reports the
saturating write/sync failure counters. Card absence or failure degrades logging
only; it must not create a CAN transmit path or directly control an output.

## Safety contract

This service has no transmit API. CAN1 remains read-only; transmit decisions are
still handled by `firmware/services/can_safety.c`.

## Host-testable implementation

- `firmware/services/can_log.h`
- `firmware/services/can_log.c`
- `firmware/services/can_log_persistence.h`
- `firmware/services/can_log_persistence.c`
- `firmware/tests/test_can_log.c`
