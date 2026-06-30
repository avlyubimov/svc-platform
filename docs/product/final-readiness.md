# Final Readiness

Status: In progress  
Last updated: 2026-06-30

This document defines what “ready” means for the current repository state. It
does not authorize PB-100 PCB layout.

## Automated gate

Run from the repository root:

```bash
make check
```

Current coverage:

- PB-100 CSV and KiCad scaffold validation.
- Optional PB-100 KiCad schematic ERC and netlist export when `kicad-cli` is
  installed.
- PB-100 KiCad role-token guard for generic `OUT1`..`OUT10` naming.
- PB-100 layout/manufacturing artifact blocker.
- Firmware config JSON/schema validation.
- Firmware host-test suite.

## Current readiness

| Area | Status | Notes |
|---|---|---|
| Architecture v1.0 | Ready | Frozen by ADR; PB-100 requirement changes still need ADR |
| PB-100 requirements | Ready for schematic planning | Baseline is frozen; schematic freeze remains open |
| PB-100 KiCad scaffold | Review-ready scaffold | Schematic ERC and netlist export pass locally with KiCad 10.0.4 |
| PB-100 PCB/layout | Blocked | Layout, Gerber, drill, placement, and manufacturing zips are blocked |
| Firmware safety core | Host-test ready | Output, battery, thermal, CAN, telemetry, events, logging, config, and rule paths covered |
| Configuration format | Host-test ready | JSON schema and example are validated against firmware defaults |
| Production package | Draft | BOMs and component families need final sourcing and schematic evidence |

## Required before schematic freeze

- Replace abstract KiCad block symbols with final schematic symbols.
- Select final critical MPNs and at least two alternatives for each critical
  component family.
- Recheck JLCPCB/PCBWay assembly availability and package suitability.
- Close PB-100 CAN1 TX-disable schematic evidence.
- Close current and thermal telemetry scaling, filtering, and calibration notes.
- Close OUT2 SOA extraction and input reverse-protection thermal review.
- Synchronize factory and garage BOM drafts with final selections.
- Run `make check` with local `kicad-cli` available, zero ERC violations, and a
  successful KiCad S-expression netlist export.

## Required before PCB layout

- `hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md` status
  changed to closed with evidence for every conditional gate.
- No open ADR requirement change touching PB-100 output count, protection model,
  role mapping, current budget, or CAN1 safety behavior.
- Final schematic review packet archived in the repository.

## Required before prototype bring-up

- PB-100 layout, fabrication outputs, assembly outputs, and inspection files.
- Bench test procedure for first power, current telemetry, thermal telemetry,
  short-circuit handling, CAN1 listen-only behavior, and output load tests.
- Firmware hardware-abstraction layer for the selected LB-100 MCU and PB-100
  telemetry paths.
- Reference vehicle harness and connector assembly notes.

## No-go conditions

- Any `PB-100.kicad_pcb` or manufacturing output before schematic freeze.
- Any vehicle CAN1 TX enable path without a new ADR and explicit hardware action.
- Any hard-coded accessory role to physical output mapping in hardware or
  firmware.
- Any firmware path that bypasses Output Manager for physical output state.
