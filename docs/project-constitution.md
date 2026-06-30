# SVC Project Constitution

## 1. SVC is a platform, not a single device

The platform must support multiple vehicles by changing firmware, configuration, CAN database, and wiring harness.

## 2. Power Board compatibility is sacred

The Power Board must be designed with a long lifecycle. New features must not require a Power Board redesign unless unavoidable.

## 3. Functions are implemented at the highest possible layer

Decision order:

1. Configuration
2. Plugin
3. Firmware
4. Logic Board
5. Power Board

Only change lower layers when higher layers cannot support the requirement.

## 4. CAN safety first

Vehicle CAN is listen-only by default.  
CAN TX must be physically disabled by default using solder jumper or hardware gate.

## 5. No hard-coded roles

Physical outputs are generic. Roles are assigned via configuration:

- USB
- Fog Left
- Fog Right
- Heated Seat
- CHIGEE
- Auxiliary Brake
- Spare

## 6. Device must work without phone or cloud

BLE, mobile app, cloud, and desktop tools are optional. Core functions must work standalone.

## 7. Configuration is separate from firmware

Firmware updates must not erase user configuration.

## 8. Documentation is part of the product

Every major decision must be documented in ADR format.

## 9. Factory assembly first

All small SMD components should be assembled by PCBWay/JLCPCB. User should only install connectors, fuses, enclosure hardware, and wiring.

## 10. Safety over convenience

No feature may compromise vehicle safety, CAN stability, battery health, or wiring safety.
