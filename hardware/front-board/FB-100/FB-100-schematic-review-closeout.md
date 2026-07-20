# FB-100 Schematic Review Closeout

Status: Retracted; schematic freeze is Open
Review date: 2026-07-20

This former closeout no longer freezes the FB-100 Rev.1 schematic inputs. The
current KiCad sheet is a text scaffold without component symbols. It
does not create or approve KiCad PCB layout, Gerbers, drills, pick-place files,
BOM/CPL order packages, manufacturing ZIP files, fabrication packages, or PCBA
orders.

## Reviewed Schematic Content

- Interface: 24-pin `JFB1` cable pinout is closed with USB service, status RGB,
  OUT1..OUT10 channel indicators, SERVICE/RESET buttons, optional OLED, and
  power/reference pins.
- USB service: USB-C device-only service path uses CC Rd behavior, ESD
  protection, shield/return policy, and VBUS sense-only no-back-power boundary.
- UI: RGB status LED, role-free channel LEDs, SERVICE/RESET controls, and
  optional OLED DNP footprint are captured without accessory role names.
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

## Remaining Non-Freeze Work

- PCB placement, routing, USB connector mechanical alignment, button/LED
  placement, fabrication outputs, assembly outputs, and JLCPCB/PCBWay order
  files are separate post-freeze work.
- Exact passives and footprints must stay synchronized with the reviewed
  schematic evidence during layout preparation.
- Any change to service connector power model, UI signal ownership, or
  mechanical interface requires ADR review.
