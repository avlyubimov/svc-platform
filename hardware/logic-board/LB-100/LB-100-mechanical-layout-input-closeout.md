# LB-100 Mechanical Layout Input Closeout

Status: Closed for LB-100 mechanical board-import inputs
Review date: 2026-07-20

This closeout converts the LB-100 pre-layout mechanical envelope into reviewed
layout-input dimensions. It does not create `LB-100.kicad_pcb`, Gerbers, drill
files, pick-place files, BOM/CPL order packages, manufacturing ZIP files,
fabrication packages, panel CAD, enclosure CAD, harness drawings, or PCBA
orders.

## Why The Blocker Existed

LB-100 had closed requirements, schematic review, and footprint-binding
evidence, but board import still lacked reviewed mechanical inputs for the
outline, mounting holes, PB/LB JPB1 stack datum, STM32H563VITx service access,
power-rail placement, microSD access, BLE antenna keepout, IMU/lux sensor
orientation, and service/expansion connector keepouts.

The blocker was valid because LB-100 carries safety-relevant vehicle interfaces
and service paths. Starting board import without a mechanical datum could place
CAN1_TX_ROUTE, RF, storage, sensors, or debug access in positions that conflict
with the PB-100 stack or future enclosure serviceability.

## Candidate Comparison

| Area | Candidate A | Candidate B | Selection |
|---|---|---|---|
| Outline | 100 mm x 70 mm rectangular prototype | Match PB-100 full outline | 100 mm x 70 mm prototype outline |
| Mounting | Four M2.5 local holes | Share PB-100 M3 holes | Four M2.5 local holes |
| JPB1 placement | Centered FX18 datum | Edge-biased stack | Centered datum |
| MCU access | Central service corridor | Hide MCU under stack | Central service corridor |
| Power rails | Near JPB1 with no-back-power zone | Near USB/service edge | Near JPB1 |
| microSD | Right-edge service access | Internal-only card slot | Right-edge access |
| BLE | Top-right edge antenna keepout | Interior antenna placement | Edge antenna keepout |
| Sensors | Documented board axes | Vehicle-specific axis assumption | Documented board axes |
| Expansion | DNP/service lower-edge keepouts | Dedicated vehicle-role connectors | Generic DNP/service keepouts |

## Recommended Solution

Use `LB-100-mechanical-layout-inputs.csv` as the LB-100 mechanical source for
the first controlled KiCad board import after the remaining signal-integrity
and symbol-promotion gates close:

- Board outline: `100.0 mm x 70.0 mm`.
- Mounting: four `2.7 mm` finished NPTH M2.5 clearance holes at
  `X5.0/Y5.0`, `X95.0/Y5.0`, `X5.0/Y65.0`, and `X95.0/Y65.0`.
- JPB1: centered FX18 stack datum at `X50.0/Y35.0`, long axis along `X`.
- MCU: central STM32H563VITx service corridor with SWD, BOOT0, RESET, and clock
  access.
- Power rails: PB_5V_OUT entry and LB_3V3 conversion near JPB1 with no-back-power
  separation from service USB.
- microSD: right-edge card access with local ESD and card-detect clearance.
- BLE: top-right edge antenna keepout with copper and enclosure RF clearance
  deferred to selected module datasheet rules.
- Sensors: documented board axes plus quiet IMU and lux/aperture zones.
- Expansion/service: generic DNP/service keepouts while CAN1_TX_ROUTE remains
  DNP/open by default.

## Engineering Impact

- Cost impact: prototype PCB area is `70 cm²`. The outline is smaller than
  PB-100 but large enough for LQFP-100 fanout, RF keepout, storage access, and
  service connectors without using vendor-minimum DFM rules.
- Thermal impact: modest positive impact because regulator placement is kept
  near JPB1 and away from BLE and sensors. Final regulator dissipation, sleep
  current, and no-back-power behavior remain separate electrical and bench
  gates.
- Production impact: improves JLCPCB/PCBWay board-import readiness by defining
  outline, holes, connector/service access, RF keepout, sensor orientation, and
  stack datum before layout. It still does not authorize Gerbers, drills,
  pick-place, BOM/CPL, panel files, manufacturing ZIPs, fabrication packages, or
  PCBA orders.
- Field reliability: four-corner retention, edge-access storage, separated RF
  and regulator zones, serviceable SWD/BOOT/RESET, and a documented CAN1_TX_ROUTE
  DNP/open boundary reduce service damage, RF margin risk, debug dead ends, and
  accidental vehicle-CAN transmit enablement.

## Risks And Open Follow-Ups

- Final enclosure CAD or PB-100 standoff hardware can still move outline,
  mounting holes, service windows, and stack clearance.
- JPB1 pin-1 mirroring, paired datum tolerance, stack compression, and vibration
  retention must still close during controlled symbol promotion and board
  import.
- CAN, USB, SD, clock, BLE antenna, and sensor placement/routing constraints
  remain open in the signal-integrity and safety layout model.
- BLE module keepout and enclosure RF material must be verified against the
  selected module datasheet and later RF inspection.
- Missing optional hardware must remain a capability-unavailable state in
  firmware rather than a board-specific firmware fork.

## Alternatives

- Match LB-100 to the full PB-100 outline. Rejected for Rev.1 because it adds
  board area without improving logic-board serviceability and can put RF/storage
  features too close to high-current PB zones.
- Use PB-100 M3 holes for a shared stack. Rejected for the first prototype
  because independent M2.5 LB retention gives more freedom to tune board spacing
  and service access.
- Place BLE internally. Rejected because edge placement gives better RF margin
  and clearer copper keepout enforcement.
- Encode vehicle-specific connector positions. Rejected because architecture
  requires capability-driven hardware and configuration-based role mapping.

## Source Evidence

- `LB-100-mechanical-layout-inputs.csv`
- `LB-100-mechanical-envelope-inventory.csv`
- `LB-100-jpb1-resource-budget.csv`
- `LB-100-power-budget-precheck.md`
- `LB-100-rail-budget-closeout-precheck.csv`
- `LB-100-stm32h563-pin-binding-precheck.csv`
- `LB-100-mcu-sourcing-precheck.csv`
- `LB-100-communication-safety-precheck.csv`
- `LB-100-service-storage-sensor-precheck.csv`
- `hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-mechanical-layout-inputs.csv`
- `production/board-order/three_board_layout_rules.md`
- `docs/adr/ADR-0002-can-read-only-default.md`
- `docs/adr/ADR-0005-stm32h5-product-target.md`
- `docs/adr/ADR-0012-system-sleep-wake-and-parking-current.md`
- `docs/adr/ADR-0014-lb-fb-baseline-requirements.md`

## Boundary

LB-100 mechanical envelope is closed as a layout input only. KiCad board import
remains blocked by the open LB-100 signal-integrity and safety layout model plus
controlled schematic symbol-promotion gate. JLCPCB/PCBWay order state remains
`NO-GO`.
