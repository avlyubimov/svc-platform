# LB-100 Footprint Binding Progress

Status: Complete For Footprint Binding
Review date: 2026-07-21

This progress note binds the LB-100 footprints that have project-local KiCad
footprint evidence. It does not create `LB-100.kicad_pcb`, Gerbers, drill files,
pick-place files, BOM/CPL order packages, manufacturing ZIP files, fabrication
packages, panel outputs, or PCBA orders.

## Closed In This Increment

- STM32H563VIT6 MCU: `LB100:LQFP-100_L14.0-W14.0-P0.50-LS16.0-BL`.
- XC6220B331MR-G 3V3 regulator: `LB100:SOT-25_L3.0-W1.6-P0.95-LS2.8-TL`.
- CAN1 / LIN / FRAM / RTC SOIC-8 class: `LB100:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL`.
- CAN2 HVSON-8-EP: `LB100:HVSON-8_L3.0-W3.0-P0.65-BL-EP`.
- RS485 SOIC-8 class: `LB100:SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL`.
- E73 BLE module: `LB100:WIRELM-SMD_E73-2G4M08S1C`.
- BMI270 IMU: `LB100:LGA-14_L3.0-W2.5-P0.50-BR`.
- VEML7700 ambient sensor: `LB100:SENSOR-SMD_EML7700-TT`.
- TF-015 microSD socket: `LB100:TF-SMD_TF-015`.
- JPB1 Hirose FX18 receptacle: `LB100:FX18-100S-0.8SV10_Hirose`, paired with `PB100:FX18-100P-0.8SV10_Hirose`.
- TCA9539-Q1 UI expander, two TPS22918-Q1 load switches, JFB1 FPC,
  HSE/LSE crystals, service headers, and all 0603/0805 passives used by the
  reviewed value-bearing schematic.

## FX18 Evidence Boundary

The JPB1 footprint is source-derived from the official Hirose FX18 catalog
recommended land pattern and the official 2026 2D drawings for
`FX18-100S-0.8SV10` and `FX18-100P-0.8SV10`. Both footprints capture six
official plated lands with four GND MF circuits, unique logical identifiers,
mirrored X geometry, and preserved pin-1 orientation. Footprint binding is
closed. The official P-SV10 plus S-SV10 pair, four shared M2.5 holes, four
20.3 +/-0.127 mm spacers, fixture, and mating inspection plan are closed for
pre-layout work by `PB-100-fx18-paired-stack-closeout.md`. Physical continuity
and vibration execution remains mandatory as PB-BENCH-014/015 before motorcycle
power or production.

## Still Open

No LB-100 footprint inventory rows remain open. Schematic symbol promotion and
the mechanical envelope gate are closed. KiCad board import is still blocked by
the separate signal-integrity and safety layout model.

## Boundary

LB-100 now has 18 source-identified/bound footprint classes, 0 open footprint
items, and 2 no-footprint-required ownership boundaries. KiCad board import
remains blocked only by the signal-integrity and safety layout gate.
