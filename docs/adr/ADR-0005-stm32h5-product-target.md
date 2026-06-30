# ADR-0005: STM32H5 target for product Logic Board

## Status
Accepted

## Context
STM32F407 is usable for prototypes, but the platform should have long-term headroom.
The product board needs native FDCAN, enough flash/RAM for FreeRTOS services,
logging, configuration handling, and security headroom for future signed update
flows.

## Decision
Target STM32H563/H573 class MCU for the LB-100 product board.

Default LB-100 target:
- STM32H563, LQFP-100 preferred for Rev.1 schematic planning.

Accepted alternatives:
- STM32H573, LQFP-100 or larger LQFP, when stronger cryptography/security
  requirements justify cost and availability risk.
- STM32F407 may be used only for early firmware prototypes and bench work.

BGA packages are not preferred for Rev.1 unless a later ADR accepts the
manufacturing and inspection tradeoff.

## Consequences
LB-100 firmware can be designed around STM32H5 features while early prototype
work can still use STM32F407 boards. Component availability must be rechecked
before schematic freeze and before each PCBA order.
