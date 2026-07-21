# PB-100 Q2 Replacement Evidence Audit

Status: `RETAIN IAUTN15S6N025ATMA1 / EMPIRICAL QUALIFICATION SELECTED`

Date: 2026-07-21

## Decision Boundary

The Product Owner allowed either of two evidence routes after Infineon's email
redirect: replace Q2 with a device whose available evidence closes
Q2Q-010 through Q2Q-015, or retain the selected Q2 and establish the missing
trajectory experimentally. This audit compares the credible 150 V candidates.
It does not change the accepted LM74930-Q1 hard-cutoff architecture.

A replacement is useful only if it removes the missing maximum-bound hot
`VDS(t)` / `ID(t)` evidence. A different 150 V rating, a larger typical SOA
plot, or a lower typical gate charge does not by itself close that gate.

## Candidate Comparison

| Candidate | Automotive / voltage / package | Useful evidence | Why it does not replace Q2 |
|---|---|---|---|
| `IAUTN15S6N025ATMA1` | Automotive, 150 V, TOLL, 2.5 mOhm maximum | Active/preferred product, AEC-Q101 validation, 175 degC operation, 0.42 K/W maximum RthJC and the lowest reviewed conduction loss | Public gate-charge conditions and SOA graph do not provide the required production-covered 101 V / 40 A / 150 degC paired trajectory; empirical qualification is required |
| `IAUTN15S6N038ATMA1` | Automotive, 150 V, TOLL, 3.8 mOhm maximum | Same current Infineon automotive 150 V family and same assembly class | Same missing trajectory evidence while conduction loss rises; no gate-closing advantage |
| `SQJQ570E` | Automotive, 150 V, PowerPAK 8x8L, 4.1 mOhm maximum | AEC-Q101 device and public electrical data | Non-drop-in package, higher loss, and no public maximum-bound 101 V / 40 A / 150 degC paired trajectory found |
| `SQJ590EP` | Automotive, 150 V, PowerPAK SO-8L, 9.8 mOhm maximum | AEC-Q101 device intended for fast switching | Non-drop-in package, approximately 3.9 times the selected 25 degC maximum RDS(on), and no gate-closing paired hot trajectory |
| `IPB048N15N5LF` | Industrial, 150 V, D2PAK, 4.8 mOhm maximum | Linear-FET family with wider linear-mode SOA | Not automotive-qualified, not TOLL/drop-in, higher loss, and its public SOA data still does not supply the required time-correlated production maximum at the project corner |
| Nexperia automotive Enhanced-SOA ASFET family | Automotive, publicly listed enhanced-SOA parts up to 60 V in the reviewed airbag family | Purpose-built improved linear-mode behavior | Voltage class cannot face the 101 V raw domain and therefore cannot be Q2 |

## Engineering Selection

Retain `IAUTN15S6N025ATMA1` and execute
`PB-100-q2-empirical-qualification-plan.md`.

This is preferred because:

- no reviewed replacement supplies the missing public qualification artifact;
- the selected part is active/preferred, automotive-qualified, 150 V and
  already bound to the reviewed TOLL assembly path;
- a blind replacement would add package, loss, thermal, sourcing, footprint and
  schematic risk while leaving Q2Q-010 through Q2Q-015 unresolved;
- a controlled empirical program directly measures the missing paired
  trajectory at the exact project corner.

This selection does not claim an Infineon production maximum. It creates
project-specific empirical qualification evidence only.

## Margin, Lifetime, Availability, and Production Effects

- Expected product lifetime remains 10-15 years, conditional on successful
  repeated-pulse qualification, normal prototype testing and order-date
  lifecycle recheck.
- The existing 49 V static VDS margin, 7.200 W hot-conduction bound and
  3.47 K/W full thermal-path requirement remain unchanged.
- Maximum junction rating remains 175 degC; the project qualification starts
  at 150 degC and does not raise the design target.
- Infineon lists the selected device active/preferred and automotive-qualified.
  LCSC stock is not claimed; JLCPCB/PCBWay supply, consignment, stencil, voiding,
  DFM and FAI remain order-date gates.
- The empirical program adds coupon, sample and laboratory cost but avoids an
  unnecessary PB-100 footprint and thermal redesign. Qualification equipment
  is laboratory infrastructure, not part of the production BOM.
- Known risk: sampled project qualification cannot become a semiconductor
  manufacturer production guarantee. Lot coverage, guardband, incoming change
  control and the parallel MyCases route mitigate but do not erase that risk.

## Official Evidence Reviewed

- Infineon selected Q2 product page:
  https://www.infineon.com/part/IAUTN15S6N025
- Infineon selected Q2 datasheet:
  https://www.infineon.com/assets/row/public/documents/10/49/infineon-iautn15s6n025-datasheet-en.pdf
- Infineon automotive 150 V TOLL/TOLG/TOLT family:
  https://www.infineon.com/package-technology/150v-mosfets-for-high-power
- Infineon OptiMOS Linear FET product brief:
  https://www.infineon.com/dgdl/Infineon-Product%2BBrief%2BOptiMOS%2BLinearFET%2B-PB-v01_00-EN.pdf?fileId=5546d4625d5945ed015d7f3ed34b00a8
- Nexperia automotive Enhanced-SOA airbag family:
  https://www.nexperia.com/products/mosfets/application-specific-mosfets/automotive-asfets-for-airbag-applications/
- Vishay automotive PowerPAK 8x8L family:
  https://www.vishay.com/en/mosfets/automotive-mosfets/powerpak-8x8l-package/
- Vishay SQJ590EP product page:
  https://www.vishay.com/en/product/62447/

## Authorization

This audit authorizes preparation of a dedicated qualification coupon under
the separate `QUALIFICATION-COUPON-ONLY` boundary. It does not authorize
PB-100 board import, `PB-100.kicad_pcb`, PB-100 placement/routing,
PB-100 Gerber/drill output,
prototype production, production release or field use. PBREL-007 remains
`Conditional` and aggregate PB-100 authorization remains `BLOCKED` until the
empirical acceptance contract passes or qualifying vendor evidence supersedes
it.
