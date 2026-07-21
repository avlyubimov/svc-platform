# PB-100 CAN1 Physical Closeout

Status: Closed pre-layout evidence for PBREL-001; physical bench remains post-prototype

ADR-0015 candidate A is implemented without moving CAN1 ownership back to
LB-100. PB-100 owns the transceiver, line protection, optional termination,
CANH/CANL, and the vehicle-harness boundary. LB-100 owns STM32 FDCAN, protocol,
and read-only firmware policy.

## Audited topology

The KiCad exported-netlist validator proves this exact chain:

`CAN1_TX_ROUTE -> U_CAN1 -> CAN1_TX_GATE_OUT -> JP_CAN1 (DNP/open) -> CAN1_TXD_SAFE -> U_CAN1_PHY.TXD`

`U_CAN1_PHY.RXD -> CAN1_RX_ROUTE` is independent and has no TX dependency.

The production assembly has two independent hardware barriers:

- `JP_CAN1` is DNP/open, so gate output cannot reach transceiver TXD.
- `JP_CAN1_NORMAL` is DNP/open and `R_CAN1_SILENT` pulls the TJA1051 S input
  high, so the transceiver remains silent even if the first link is fitted by
  mistake.

The gate has a populated 47 kohm OE-disable pull. The physical OE node feeds
`CAN1_TX_DISABLED_STATUS` through 1 kohm with a 100 kohm pull-up. TXD has a
47 kohm recessive pull-up. These are real schematic nets and pass exported XML
topology checks; they are not text-marker assertions.

## Vehicle harness boundary

The garage-installed sealed pair is frozen for CAN/service use:

- receptacle housing: TE DEUTSCH `DTM04-4P`;
- plug housing: TE DEUTSCH `DTM06-4S`;
- pin contact: `0460-202-20141`;
- socket contact: `0462-201-20141`;
- wedgelocks: `WM-4P` and `WM-4S`;
- conductor class: 0.5-1.0 mm2 / 20-18 AWG; CAN pair must be twisted;
- cavity 1: GND reference;
- cavity 2: CANL;
- cavity 3: CANH;
- cavity 4: `CAN_SERVICE_RESERVE`, no-connect/DNP by default.

This is an off-board harness termination and therefore has no PCB footprint or
CPL entry. It must not be used for output power.

## Production and test controls

- Factory BOM and CPL generation must contain no placement for `JP_CAN1` or
  `JP_CAN1_NORMAL`; AOI/visual first-article evidence must show both open.
- Any populated link is a lot rejection unless a future ADR explicitly changes
  the vehicle-CAN TX policy.
- PB-BENCH-012 verifies reset, LB-unpowered, listen-only RX, disabled-status,
  and zero transmitted vehicle-CAN frames after prototype assembly.
- Configuration and firmware can never populate either physical link.

PB-BENCH-012 is intentionally a post-prototype release gate under ADR-0013. It
blocks motorcycle first power/field use, but does not make schematic capture an
impossible prerequisite for prototype hardware.

## Primary sources

- SN74LVC1G125-Q1: <https://www.ti.com/lit/ds/symlink/sn74lvc1g125-q1.pdf>
- TJA1051: <https://www.nxp.com/docs/en/data-sheet/TJA1051.pdf>
- DTM04-4P: <https://www.te.com/en/product-DTM04-4P.html>
- DTM06-4S: <https://www.te.com/en/product-DTM06-4S.html>
