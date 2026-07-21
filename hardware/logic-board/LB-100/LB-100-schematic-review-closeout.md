# LB-100 Schematic Review Closeout

Status: Closed for schematic freeze
Review date: 2026-07-21

This closeout freezes the LB-100 Rev.1 value-bearing schematic inputs. The
deterministic KiCad sheet contains 81 component instances, 191 exported nets,
project-local symbols, and non-empty project-local Footprint properties.
ADR-0015 Accepted assigns the CAN1 physical layer to PB-100 while LB-100
retains STM32 FDCAN and read-only firmware policy. It does not create or approve
KiCad PCB layout or manufacturing outputs.

## Reviewed Schematic Content

- MCU: STM32H563VITx LQFP100 baseline from ADR-0005 with STM32H573VITx security
  alternate and STM32H563RGT6 downsized fallback only after resource reduction.
- JPB1: exact 100-pin PB-100/LB-100 binding plus four GND MF circuits;
  the corrected `FX18-100P-0.8SV10`/`FX18-100S-0.8SV10` pair and its
  six official plated lands close pre-layout mechanics.
- Power: `PB_5V_OUT` 500 mA sustained allocation, calculated LB-100 sustained
  plus FB-100 load 229.2 mA, service peak 381.2 mA, two TPS22918-Q1 switched
  domains, sourced/decoupled ADC_REF, one-point AGND return, and a no-back-power
  USB boundary through the 5 V-tolerant U14 digital detector with a defined
  FB-side pulldown.
- CAN safety: ADR-0015 Accepted keeps the CAN1 transceiver, gate, protection,
  termination, CANH/CANL, and vehicle harness on PB-100; LB-100 owns only
  STM32 FDCAN, protocol, and read-only firmware policy. CAN2 remains the
  transmit-capable expansion bus.
- Services: USB service, BLE, microSD, RTC, FRAM, back-power-safe IMU/lux
  supplies, U15-U17 switched-domain Ioff isolation on E73 UART/reset,
  TCA9539-Q1 slow UI expansion, direct STM32 PD7 LTC3212 control,
  LIN/RS485 DNP reserve, SWD, clocks, BOOT0, reset, and buttons are captured.
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
- `LB-100-component-decision-record.md`
- `LB-100-fb-electrical-corrective-review-2026-07-21.md`
- `LB-100-fb-powered-off-corrective-review-2026-07-21.md`
- `hardware/power-board/PB-100/PB-100-fx18-paired-stack-closeout.md`
- `tools/validate_board_schematics.py`

## Validation Result

- KiCad XML netlist export: 81 components, 191 nets.
- ERC: zero errors. The only findings are two reviewed isolated labels for
  `USB_CC1` and `USB_CC2`; those lines intentionally terminate on FB-100 rather
  than an LB component.
- Topology: CAN1 safety routes, JPB1 MF GND, STM32 USB/SWD, digital VBUS
  presence, ADC_REF/AGND, direct LTC3212 timing, back-power-safe sensor rails,
  E73 UART/reset powered-off isolation, JFB1 UI mapping, every footprint file,
  and every symbol-to-pad set pass.
- Electrical types: every reviewed IC has non-passive functional pin types and
  at least one `power_in`; the focused validator rejects an all-passive library.

## Remaining Non-Freeze Work

- PCB placement, routing, stack-up, impedance, mounting, fabrication outputs,
  assembly outputs, and JLCPCB/PCBWay order files are separate post-freeze work.
- Exact values and footprints are now generator- and validator-locked; changes
  require regenerating the sheets and passing the exported-netlist audit.
- Any change to MCU family, CAN1 read-only policy, PB-100 JPB1 contract,
  sleep/wake current budget, or service-power model requires ADR review.
