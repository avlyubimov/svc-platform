# ADR-0001: Use three-board architecture

## Status
Accepted

## Context
The device must live for many years. The power stage should not be redesigned when MCU, connectivity, or UI changes.

## Decision
Use three boards:
- PB-100 Power Board
- LB-100 Logic Board
- FB-100 Front Panel Board

## Consequences
Power Board can remain stable while Logic Board evolves.
