# CAN Event Decode

CAN Event Decode maps received CAN frames to internal Event Bus events through
caller-provided rules.

## Initial responsibilities

- Match received frames by CAN port and identifier mask.
- Evaluate configured byte/bit conditions.
- Publish state-change events such as high-beam or indicator transitions.
- Suppress repeated events while a decoded state is unchanged.
- Report dropped events when the Event Bus is full.
- Keep decoder rule state unchanged when a state-change event is dropped, so the
  next matching received frame can retry event publication.

## Safety contract

The decoder consumes received frames only and publishes internal events. It does
not transmit CAN frames and does not control outputs. Rule Engine and Output
Manager remain the only path from events to output changes.
Dropped state-change events do not advance decode state, preventing a full Event
Bus from permanently hiding a CAN-derived edge.

## Host-testable implementation

- `firmware/services/can_decode.h`
- `firmware/services/can_decode.c`
- `firmware/tests/test_can_decode.c`
