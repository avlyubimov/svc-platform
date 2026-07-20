# PB-100 Input Reverse-Protection MOSFET Strategy

Status: 80 V voltage class accepted by Product Owner; SOA, thermal, sourcing,
and PCB layout remain open

## Problem

The input ideal-diode path must carry the 40 A board budget while surviving the
active load-dump clamp plus loop overshoot. A single 2.1 mOhm PowerPAK device
would dissipate about 6.72 W at 40 A with a 2.0 hot-resistance multiplier and
is rejected. The former 60 V TOLL candidate has only 6.7 V nominal headroom
above the 53.3 V TVS planning clamp.

## Decision

Use one `BUK7S1R2-80M` 80 V LFPAK88 MOSFET for Q1. The KiCad symbol and
footprint use pin 1 gate, pins 2 through 4 source, and mounting base `mb` drain.

| Strategy | Hot RDS(on) assumption | 40 A estimate | Status |
|---|---:|---:|---|
| `BUK7S1R2-80M` 80 V LFPAK88 | 2.4 mOhm at 125 C | 3.84 W | Selected |
| `IAUTN08S5N012L` 80 V TOLL | Candidate-specific review | TBD | Non-drop-in alternative A |
| `BUK7J2R4-80M` 80 V LFPAK56E | Higher resistance than selected part | 7.68 W planning estimate | Non-drop-in alternative B |

`IAUTN06S5N008` 60 V TOLL and dual `SIDR626LDP` 60 V PowerPAK calculations
remain historical evidence. They are not approved Rev.1 assembly substitutions.

## Operating and lifetime evidence

- The selected 80 V class has 26.7 V nominal headroom above the 53.3 V clamp
  planning point. Actual `Vclamp + Lloop * di/dt` stress still requires
  reproducible model or bench validation.
- The selected data sheet gives 175 C maximum junction temperature. Final
  allowable junction rise must be derived from ambient, copper, transient duty,
  SOA, solder voiding, and enclosure conditions.
- Expected lifetime remains the automotive project target, but is not claimed
  closed until the mission profile, junction margin, qualification status, and
  production-source continuity are recorded.

## Production evidence and risks

- The reviewed BUK7S1R2-80M data sheet is preliminary. Exact AEC-Q101
  production qualification and orderability must be reconfirmed.
- No locked LCSC code or JLCPCB stock quantity is claimed.
- JLCPCB/PCBWay must confirm LFPAK88 bottom-termination assembly, segmented
  paste, solder-void acceptance, and inspection process.
- Both alternatives use different footprints and require controlled pin-map,
  SOA, thermal, source, and factory review before substitution.

## Schematic and release requirements

- Q1 remains `BUK7S1R2-80M` with
  `PB100:LFPAK88_SOT1235_Nexperia` in the Rev.1 schematic and BOM.
- Source/drain copper must later be sized and validated for at least the 40 A
  board budget after thermal derating.
- Input current measurement remains in the protected path used by firmware
  current-budget enforcement.
- Close gate-clamp behavior, 40 A SOA, fuse energy, thermal margin, actual TVS
  overshoot, production status, and factory handling before layout.
- Do not create placement, high-current copper, Gerber, drill, or pick-place
  output from this voltage-class decision alone.

## Evidence links

- Nexperia BUK7S1R2-80M data sheet:
  <https://assets.nexperia.com/documents/data-sheet/BUK7S1R2-80M.pdf>
- Infineon IAUTN08S5N012L product page:
  <https://www.infineon.com/part/IAUTN08S5N012L>
- Voltage-class decision: `PB-100-mosfet-voltage-margin-review.md`.
- Thermal calculation: `PB-100-thermal-estimates.csv`.
