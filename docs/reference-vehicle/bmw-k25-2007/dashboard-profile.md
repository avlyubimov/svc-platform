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

## Dashboard v1 implementation

The SwiftUI and Jetpack Compose phone targets load this technical profile
independently from the selected BrandPack. Both implementations:

- render a 0–9000 rpm arc with boundaries at 7000 and 7800 rpm;
- use 80 rpm display-color hysteresis while keeping the numeric RPM current;
- omit any rev-limiter/cut-off marker;
- render speed/RPM/gear and all other missing signals as `—`;
- keep gear explicitly unavailable under telemetry v1 instead of estimating it;
- label `telemetry.leanAngle` as `SVC LEAN`, mark it degraded before
  calibration, and allow trip-maximum reset only at confirmed zero speed;
- keep level calibration disabled until the separate Demo Mode change;
- reserve calibration data for a mounting transform and zero offset; a future
  estimator must fuse accelerometer and gyroscope evidence and must not treat
  one accelerometer sample as a finished lean angle;
- use the public SVC visual identity without manufacturer marks.

The application does not add CAN identifiers, write CAN frames, or change any
hardware/firmware behavior.

## Deferred delivery sequence

Dashboard Demo Mode, telemetry protocol v2, selectable real BLE repositories,
and verified BMW dashboard signals remain separate pull requests. The expected
signal and compatibility contracts are recorded in
`software/mobile/docs/ride-dashboard-roadmap.md`; they are not represented as
working integration in Dashboard v1.
