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
- **Front Board FB-100**: USB-C service, status LEDs, service/reset controls and
  optional FOG-button fit review.
- **Firmware FW**: FreeRTOS-based modular firmware.
- **SVC Studio**: desktop configurator.
- **SVC Mobile**: mobile configurator.
- **CAN DB**: vehicle-specific CAN decoding database.

## First vehicle use case

BMW R1200GS K25 reference configuration needs:
- OUT1 cigarette socket and future compressor limited to 10-12 A
- OUT2 high-current reserve up to 18 A
- OUT3/OUT4 first auxiliary-lamp pair and OUT6/OUT7 second pair
- OUT5/OUT8/OUT9 low-current reserves and OUT10 medium-current reserve
- protected `FOG_A_SW_IN`/`FOG_B_SW_IN` double handlebar requests with staged channel start per pair
- independent near-battery `C36_BIDIRECTIONAL` accessory/rescue-charge branch
- BMW CAN read-only logging and decoding

The stock headlamp remains on factory wiring. Physical power outputs stay
generic `OUT1` through `OUT10`; these reference roles are configuration only.
C36 is not a PB managed output and is not a starter-current source.

## Current hardware lifecycle

- PB-100: `EVT-LAYOUT-AUTHORIZED`.
- LB-100: `EVT-LAYOUT-AUTHORIZED`.
- FB-100: `EVT-LAYOUT-AUTHORIZED`; existing placement continues to routing.
- EVT fabrication: blocked until board-specific `EVT-FAB-REVIEW` closes.
- Production: blocked until Rev.1 validation, Rev.2 correction, critical retest
  and Product Owner `PRODUCTION-RELEASE` approval.
