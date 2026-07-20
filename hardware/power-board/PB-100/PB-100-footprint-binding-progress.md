# PB-100 Footprint Binding Progress

Status: Partial
Review date: 2026-07-20

This progress note binds the PB-100 footprints that have project-local KiCad
footprint evidence. It does not create `PB-100.kicad_pcb`, Gerbers, drill
files, pick-place files, BOM/CPL order packages, manufacturing ZIP files,
fabrication packages, panel outputs, or PCBA orders.

## Closed In This Increment

- TPS48110 high-side controller: `PB100:VSSOP-20_19P-L5.0-W3.0-P0.50-LS5.0-BL_PE16`.
- SIDR626LDP default output MOSFET: `PB100:POWERPAK-SO-8_L6.1-W5.1-P1.27-BL-EP`.
- LM74700 reverse-protection controller: `PB100:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL`.
- LM5164 logic buck: `PB100:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL-EP2.9`.
- INA228-class input-current monitor: `PB100:VSSOP-10_L3.0-W3.0-P0.50-LS4.9-BL`.
- TDK-class 0402 thermal NTCs: `PB100:R0402`.

## Still Open

The PB-100 footprint gate remains Open. These package classes still need local
footprint evidence before board import:

- TOLL / PG-HSOF-8-1 input-reverse and OUT2 escape MOSFET path.
- LFPAK88 80 V alternate MOSFET path.
- DO-218AC input TVS.
- CSS4J-4026 four-terminal current shunt.
- Optional digital temperature sensor if retained as DNP.
- FX18 100-pin board-to-board connector pair.
- CAN1 TX-disable final DNP/open link or logic-gate footprint decision.

## Boundary

PB-100 now has 6 bound on-board footprint items, 9 open on-board footprint
items, and 2 garage/not-required footprint items. KiCad board import remains
blocked by the open PB footprint rows plus mechanical and thermal/current layout
gates.
