# PB-100 Input Reverse-Protection MOSFET Strategy

Status: exact 80 V Q1 and pre-layout SOA/thermal/sourcing evidence closed;
value-bearing gate-network promotion and physical layout acceptance remain open

## Problem

The input ideal-diode path must carry the 40 A board budget while surviving the
active load-dump clamp plus loop overshoot. A single 2.1 mOhm PowerPAK device
would dissipate about 6.72 W at 40 A with a 2.0 hot-resistance multiplier and
is rejected. The former 60 V TOLL candidate has only 6.7 V nominal headroom
above the 53.3 V TVS planning clamp.

## Decision

Use one `IAUT300N08S5N012ATMA2` 80 V TOLL MOSFET for Q1. The KiCad symbol and
footprint use pin 1 gate, pins 2 through 8 source, and `Tab` drain.

| Strategy | Hot RDS(on) assumption | 40 A estimate | Status |
|---|---:|---:|---|
| `IAUT300N08S5N012ATMA2` 80 V TOLL | 2.52 mOhm at 125 C | 4.032 W | Selected |
| `IAUT300N08S5N014ATMA1` 80 V TOLL | 2.94 mOhm conservative hot planning bound | 4.704 W | Same-footprint controlled alternative A |
| `BUK7J2R4-80M` 80 V LFPAK56E | Higher resistance than selected part | 7.68 W planning estimate | Non-drop-in alternative B |

`IAUTN06S5N008` 60 V TOLL and dual `SIDR626LDP` 60 V PowerPAK calculations
remain historical evidence. They are not approved Rev.1 assembly substitutions.

## Operating and lifetime evidence

- The generated 59.45 V downstream-stress bound leaves 20.55 V to the selected
  80 V rating. Layout must enforce the 20 nH clamp-loop ceiling and
  PB-BENCH-004 rejects measured stress at or above 60 V.
- At the hard 125 C case ceiling the 4.032 W bound and 0.4 K/W RthJC produce
  126.61 C junction, leaving 48.39 C to the 175 C absolute maximum.
- Manufacturer evidence marks the selected automotive part active/preferred and
  planned through at least 2038. The project lifetime target remains 10-15 years;
  order-date lifecycle and authorized-reel continuity are still rechecked.

## Production evidence and risks

- The selected part is automotive/AEC-qualified, active/preferred, tape/reel,
  MSL1, and uses the reviewed PG-HSOF-8-1 TOLL footprint.
- LCSC/JLC cross-reference does not constitute a live-stock claim. Recheck the
  authorized reel, assembler quote, DFM, stencil, voiding, and FAI at order date.
- JLCPCB/PCBWay must confirm TOLL bottom-termination assembly, segmented paste,
  solder-void acceptance, and inspection process.
- Alternative A is same-footprint but still needs electrical revalidation;
  alternative B is non-drop-in and needs controlled pin-map, SOA, thermal,
  source, and factory review before substitution.

## Schematic and release requirements

- Q1 remains `IAUT300N08S5N012ATMA2` with
  `PB100:PG-HSOF-8-1_TOLL_Infineon` in the Rev.1 schematic and BOM.
- Source/drain copper must later be sized and validated for at least the 40 A
  board budget after thermal derating.
- Input current measurement remains in the protected path used by firmware
  current-budget enforcement.
- Promote the selected VCAP, enable, gate-series, discharge, and zener values
  into the value-bearing sheet before schematic freeze.
- During layout, prove the plane/polygon/bus path, extracted TVS loop,
  solder-void controls, and enclosure thermal rise before manufacturing release.
- Do not create placement, high-current copper, Gerber, drill, or pick-place
  output from this voltage-class decision alone.

## Evidence links

- Infineon IAUT300N08S5N012ATMA2 data sheet:
  <https://www.infineon.com/assets/row/public/documents/10/49/infineon-iaut300n08s5n012-datasheet-en.pdf>
- Infineon IAUT300N08S5N014 product page:
  <https://www.infineon.com/part/IAUT300N08S5N014>
- Voltage-class decision: `PB-100-mosfet-voltage-margin-review.md`.
- Thermal calculation: `PB-100-thermal-estimates.csv`.
