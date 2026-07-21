# PB-100 Input Protection Selection

Status: Q1 selected; PBREL-007 Conditional with pre-layout stage accepted under ADR-0018

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
This keeps Q1 below the maximum 54.89 V protected-node
target while Q2 withstands the complete 101 V source after output discharge.

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

`PB-100-surge-stopper-evidence.csv` covers all 16 combinations of 79/101 V,
0.5/4 ohm, 40/400 ms, and 25/125 degC initial junction temperature. The
8.09 us turn-off bound is screened at 40 A against a conservative digitized
200 A lower bound from the 101 V / 10 us / 25 degC SOA curve. Junction-
temperature headroom derating gives 66.67 A at 125 degC and 1.67x margin. The
0.0327 J rectangular transition value is informational and is not compared
with avalanche energy. The 150 V Q2 retains 49 V static margin; Q1 retains
25.11 V at the worst 54.89 V cutoff.

`PB-100-input-q2-evidence.csv` calculates 4.000 W at the 2.5 mOhm 25 degC
maximum and 7.200 W from a conservative 4.50 mOhm hot bound. The complete
Q2 thermal path must be no worse than 3.47 K/W for 125 degC ambient and the
150 degC target.

The calculations close the pre-layout stage only, not final dynamic proof.
PBREL-007 remains Conditional overall. Extracted
loop inductance, overshoot, Q2 SOA, normal-conduction thermal behavior, and
enclosure coupling remain post-layout evidence. PB-BENCH-004 remains a
post-prototype gate.

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

- PBREL-006 is closed; PBREL-007 remains Conditional overall with its
  pre-layout stage closed at `LAYOUT-ONLY`.
- Controlled PCB layout still requires normal schematic-freeze and layout-start
  approval.
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
