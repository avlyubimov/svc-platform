# PB-100 80 V MOSFET Voltage-Class Decision

Status: Q1 design selection closed; controlled PCB work remains LAYOUT-ONLY pending schematic-freeze authorization

## Decision

PB-100 Rev.1 uses `IAUT300N08S5N012ATMA2` for input reverse MOSFET Q1 and
output MOSFETs Q101 through Q110. It is an active/preferred automotive 80 V
MOSFET in PG-HSOF-8-1 TOLL. The exact orderable part is tape-and-reel, MSL1,
AEC qualified, and the manufacturer currently plans availability through at
least 2038.

Every selected schematic instance binds
`PB100:PG-HSOF-8-1_TOLL_Infineon` with pin 1 gate, pins 2 through 8 source, and
`Tab` drain. The checked-in footprint keeps 42 separated paste apertures over
the drain copper. The historical LFPAK88 and former 60 V footprint evidence is
retained but is not selected.

## Why this component

- Q1 is on the protected side of the LM74930-Q1 common-source cutoff pair, so
  its 80 V rating is screened against the generated 48.99-54.89 V cutoff range;
  raw 79-101 V load dump is interrupted by the 150 V Q2.
- Maximum RDS(on) is 1.2 mOhm at 10 V; the conservative hot design bound uses
  2.1x, or 2.52 mOhm.
- Maximum RthJC is 0.4 K/W, maximum junction temperature is 175 degC, maximum
  gate charge is 231 nC, and the package is 100% avalanche tested.
- At the 40 A board budget Q1 dissipates 4.032 W at the hot resistance bound.
  At 125 degC ambient and the 150 degC design target, the complete passive path
  from junction through PCB copper and thermal pad to the metal enclosure must
  not exceed 6.20 K/W. Layout extraction and PB-BENCH-010 must prove it.
- One exact package for Q1 and Q101-Q110 reduces stencil, inspection, and
  substitution ambiguity while preserving role-free outputs.

## Alternatives

### Alternative A — `IAUT300N08S5N014ATMA1`

Active/preferred 80 V automotive TOLL with the same PG-HSOF-8-1 pin contract,
1.4 mOhm maximum RDS(on), 0.5 K/W maximum RthJC, and manufacturer availability
planned through at least 2038. It is the preferred same-footprint alternate,
but a substitution still requires updated SOA, gate-charge, loss, BOM, and
factory review.

### Alternative B — `BUK7J2R4-80MX`

Production 80 V automotive `BUK7J2R4-80M` in LFPAK56E. It offers gull-wing AOI
inspection and lower gate charge, but its 2.4 mOhm maximum room-temperature
RDS(on), different footprint, and smaller package reduce Q1/OUT2 thermal margin.
It is deliberately non-drop-in.

### Rejected preliminary and 60 V paths

Preliminary `BUK7S1R2-80M` LFPAK88 is not a production selection. The 60 V
`SIDR626LDP` and `IAUTN06S5N008` paths are also rejected because 60 V provides
no useful component/measurement tolerance against the load-dump clamp.

## Availability and factory path

The selected Infineon part is active/preferred, but the project does not claim
live JLC stock. Rev.1 allows JLC global/preorder/private-part consignment or
PCBWay kitted/consigned assembly using an authorized-distributor reel. TOLL
stencil, paste coverage, MSL handling, polarity, solder-void acceptance, and
first-article inspection must be reconfirmed with the actual assembler quote.

This pre-layout source/process evidence closes the PBREL-006 design-selection
gate and supports the power-package portion of PBREL-011. Copper/thermal
extraction controls PROTO-ONLY and PB-BENCH-010 controls the blocker-specific
production-ready transition.

## Hard escape conditions

- Reject any layout whose extracted common-source cutoff loop invalidates the
  accepted LM74930-Q1/Q2 transient model.
- Reopen thermal design if the extracted or measured full passive Q1 path
  exceeds 6.20 K/W or Q1 reaches 150 degC at 40 A and 125 degC ambient.
- Do not substitute any MOSFET from a BOM-only equivalence; repeat electrical,
  footprint, thermal, source, and factory review.

## Primary evidence

- Selected product page: <https://www.infineon.com/part/IAUT300N08S5N012>
- Selected data sheet:
  <https://www.infineon.com/assets/row/public/documents/10/49/infineon-iaut300n08s5n012-datasheet-en.pdf>
- Same-footprint alternative: <https://www.infineon.com/part/IAUT300N08S5N014>
- Non-drop-in alternative: <https://www.nexperia.com/product/BUK7J2R4-80M>
- Generated Q1 evidence: `PB-100-input-q1-evidence.csv`.
- Generated transient evidence: `PB-100-transient-margin-evidence.csv`.
