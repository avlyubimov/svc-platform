# PB-100 80 V MOSFET Voltage-Class Decision

Status: Accepted by Product Owner on 2026-07-20; voltage class frozen, PCB layout not authorized

## Decision

PB-100 Rev.1 uses `BUK7S1R2-80M` in LFPAK88 SOT1235 for input reverse
MOSFET Q1 and output MOSFETs Q101 through Q110. All eleven schematic instances
bind `PB100:LFPAK88_SOT1235_Nexperia` and use the data-sheet pin contract:
pin 1 gate, pins 2 through 4 source, and mounting base `mb` drain.

The former 60 V `SIDR626LDP` and `IAUTN06S5N008` paths are rejected for the
Rev.1 assembly baseline. Their footprint and calculation records remain as
engineering history and are not approved substitutes. Returning to a 60 V
path requires explicit Product Owner review plus reproducible overshoot proof.

## Why this component

- 80 V VDS gives 26.7 V nominal headroom above the current 53.3 V TVS clamp
  planning point, versus only 6.7 V for a 60 V MOSFET.
- The manufacturer preliminary data sheet specifies 1.2 mOhm maximum RDS(on)
  at 25 C, 2.4 mOhm at 125 C, a 175 C maximum junction temperature, and
  AEC-Q101 qualification intent.
- The existing reviewed LFPAK88 footprint has pin/pad identity evidence and
  twelve segmented paste apertures over the mounting-base drain pad.
- One voltage and package baseline across Q1 and Q101 through Q110 reduces
  substitution and assembly ambiguity while preserving generic output roles.

## Alternatives

### Alternative A — `IAUTN08S5N012L`, 80 V TOLL

Retained as an automotive 80 V production alternative. It is not drop-in:
TOLL uses a different footprint, paste field, copper geometry, and thermal
model. A controlled substitution must repeat pin-map, SOA, thermal, assembly,
and sourcing review. It was not selected because one LFPAK88 baseline is
already captured and reduces Rev.1 package variation.

### Alternative B — `BUK7J2R4-80M`, 80 V LFPAK56E

Retained as an 80 V automotive Nexperia-family alternative. It is not drop-in
because LFPAK56E has a different package and higher conduction loss at the
40 A board input. It was not selected because the smaller package gives less
thermal margin for Q1 and OUT2.

### Rejected 60 V paths

`SIDR626LDP` and `IAUTN06S5N008` could be reconsidered only if clamp-loop
overshoot were proven below their reviewed limit and the Product Owner approved
a future baseline change. They are not Rev.1 alternatives. Product Owner chose
80 V so Rev.1 does not depend on that narrow 6.7 V nominal headroom.

## Operating and thermal margin

At the current 53.3 V clamp planning point:

| Voltage class | Nominal headroom | Result |
|---|---:|---|
| 60 V | 6.7 V | Rejected for Rev.1 MOSFET assembly baseline |
| 80 V | 26.7 V | Selected; actual clamp-loop stress still requires validation |
| 100 V | 46.7 V | Retained for controller and buck paths |

Using 2.4 mOhm at 125 C as a conservative conduction value gives 3.84 W at
40 A for Q1, 0.78 W at 18 A for OUT2, 0.35 W at 12 A, 0.15 W at 8 A, and
0.04 W at 4 A. These values exclude switching, inrush, avalanche, copper and
connector loss. They close only the voltage-class choice, not the SOA or
thermal-layout gates.

The design target is operation below the 175 C absolute maximum with junction
margin demonstrated from the final copper, ambient, airflow, pulse duty cycle,
and assembly voiding evidence. No lifetime claim is accepted yet; automotive
service-life suitability remains conditional on that thermal mission-profile
review and qualified production sourcing.

## Availability and production

- Automotive qualification: the selected data sheet identifies AEC-Q101;
  exact production qualification status must be reconfirmed because the
  reviewed February 2024 data sheet is preliminary.
- LCSC/JLCPCB: no locked live stock code is claimed. Exact reel availability
  and extended/consigned assembly handling remain open.
- PCBWay/JLCPCB compatibility: LFPAK88 paste segmentation is captured, but
  factory confirmation of bottom-termination handling, solder void criteria,
  AOI/X-ray plan, and thermal-pad process is required before order.
- Expected lifetime: automotive project lifetime target; not yet substantiated
  until production-status, mission-profile, junction-temperature, and source
  continuity evidence close.

## Known risks and remaining gates

- The preferred data sheet is preliminary; production status or orderability
  may force a controlled migration to one of the 80 V alternatives.
- Q1 40 A copper and thermal design, OUT2 startup SOA, per-channel inductive
  energy, and actual TVS-plus-loop overshoot remain open.
- `Vstress = Vclamp + Lloop * di/dt` must be validated with reproducible model
  or bench evidence. The 80 V selection increases margin but does not replace
  transient verification.
- No PCB placement, high-current copper, Gerber, drill, or pick-place output is
  authorized by this decision alone.

## Evidence

- Nexperia BUK7S1R2-80M data sheet:
  <https://assets.nexperia.com/documents/data-sheet/BUK7S1R2-80M.pdf>
- Infineon IAUTN08S5N012L product page:
  <https://www.infineon.com/part/IAUTN08S5N012L>
- TVS margin trace: `PB-100-tvs-load-dump-margin-trace.csv`.
- Thermal estimates: `PB-100-thermal-estimates.csv`.
- Factory sourcing recheck:
  `production/bom/pb100_assembly_sourcing_recheck.csv`.
