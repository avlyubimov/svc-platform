# CAN Safety Policy

## Default mode

Vehicle CAN is read-only.

## Hardware policy

CAN TX to vehicle bus must be physically disabled by default:
- solder jumper open;
- or TX gate disabled;
- or transceiver silent mode.

PB-100 schematic input for CAN1 TX disable is tracked in
`hardware/power-board/PB-100/PB-100-can1-tx-disable.md`.

## Firmware policy

Rev.1 firmware must not transmit frames to vehicle CAN.

Firmware guard implementation:

- `firmware/services/can_safety.h`
- `firmware/services/can_safety.c`
- `firmware/tests/test_can_safety.c`

## Allowed actions

- listen
- log frames
- decode known frames
- generate internal events

## Prohibited actions in Rev.1

- sending commands to ZFE
- spoofing modules
- clearing faults
- changing vehicle state
