# PB-100 Controlled Layout Progress

Status: `EVT-LAYOUT-AUTHORIZED` — partial schematic import and placement exist

## Completed Milestone

- Generated the controlled four-layer `kicad/PB-100.kicad_pcb` with the
  reviewed 150 mm x 90 mm outline, four local M3 holes and four shared M2.5
  PB/LB stack holes.
- Imported and placed every schematic component that currently has a reviewed
  Footprint property: 33 parts covering Q1/Q2/U1, Q101..Q110, JPB1, the
  complete PB-owned CAN1 physical/default-disable population and the protected
  three-wire FOG cable entry.
- Applied battery-entry, OUT1/OUT2, OUT3..OUT10, fuse-service and CAN/service
  placement zones plus explicit Rev.1 EVT and partial-import markings.
- Routed the already complete low-current CAN1 safety island and the protected
  FOG cable entry: 110 segments and 14 through vias are recorded in
  `kicad/PB-100-can-routing.csv` and `kicad/PB-100-fog-entry-routing.csv`.
  `D_FOG1` is placed beside `JFOG1`; `R_FOG_GND` is the default `SW_COMMON`
  selection and `R_FOG_12V` plus `F_FOG_12V` remain DNP.
- Preserved C36 as the off-board, separately fused `VBAT_RAW`
  `C36_BIDIRECTIONAL` branch outside OUT1..OUT10 and `IIN_SENSE`.
- Added deterministic generation and CI validation. KiCad reports no copper
  shorts, track crossings, clearance violations, edge violations, courtyard
  overlaps or mounting-hole conflicts in the routed CAN/FOG subset. Open
  connectivity is 127 without creating provisional power copper.

## EVT-FAB Blockers

- Promote the 46 still-missing on-board footprints and all exact values into
  the schematic, including the selected output-controller passives/clamps,
  shunt/INA228, logic buck, thermal sensors, test points and harness transition
  provisions. Resolve the six U1 unconnected-pin parity findings.
- Re-import for zero schematic parity findings, then finish placement, signal
  routing, 40 A power copper, Kelvin shunt, power vias, replaceable gate elements, DNP alternatives,
  isolation/safe-off hooks, thermocouple sites and EVT serial field.
- Close zero DRC/unconnected/parity, 40 A electrothermal, Q1/Q2 clamp-loop
  parasitic, connector fit, probe/safety fixture, supplier DFM and Product Owner
  pre-fab review requirements.

This partial board is not suitable for fabrication. No manufacturing outputs
exist, and PBREL-007 remains a separate `PRODUCTION-RELEASE` blocker only.
