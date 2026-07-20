# LB-100 Schematic Freeze Checklist

Status: Open

This checklist closes LB-100 schematic planning for PCB-layout start. It does
not authorize Gerbers, drills, pick-place, BOM/CPL order packages, manufacturing
ZIP files, fabrication packages, or PCBA orders.

## Completion Rule

LB-100 schematic freeze is allowed only when every required gate is `Closed`.
Changes to the MCU family, CAN1 read-only policy, PB-100 board-to-board
contract, sleep/wake current budget, or service-power model require an ADR
before this checklist can close.

## Required Gates

| Gate | Status | Evidence | Close condition |
|---|---|---|---|
| Architecture baseline | Closed | `docs/architecture/Architecture-Review-v1.0.md`, `docs/adr/ADR-0009-architecture-v1-freeze.md` | Three-board architecture remains frozen |
| LB-100 requirements | Closed | `hardware/logic-board/LB-100/LB-100-requirements.md`, `docs/adr/ADR-0014-lb-fb-baseline-requirements.md` | Rev.1 LB-100 baseline remains unchanged |
| MCU and pin binding | Closed | `docs/adr/ADR-0005-stm32h5-product-target.md`, `hardware/logic-board/LB-100/LB-100-jpb1-resource-budget.csv`, `hardware/logic-board/LB-100/LB-100-stm32h563-pin-binding-precheck.csv`, `hardware/logic-board/LB-100/LB-100-mcu-sourcing-precheck.csv` | STM32H563 LQFP-100 pinout, clocks, reset, boot, SWD, supply pins, USB pins, and alternates are reviewed |
| Power tree and sleep budget | Closed | `hardware/logic-board/LB-100/LB-100-power-budget-precheck.md`, `hardware/logic-board/LB-100/LB-100-rail-tree-precheck.csv`, `hardware/logic-board/LB-100/LB-100-rail-budget-closeout-precheck.csv`, `docs/adr/ADR-0012-system-sleep-wake-and-parking-current.md` | Active, sleep, deep-sleep, wake, USB, and back-power states fit the `PB_5V_OUT` contract |
| PB-100 interface | Conditional | `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-resource-binding.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`, `hardware/logic-board/LB-100/LB-100-jpb1-resource-budget.csv`, `hardware/logic-board/LB-100/LB-100-stm32h563-pin-binding-precheck.csv` | Exact JPB1 signal ownership and six official plated FX18 lands with four GND MF circuits are captured; physical 20 mm stack tolerance, vibration retention, assembly fixture, and mating review remain open |
| CAN and expansion safety | Closed | `docs/adr/ADR-0002-can-read-only-default.md`, `docs/adr/ADR-0015-can1-physical-layer-board-ownership.md`, `docs/can/can-safety.md`, `hardware/logic-board/LB-100/LB-100-communication-safety-precheck.csv`, `hardware/logic-board/LB-100/LB-100-component-sourcing-precheck.csv` | ADR-0015 Accepted assigns CAN1 physical-layer ownership to PB-100; LB-100 retains STM32 FDCAN and read-only firmware policy while CAN2/LIN/RS485/UART resources remain separate |
| Service, storage, and sensors | Closed | `hardware/logic-board/LB-100/LB-100-requirements.md`, `hardware/logic-board/LB-100/LB-100-service-storage-sensor-precheck.csv`, `hardware/logic-board/LB-100/LB-100-component-sourcing-precheck.csv` | USB-C service path, BLE, microSD, RTC, FRAM, IMU, lux sensor, ESD, and power isolation are selected |
| Factory assembly readiness | Closed | `docs/production/component-family-shortlist.md`, `hardware/logic-board/LB-100/LB-100-mcu-sourcing-precheck.csv`, `hardware/logic-board/LB-100/LB-100-component-sourcing-precheck.csv` | Critical LB-100 components have preferred parts, alternatives where critical, and current JLCPCB/PCBWay sourcing review |
| KiCad schematic review | Conditional | `hardware/logic-board/LB-100/kicad/LB-100.kicad_sch`, `hardware/logic-board/LB-100/kicad/LB-100.kicad_pro`, `hardware/logic-board/LB-100/LB-100-schematic-review-closeout.md` | Replace the text scaffold with reviewed component symbols values nets footprint properties and ERC evidence |

## Active Blockers

LB-100 release blockers remain active in
`hardware/logic-board/LB-100/LB-100-board-release-blocker-register.csv`: the
current KiCad file is a text scaffold with no component instances. The two
active blockers are `LBREL-003` for physical FX18 paired-stack validation and
`LBREL-007` for reviewed value-bearing schematic capture. ADR-0015 Accepted
assigns the CAN1 physical layer to PB-100, and both FX18 footprints already
contain six official plated lands with four GND MF circuits. PCB layout and
manufacturing output remain blocked until the two active blockers close.
