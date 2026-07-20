# Three-Board PCB Layout Rules Baseline

Status: Active
Evidence date: 2026-07-20

This baseline starts controlled PCB-layout preparation for PB-100, LB-100, and
FB-100 after schematic freeze. It does not create KiCad PCB layout files,
Gerbers, drills, pick-place files, BOM/CPL order packages, manufacturing ZIP
files, fabrication packages, or PCBA orders.

## Source Evidence

- JLCPCB PCB capabilities:
  `https://jlcpcb.com/capabilities/pcb-capabilities`.
- JLCPCB PCB assembly capabilities:
  `https://jlcpcb.com/capabilities/pcb-assembly-capabilities`.
- JLCPCB panelization and edge-clearance guidance:
  `https://jlcpcb.com/blog/pcb-panelization`.
- PCBWay manufacturing tolerances:
  `https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html`.
- PCBWay panel requirements for assembly:
  `https://www.pcbway.com/pcb_prototype/Panel_Requirements_for_Assembly.html`.

## Conservative DRC Floor

- Default signal trace/space floor: `0.15 mm / 0.15 mm` or larger.
- Default non-BGA via floor: `0.30 mm` finished hole with `0.60 mm` pad or
  larger.
- Do not use vendor minimums as normal design values. Smaller geometry requires
  a board-specific DFM note, vendor-source evidence, and layout review approval.
- For 2 oz or heavier copper, use the applicable vendor heavy-copper
  trace/space floor and keep power-path geometry above the minimum whenever
  routing space allows.
- PB-100 high-current paths must be polygons, planes, or buses sized by
  current, temperature rise, fuse coordination, connector derating, and return
  path review. The signal DRC floor is never sufficient evidence for PB-100
  power copper.

## Assembly Baseline

- Prefer `0603` and larger passive packages for serviceability. `0402` is
  allowed only for factory-owned dense sections with sourcing and inspection
  review.
- Avoid packages smaller than `0402` in Rev.1 unless a specific footprint,
  assembly-source, inspection, and rework review is closed.
- Add global fiducials for each assembled board; add local fiducials around
  fine-pitch connectors, USB-C, dense MCU regions, and any BGA/QFN escape if
  such packages are introduced by approved requirements.
- Keep polarity, pin-1, DNP/open, and variant-population markings reviewable in
  schematic, BOM, silkscreen notes, and assembly drawings before order release.

## Mechanical And Panel Baseline

- Board outline, mounting holes, connector edge positions, cable exits, and
  enclosure keepouts must close before routing review.
- Keep stress-sensitive or tall components at least `2.0 mm` from scored or
  routed separation edges unless a board-specific mechanical review approves a
  smaller clearance.
- Keep ordinary components at least `1.0 mm` from V-score edges and at least
  `0.5 mm` from tab-routed edges unless vendor DFM review approves otherwise.
- Panelization is not a repo-generated release artifact at layout start. Final
  panel method, rails, tooling holes, fiducials, and breakaway strategy close
  during manufacturing-package review.

## Board-Specific Layout Boundaries

- PB-100: place input protection, high-current outputs, fuses, connectors,
  shunts, thermal sensors, and JPB1 only after footprint binding and mechanical
  envelope gates close. High-current copper requires a separate thermal/current
  review before board-print release.
- LB-100: place STM32H563VITx, JPB1, CAN, service/storage, BLE, sensors, and
  power rails only after footprint binding and PB/LB mezzanine stack review
  close. CAN1 remains read-only by default and `CAN1_TX_ROUTE` stays DNP/open.
- FB-100: place USB-C, ESD protection, service buttons, channel LEDs, status
  LEDs, and JFB1 only after USB-C edge, no-back-power, panel/mechanical, and
  service-access gates close.

## Output Boundary

The next allowed work is footprint binding, mechanical envelope closure, and
controlled KiCad board creation for layout review. Manufacturing outputs remain blocked
until every board has reviewed PCB layout, DRC/ERC/DFM evidence, assembly-source
review, fabrication outputs, assembly outputs, and Product Owner approval.
