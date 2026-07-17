# PB-100 CAN1 TX Disable Design Calculation

Status: Candidate values for schematic review; not final

This note defines a value-bearing Rev.1 candidate for the CAN1 physical
TX-disable path. It preserves the ADR-0002 rule that vehicle CAN is read-only
by default. It does not authorize CAN1 transmit support, PCB layout, footprint
lock, or manufacturing output.

## Inputs

- `CAN1_TX_ROUTE` must be DNP/open by default with no default-populated vehicle
  CAN TX path.
- `CAN1_TX_DISABLE_CMD` is a disable command, not an enable command.
- `CAN1_TX_DISABLED_STATUS` must be sourced from a physical disabled-state node,
  not from firmware-only state.
- Any CAN1 TX support requires a future ADR plus an explicit hardware action.
- `CAN1_RX_ROUTE` may remain independent for listen-only RX if CAN1 crosses
  PB-100.

## Candidate Rev.1 network

| Item | Candidate | Rationale | Still open |
|---|---|---|---|
| `JP_CAN1` TX link | 0 Ω 0603 link DNP/open in series with `CAN1_TX_ROUTE` | Physical missing-link barrier and no default-populated TX item | Final footprint and production DNP note |
| Solder-jumper alternate | Normally-open two-pad solder bridge DNP/open | Factory-visible physical action if a future ADR accepts TX | Assembly process review |
| `U_CAN1` gate | `SN74LVC1G125-Q1`-class non-inverting 3-state buffer on `LB_3V3_IO` | Output disabled when `OE` is high and supports automotive logic gate path | Exact package and symbol pin review |
| Disable pull | 47 kΩ from `CAN1_TX_DISABLE_CMD` / `OE` node to `LB_3V3_IO` | Defaults `U_CAN1` disabled while LB-100 is reset if rail is present | Reset/unpowered bench test |
| Downstream TXD bias | 47 kΩ pull-up from gated TXD output to transceiver VIO or `LB_3V3_IO` | Holds CAN transceiver TXD recessive if the gate is high-Z | Final transceiver VIO ownership |
| Status readback | 1 kΩ series from the physical `OE` disable node to `CAN1_TX_DISABLED_STATUS` | LB-100 reads the gate disable state rather than a firmware variable | If review requires auxiliary DNP-link detect |
| Status default | 100 kΩ pull-up to `LB_3V3_IO` on `CAN1_TX_DISABLED_STATUS` | Status reads disabled when the gate-control node is high or open | Exact LB input leakage |
| Optional filter | 1 nF DNP from `CAN1_TX_DISABLED_STATUS` to `GND` | Bench-only debounce option without hiding reset faults | Timing review |

The default assembly keeps `JP_CAN1` DNP/open. Populating `U_CAN1` does not
create a vehicle-CAN TX path unless a future ADR also changes the DNP/open
hardware state. If `LB_3V3_IO` is absent, the gate is unpowered and the DNP/open
TX link remains the primary safety barrier.

## Physical status boundary

The candidate status path reports the physical gate-control node. It is not a
firmware flag and is not derived from a configuration setting. The DNP/open
`JP_CAN1` link remains verified through schematic, BOM, and production review.
If schematic review requires direct link-state detection, add an auxiliary
normally-open jumper-detect contact before freeze; do not infer link population
from firmware.

## Bench checks before freeze

- With LB-100 reset, verify `CAN1_TX_DISABLE_CMD` / `OE` is pulled disabled.
- With LB-100 unpowered, verify no TX signal reaches the vehicle-CAN TX path.
- With `JP_CAN1` DNP/open, verify `CAN1_TX_ROUTE` has no default-populated path.
- Verify `CAN1_TX_DISABLED_STATUS` reflects the physical disable node.
- Verify `CAN1_RX_ROUTE` listen-only population does not require TX population.

## Freeze blockers

- Confirm exact `SN74LVC1G125-Q1` orderable suffix or select an automotive
  equivalent 3-state buffer.
- Review active-high disabled polarity against the final transceiver TXD pin.
- Confirm `LB_3V3_IO` availability and reset sequencing for the gate and status
  pull-ups.
- Add direct DNP-link detect if independent review requires it.
- Confirm factory DNP handling for `JP_CAN1` and the production BOM note.
- Keep PCB layout blocked until schematic freeze closes.

## Evidence links

- ADR-0002 CAN read-only default:
  `docs/adr/ADR-0002-can-read-only-default.md`
- TI SN74LVC1G125-Q1 data sheet:
  https://www.ti.com/lit/ds/symlink/sn74lvc1g125-q1.pdf
