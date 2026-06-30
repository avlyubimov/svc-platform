# ADR-0008: PB-100 uses a board-level current budget

## Status
Accepted

## Context
PB-100 exposes 10 generic outputs. The reference fuse ratings add up to 100 A
and the reference current limits add up to 82 A, but the garage BOM currently
targets a 50 A main fuse near the battery.

This is normal for a configurable power distribution board: not every possible
accessory role is expected to run at maximum current at the same time.

## Decision
PB-100 output channels are intentionally over-subscribed relative to the main
input fuse and board continuous-current budget.

The system must enforce:
- Per-channel fuse and current limits.
- Board-level total current budget.
- Configurable load priorities.
- Load shedding or startup refusal when the configured budget would be exceeded.

Rev.1 schematic planning uses these initial targets:
- Main harness fuse target: 50 A.
- Board continuous-current design target: at least 40 A after thermal validation.
- Default firmware/configuration total-current limit: 40 A.

## Consequences
PB-100 can support many accessory roles without being sized for every channel at
maximum current simultaneously.

Firmware, configuration, and test plans must treat total-current enforcement as
a safety feature. Thermal validation and connector selection must confirm or
revise the 40 A continuous target before schematic freeze.
