# PB-100 Footprint Binding Progress

Status: Complete For Footprint Binding
Review date: 2026-07-20

This progress note binds the PB-100 footprints that have project-local KiCad
footprint evidence. It does not create `PB-100.kicad_pcb`, Gerbers, drill
files, pick-place files, BOM/CPL order packages, manufacturing ZIP files,
fabrication packages, panel outputs, or PCBA orders.

## Closed In This Increment

- TPS48110 high-side controller: `PB100:VSSOP-20_19P-L5.0-W3.0-P0.50-LS5.0-BL_PE16`.
- BUK7S1R2-80M selected 80 V output and input-reverse MOSFET:
  `PB100:LFPAK88_SOT1235_Nexperia`.
- SIDR626LDP historical 60 V package evidence:
  `PB100:POWERPAK-SO-8_L6.1-W5.1-P1.27-BL-EP`; it is not a Rev.1 assembly
  substitute.
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
- Infineon PG-HSOF-8-1 TOLL historical 60 V footprint:
  `PB100:PG-HSOF-8-1_TOLL_Infineon`; retained as evidence only.

## FX18 Evidence Boundary

The FX18 footprints are source-derived from the official Hirose FX18 catalog
recommended land pattern and the official 2026 2D drawings for
`FX18-100P-0.8SV10` and `FX18-100S-0.8SV20`. Both footprints capture six
official plated lands with four GND MF circuits, unique logical identifiers,
mirrored X geometry, and preserved pin-1 orientation. Footprint binding is
closed; physical paired datum, 20 mm stack tolerance, vibration retention,
assembly-fixture, and handling evidence remain in the mechanical envelope gate
before board import.

## Footprint Inventory Result

The PB-100 footprint-binding inventory has no remaining Open rows. These
non-footprint gates still block KiCad board import:

- Controlled schematic symbol promotion from preliminary symbols to bound
  footprint properties.
- Mechanical envelope review.
- Thermal/current layout model and high-current copper review.
- Package-specific paste aperture via field solder voiding and assembly notes.

## Boundary

PB-100 now has 15 bound on-board footprint items, 0 open on-board footprint
items, and 2 garage/not-required footprint items. KiCad board import remains
blocked by mechanical, thermal/current layout, and controlled schematic symbol
promotion gates.
