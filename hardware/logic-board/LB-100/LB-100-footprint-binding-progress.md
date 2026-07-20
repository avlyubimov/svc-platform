# LB-100 Footprint Binding Progress

Status: Partial
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

## Still Open

The LB-100 footprint gate remains Open only because JPB1 is not locally bound.
The FX18 100-pin mezzanine pair needs project-local footprint evidence plus
stack-height, pin-1, orientation, and vibration/assembly review before board
import.

## Boundary

LB-100 now has 12 bound on-board footprint items, 1 open on-board footprint
item, and 1 not-required service-USB footprint item. KiCad board import remains
blocked by the open JPB1 footprint row plus mechanical and signal-integrity
layout gates.
