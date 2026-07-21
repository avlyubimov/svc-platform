# ADR-0018: PB-100 Active Surge Stopper and Passive Q1 Cooling

Status: Accepted — Product Owner direction on 2026-07-21

## Context

ADR-0016 proved that the single SM8S33AHM3/I branch cannot absorb the complete
79-101 V, 0.5-4 ohm, 40-400 ms load-dump envelope with acceptable thermal and
voltage margin. PBREL-006 also mixed the completed Q1 selection with physical
thermal evidence that cannot exist before PCB layout.

## Decision

- Q1 is fixed as `IAUT300N08S5N012ATMA2`, 80 V, PG-HSOF-8-1 TOLL.
- Q1 uses passive cooling only: PCB copper polygons and a thermal interface to
  the metal enclosure. Active cooling is not selected.
- The Q1 design target is `Tj <= 150 degC`. At 125 degC ambient and the
  generated 4.032 W hot-loss bound, the complete ambient-to-junction path must
  be `<= 6.20 K/W`.
- PBREL-006 closes as a pre-layout component-selection gate. Copper/current and
  thermal extraction remain its post-layout gate; PB-BENCH-010 at 40 A remains
  its prototype-qualification gate.
- Replace LM74700-Q1 plus the active single-SM8S33A branch with
  `LM74930QRGERQ1` in hard overvoltage-cutoff mode. Load disconnection during
  load dump is explicitly allowed.
- Use two 42.2 kOhm 1% series upper resistors and a 1.00 kOhm 1% lower
  resistor. The split keeps each upper resistor below 51 V at the 101 V design
  corner. The generated tolerance and leakage model gives 48.99-54.89 V
  cutoff, meeting the `<= 55 V` requirement.
- Keep the selected 80 V Q1 on the protected DGATE side. Add
  `IAUTN15S6N025ATMA1`, 150 V TOLL, as Q2 on HGATE/raw input. Q2 must withstand
  the full 101 V input after the protected output discharges; using the 80 V Q1
  as the raw-side cutoff device is prohibited.
- The single SM8S33AHM3/I footprint is retained DNP for traceability and is not
  an approved load-dump energy sink.

## Component Comparison

- Selected Q1: IAUT300N08S5N012ATMA2; lowest reviewed hot-path loss, 80 V,
  reviewed TOLL assembly path, and long lifecycle evidence.
- Q1 alternative A: IAUT300N08S5N014ATMA1; same package but higher loss.
- Q1 alternative B: BUK7J2R4-80MX; non-drop-in and higher loss.
- Selected Q2: IAUTN15S6N025ATMA1; 150 V, 2.5 mOhm maximum at 25 degC,
  TOLL, AEC-Q101 qualified. Its avalanche rating is not used as linear-mode
  turn-off evidence.
- Q2 alternative A: IAUTN12S5N017ATMA1; lower loss but only 19 V static margin
  to 101 V before layout overshoot.
- Q2 alternative B: IAUTN15S6N038ATMA1; 150 V but higher conduction loss.

## Margins and Evidence

The corrected generated model covers 24 combinations of 79/101 V,
0.5/4 ohm, 40/400 ms, and three Q2 thermal states: 25 degC cold start,
125 degC hot soak, and 125 degC ambient after steady 40 A preload. Initial
junction temperature is calculated as `Tambient + Pcontinuous * RthJA_target`;
the hot steady state therefore starts the load dump at 150 degC rather than
125 degC.

The 7 us maximum LM74930-Q1 OV deglitch is not treated as linear-mode time.
Q2 remains fully enhanced during that delay with approximately 0.18 V VDS at
40 A and the conservative 4.50 mOhm hot resistance. The provisional Miller
transition uses Q2 maximum 40 nC Qgd divided by the LM74930-Q1 minimum 128 mA
HGATE sink, giving 0.31 us. A conservative digitized lower bound of 500 A at
101 V from the 25 degC, 1 us SOA curve is derated by junction-temperature
headroom to 83.33 A at 150 degC, leaving a provisional 2.08x current screen.
The rectangular transition-energy bound remains supporting information only,
not avalanche or SOA qualification.

Q2 dissipates 4.000 W at 40 A using the 2.5 mOhm 25 degC maximum. A
conservative 1.8x hot multiplier gives 4.50 mOhm and 7.200 W. At 125 degC
ambient and a 150 degC design target, the complete Q2 ambient-to-junction path
must be no worse than 3.47 K/W. Q2 has 49 V static VDS margin to the 101 V
source; protected Q1 retains 25.11 V to its 80 V rating at the maximum 54.89 V
cutoff.

The hot-corner screen does not close PBREL-007 pre-layout. Infineon marks Qgd
as design-specified rather than production-tested and specifies its maximum at
75 V / 123 A, not the 101 V / 40 A cutoff corner; the SOA bound is also
digitized from a typical graph. A qualified maximum-bound gate-discharge model
or vendor-supported trajectory is required before `LAYOUT-ONLY`. Until then
PBREL-007 pre-layout is Conditional and aggregate authorization is `BLOCKED`.
After pre-layout closure, extracted loop inductance, switching overshoot, Q2
dynamic SOA, copper/current density, both MOSFET thermal paths, and enclosure
coupling remain mandatory post-layout evidence. PB-BENCH-004 and PB-BENCH-010
remain mandatory after an engineering prototype exists.

## Production and Lifetime

Both selected MOSFETs are automotive-qualified TOLL devices with 175 degC
maximum junction ratings and MSL1 reflow support. LM74930-Q1 is AEC-Q100 grade
1 in a 24-pin RGE VQFN. JLCPCB/PCBWay compatibility requires order-date source,
quote, stencil, voiding, DFM, and first-article confirmation. LCSC availability
is not claimed and must be rechecked at order date. Expected project lifetime
remains 10-15 years, subject to controlled alternates and lifecycle recheck.

## Consequences

- PBREL-006 is closed as a design-selection blocker. PBREL-007 pre-layout
  remains Conditional and aggregate authorization is `BLOCKED`.
- No `.kicad_pcb` or manufacturing package is created by this decision.
- `PROTO-ONLY` remains blocked until post-layout extraction is reviewed.
- Production and field use remain `NO-GO` until prototype qualification and all
  normal production gates close.
- No second developer is required.

## Evidence

- TI LM74930-Q1 datasheet: https://www.ti.com/lit/ds/symlink/lm74930-q1.pdf
- TI unsuppressed load-dump application brief: https://www.ti.com/lit/ab/snoaaa1/snoaaa1.pdf
- Infineon Q1 datasheet: https://www.infineon.com/assets/row/public/documents/10/49/infineon-iaut300n08s5n012-datasheet-en.pdf
- Infineon Q2 datasheet: https://www.infineon.com/assets/row/public/documents/10/49/infineon-iautn15s6n025-datasheet-en.pdf
- `hardware/power-board/PB-100/PB-100-input-q1-evidence.csv`
- `hardware/power-board/PB-100/PB-100-input-q2-evidence.csv`
- `hardware/power-board/PB-100/PB-100-surge-stopper-evidence.csv`
