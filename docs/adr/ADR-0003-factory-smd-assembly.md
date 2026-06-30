# ADR-0003: Factory SMD assembly

## Status
Accepted

## Context
The builder has only a soldering iron and no working rework station. Fine-pitch MCU and small SMD assembly should not be manual.

## Decision
All fine-pitch and small SMD parts are intended for factory assembly by JLCPCB/PCBWay.

## Consequences
BOM must be production-friendly. Garage assembly is limited to connectors, fuses, enclosure, wiring.
