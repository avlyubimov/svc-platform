# ADR-0009: Freeze SVC architecture v1.0

## Status
Accepted

## Context
Architecture Review v1.0 reached freeze candidate status after the core safety,
manufacturing, output-mapping, component-family, high-side switching, and
current-budget decisions were accepted.

The project owner approved continuing implementation on 2026-06-30.

## Decision
Freeze SVC architecture v1.0 as the baseline for PB-100 schematic planning,
LB-100 firmware architecture, and production planning.

The frozen baseline includes:
- Three-board architecture: PB-100, LB-100, FB-100.
- Read-only vehicle CAN by default.
- Generic output channels with configuration-based role mapping.
- PB-100 high-side output switching.
- PB-100 board-level current budget.
- Factory SMD assembly with separate garage BOM.
- Initial component-family shortlist with alternatives.

## Consequences
PB-100 schematic planning may begin.

Power Board requirement changes still require an ADR. KiCad PCB layout remains a
separate implementation step and must not start until schematic requirements,
pin budget, and component families are reviewed.
