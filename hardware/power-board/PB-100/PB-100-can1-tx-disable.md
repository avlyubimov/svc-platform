# PB-100 CAN1 TX Disable Schematic Input

Status: Schematic-planning input

This document implements the ADR-0002 and Architecture v1.0 rule that vehicle
CAN is read-only by default. It does not authorize CAN1 transmit support.

## Applicability

This input applies if CAN1 routing, a CAN1 transceiver, or a CAN1 safety gate
crosses PB-100. If CAN1 stays entirely on LB-100, LB-100 must implement an
equivalent default-disabled hardware path and PB-100 keeps the related `JPB1`
signals DNP.

## Rev.1 default

- `CAN1_RX_ROUTE` may be populated for listen-only reception.
- `CAN1_TX_ROUTE` is DNP/open by default.
- Any CAN1 TX path to the vehicle bus requires both a future ADR and an explicit
  hardware action.
- `CAN1_TX_DISABLE_CMD` is a disable command, not an enable command. The
  hardware default must assert disable while LB-100 is reset, unpowered, or not
  fitted.
- `CAN1_TX_DISABLED_STATUS` must report the physical disabled state back to
  LB-100 where the safety gate crosses PB-100.

## Required hardware behavior

| State | Required behavior |
|---|---|
| LB-100 unpowered or reset | CAN1 TX path remains disabled |
| PB-100 unpowered or reset | No CAN1 TX path is enabled through PB-100 |
| Firmware drives CAN1 TX | No vehicle-bus transmit path exists in Rev.1 default assembly |
| Future ADR accepts CAN1 TX | Hardware action is still required before TX can reach vehicle CAN |
| TX-disable status fault | Firmware treats vehicle CAN as listen-only and blocks any TX attempt |

## Allowed schematic mechanisms

Use one or more of these mechanisms:

- DNP zero-ohm link or solder jumper in the CAN1 TX path.
- Logic gate with a hardware pull that defaults to TX disabled.
- Transceiver silent/listen-only pin pulled to silent by default.
- Readback path for the physical disable state.

The preferred Rev.1 schematic input is both a DNP/open TX route and a default
asserted disable gate. This gives a physical missing-link barrier plus an
electrical disable state.

## Rev.1 capture contract

The schematic capture packet must show these two refs if CAN1 safety crosses
PB-100:

| Ref | Required default | Capture intent |
|---|---|---|
| `JP_CAN1` | DNP/open | Physical missing-link barrier in `CAN1_TX_ROUTE`; no default-populated TX item |
| `U_CAN1` | Disabled | Optional gate or transceiver silent-control element with hardware default that asserts `CAN1_TX_DISABLE_CMD` while LB-100 is reset, unpowered, or absent |

`CAN1_TX_DISABLED_STATUS` must be sourced from the physical disabled state where
the gate exists. A firmware variable, configuration flag, or MCU output alone is
not acceptable as disabled-status evidence.

Configuration cannot enable vehicle-CAN TX in Rev.1. Any CAN1 TX support needs
a future ADR plus an explicit hardware action that changes the DNP/open
production state.

## `JPB1` signal contract

| Signal | Direction | Rev.1 default |
|---|---|---|
| `CAN1_TX_DISABLE_CMD` | LB-100 to PB-100 | Disable asserted by hardware pull |
| `CAN1_TX_DISABLED_STATUS` | PB-100 to LB-100 | Asserted when the physical TX path is disabled |
| `CAN1_RX_ROUTE` | PB-100 to LB-100 | DNP unless CAN1 is routed through PB-100 |
| `CAN1_TX_ROUTE` | LB-100 to PB-100 | DNP/open and hardware-gated unless future ADR allows TX |

## Schematic review checks

- CAN1 TX route is visibly marked DNP/open by default.
- Disable command default state is shown with a pull resistor or equivalent
  hardware default.
- Disable status cannot falsely indicate enabled-safe while the TX gate is
  unknown.
- CAN1 RX can be populated independently from CAN1 TX.
- Schematic notes state that Rev.1 firmware must not transmit on vehicle CAN.
- Any future CAN1 TX enable path is marked as requiring a new ADR and explicit
  hardware action.
- Factory BOM output marks `JP_CAN1` or equivalent TX link DNP/open and not a
  default-populated TX item.
