# ADR-0015: Assign CAN1 physical-layer ownership

## Status
Proposed — Product Owner decision required

## Context
ADR-0002 requires vehicle CAN1 transmit to be physically disabled by default.
ADR-0014 assigns CAN interfaces and firmware execution to LB-100, but it does
not explicitly separate protocol/controller ownership from transceiver,
protection, termination, and vehicle-harness ownership.

The current JPB1 map carries four CAN1-related logic signals:

- `CAN1_TX_DISABLE_CMD`
- `CAN1_TX_DISABLED_STATUS`
- `CAN1_RX_ROUTE`
- `CAN1_TX_ROUTE`

PB-100 now has the electrically verified safety order
`CAN1_TX_ROUTE -> U_CAN1 -> CAN1_TX_GATE_OUT -> JP_CAN1 (DNP/open) ->
CAN1_TXD_SAFE`. `CAN1_TXD_SAFE` is local to PB-100 and is not present on JPB1.
Therefore a transceiver located on LB-100 cannot connect its TXD pin to this
post-jumper net without another board-to-board signal. The existing instruction
to connect an LB-100 transceiver directly to `CAN1_TXD_SAFE` is physically
impossible under the current connector contract.

## Candidate comparison

### A. PB-100 owns the CAN1 physical layer — recommended

LB-100 retains the STM32 FDCAN controller, protocol handling, and read-only
firmware policy. PB-100 owns the CAN1 transceiver, bus protection, termination
population options, and vehicle-harness interface.

The existing JPB1 signals are sufficient: MCU TX crosses as
`CAN1_TX_ROUTE`; the PB-local safe output drives transceiver TXD; transceiver
RXD returns as `CAN1_RX_ROUTE`; command and physical-status readback use the
other two pins. CANH/CANL do not cross JPB1.

- Cost impact: neutral; the design still uses one CAN1 transceiver and its
  protection, but their BOM and assembly ownership move from LB-100 to PB-100.
- Thermal impact: approximately the existing 25 mA receive-only budget moves
  to PB-100; junction and regulator margin must be recalculated from the final
  transceiver data sheet and PB rail choice.
- Production impact: PB gains the transceiver, ESD, optional termination, and
  CAN connector/harness inspection; LB removes those physical-layer parts.
- Field reliability: shortest protected CANH/CANL path to the vehicle harness,
  no unprotected differential pair through the mezzanine connector, and no
  extra post-jumper logic crossing.
- Main risks: PB switching noise, ground return, common-mode range, VIO/VCC
  sequencing, termination ownership, and transceiver placement require EMC and
  layout review.

### B. LB-100 owns the complete CAN1 interface

Move the gate, DNP link, readback, transceiver, protection, termination, and
vehicle CAN connector to LB-100. PB-100 keeps its CAN1 option footprints DNP
and the related JPB1 signals unused in the default assembly.

- Cost impact: neutral, but the LB mechanical/harness interface changes.
- Thermal impact: remains in the existing LB transceiver budget.
- Production impact: current LB sourcing ownership remains valid; PB CAN1
  safety components become retained DNP capability.
- Field reliability: gate and transceiver are colocated, but the vehicle CAN
  harness must reach LB-100 and the current PB CAN service-exit plan is no
  longer valid.
- Main risks: enclosure access, ESD entry location, ground return, and service
  routing need a new LB mechanical review.

### C. PB gate with LB transceiver and an added return path — not recommended

Add a new `CAN1_TXD_SAFE_RETURN` connection after `JP_CAN1` and route it back
to an LB transceiver, consuming a spare JPB1 position. If the vehicle harness
still enters PB-100, CANH/CANL would also need a reviewed board crossing.

- Cost impact: small BOM impact but higher connector/pin and verification cost.
- Thermal impact: remains on LB-100.
- Production impact: both boards own safety-chain fragments and require paired
  continuity inspection.
- Field reliability: more connectors, longer logic/differential paths, more
  failure modes, and a more difficult no-bypass proof.
- Main risks: connector intermittency, ground-domain sequencing, EMC, pin-map
  churn, and ambiguous safety ownership.

## Recommendation

Approve candidate A. It preserves the already verified PB safety chain, the
current four-signal JPB1 contract, and the PB-side CAN harness corridor while
keeping CAN protocol and firmware ownership on LB-100. It also places the
transceiver and protection closest to the external bus entry.

## Required implementation evidence after approval

- Product Owner changes this ADR to `Accepted`.
- PB-100 transceiver family, VCC/VIO rails, silent-mode default, ESD,
  common-mode choke/termination population, connector, and CANH/CANL ownership
  are captured from manufacturer data sheets.
- `CAN1_TXD_SAFE` connects only to the selected PB transceiver TXD.
- Transceiver RXD connects only to `CAN1_RX_ROUTE`.
- Exported PB/LB netlists prove no bypass around `JP_CAN1` and preserve physical
  disabled-status readback.
- BOM, sourcing, power budgets, footprint inventories, assembly notes, and
  reset/unpowered verification are moved to their approved board owners.
- Critical components retain at least two alternatives and assembly evidence
  for JLCPCB/PCBWay.

## Consequences while Proposed

PBREL-001 and LBREL-004 remain `Conditional`. Neither CAN1 transceiver may be
placed in a board schematic, and PCB layout remains blocked. No existing DNP
footprint is removed.
