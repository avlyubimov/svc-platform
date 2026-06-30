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
