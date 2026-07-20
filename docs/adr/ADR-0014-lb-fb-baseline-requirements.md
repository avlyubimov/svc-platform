# ADR-0014: Freeze LB-100 and FB-100 baseline requirements for schematic planning

## Status
Accepted

## Context
SVC is a three-board platform: PB-100, LB-100, and FB-100. PB-100 now has a
schematic-planning package and board-release gates, but LB-100 and FB-100 only
had requirements notes. A JLCPCB/PCBWay order for the product cannot be treated
as ready while the logic and front boards have no explicit freeze gates.

## Decision
Freeze the Rev.1 baseline requirements for LB-100 and FB-100 so schematic
planning and non-layout KiCad scaffolding may proceed.

LB-100 Rev.1 baseline:

- STM32H563 LQFP-100 remains the default target from ADR-0005.
- STM32H573 remains an accepted alternative when security requirements justify
  cost and sourcing risk.
- PB-100 provides a protected `PB_5V_OUT` allocation of 500 mA sustained unless
  LB-100 schematic review proves a higher-current requirement.
- CAN1 vehicle access remains read-only by default and cannot be enabled by
  configuration or firmware alone.
- LB-100 owns firmware execution, CAN/LIN/RS485/UART interfaces, USB service
  path, BLE, microSD, RTC, FRAM, IMU, lux sensing, and external inputs.
- Sleep, deep-sleep, wake, and back-power behavior must satisfy ADR-0012 before
  vehicle installation.

FB-100 Rev.1 baseline:

- FB-100 is the service and local UI board.
- It carries USB-C service access, RGB/status indication, channel indication,
  SERVICE/RESET button behavior, and an optional OLED footprint.
- FB-100 must not encode vehicle accessory roles; indicators map to logical
  status/channel signals.
- FB-100 must not back-power LB-100 or PB-100 through USB, signal lines, or
  button/LED circuitry without an explicit reviewed power path.

This ADR does not change PB-100 requirements and does not authorize PCB layout,
Gerbers, drill files, pick-place files, BOM/CPL order packages, or PCBA orders.

## Consequences
LB-100 and FB-100 must gain their own schematic-freeze checklists, blocker
registers, and release manifests before any board-order package is considered.

The project-level board-order gate must report all three boards. A three-board
JLCPCB/PCBWay order remains NO-GO until PB-100, LB-100, and FB-100 each have
closed schematic freeze, reviewed KiCad schematic/layout files, fabrication
outputs, and assembly/order evidence.
