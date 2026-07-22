# CAN RX Log and microSD Persistence

CAN RX Log is the receive-only capture boundary for CAN frames.

## Responsibilities

- Store received CAN1 and CAN2 frames in a 32-frame diagnostic RAM ring.
- Track diagnostic overwrites and CAN1/CAN2 receive counts with saturating
  counters.
- Copy CAN1 receive frames from the ISR into a separate single-producer,
  single-consumer queue with 128 slots (127 usable).
- Persist that queue from one logger task through a FatFs/microSD port.
- Reject invalid ports and DLC values.
- Keep CAN2 in RAM unless a later policy explicitly enables a separate
  persistent stream.

## Concurrency contract

The diagnostic ring is not the persistence queue. Its overwrite policy is
useful for recent in-memory diagnostics, but storage code never removes entries
from it. The CAN receive ISR may append a CAN1 frame to both structures; only
the dedicated queue is consumed by the logger task. A full persistence queue
drops the new storage copy and increments a saturating counter. It never
overwrites a slot that the logger may be writing.

The logger peeks a bounded batch and calls `sync` before advancing the queue
tail. ISR appends during a slow write or sync therefore cannot replace the
immutable batch or cause the task to remove newer frames. Short writes and sync
failures retain the same queue entries and sequence numbers for retry. The ISR
never calls a filesystem or storage callback and no interrupt lock is held
while the card is accessed.

## Record format

`can_log_persistence.c` converts each queued CAN1 RX frame into a fixed 44-byte
little-endian `SVCL` v2 record. The record contains format/type bytes, a 64-bit
sequence, a 64-bit microsecond timestamp, CAN identifier, DLC, eight
zero-padded data bytes, three reserved bytes and a CRC-32 over the first 40
bytes. The v1 40-byte/millisecond record is intentionally not appended to a v2
file.

A failed sync leaves the frame queued. If the unsynced record survived, restart
recovers its sequence and the queued retry can produce the same CAN frame under
the next sequence; if it did not survive, the original sequence is reused. A
power loss can also leave a partial record. Recovery rejects partial or bad-CRC
tails. The storage contract is therefore at-least-once; offline readers that
need event uniqueness deduplicate by sequence plus frame timestamp/ID/data.

## FatFs session adapter

`can_log_fatfs.c` supplies the storage backend used by the logger task. Its
platform port maps to `f_mount`, directory scan, `f_open`, positioned read,
append/write, `f_sync`, `f_expand`, truncate and close operations.

Each file begins with a fixed 128-byte `SVCS` v2 header containing format
version, session ID, session reason, 64-bit microsecond start time, initial
sequence, record size, rotation limit, CAN bitrate, hardware version, firmware
version, board serial and CRC. These identity fields are mandatory; an invalid
or v1/mismatched latest header is preserved and followed by a new session ID
instead of being overwritten or appended with incompatible records.
The adapter:

- scans for and reopens the highest session ID at or above the configured
  first ID, so reboot after rotation does not silently return to an older file;
- preallocates the configured extent without changing logical file length;
- rotates before a record would exceed the configured byte limit;
- scans records after restart, restores the next sequence and truncates a torn
  or corrupt tail to the last valid 44-byte boundary;
- attempts `sync` and `close` independently during stop and rotation, so a
  failed sync never suppresses the close attempt;
- exposes a logger-task-only restart path that closes any stale handle,
  remounts, reopens/recovers the latest file and resets persistence sequencing
  from recovered media state before queued frames are retried.

The repository implements and host-tests this adapter contract, session format,
rotation and recovery. The target-specific STM32 SDMMC/SPI `diskio` and FatFs
binding is still an integration gate before motorcycle CAN testing. Card
absence or failure degrades logging only and must be surfaced diagnostically.

Only the single logger task may peek and consume the persistence queue. The
platform flushes before controlled power-down and reports queue drops plus the
saturating write/sync and retry counters.

## Safety contract

This service has no transmit API. CAN1 remains read-only; transmit decisions are
still handled by `firmware/services/can_safety.c`. Storage state must never
create a CAN transmit path or directly control an output.

## Host-testable implementation

- `firmware/services/can_log.h`
- `firmware/services/can_log.c`
- `firmware/services/can_log_queue.h`
- `firmware/services/can_log_queue.c`
- `firmware/services/can_log_persistence.h`
- `firmware/services/can_log_persistence.c`
- `firmware/services/can_log_fatfs.h`
- `firmware/services/can_log_fatfs.c`
- `firmware/services/can_log_task.h`
- `firmware/services/can_log_task.c`
- `firmware/tests/test_can_log.c`
