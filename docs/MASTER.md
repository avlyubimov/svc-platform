# SVC MASTER Document

## Product name

SVC — Smart Vehicle Controller

## Reference Vehicle #001

BMW R1200GS K25 2007  
VIN: WB10307A97ZU65028

## Product philosophy

SVC is a modular, open, long-lifecycle vehicle accessory controller. It should combine a robust power distribution system with software-defined behavior, CAN-aware logic, sensors, logging, and rule-based automation.

## Platform components

- **Power Board PB-100**: high-current outputs, protection, fuses, current sensing.
- **Logic Board LB-100**: MCU, CAN, BLE, SD, RTC, FRAM, sensors.
- **Front Board FB-100**: USB-C service, status LEDs, service button.
- **Firmware FW**: FreeRTOS-based modular firmware.
- **SVC Studio**: desktop configurator.
- **SVC Mobile**: mobile configurator.
- **CAN DB**: vehicle-specific CAN decoding database.

## First vehicle use case

BMW R1200GS K25 needs:
- USB-C LOBoo power
- cigarette socket / compressor
- left/right fog lights with lux and CAN-aware logic
- CHIGEE / navigation power
- heated seat channels
- DVR
- auxiliary brake / rear light
- spare channel
- BMW CAN read-only logging and decoding
