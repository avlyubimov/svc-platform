# LB-100 Logic Board Requirements

## Purpose

Replaceable computing and communication board.

## Target product MCU

STM32H563/H573 class.

Default Rev.1 target: STM32H563 LQFP-100.

Accepted alternative: STM32H573 when stronger cryptography/security
requirements justify cost and availability risk.

## Prototype MCU

STM32F407/F429 acceptable for early firmware prototyping.

## Interfaces

- CAN1 vehicle read-only
- CAN2 expansion
- BLE
- USB-C service
- microSD
- RTC
- FRAM
- IMU
- Lux sensor
- LIN footprint
- RS485 footprint
- external inputs

## Power budget precheck

- LB-100 Rev.1 schematic review must budget its `PB_5V_OUT` load before PB-100
  schematic freeze.
- Initial LB-100 allocation from PB-100 is 500 mA sustained.
- If LB-100 needs more than 500 mA sustained from `PB_5V_OUT`, PB-100 must keep
  the LM5013-Q1-class higher-current 100 V buck fallback active before schematic
  freeze.
- `LB_3V3_IO` is a PB-side logic reference and pull-up domain, not an accessory
  supply.
- Sleep and deep-sleep current evidence must satisfy ADR-0012 before vehicle
  installation.

Detailed precheck: `hardware/logic-board/LB-100/LB-100-power-budget-precheck.md`.

## Safety boundaries

- CAN1 vehicle interface is read-only by default.
- CAN1 TX must not be enabled in firmware unless a future ADR changes policy.
- Output control must go through Output Manager and role mapping.
- Board-level current budget enforcement is a firmware safety requirement.
