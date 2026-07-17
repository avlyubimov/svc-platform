# PB-100 MOSFET Voltage-Margin Review

Status: Schematic-review input; not final

This note defines how PB-100 Rev.1 should close the remaining 60 V MOSFET
margin risk behind the active `SM8S33AHM3/I` load-dump TVS branch. It does not
freeze a MOSFET MPN, footprint, copper geometry, or PCB layout.

## Inputs

- Active input TVS branch: Vishay `SM8S33AHM3/I` HM3 DO-218AC.
- Active clamp point used in PB-100 planning: 53.3 V at 124 A.
- Existing 100 V paths pass this clamp with margin.
- Existing 60 V MOSFET paths remain conditional because board parasitics can add
  overshoot above the TVS data-sheet clamp point.
- Direct 40 V smart-switch rails remain deferred by ADR-0011.

## Margin math

| Voltage class | Margin above 53.3 V clamp | Planning result |
|---|---:|---|
| 60 V | 6.7 V | Conditional; requires measured or simulated overshoot evidence |
| 80 V | 26.7 V | Preferred schematic-review escape path if SOA and assembly pass |
| 100 V | 46.7 V | Pass-with-margin class for controller and buck paths |

The 60 V class has only about 11 percent headroom before parasitic overshoot.
The 80 V class has about 33 percent headroom before parasitic overshoot. Rev.1
should not close schematic freeze on a 60 V MOSFET path unless the transient
overshoot review explicitly accepts that margin.

## Rev.1 Close Direction

- Treat `BUK7S1R2-80M` or equivalent 80 V LFPAK88-class MOSFET as the preferred
  voltage-margin review path for the input reverse MOSFET if the TOLL 60 V path
  cannot prove overshoot margin.
- Treat an 80 V output MOSFET class as the preferred review escape for OUT2 and
  other output MOSFETs if `SIDR626LDP` 60 V SOA plus overshoot evidence does not
  close.
- Keep `SIDR626LDP` available for output schematic planning only when SOA,
  thermal, factory assembly, and overshoot evidence all close together.
- Keep `IAUTN06S5N008ATMA1` available for input reverse protection only when
  its TOLL package assembly and 60 V overshoot evidence both close.
- Do not introduce a lower-clamp TVS branch or direct 40 V smart-switch rail
  without a future ADR or explicit release review.

## Freeze Impact

- `PBREL-004` and `PBREL-005` cannot close until the selected output MOSFET
  voltage class, SOA, thermal path, and assembly evidence are tied to final
  schematic values.
- `PBREL-006` cannot close until the input reverse MOSFET voltage class,
  package, gate network, and 40 A thermal path close.
- `PBREL-007` cannot close until either 60 V overshoot evidence is accepted or
  the affected MOSFET paths move to an 80 V or higher voltage class.

## Evidence

- TVS margin trace: `PB-100-tvs-load-dump-margin-trace.csv`.
- TVS freeze review: `PB-100-tvs-load-dump-freeze-review.csv`.
- Input reverse package trace: `PB-100-input-reverse-package-trace.csv`.
- OUT2 SOA envelope: `PB-100-out2-soa.md`.
- Factory sourcing recheck: `production/bom/pb100_assembly_sourcing_recheck.csv`.
