# ADR-0012: Define system sleep, wake, and parking-current limits

## Status
Accepted

## Context
SVC is permanently connected to the motorcycle battery. Without an explicit
off-ignition power policy, LB-100 power selection, wake-source routing, firmware
state machines, and long-parking behavior can accidentally exceed acceptable
parasitic drain.

The existing architecture already requires low-battery shutdown and safe
default-off outputs. It does not yet define the allowed current draw while the
motorcycle is parked, the transition time into sleep, or which sources may wake
the controller.

## Decision
Define two off-ignition power states for the platform:

- Sleep: target current at battery input is at most 1.0 mA, hard maximum 2.0 mA.
- Deep sleep: target current at battery input is at most 250 µA, hard maximum
  500 µA.

Off-ignition transition requirements:

- Enter sleep within 60 seconds after ignition/accessory-off when no service
  session or configured delayed-output action is active.
- Enter deep sleep within 24 hours of continuous parking.
- Keep all PB-100 outputs off in sleep and deep sleep unless a future accepted
  ADR explicitly defines a wake-safe always-on output class.
- Do not use vehicle CAN1 transmit for wake, sleep, or keepalive behavior.

Allowed wake sources for Rev.1:

- Ignition/accessory sense.
- USB/service power present.
- Service button.
- RTC/maintenance timer with outputs remaining off by default.
- CAN1 wake only as a listen-only receiver event if the transceiver and firmware
  preserve ADR-0002 read-only behavior and do not enable CAN1 TX.

Parking-discharge limits:

- First week parked: maximum controller drain budget is 0.35 Ah.
- One month parked after deep sleep transition: maximum controller drain budget
  is 0.45 Ah.

These are system-level limits. Final LB-100 regulator, wake, and firmware
implementation must prove the measured current budget before schematic freeze of
logic power and before any vehicle installation.

## Consequences
LB-100 power-tree selection must include sleep/deep-sleep current evidence.
Firmware must implement explicit sleep/deep-sleep state transitions before
hardware bring-up. PB-100 outputs remain generic and default-off; this ADR does
not change PB-100 output count, role mapping, board current budget, or CAN1
read-only default.
