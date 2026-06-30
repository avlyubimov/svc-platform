# CAN Safety Policy

## Default mode

Vehicle CAN is read-only.

## Hardware policy

CAN TX to vehicle bus must be physically disabled by default:
- solder jumper open;
- or TX gate disabled;
- or transceiver silent mode.

## Firmware policy

Rev.1 firmware must not transmit frames to vehicle CAN.

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
