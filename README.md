# SVC Platform — Smart Vehicle Controller

SVC is an open modular embedded platform for controlling auxiliary equipment on motorcycles and other vehicles.

Reference Vehicle #001: **BMW R1200GS K25 2007**  
VIN: **WB10307A97ZU65028**

## Mission

SVC is an open modular platform for vehicle accessory control. It should allow new functionality to be added primarily through configuration, plugins, firmware updates, or Logic Board replacement without redesigning the Power Board.

## Current status

Architecture v1.0 is frozen. PB-100 schematic planning is ready for schematic
review, with KiCad schematic scaffold started. Firmware MVP has host-tested
safety, configuration, role-mapping, rule-runner, CAN safety, and PWM ownership
services in progress.

Do not start PCB layout until the PB-100 schematic freeze checklist is closed.
Repository validation blocks PB-100 layout/manufacturing artifacts before that
freeze.

Final readiness gates are tracked in `docs/product/final-readiness.md`.

## Validation

```bash
make check
```

This runs PB-100 artifact validation, KiCad schematic ERC when `kicad-cli` is
available, firmware config JSON validation, and firmware host tests. The same
command runs in GitHub Actions on push and pull request.

Current host checks cover PB-100 schematic-planning artifacts, config/schema
consistency, output safety, battery cutoff, CAN1 TX denial, event dispatch,
role-based rules, and PWM duty-cycle ownership.

## Repository structure

```text
docs/                 Architecture, ADR, requirements, production docs
hardware/             KiCad and mechanical files
firmware/             Embedded firmware, bootloader, plugins
software/             SVC Studio and SVC Mobile
can-db/               Vehicle CAN databases
production/           BOM, Gerber, Pick&Place, assembly docs
```

## Board naming

- **PB-100** — Power Board, intended to remain stable for 10–15 years.
- **LB-100** — Logic Board, replaceable/upgradeable.
- **FB-100** — Front Panel Board, service interface and indicators.

## Hard rule

**Power Board is sacred.**  
New features should not require Power Board redesign unless all configuration/plugin/firmware/Logic Board options are exhausted.
