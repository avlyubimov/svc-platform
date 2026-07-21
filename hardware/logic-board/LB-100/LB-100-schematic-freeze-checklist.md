# LB-100 Schematic Freeze Checklist

Status: Closed

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
| PB-100 interface | Closed | `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`, `hardware/power-board/PB-100/PB-100-fx18-paired-stack-closeout.md`, `hardware/power-board/PB-100/PB-100-fx18-mf-contact-ownership-precheck.csv`, `hardware/logic-board/LB-100/LB-100-stm32h563-pin-binding-precheck.csv` | Exact JPB1 ownership, corrected 20 mm FX18 pair, 20.3 +/-0.127 mm four-spacer retention, six official plated lands, four GND MF circuits, fixture, and inspection plan are reviewed; physical PB-BENCH-014/015 remain post-prototype per ADR-0013 |
| CAN and expansion safety | Closed | `docs/adr/ADR-0002-can-read-only-default.md`, `docs/adr/ADR-0015-can1-physical-layer-board-ownership.md`, `docs/can/can-safety.md`, `hardware/logic-board/LB-100/LB-100-communication-safety-precheck.csv`, `hardware/logic-board/LB-100/LB-100-component-sourcing-precheck.csv` | ADR-0015 Accepted assigns CAN1 physical-layer ownership to PB-100; LB-100 retains STM32 FDCAN and read-only firmware policy while CAN2/LIN/RS485/UART resources remain separate |
| Service, storage, and sensors | Closed | `hardware/logic-board/LB-100/LB-100-requirements.md`, `hardware/logic-board/LB-100/LB-100-service-storage-sensor-precheck.csv`, `hardware/logic-board/LB-100/LB-100-component-sourcing-precheck.csv`, `hardware/logic-board/LB-100/LB-100-fb-powered-off-corrective-review-2026-07-21.md` | USB-C service path, BLE, microSD, RTC, FRAM, IMU, lux sensor, ESD, and powered-off isolation are selected; E73 UART/reset remain below VDD + 0.3 V when RADIO_SENSOR_3V3 is off |
| Factory assembly readiness | Closed | `docs/production/component-family-shortlist.md`, `hardware/logic-board/LB-100/LB-100-mcu-sourcing-precheck.csv`, `hardware/logic-board/LB-100/LB-100-component-sourcing-precheck.csv` | Critical LB-100 components have preferred parts, alternatives where critical, and current JLCPCB/PCBWay sourcing review |
| KiCad schematic review | Closed | `hardware/logic-board/LB-100/kicad/LB-100.kicad_sch`, `hardware/logic-board/LB-100/kicad/lib/LB100.kicad_sym`, `hardware/logic-board/LB-100/LB-100-schematic-review-closeout.md`, `tools/validate_board_schematics.py` | Deterministic value-bearing capture exports 81 components and 191 electrical nets; exact E73 powered-off isolation and all prior topology typed IC pins and symbol/footprint pads pass; ERC has no errors and only the reviewed cross-board USB_CC1/USB_CC2 isolated-label warnings |

## Release Boundary

`LB-100-board-release-blocker-register.csv` has zero active LBREL blockers.
Schematic freeze and
mechanical pre-layout evidence are closed, but KiCad board import still waits
for the separate CAN/USB/SD/clock/BLE signal-integrity and safety layout model.
No `.kicad_pcb`, Gerber, drill, placement, or manufacturing package is created
or approved by this freeze.
