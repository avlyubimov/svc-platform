# FB-100 Schematic Review Closeout

Status: Closed for schematic freeze
Review date: 2026-07-21

This closeout freezes the FB-100 Rev.1 value-bearing schematic inputs. The
deterministic KiCad sheet contains 44 component instances, 46 exported nets,
project-local symbols, and non-empty project-local Footprint properties. It does
not create or approve KiCad PCB layout or manufacturing outputs.

## Reviewed Schematic Content

- Interface: 24-pin `JFB1` cable pinout is closed with USB service, status RGB,
  OUT1..OUT10 channel indicators, SERVICE/RESET buttons, optional OLED, and
  power/reference pins.
- USB service: USB-C device-only service path uses CC Rd behavior, ESD,
  shield/return policy, and R13 3.9 kOhm / R14 15 kOhm / C1 100 nF
  `USB_VBUS_DETECT_RAW` to the LB 5 V-tolerant digital detector with a defined
  disconnected low state and no power injection.
- UI: direct STM32-driven LTC3212 one-wire driver and common-anode RGB status LED, ten role-free
  1 kOhm channel LED paths, SERVICE/RESET controls, and optional OLED module
  header DNP are captured without accessory role names.
- Mechanical: prototype envelope, mounting, USB access, LED/button alignment,
  OLED keep-out, service sealing, and enclosure boundary are reviewed.
- Assembly: factory/garage component sourcing is date-stamped with alternates
  for USB-C connector, USB ESD, LEDs, FFC/FPC, buttons, OLED DNP, and passives.

## Evidence

- `FB-100-schematic-freeze-checklist.md`
- `FB-100-board-release-blocker-register.csv`
- `FB-100-interface-signal-plan.csv`
- `FB-100-interface-pinout-closeout.csv`
- `FB-100-usb-service-closeout-precheck.csv`
- `FB-100-ui-control-closeout-precheck.csv`
- `FB-100-ui-mechanical-precheck.csv`
- `FB-100-mechanical-envelope-precheck.csv`
- `FB-100-component-sourcing-precheck.csv`
- `hardware/front-board/FB-100/kicad/FB-100.kicad_sch`
- `FB-100-component-decision-record.md`
- `hardware/logic-board/LB-100/LB-100-fb-powered-off-corrective-review-2026-07-21.md`
- `tools/validate_board_schematics.py`

## Validation Result

- KiCad XML netlist export: 44 components, 46 nets.
- ERC: zero findings.
- Topology: USB-C device role, two CC Rd resistors, flow-through ESD, VBUS
  defined-low VBUS presence network, no-back-power boundary, channel LEDs, one-wire RGB,
  buttons, DNP OLED, every footprint file, and every symbol-to-pad set pass the
  focused validator.

## Remaining Non-Freeze Work

- PCB placement, routing, USB connector mechanical alignment, button/LED
  placement, fabrication outputs, assembly outputs, and JLCPCB/PCBWay order
  files are separate post-freeze work.
- Exact values and footprints are now generator- and validator-locked; changes
  require regenerating the sheets and passing the exported-netlist audit.
- Any change to service connector power model, UI signal ownership, or
  mechanical interface requires ADR review.
