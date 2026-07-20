# PB-100 Mechanical Layout Input Closeout

Status: Conditional; JPB1 physical paired-stack mechanics remain open

The outline and placement datum remain useful inputs, but this closeout does not
close the physical 20 mm stack tolerance, vibration retention, mating
inspection, or assembly-fixture evidence. Both FX18 footprints already contain
six official plated lands with four GND MF circuits. Board import remains
blocked.
Review date: 2026-07-20

This closeout converts the PB-100 pre-layout mechanical envelope into reviewed
layout-input dimensions. It does not create `PB-100.kicad_pcb`, Gerbers, drill
files, pick-place files, BOM/CPL order packages, manufacturing ZIP files,
fabrication packages, panel CAD, enclosure CAD, harness drawings, or PCBA
orders.

## Why The Blocker Existed

PB-100 had closed schematic and footprint evidence, but board import still
lacked reviewed mechanical inputs for the board outline, mounting datum,
service-cover clearance, battery harness entry, generic OUT1..OUT10 exits, fuse
service access, JPB1 stack placement, high-current power zones, and CAN/service
signal exit.

The blocker was valid because KiCad board import would otherwise require layout
decisions without a documented datum or service boundary. That would risk
hard-coding harness roles, placing high-current copper by convenience, or
creating fabrication assumptions before schematic and layout gates authorize
them.

## Candidate Comparison

| Area | Candidate A | Candidate B | Selection |
|---|---|---|---|
| Outline | 150 mm x 90 mm rectangular prototype | Wait for final enclosure CAD | 150 mm x 90 mm prototype outline |
| Mounting | Four M3 holes | Two holes plus edge support | Four M3 holes |
| Battery entry | Off-board fused harness | PCB-mounted high-current input connector | Off-board fused harness |
| OUT1/OUT2 exits | Off-board DTP harness exits | PCB-mounted high-current housings | Off-board DTP exits |
| OUT3..OUT10 exits | Off-board DT harness exits | Role-specific panel connector grouping | Off-board generic DT exits |
| Fuse access | Off-board garage-service fuse zone | PCB-mounted fuse holders | Off-board service-cover zone |
| JPB1 placement | Centered FX18 datum | Edge-biased mezzanine | Centered datum |
| Power zones | Explicit pre-layout placement zones | Free placement during layout | Explicit high-current zones |
| CAN/service exit | Separate low-current edge | Shared power-harness edge | Separate low-current edge |

## Recommended Solution

Use `PB-100-mechanical-layout-inputs.csv` as the PB-100 mechanical source for
the first controlled KiCad board import after the remaining thermal/current
layout model and symbol-promotion gates close:

- Board outline: `150.0 mm x 90.0 mm`.
- Mounting: four `3.2 mm` finished NPTH M3 clearance holes at
  `X6.0/Y6.0`, `X144.0/Y6.0`, `X6.0/Y84.0`, and `X144.0/Y84.0`.
- Battery entry: off-board near-battery-fused harness on the `X=0` edge.
- OUT1/OUT2: generic high-current DTP harness exits on the lower long edge.
- OUT3..OUT10: generic DT harness exits on the upper long edge.
- Fuses: off-board service-cover zone with generic OUT1..OUT10 labeling.
- JPB1: centered FX18 stack datum at `X75.0/Y45.0`, long axis along `X`.
- Power zones: input/reverse protection, OUT1/OUT2, and OUT3..OUT10 zones are
  reserved without routing copper.
- CAN/service: separate low-current exit on the `X=150.0` edge with CAN1 TX
  preserved as DNP/open by default.

## Engineering Impact

- Cost impact: prototype PCB area is `135 cm²`. This is intentionally larger
  than a minimum outline to buy routing, thermal, harness, fuse-service, and
  inspection margin within the `<=500 USD` prototype budget.
- Thermal impact: positive at planning level because high-current zones reserve
  area for MOSFET copper, shunt Kelvin routing, TVS heat spreading, and thermal
  sensor proximity. Final copper width, via field, paste aperture, and
  enclosure heat path remain in the open thermal/current layout model.
- Production impact: improves JLCPCB/PCBWay board-import readiness by defining
  outline, holes, harness corridors, service access, and keepouts before layout.
  It still does not authorize Gerbers, drills, pick-place, BOM/CPL, panel files,
  manufacturing ZIPs, fabrication packages, or PCBA orders.
- Field reliability: four-corner M3 retention, off-board strain relief,
  separated power and signal exits, serviceable fuses, and generic harness
  labeling reduce vibration, cable fatigue, accidental role binding, and
  service mistakes.

## Risks And Open Follow-Ups

- Final enclosure CAD can still move outline, mounting holes, service-cover
  windows, connector exits, and strain-relief hardware.
- OUT1/OUT2 DTP and OUT3..OUT10 DT exact housings, seals, boots, backshells,
  cable bend radius, and harness labels remain garage BOM and enclosure review
  inputs.
- JPB1 pin-1 mirroring, paired PB/LB datum tolerance, board spacing, and
  vibration retention must still be verified during controlled symbol promotion
  and board import.
- High-current zones do not prove thermal performance. MOSFET SOA, shunt
  heating, TVS surge energy, copper temperature rise, fuse coordination, and
  enclosure heat path remain open thermal/current layout evidence.
- CAN1 remains read-only by default. Any populated vehicle-CAN TX path still
  requires a future ADR plus explicit hardware action.

## Alternatives

- Wait for final enclosure CAD before mechanical closure. Rejected for Rev.1
  board-import planning because it blocks schematic-to-board transfer even
  though the current gate only needs a reviewed prototype datum.
- Put high-current connectors and fuses directly on PB-100. Rejected for Rev.1
  because ADR-0003 and the garage plan keep user-installed connectors, fuses,
  enclosure hardware, and wiring outside factory SMD assembly.
- Shrink the board outline now. Rejected because high-current copper, fuse
  serviceability, creepage, inspection, and rework margin have higher priority
  than first-prototype PCB area cost.

## Source Evidence

- `PB-100-mechanical-layout-inputs.csv`
- `PB-100-mechanical-envelope-inventory.csv`
- `PB-100-garage-connector-fuse-plan.md`
- `PB-100-garage-purchase-kit-candidates.csv`
- `PB-100-b2b-interface-closeout-precheck.csv`
- `PB-100-board-current-budget-design-calculation.md`
- `PB-100-thermal-estimates.csv`
- `PB-100-output-stage-design-values.csv`
- `PB-100-can1-tx-disable.md`
- `production/board-order/three_board_layout_rules.md`
- `docs/adr/ADR-0002-can-read-only-default.md`
- `docs/adr/ADR-0003-factory-smd-assembly.md`
- `docs/adr/ADR-0004-generic-outputs-role-mapping.md`
- `docs/adr/ADR-0008-pb-100-current-budget.md`

## Boundary

PB-100 mechanical envelope is closed as a layout input only. KiCad board import
remains blocked by the open PB-100 thermal/current layout model and controlled
schematic symbol-promotion gate. JLCPCB/PCBWay order state remains `NO-GO`.
