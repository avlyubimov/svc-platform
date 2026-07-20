# CAN RX Log

CAN RX Log is the firmware receive-only capture boundary for CAN frames.

## Initial responsibilities

- Store received CAN1 and CAN2 frames in a fixed-size ring buffer.
- Track dropped frames when the ring buffer overwrites the oldest retained
  frame, saturating the diagnostic drop counter instead of wrapping it.
- Track CAN1 and CAN2 receive counts separately with saturating counters.
- Reject invalid ports and DLC values.
- Provide readback for later logger/API/decoder layers.

## Safety contract

This service has no transmit API. CAN1 remains read-only; transmit decisions are
still handled by `firmware/services/can_safety.c`.

## Host-testable implementation

- `firmware/services/can_log.h`
- `firmware/services/can_log.c`
- `firmware/tests/test_can_log.c`
