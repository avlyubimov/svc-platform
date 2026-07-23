# BMW R1200GS K25 2007 dashboard profile

## Scope

This document records the Product Owner-approved performance configuration for
SVC Reference Vehicle #001. It configures phone dashboard scales and warnings;
it is not evidence that any BMW CAN signal has been decoded.

## Reference values

| Parameter | Value |
| --- | --- |
| Engine | 1170 cc, two-cylinder boxer |
| Gearbox | 6 gears |
| Idle speed | 1150 ± 50 rpm |
| Maximum torque | 115 N·m at 5500 rpm |
| Nominal power | 74 kW at 7000 rpm |
| Maximum permitted engine speed | 7800 rpm |
| SVC tachometer scale | 0–9000 rpm |
| Fuel capacity | 20 L |
| Fuel reserve | 4 L |
| Ice warning | Below 3 °C |
| Rev limiter | Unknown |

## Tachometer contract

- normal zone: 0–6999 rpm;
- warning zone: 7000–7799 rpm;
- red zone: 7800–9000 rpm;
- no rev-limiter or cut-off marker is drawn;
- a Generic Motorcycle profile has no configured warning or red zone.

These are presentation thresholds. They do not authorize engine control and do
not change any device-side safety behavior.

## Data boundary

BMW CAN remains strictly listen-only. Speed, RPM, gear, temperature, fuel, and
warning signals remain unavailable until their CAN identifiers, byte order,
scaling, offsets, cadence, timeout, and invalid/stale behavior have been
verified from recorded data. Unknown data must render as unavailable, never as
zero or a fabricated healthy state.

The dashboard may use `telemetry.leanAngle` only as an SVC-estimated angle. It
must not present that value as an OEM BMW measurement.
