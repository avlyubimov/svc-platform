# PB-100 Schematic Freeze Checklist

Status: Open

This checklist is the gate between PB-100 schematic planning and PCB layout. It
does not authorize KiCad PCB layout work.

## Completion rule

PB-100 schematic freeze is allowed only when every required gate is `Closed`.
Any change to PB-100 output count, protection model, role-mapping model,
board-level current budget, or CAN1 safety behavior requires a new ADR before
this checklist can close.

## Status values

- `Closed`: Evidence exists and no schematic blocker remains.
- `Conditional`: Direction is accepted, but schematic-level evidence is still
  required.
- `Open`: Work is not complete.
- `Blocked`: A known conflict must be resolved before schematic freeze.

## Required gates

| Gate | Status | Evidence | Close condition |
|---|---|---|---|
| Architecture baseline | Closed | `docs/architecture/Architecture-Review-v1.0.md`, `docs/adr/ADR-0009-architecture-v1-freeze.md` | Architecture remains frozen and no PB-100 requirement change is pending |
| PB-100 requirements | Closed | `docs/requirements/pb-100-requirements.md`, `docs/adr/ADR-0006-pb-100-baseline-requirements.md` | Requirements changes are handled only through ADR |
| Generic output model | Closed | `docs/adr/ADR-0004-generic-outputs-role-mapping.md`, `hardware/power-board/PB-100/PB-100-output-channel-matrix.csv` | Schematic nets and silkscreen use only neutral `OUT1` through `OUT10` identifiers |
| CAN1 safety policy | Conditional | `docs/adr/ADR-0002-can-read-only-default.md`, `docs/can/can-safety.md`, `hardware/power-board/PB-100/PB-100-can1-tx-disable.md` | Schematic implements DNP/open TX path, default disable state, and LB-100-visible disabled status |
| Board current budget | Conditional | `docs/adr/ADR-0008-pb-100-current-budget.md` | Input measurement, connector ratings, copper/thermal assumptions, and firmware-visible budget enforcement are all represented in schematic inputs |
| Board-to-board interface | Conditional | `hardware/power-board/PB-100/PB-100-b2b-pin-budget.csv`, `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv` | Connector MPN and LB-100 MCU resource binding are reviewed against the pin map |
| High/medium output stage | Conditional | `docs/adr/ADR-0010-pb-100-power-path-candidate-strategy.md`, `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`, `hardware/power-board/PB-100/PB-100-out2-soa.md` | Controller, MOSFET, sense path, fuse, and inductive-load protection are validated per output class |
| Low-current output stage | Conditional | `docs/adr/ADR-0011-pb-100-low-current-output-stage.md`, `hardware/power-board/PB-100/PB-100-preliminary-validation.md` | OUT5/OUT8/OUT9 external-controller implementation is validated without a direct 40 V smart-switch rail |
| Input reverse protection | Conditional | `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`, `hardware/power-board/PB-100/PB-100-thermal-estimates.csv` | Selected input MOSFET package and copper strategy pass 40 A thermal and SOA review |
| TVS/load-dump protection | Conditional | `hardware/power-board/PB-100/PB-100-protection-validation.csv` | Clamp strategy is compatible with every downstream absolute maximum rating |
| Logic power rails | Open | `hardware/power-board/PB-100/PB-100-power-path-candidates.csv` | Buck and post-regulator strategy covers cold crank, load dump, telemetry, and LB-100 supply requirements |
| Current telemetry | Open | `docs/requirements/pb-100-requirements.md` | Per-output current and total input current measurement ranges are selected and mapped to LB-100 |
| Thermal telemetry | Open | `docs/requirements/pb-100-requirements.md` | PCB and power-zone temperature sensing strategy is selected and mapped to LB-100 |
| Factory assembly readiness | Conditional | `docs/production/component-family-shortlist.md`, `production/bom/factory_bom_draft.csv` | Critical components have at least two alternatives and assembly-source status is checked |
| Garage assembly readiness | Conditional | `production/bom/garage_bom_draft.csv` | User-installed items are limited to connectors, fuses, enclosure hardware, and wiring |
| Bench validation plan | Closed | `docs/testing/test-plan.md` | PB-100 bring-up, protection, thermal, current-budget, and CAN1 listen-only tests are explicitly listed |

## Active blockers

No active planning blockers remain. Conditional gates still require schematic
evidence before freeze.

## Resolved blockers

| ID | Resolution | Evidence |
|---|---|---|
| PB-FRZ-001 | OUT5/OUT8/OUT9 moved to external controller plus MOSFET Rev.1 baseline | `docs/adr/ADR-0011-pb-100-low-current-output-stage.md` |
| PB-FRZ-002 | OUT2 startup/inrush SOA envelope and escape strategy defined | `hardware/power-board/PB-100/PB-100-out2-soa.md` |
| PB-FRZ-003 | Dedicated low-Rds input MOSFET strategy selected for 40 A reverse protection | `hardware/power-board/PB-100/PB-100-input-reverse-protection.md` |
| PB-FRZ-004 | `JPB1` board-to-board schematic-planning pin map created | `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv` |
| PB-FRZ-005 | CAN1 TX-disable schematic input created with DNP/open TX default and status readback | `hardware/power-board/PB-100/PB-100-can1-tx-disable.md` |

## Review packet for freeze

Before marking this checklist `Closed`, the review packet must include:

- Updated schematic package.
- Final output channel matrix.
- Final power-path candidate table with selected and alternate MPNs.
- Thermal and protection validation tables.
- Final PB-100 to LB-100 pin map.
- CAN1 TX-disable schematic input and verification notes.
- Factory and garage BOM drafts synchronized with selected MPNs.
- Bench validation plan for protection, telemetry, current budget, and CAN1
  listen-only behavior.
