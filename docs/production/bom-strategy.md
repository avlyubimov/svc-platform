# BOM Strategy

## Two BOMs

### Factory BOM
Everything installed by PCBWay/JLCPCB:
- MCU
- CAN transceivers
- DC/DC
- FRAM
- RTC
- IMU
- light sensor
- current sensors
- MOSFETs
- TVS/ESD/protection
- small passives

### Garage BOM
Everything installed manually:
- Deutsch connectors
- fuses
- enclosure
- gasket
- screws
- wires
- heat shrink
- harness tape
- mounting hardware

## Rule

If a part is QFN, LQFP, 0402, 0603, or otherwise annoying to solder manually, it belongs in Factory BOM.
