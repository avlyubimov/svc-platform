# E73 to STM32 update UART v1

The E73 is a transport peer. STM32 owns staging flash, artifact verification,
installation admission, reboot, test confirmation, and rollback.

## Framing

UART uses 8-N-1 with target baud rate selected during LB-100 firmware
integration. Every frame is COBS encoded and terminated by `0x00`.

Decoded header:

```text
offset  size  field
0       2     magic 0x5356
2       1     frame version (1)
3       1     frame type
4       4     transfer ID
8       4     sequence
12      4     absolute offset
16      2     payload length
18      N     payload
18+N    4     CRC-32 over header and payload
```

Frame types are `HELLO`, `BEGIN`, `DATA`, `STATUS`, `FINISH`, `ABORT`, and
`INSTALL_REQUEST`.

## Commit rule

STM32 acknowledges a `DATA` frame only after the chunk is written and read back
from its download slot. Status reports `committedOffset` and `nextSequence`.
E73 retries the requested sequence after CRC, ordering, or storage failure.

After reconnect/reset, E73 sends `HELLO` and `BEGIN` with the same immutable
transfer metadata. STM32 either returns the persisted resume point or rejects
the transfer. Changed target, size, SHA-256, hardware allowlist, or protocol
invalidates resume.

## Safety

- E73 never writes STM32 active flash.
- `INSTALL_REQUEST` carries the phone confirmation but does not override STM32
  admission checks.
- STM32 validates length, SHA-256, signature, hardware revision, protocol, and
  minimum bootloader before reboot.
- UART update does not replace STM32 SWD/USB boot-chain recovery.
