# SVC Architecture Review v1.0

Status: Draft

## 1. Architecture goal

Design a modular smart vehicle controller that can support future features primarily through configuration, plugins, firmware, or Logic Board replacement.

## 2. Board architecture

```text
Power Board PB-100
        ▲
        │ 100-pin mezzanine / board-to-board interface
        │
Logic Board LB-100
        ▲
        │ board-to-board / cable
        │
Front Panel Board FB-100
```

## 3. Power domains

- Always-on logic domain
- Switched accessory domain
- High-current domain
- Sensor domain
- Service/programming domain

## 4. Required outputs

PB-100 must provide at least 10 generic protected outputs:

| Output | Default role | Target current | PWM |
|---|---|---:|---|
| OUT1 | USB-C LOBoo | 15 A | yes |
| OUT2 | Cigarette / compressor | 20 A | optional |
| OUT3 | Fog Left | 10 A | yes |
| OUT4 | Fog Right | 10 A | yes |
| OUT5 | CHIGEE / navigation | 5 A | yes |
| OUT6 | Heated Seat Rider | 10 A | yes |
| OUT7 | Heated Seat Passenger | 10 A | yes |
| OUT8 | DVR | 5 A | yes |
| OUT9 | Aux brake / rear light | 5 A | yes |
| OUT10 | Spare | 10 A | yes |

## 5. Each output must support

- Fuse
- MOSFET switching
- PWM where applicable
- Current measurement
- Overcurrent protection
- Thermal derating
- Fault lockout
- Role assignment by configuration

## 6. Vehicle network

- CAN1: vehicle CAN, read-only by default
- CAN2: expansion / bench / accessory CAN
- LIN footprint
- RS485 footprint
- UART expansion

## 7. Sensors

- Battery voltage
- Total input current
- Per-channel current
- PCB temperature
- MOSFET/power-zone temperature
- Ambient light sensor
- IMU
- External temperature input
- RTC
- FRAM
- Optional barometer/humidity footprint

## 8. Software architecture

```text
Drivers
  ↓
Event Bus
  ↓
Services
  ↓
Rule Engine
  ↓
Output Manager
  ↓
Logger / API
```

No module should directly manipulate another feature. CAN creates events; rules consume events; output manager applies actions.

## 9. Configuration

Configuration is separate from firmware and contains:
- channel role mapping
- current limits
- PWM limits
- profiles
- IF/THEN rules
- battery thresholds
- vehicle profile
- CAN database selection

## 10. Manufacturing

- SMD parts assembled by PCBWay/JLCPCB.
- User installs only connectors, fuses, enclosure hardware, wiring.
- Components should preferably be available through LCSC/JLCPCB assembly.
- Critical components must have alternatives.

## 11. Reference vehicle

BMW R1200GS K25 2007 is the first integration target.
