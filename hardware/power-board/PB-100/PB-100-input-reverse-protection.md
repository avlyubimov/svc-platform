# PB-100 Input Protection Selection

Status: Q1 selected; PBREL-007 pre-layout Conditional under ADR-0018

## Selected Architecture

- `Q1`: `IAUT300N08S5N012ATMA2`, selected 80 V TOLL in PG-HSOF-8-1, controlled by
  LM74930-Q1 DGATE for ideal-diode/reverse-current operation.
- `Q2`: `IAUTN15S6N025ATMA1`, 150 V, PG-HSOF-8-1 TOLL, controlled by HGATE as
  the raw-side overvoltage cutoff switch.
- `U1`: `LM74930QRGERQ1`, 24-pin RGE VQFN, hard cutoff with OVCLAMP grounded.
- `R3/R4/R5`: 42.2 kOhm + 42.2 kOhm / 1.00 kOhm, 1%. Splitting the upper
  resistor keeps each body below 51 V at the 101 V corner. Generated cutoff is
  48.99-54.89 V including comparator threshold, resistor tolerance, and input
  leakage.
- The load is allowed to disconnect during load dump. The old single
  `SM8S33AHM3/I` energy-absorption branch is rejected and its D1 footprint is
  retained DNP only.

Q1 and Q2 use common-source back-to-back orientation. Q2 drain faces
`VBAT_RAW`; Q2 source and Q1 source meet at `INPUT_COMMON_SOURCE`; Q1 drain
feeds `VBAT_REV_PROT`, and the total-current shunt then feeds `VBAT_PROT`.
The maximum 54.89 V value is the OV threshold, not the protected-node peak.
The generated 59.52 V pre-layout peak budget keeps Q1 below its 80 V rating,
while Q2 withstands the complete 101 V source after output discharge.

## Q1 Passive Thermal Decision

The selected Q1 hot review resistance is 2.52 mOhm. At 40 A:

`P = 40^2 * 2.52 mOhm = 4.032 W`

Cooling is passive: PCB copper polygons plus a thermal pad to the metal
enclosure. No fan or other active cooling is selected. The design target is
`Tj <= 150 degC`; at 125 degC ambient the complete thermal path must satisfy:

`RthetaJA,total <= (150 - 125) / 4.032 = 6.20 K/W`

The component selection portion of PBREL-006 is closed. The actual copper,
solder-void, interface-pad, enclosure, and ambient thermal path is physically
verified after layout and by PB-BENCH-010 at 40 A.

## Surge and SOA Screening

`PB-100-surge-stopper-evidence.csv` covers 48 combinations of 79/101 V,
0.5/4 ohm, 40/400 ms, 5/10 ms rise time, and cold, hot-soak, and hot
steady-40 A thermal states.
The hot state links 7.200 W conduction through the 3.47 K/W target path, so
load dump starts at `Tj=150 degC`. The 7 us OV deglitch is modeled with Q2
fully enhanced at approximately 0.18 V VDS. Linear transition is modeled
separately: maximum 40 nC Qgd gives a 0.31 us Miller VDS-rise, and the
complete maximum 52 nC Qgs conservatively bounds post-Miller ID fall at
0.41 us. The complete provisional charge envelope is 0.72 us. A conservative
digitized 500 A lower bound from the
101 V / 1 us / 25 degC SOA curve derates to 83.33 A at 150 degC, or a
provisional 2.08x screen. Rectangular transition energy is informational and
is not compared with avalanche energy. The 150 V Q2 retains 49 V static
margin. The 54.89 V value is only the OV threshold: 0.1225 V rise during the
7 us delay plus a 4.50 V commutation allocation gives a 59.52 V
protected-node peak budget and 20.48 V margin to the 80 V Q1 rating.

`PB-100-input-q2-evidence.csv` calculates 4.000 W at the 2.5 mOhm 25 degC
maximum and 7.200 W from a conservative 4.50 mOhm hot bound. The complete
Q2 thermal path must be no worse than 3.47 K/W for 125 degC ambient and the
150 degC target.

The calculations do not yet close the pre-layout stage. Qgd/Qgs are
design-specified at 75 V / 123 A rather than production-tested at the
101 V / 40 A cutoff corner, and the SOA bound is graph-derived. A qualified
maximum-bound trajectory is required before `LAYOUT-ONLY`. PBREL-007 remains
Conditional and aggregate authorization is `BLOCKED`. After pre-layout
closure, extracted loop inductance, overshoot, Q2 SOA, normal-conduction
thermal behavior, and enclosure coupling remain post-layout evidence.
PB-BENCH-004 remains a post-prototype gate.

## Alternatives and Risks

- Q1 alternative A `IAUT300N08S5N014ATMA1` is same-footprint but higher loss.
- Q1 alternative B `BUK7J2R4-80MX` is non-drop-in and higher loss.
  `IAUT300N08S5N014ATMA1` and `BUK7J2R4-80MX` are not approved Rev.1 assembly substitutions without controlled review.
- Q2 alternative A `IAUTN12S5N017ATMA1` has lower loss but insufficient static
  margin for uncontrolled layout overshoot.
- Q2 alternative B `IAUTN15S6N038ATMA1` retains 150 V but has higher loss.
- Active cutoff adds Q2 conduction heat and can interrupt the protected rail.
  Firmware must treat the interruption as loss of supply, not a recoverable
  command failure.

Both selected MOSFETs are automotive-qualified, MSL1 TOLL parts with 175 degC
maximum junction ratings. JLCPCB/PCBWay assembly requires segmented paste,
voiding/inspection, DFM, and FAI confirmation. LCSC availability and authorized
reel supply are rechecked at order date. Expected lifetime is 10-15 years with
controlled alternates and lifecycle monitoring.

## Release Boundary

- PBREL-006 is closed; PBREL-007 pre-layout remains Conditional and aggregate
  authorization is `BLOCKED`.
- Controlled PCB layout requires PBREL-007 pre-layout closure plus normal
  schematic-freeze and layout-start approval.
- `PROTO-ONLY` requires post-layout copper, thermal, SOA, and clamp-loop
  extraction.
- Production and field use remain `NO-GO` until PB-BENCH-004,
  PB-BENCH-010, and all normal production gates close.
- No `.kicad_pcb` or manufacturing output is created by this selection.

## Sources

- <https://www.ti.com/lit/ds/symlink/lm74930-q1.pdf>
- <https://www.ti.com/lit/ab/snoaaa1/snoaaa1.pdf>
- <https://www.infineon.com/assets/row/public/documents/10/49/infineon-iaut300n08s5n012-datasheet-en.pdf>
- <https://www.infineon.com/assets/row/public/documents/10/49/infineon-iautn15s6n025-datasheet-en.pdf>
