# SVC Ride Dashboard delivery boundary

## Implemented in Dashboard v1

- shared versioned performance profiles independent from BrandPacks;
- SwiftUI and Jetpack Compose phone dashboards;
- adaptive landscape/portrait layouts and platform previews;
- profile-driven tachometer scale/zones with display hysteresis;
- explicit gear presentation with telemetry v1 fixed to unavailable;
- SVC-estimated lean presentation and stationary-only trip-maximum reset;
- telemetry quality-state mapping;
- SVC Day, SVC Night, and automatic ambient-light themes;
- Reduce Motion behavior;
- reduced information-only CarPlay and Android Auto scaffolds.

No manufacturer artwork is required by the Dashboard. Public documentation
uses only the SVC identity.

## Pull request 3 — Dashboard Demo Mode

Add the approved ignition-off, idle, city, highway, corner, night, reserve,
ice, high-RPM, overcurrent, CAN-unavailable, and BLE-disconnected scenarios.
Demo data must be visibly labelled and remain outside the wire protocol. Gear
simulation and local level calibration are permitted only in this mode.

## Pull request 4 — Telemetry protocol v2

Retain telemetry v1 decoding and add versioned measurements for gear, odometer,
trip distance, remaining range, lighting/indicator states, oil/charging
warnings, engine oil level, ABS, ASC, and RDC pressures. Each field needs type,
unit, source, validity/quality, timeout, unavailable semantics, examples, and
v1 fallback behavior.

Planned contract (not yet a wire schema):

| Measurement | Planned value | Unit | Initial timeout |
| --- | --- | --- | --- |
| `gear` | enum `N`, `1`–`6`, `BETWEEN` | `state` | evidence-backed CAN timeout |
| `odometer` | number | `km` | evidence-backed CAN timeout |
| `tripDistance` | number | `km` | evidence-backed CAN timeout |
| `remainingRange` | number | `km` | evidence-backed CAN timeout |
| `turnLeft`, `turnRight`, `hazard`, `highBeam`, `neutral` | boolean | `state` | evidence-backed CAN timeout |
| `oilPressureWarning`, `chargingWarning` | boolean | `state` | evidence-backed CAN timeout |
| `engineOilLevel` | enum/number after verification | to be verified | evidence-backed CAN timeout |
| `absState`, `ascState` | enum after verification | `state` | evidence-backed CAN timeout |
| `rdcFrontPressure`, `rdcRearPressure` | number | `kPa` | evidence-backed CAN timeout |

Every item remains a full SVC measurement with `source`, `timestamp`, `valid`,
`stale`, and `quality`. The protocol-v2 PR must assign actual timeouts only from
verified frame cadence. A v1 device or a v2 device without the signal maps the
field to `unavailable`; clients must not synthesize a value. A v2 client keeps
the existing v1 decoder and negotiates the version before decoding additions.

## Pull request 5 — Real BLE telemetry

Make mock/demo/real repositories explicitly selectable. Connect the existing
CoreBluetooth and Android BLE transports to negotiated telemetry notifications,
reconnect, sequence-gap detection, stale timeouts, connection quality, and
background recovery. Do not mix channel control or OTA installation into this
change.

## Pull request 6 — Verified BMW K25 signals

Use only listen-only logs from an available test board. A signal enters the
DBC/decoder only after the evidence gate in
`docs/can/bmw-k25-can-db-plan.md`. Candidate CAN identifiers remain unverified
and unavailable to Dashboard v1.

## Explicit non-claims

- Dashboard v1 is mock-backed, not a completed vehicle integration.
- Telemetry v1 provides no gear, indicator, ABS, ASC, or RDC measurement.
- Level calibration has no real BLE command.
- CarPlay/Android Auto do not host the full graphical dashboard.
- No hardware, firmware, power-output, OTA, or BMW CAN behavior changes here.
