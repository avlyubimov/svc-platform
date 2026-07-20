# LB-100 Schematic Review Closeout

Status: Retracted; schematic freeze is Open
Review date: 2026-07-20

This former closeout no longer freezes the LB-100 Rev.1 schematic inputs. The
current KiCad sheet has no component symbols. Both FX18 footprints contain
six official plated lands with four GND MF circuits, but physical paired-stack
validation remains open. ADR-0015 Accepted assigns the CAN1 physical layer to
PB-100 while LB-100 retains STM32 FDCAN and read-only firmware policy. It
does not create or approve KiCad PCB layout, Gerbers, drills, pick-place files,
BOM/CPL order packages, manufacturing ZIP files, fabrication packages, or PCBA
orders.

## Reviewed Schematic Content

- MCU: STM32H563VITx LQFP100 baseline from ADR-0005 with STM32H573VITx security
  alternate and STM32H563RGT6 downsized fallback only after resource reduction.
- JPB1: exact 100-pin PB-100/LB-100 binding from
  `LB-100-stm32h563-pin-binding-precheck.csv`.
- Power: `PB_5V_OUT` 500 mA sustained allocation, calculated LB-100 sustained
  load 219.2 mA, service peak 415.2 mA, and no-back-power USB boundary.
- CAN safety: ADR-0015 Accepted keeps the CAN1 transceiver, gate, protection,
  termination, CANH/CANL, and vehicle harness on PB-100; LB-100 owns only
  STM32 FDCAN, protocol, and read-only firmware policy. CAN2 remains the
  transmit-capable expansion bus.
- Services: USB service, BLE, microSD, RTC, FRAM, IMU, lux, LIN/RS485/UART DNP
  reserve, SWD, BOOT0, reset, and service-button resources are captured.
- Assembly: factory-owned MCU, regulators, transceivers, BLE, storage, sensors,
  USB-boundary parts, and DNP options have dated sourcing evidence.

## Evidence

- `LB-100-schematic-freeze-checklist.md`
- `LB-100-board-release-blocker-register.csv`
- `LB-100-stm32h563-pin-binding-precheck.csv`
- `LB-100-rail-budget-closeout-precheck.csv`
- `LB-100-communication-safety-precheck.csv`
- `LB-100-service-storage-sensor-precheck.csv`
- `LB-100-mcu-sourcing-precheck.csv`
- `LB-100-component-sourcing-precheck.csv`
- `hardware/logic-board/LB-100/kicad/LB-100.kicad_sch`

## Remaining Non-Freeze Work

- PCB placement, routing, stack-up, impedance, mounting, fabrication outputs,
  assembly outputs, and JLCPCB/PCBWay order files are separate post-freeze work.
- Exact passives and footprints must stay synchronized with the reviewed
  schematic evidence during layout preparation.
- Any change to MCU family, CAN1 read-only policy, PB-100 JPB1 contract,
  sleep/wake current budget, or service-power model requires ADR review.
