# ADR-0005: STM32H5 target for product Logic Board

## Status
Proposed

## Context
STM32F407 is usable for prototypes, but the platform should have long-term headroom.

## Decision
Target STM32H563/H573 class MCU for LB-100 product board. STM32F407 may be used for early prototypes.

## Consequences
More headroom, modern security, FDCAN, and longer lifecycle. Component availability must be verified before schematic freeze.
