# PB-100 Power Board Requirements

Status: Synced with architecture baseline

## Purpose

Long-lifecycle high-current board.

Canonical requirements are maintained in
`docs/requirements/pb-100-requirements.md`.

## Outputs

10 generic outputs with:
- fuse
- high-side electronic switching
- PWM support where applicable
- current measurement
- fault detection
- thermal protection
- role mapping by configuration
- board-level current budget enforcement

## Current budget

- Main harness fuse target: 50 A
- Board continuous-current target: at least 40 A after thermal validation
- Default configuration total-current limit: 40 A

## Must not change often

This board is intended to remain compatible across future Logic Board revisions.

## Implementation package

Schematic planning starts in `hardware/power-board/PB-100/PB-100-schematic-package.md`.
The initial logical board-to-board pin budget is
`hardware/power-board/PB-100/PB-100-b2b-pin-budget.csv`.
The schematic-planning board-to-board pin map is
`hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`.
Schematic freeze is tracked in
`hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md`.
