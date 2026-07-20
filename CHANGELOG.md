# Changelog

## Unreleased

- Initial SVC platform architecture.
- Added project constitution.
- Added Architecture Review draft.
- Added ADRs.
- Added Factory/Garage BOM drafts.
- Added firmware safety enforcement for delayed battery cutoff, runtime
  load-shedding, thermal derate, and PWM increase revalidation.
- Added system sleep/wake and parking-current ADR plus requirements.
- Hardened PB-100 KiCad validation to require fixed KiCad CLI, reject
  placeholder sheets, and enforce ERC/netlist/component/net gates.
- Added preliminary PB-100 KiCad child-sheet capture content that passes ERC and
  netlist export while keeping PCB layout blocked until schematic freeze.
- Added a PB-100 board-release blocker register so every conditional schematic
  freeze gate explicitly blocks PCB layout until its close evidence is complete.
- Added candidate LM5164-Q1 logic-power values for schematic review while
  keeping them not final before freeze.
- Added candidate PB-100 NTC divider values for schematic review while keeping
  thermal placement and calibration open.
- Added candidate PB-100 total-current telemetry values for schematic review
  while keeping shunt copper, bus ownership, and calibration open.
- Added candidate PB-100 CAN1 TX-disable hardware values while keeping vehicle
  CAN TX DNP/open and future-ADR gated.
- Added a PB-100/LB-100 B2B resource precheck for STM32H563 pin-binding review
  without freezing exact MCU pins.
- Aligned firmware rule action grammar across the JSON Schema, repository
  validator, and host-tested parser for supported roles and canonical 0..100
  PWM values.
- Hardened multi-action rule-set compilation so invalid action text is rejected
  before compiled rule entries are written.
- Hardened System Safety runtime current-budget enforcement so stale or invalid
  total-current telemetry disables active outputs.
