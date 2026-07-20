# LB-100 Footprint Binding Progress

Status: Complete For Footprint Binding
Review date: 2026-07-20

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
- JPB1 Hirose FX18 receptacle: `LB100:FX18-100S-0.8SV20_Hirose`, paired with `PB100:FX18-100P-0.8SV10_Hirose`.

## FX18 Evidence Boundary

The JPB1 footprint is source-derived from the official Hirose FX18 catalog
recommended land pattern and the official 2026 2D drawings for
`FX18-100S-0.8SV20` and `FX18-100P-0.8SV10`. It closes LB-100 footprint
binding only. The MF/TH mechanical pads, mating datum, 20 mm stack spacing,
pin-1 orientation across PB/LB, vibration retention, and assembly handling
remain in the mechanical envelope gate before board import.

## Still Open

No LB-100 footprint inventory rows remain open. KiCad board import is still
blocked by the open mechanical envelope gate, signal-integrity layout gate, and
controlled schematic symbol promotion from empty Footprint properties.

## Boundary

LB-100 now has 13 bound on-board footprint items, 0 open on-board footprint
items, and 1 not-required service-USB footprint item. KiCad board import remains
blocked by mechanical and signal-integrity layout gates.
