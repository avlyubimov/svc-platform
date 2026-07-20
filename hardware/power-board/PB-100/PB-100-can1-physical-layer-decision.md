# PB-100 CAN1 Physical-Layer Decision

## Decision

Product Owner accepted ADR-0015 candidate A on 2026-07-20. PB-100 owns the
CAN1 transceiver, local protection, optional common-mode choke and termination,
`CANH`/`CANL`, and the vehicle-harness boundary. LB-100 retains STM32 FDCAN,
protocol handling, and read-only firmware policy.

The Rev.1 candidate is `TJA1051TK/3/1J` in HVSON8 with exposed pad. Its TXD is
connected only to `CAN1_TXD_SAFE`; RXD is connected only to
`CAN1_RX_ROUTE`. VCC uses `PB_5V_OUT`, VIO uses `LB_3V3_IO`, pins 2 and 9
use `GND`, and each supply has a local 100 nF X7R decoupler. The S input has a
47 kOhm pull-up so the default assembly is silent/receive-only.
`JP_CAN1_NORMAL` is DNP/open and can pull S low only after a future ADR and an
explicit hardware population action.

`ESD2CANFD24QDBZRQ1` protects both bus lines in a leaded SOT-23 package.
`R_CAN1_TERM` is a 120 Ohm 1% 0603 DNP option across the bus. No common-mode
choke is populated in the baseline: the PCB corridor and PB ownership are
retained, but a choke MPN and footprint may be introduced only if conducted or
radiated EMC evidence shows it is needed. No CANH/CANL signal crosses JPB1.

## Why these components

### Transceiver

- Preferred: NXP `TJA1051TK/3/1J`, JLCPCB/LCSC `C2875699`, HVSON8-EP. It
  provides a VIO pin for the 3.3 V LB domain, CAN FD operation up to 5 Mbit/s,
  silent mode with an active receiver, TXD dominant timeout, undervoltage and
  thermal protection, and AEC-Q100 qualification.
- Alternative A: NXP `TJA1057GTK/3Z`, the same functional pin order and
  HVSON8-EP implementation class. NXP lists this as an active longevity-family
  successor with a minimum 15-year product-longevity commitment. It is the
  preferred lifecycle substitution after assembly-source confirmation.
- Alternative B: TI `TCAN1042HGV-Q1`. It provides 5 Mbit/s CAN FD, 3.3/5 V
  logic compatibility, AEC-Q100 qualification and a high bus-fault rating, but
  its standby/control behavior and VSON/SOIC footprint require a separate
  schematic and footprint review. It is not a drop-in assembly substitution.

The older `TJA1051T/1J` is not selected for CAN1 because it lacks the VIO pin
used to isolate the 3.3 V LB logic domain from the 5 V transceiver supply. A
transceiver on LB-100 is rejected because `CAN1_TXD_SAFE` is PB-local and there
is no safe-return JPB1 signal. This is the physical contradiction resolved by
ADR-0015.

### ESD and termination

- Preferred: TI `ESD2CANFD24QDBZRQ1`, a two-channel 24 V bidirectional CAN-FD
  protector in the AOI-friendly DBZ SOT-23 package, with low line capacitance
  and automotive qualification.
- Alternative A: Nexperia `PESD2CANFD24V-T`, a dual-line automotive CAN-FD
  protector in SOT23. Pin assignment, exact clamp curve, and assembly source
  must be rechecked before substitution.
- Alternative B: onsemi `NUP2105LT1G`, retained only as a sourcing escape;
  capacitance and clamp performance must be revalidated against the selected
  CAN data rate and transceiver limits.
- The 120 Ohm termination is DNP because vehicle-bus termination belongs at
  the two physical bus ends. Population requires a harness/topology review.

## Operating and thermal margin

- `PB_5V_OUT` nominal 5 V is centered in the NXP 4.5 V to 5.5 V VCC range.
- `LB_3V3_IO` nominal 3.3 V is inside the 2.91 V to 5.5 V VIO range.
- The PB logic budget reserves 70 mA for transceiver dominant/service current;
  normal receive-only planning uses 10 mA. VIO current remains a small LB I/O
  load and is not counted as a 5 V source.
- The transceiver and preferred MOSFET-class components use automotive
  temperature qualification. Final placement must verify the transceiver
  junction estimate against its 150 degC maximum and keep it away from PB
  switching hot spots; the target design limit is 125 degC junction.
- The ESD component is at the harness entry with the shortest practical return
  to `GND`. CANH/CANL must be routed as a controlled differential pair; the
  optional termination stub and ESD stubs must be short.

## Lifetime, availability, and assembly

- Expected vehicle service target: at least 10 years. The preferred NXP part
  has active distributor/JLC evidence for the prototype; the TJA1057 alternate
  carries the stronger published longevity commitment.
- JLCPCB: `TJA1051TK/3/1J` has an identified Extended-library source
  (`C2875699`). ESD, X7R capacitors, resistors, and DNP handling require a
  fresh pre-order stock check.
- PCBWay: HVSON8 exposed-pad, SOT-23 and 0402/0603 assembly are conventional,
  but paste segmentation, AOI access, DNP markings, and alternate sourcing
  remain quotation checks.
- The HVSON exposed pad is `GND` and uses segmented paste apertures. The SOT-23
  ESD package is leaded and AOI-visible.

## Known risks and closeout evidence

- PB switching noise and ground return can degrade CAN common-mode/EMC margin.
- A common-mode choke decision remains evidence-driven; do not add a generic
  footprint without an exact AEC-Q200 part and insertion-loss review.
- The exact sealed vehicle connector/harness MPN remains a mechanical and
  sourcing gate. The schematic net names deliberately end at
  `CAN1_HARNESS_H` and `CAN1_HARNESS_L` until that connector is selected.
- `JP_CAN1` and `JP_CAN1_NORMAL` must both remain DNP/open in the default BOM.
- Bench closeout must verify reset, unpowered, either-link-open, both-links-open,
  RX operation, disabled-status readback, ESD continuity, and absence of CAN TX
  frames. Exported-netlist validation must continue to prove the exact chain.

## Primary sources

- NXP TJA1051 data sheet: https://www.nxp.com/docs/en/data-sheet/TJA1051.pdf
- NXP TJA1057 data sheet: https://www.nxp.com/docs/en/data-sheet/TJA1057.pdf
- NXP TJA1057 product page: https://www.nxp.com/products/TJA1057
- TI TCAN1042HGV-Q1: https://www.ti.com/product/TCAN1042HGV-Q1
- TI ESD2CANxx24-Q1 data sheet: https://www.ti.com/lit/ds/symlink/esd2can24-q1.pdf
- Nexperia PESD2CANFD24V-T: https://www.nexperia.com/product/PESD2CANFD24V-T
