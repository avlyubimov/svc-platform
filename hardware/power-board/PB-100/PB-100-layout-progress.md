# PB-100 Controlled Layout Progress

Status: `EVT-LAYOUT-AUTHORIZED` — routed baseline exists; `EVT-FAB-REVIEW` remains blocked

## Completed Milestone

- Generated the controlled eight-layer `kicad/PB-100.kicad_pcb` with the
  reviewed 150 mm x 90 mm outline, four local M3 holes and four shared M2.5
  PB/LB stack holes. The stack keeps In2.Cu as the continuous GND reference
  and In5.Cu as the protected-battery distribution plane.
- Imported and placed all 414 footprint-bound schematic parts plus eight
  board-only mounting holes. Schematic parity is closed except for the eight
  intentional mounting-hole footprints.
- Preserved the accepted architecture: ten generic outputs, configuration-
  mapped channel roles, the 40 A board target, removable input isolation,
  factory/DNP alternatives, and the physically default-disabled CAN1 TX path.
- Added explicit battery-entry and output-current zones, protected-bus
  transitions and conventional through-via fields. The broad generated
  segments and zones remain the only copper credited to the high-current path;
  preliminary 0.20 mm attachment traces are not current-capacity evidence.
- Recorded 5,778 deterministic routing-manifest items in
  `kicad/PB-100-routing.csv`: 5,016 segments and 762 conventional through
  vias. Together with generator-owned power copper, the board contains 5,049
  segments, 874 vias and 38 zones.
- Added deterministic route export, residual-route handling and validation.
  A clean regeneration followed by KiCad 10.0.4 zone refill reports no shorts,
  track crossings, copper-clearance, edge-clearance, drill or keepout
  violations introduced by this routing baseline.
- Reduced open connectivity from 499 to 36. The DRC-clean closeout includes
  the previously trapped `LB_3V3_IO`, `PB_I2C_INT`, `OUT1_IWRN` and
  `OUT2_IWRN` branches. Dense controller fan-out was recovered with local
  signal-layer jogs and 0.60/0.30 mm filled/capped conventional through vias;
  no blind or buried vias were introduced. The remaining items are explicit
  blockers rather than hidden or waived connections.

## EVT-FAB Blockers

- Close all 36 remaining connections. The largest groups are 14 GND
  pad/pour/plane fragments, four `OUT7_SWITCHED` branches, three
  `VBAT_PROT` attachments, two `VBAT_REV_PROT` branches and two
  `OUT4_SWITCHED` branches. Eleven single residuals remain across controller
  support, timing/sense, output-zone and power-option nets.
- Replace preliminary attachment routing where required by the final
  current/thermal model. In particular, close the protected 5 V and 3.3 V rail
  widths, buck switch loop, clamp-current returns, CAN1 coupled-pair geometry
  and all high-current zone neck/current-density evidence before fabrication.
- Resolve the current project-context refilled warning baseline: 27
  project-library footprint mismatches, eight project-library footprint
  issues, 136 silk-over-copper findings, nine starved thermals and 17
  silkscreen overlaps.
- Close 40 A electrothermal extraction, Q1/Q2 and output clamp-loop parasitics,
  connector fit, probe/safety fixture access, supplier stack/DFM review and
  Product Owner pre-fabrication approval.

This routed baseline is not suitable for fabrication. No Gerbers, drills,
pick-place, manufacturing ZIP or order package is authorized or generated.
`PBREL-007` remains a separate `PRODUCTION-RELEASE` blocker.

Reason: ADR-0020 authorizes placement, routing and pours, but not fabrication.
The current milestone preserves the accepted architecture and gives the
remaining work a deterministic, DRC-checked starting point without treating
autorouter connectivity or thin attachment traces as 40 A, EMC, thermal or
production evidence.
