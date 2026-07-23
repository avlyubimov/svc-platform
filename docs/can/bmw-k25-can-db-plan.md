# BMW K25 CAN Database Plan

## Goal

Build a safe read-only CAN database for BMW R1200GS K25.

## Initial signals to identify

- ignition
- engine running
- RPM
- speed
- high beam
- low beam
- left indicator
- right indicator
- brake
- hazard
- battery voltage if present
- RDC pressure after retrofit
- ESA status after retrofit
- ASC status after retrofit

## Capture method

1. SVC CAN logger in listen-only mode.
2. Repeat controlled actions one by one.
3. Compare frame changes.
4. Document IDs and signal bits.
5. Validate across multiple rides.

## Unverified dashboard candidates

The following identifiers are research candidates only and must not enter the
working DBC/decoder until the verification gate below is complete:

| Candidate | Possible contents | Status |
| --- | --- | --- |
| `0x10C` | RPM, throttle position | Unverified |
| `0x130` | high beam, brakes, turn indicators | Unverified |
| `0x2A8` | road speed | Unverified |
| `0x2BC` | gear, temperature, oil, consumption | Unverified |

No byte order, bit position, scaling, offset, validity marker, or timeout is
approved for these candidates. Dashboard v1 therefore shows unavailable
measurements and never computes gear from speed/RPM.

## Signal verification gate

Before moving any candidate into a DBC or production decoder:

1. reproduce it in at least three independent recordings;
2. compare it with the stock instrument cluster or ISTA;
3. verify byte order, bit position, scaling, and offset;
4. cover engine start/stop and relevant controlled state transitions;
5. identify invalid/reserved values and stale behavior;
6. document frame cadence and select an evidence-backed timeout;
7. retain physical and software listen-only operation throughout capture.

BMW K25 CAN remains strictly read-only. UI demand is not verification evidence.
