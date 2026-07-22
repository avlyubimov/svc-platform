# PB-100 Fog Switch Interface

Status: layout authorized; exact external connector and protection selection is
an `EVT-FAB-REVIEW` item.

## Interface

The primary control is a separate weather-protected handlebar dry-contact
switch between `FOG_SW_IN` and `SW_GND`. It carries signal current only.
PB-100 routes the protected request to JPB1 pin 82; LB-100 binds it to STM32
PA8 with a 10 kOhm pull-up and 10 nF RC capacitor. The external connector path
must add ESD/EMI protection and a reviewed series impedance before fabrication.
Firmware debounces the active-low signal, detects a stuck switch, clears the
request at boot/reset and passes it to Output Manager. It never bypasses
current, voltage, thermal, telemetry, fault or safe-off policy.

OUT3/OUT4 form the first configurable pair and OUT6/OUT7 the second reference
pair. Manual enable starts the second pair after a configurable delay; manual
disable turns both pairs off immediately. `SERVICE` and `RESET` are excluded.
An optional FB-100 `FOG` button may be added only after mechanical fit review.

## Candidate Comparison

- **Selected architecture:** sealed two-wire dry-contact switch and connector,
  PB-side automotive ESD/EMI protection, LB-side pull-up/filter.
- **Alternative A:** sealed active 12 V switch module; rejected for Rev.1
  because it adds level translation and module quiescent-current dependencies.
- **Alternative B:** reuse FB-100 SERVICE/RESET; rejected because it conflates
  safety/service semantics and does not provide the primary handlebar control.

## Engineering Record

- Expected lifetime: 10-15 years with a replaceable sealed switch and harness.
- Operating margin: protection must tolerate the selected vehicle ESD/EMI
  environment while clamping PA8 inside absolute maximum limits.
- Maximum junction temperature: record the selected protection device limit and
  derated pulse capability before `EVT-FAB-AUTHORIZED`.
- Availability: select a preferred connector/switch/protection set plus two
  documented alternatives before the EVT package closes.
- Automotive qualification: prefer AEC-Q101 protection and automotive sealed
  connector families; any exception requires review evidence.
- JLCPCB/PCBWay/LCSC: factory protection footprints and order codes require
  purchase-time assembly checks; the handlebar switch/harness is garage-owned.
- Known risks: false activation, stuck contact, water ingress, long-harness EMI
  and ground offset. ESD/EMI protection, RC filtering, debounce, stuck-input
  diagnostics, default-off boot and Output Manager authority mitigate them.
