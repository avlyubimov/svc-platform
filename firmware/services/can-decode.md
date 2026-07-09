# CAN Event Decode

CAN Event Decode maps received CAN frames to internal Event Bus events through
caller-provided rules.

## Initial responsibilities

- Match received frames by CAN port and identifier mask.
- Evaluate configured byte/bit conditions.
- Publish state-change events such as high-beam or indicator transitions.
- Suppress repeated events while a decoded state is unchanged.
- Report dropped events when the Event Bus is full.

## Safety contract

The decoder consumes received frames only and publishes internal events. It does
not transmit CAN frames and does not control outputs. Rule Engine and Output
Manager remain the only path from events to output changes.

## Host-testable implementation

- `firmware/services/can_decode.h`
- `firmware/services/can_decode.c`
- `firmware/tests/test_can_decode.c`
