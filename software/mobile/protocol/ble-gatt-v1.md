# SVC BLE GATT API v1

All multibyte integers are little-endian. JSON characteristics use UTF-8.
Binary transfer frames use the layout defined below. UUIDs are fixed for v1;
breaking changes require a new service version.

## Services

| Function | Service UUID | Characteristic UUIDs |
|---|---|---|
| Device Information | Bluetooth SIG `0x180A` | manufacturer, model, serial, hardware, firmware |
| Connection / Pairing | `9f9e1000-7b7a-4f4f-a001-535643000001` | capabilities `...1001`, challenge `...1002`, session `...1003` |
| Live Telemetry | `9f9e2000-7b7a-4f4f-a001-535643000001` | snapshot `...2001`, notification `...2002` |
| Channel Status | `9f9e3000-7b7a-4f4f-a001-535643000001` | snapshot `...3001`, notification `...3002` |
| Diagnostics | `9f9e4000-7b7a-4f4f-a001-535643000001` | snapshot `...4001`, notification `...4002` |
| Configuration | `9f9e5000-7b7a-4f4f-a001-535643000001` | read `...5001`, safe command `...5002`, result `...5003` |
| Event Log | `9f9e6000-7b7a-4f4f-a001-535643000001` | cursor `...6001`, entries `...6002` |
| Firmware Update Control | `9f9e7000-7b7a-4f4f-a001-535643000001` | request `...7001`, response `...7002` |
| Firmware Update Data | `9f9e7100-7b7a-4f4f-a001-535643000001` | chunk `...7101` |
| Firmware Update Status | `9f9e7200-7b7a-4f4f-a001-535643000001` | status `...7201`, notification `...7202` |

The abbreviated suffix in the table replaces the first UUID group only. For
example, telemetry snapshot is
`9f9e2001-7b7a-4f4f-a001-535643000001`.

E73 self-update additionally exposes the standard Zephyr MCUmgr SMP service
`8D53DC1D-1DB7-4CD3-868B-8A527460AA84` and characteristic
`DA2E7828-FBCE-4E01-AE9E-261174997C48`. The custom update services coordinate
the SVC bundle and STM32 forwarding; they do not redefine SMP framing.

## Version negotiation

Capabilities response:

```json
{
  "supportedProtocolVersions": [1],
  "selectedProtocolVersion": 1,
  "hardwareRevision": "LB-100-REV1",
  "maxChunkSize": 244,
  "features": ["telemetry-v1", "stm32-forward-v1", "mcumgr-smp"]
}
```

The client sends its supported versions first. The device selects the highest
intersection. No intersection terminates the session with
`protocol_incompatible`; silently downgrading or guessing is prohibited.

## Authentication and confirmation

1. Establish BLE LE Secure Connections with authenticated pairing and bonding.
2. Exchange nonces through the challenge characteristic.
3. Bind a short-lived application session to the BLE identity, negotiated
   protocol, nonces, and device identity.
4. Confirm the session on the phone for operations marked `confirmationRequired`.
5. Expire the session on disconnect, timeout, identity change, or repeated
   authentication failure.

Read-only telemetry can be allowed after encrypted bonding. Configuration writes,
log deletion, calibration changes, transfer start, and installation require an
authenticated confirmed session. V1 defines no power-output command.

The production challenge/signature construction and key provisioning require a
separate security review. The mock transport never represents production
authentication.

## Telemetry

The snapshot and notification characteristics carry
`telemetry-v1.schema.json`. Notifications contain a complete coherent snapshot
or a future explicitly versioned delta. A receiver detects loss through the
top-level sequence number and requests a snapshot.

Undecoded CAN values use `value: null`, `valid: false`, `stale: false`, and
`quality: "unavailable"`. They are never populated with plausible mock numbers
on a real device.

## Commands

`command-v1.schema.json` is the envelope. V1 accepts read, pairing, calibration
staging, configuration staging, event-log cursor, and OTA operations. It does
not accept direct physical-channel control.

Every command carries a unique request ID, selected protocol version, timestamp,
session ID when required, and explicit user confirmation for dangerous actions.
Device-side authorization remains authoritative.

## Chunk frame

```text
offset  size  field
0       4     transfer_id
4       4     absolute_offset
8       4     sequence
12      2     payload_length
14      4     payload_crc32 (IEEE)
18      N     payload
```

The negotiated chunk size includes the 18-byte header. The receiver rejects a
length beyond negotiated MTU, CRC mismatch, wrong transfer ID, wrong offset, or
unexpected sequence.

## ACK, retry, and resume

Status notifications contain:

```json
{
  "transferId": 42,
  "state": "receiving",
  "committedOffset": 4096,
  "nextSequence": 17,
  "lastError": null,
  "retrySequence": null
}
```

- ACK means the chunk is durably committed to the receiver's staging path.
- CRC or ordering failure returns `retrySequence`.
- Re-sending the last committed sequence with identical offset, length, and CRC
  is idempotent and returns the current ACK.
- A different payload for an already committed sequence aborts the session.
- After reconnect, the client re-authenticates and sends `resume` with transfer
  metadata. The receiver returns the committed offset and next sequence.
- Resume is denied when target, size, SHA-256, hardware revision, or protocol
  differs from the persisted session.

## Install

`prepareInstall` runs manifest and OTA admission checks. `install` requires a
fresh explicit phone confirmation and repeats all device-side checks. CarPlay
and Android Auto clients do not expose either operation.
