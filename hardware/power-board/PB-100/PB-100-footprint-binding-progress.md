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
- JPB1 Hirose FX18 PB/LB pair: `PB100:FX18-100P-0.8SV10_Hirose` paired with `LB100:FX18-100S-0.8SV20_Hirose`.
- LM5013-Q1 logic buck alternate: package-compatible with the existing reviewed `PB100:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL-EP2.9` DDA SO PowerPAD-8 footprint.
- CAN1 TX-disable hardware: `PB100:R0603_DNP_LINK_1608Metric` for default-open `JP_CAN1` and `PB100:SOT-23-5_DBV_TI` for the `SN74LVC1G125-Q1`-class default-disabled gate candidate.
- Vishay SM8S input TVS: `PB100:DO-218AC_Vishay_SM8S`.
- Bourns CSS4J-4026 total input current shunt: `PB100:CSS4J-4026_Bourns`.
- TMP112-Q1 optional DNP digital temperature sensor: `PB100:SOT-563-6_DRL_TI`.

## FX18 Evidence Boundary

The FX18 footprints are source-derived from the official Hirose FX18 catalog
recommended land pattern and the official 2026 2D drawings for
`FX18-100P-0.8SV10` and `FX18-100S-0.8SV20`. They close signal-pad footprint
binding only. The MF/TH mechanical pads, paired datum, 20 mm stack spacing,
pin-1 orientation across boards, vibration retention, and assembly handling
remain in the mechanical envelope gate before board import.

## Still Open

The PB-100 footprint gate remains Open. These package classes still need local
footprint evidence before board import:

- TOLL / PG-HSOF-8-1 input-reverse and OUT2 escape MOSFET path.
- LFPAK88 80 V alternate MOSFET path.

## Boundary

PB-100 now has 12 bound on-board footprint items, 3 open on-board footprint
items, and 2 garage/not-required footprint items. KiCad board import remains
blocked by the open PB footprint rows plus mechanical and thermal/current layout
gates.
