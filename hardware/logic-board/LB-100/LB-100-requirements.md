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

## Safety boundaries

- CAN1 vehicle interface is read-only by default.
- CAN1 TX must not be enabled in firmware unless a future ADR changes policy.
- Output control must go through Output Manager and role mapping.
- Board-level current budget enforcement is a firmware safety requirement.
