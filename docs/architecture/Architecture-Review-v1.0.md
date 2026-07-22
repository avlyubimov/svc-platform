# SVC Architecture Review v1.0

Status: Frozen

This review defines the v1.0 architecture baseline for SVC. PB-100 schematic
planning may proceed after freeze. KiCad PCB layout remains blocked until
schematic inputs are reviewed.

Architecture v1.0 was accepted by the project owner on 2026-06-30 and frozen in
ADR-0009.

## 1. Architecture goal

Design a modular smart vehicle controller that can support future features primarily through configuration, plugins, firmware, or Logic Board replacement.

The primary lifecycle constraint is that PB-100 must remain stable while LB-100,
FB-100, firmware, configuration, and vehicle profiles evolve.

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

### 2.1 Board responsibilities

| Board | Responsibility | Expected change rate |
|---|---|---|
| PB-100 | Vehicle power input, protected generic outputs, current/thermal sensing, fuse interface, high-current connectors | Low |
| LB-100 | MCU, firmware execution, CAN/LIN/RS485/UART interfaces, storage, RTC/FRAM, sensors, rule engine | Medium |
| FB-100 | USB-C service access, service button, status indication | Medium |

PB-100 exposes generic power capabilities. It must not encode accessory roles in
silkscreen, net names, firmware constants, or mechanical assumptions beyond
neutral output identifiers such as OUT1..OUT10.

## 3. Power domains

- Always-on logic domain
- Switched accessory domain
- High-current domain
- Sensor domain
- Service/programming domain

Power-domain requirements:

- PB-100 accepts vehicle battery input and must tolerate the system electrical
  requirements in `docs/requirements/system-requirements.md`.
- A main fuse is installed near the battery in the harness.
- Per-output fuses are user-serviceable.
- Reverse-polarity, surge/transient, and ESD protection are required before
  schematic freeze.
- Logic power must remain stable through normal motorcycle cranking dips where
  practical.

## 4. Required outputs

PB-100 must provide at least 10 generic protected outputs:

| Output | Reference default role | Target fuse | Target current limit | PWM |
|---|---|---:|---:|---|
| OUT1 | Cigarette socket / future compressor | 15 A | 12 A | yes |
| OUT2 | High-current reserve | 20 A | 18 A | optional |
| OUT3 | Fog primary left | 10 A | 8 A | yes |
| OUT4 | Fog primary right | 10 A | 8 A | yes |
| OUT5 | Low-current reserve 1 | 5 A | 4 A | yes |
| OUT6 | Fog secondary left | 10 A | 8 A | yes |
| OUT7 | Fog secondary right | 10 A | 8 A | yes |
| OUT8 | Low-current reserve 2 | 5 A | 4 A | yes |
| OUT9 | Low-current reserve 3 | 5 A | 4 A | yes |
| OUT10 | Medium-current reserve | 10 A | 8 A | yes |

Reference default roles are configuration defaults for Vehicle Profile #001 only.
They are not hardware roles.

ADR-0020 additionally defines the independent `C36_BIDIRECTIONAL` battery
branch and the protected `FOG_A_SW_IN`/`FOG_B_SW_IN` manual requests. Neither changes the
generic OUT1 through OUT10 PCB naming or permits firmware to bypass safe-off.

## 5. Each output must support

- Fuse
- High-side electronic switching
- PWM where applicable
- Current measurement
- Overcurrent protection
- Thermal derating
- Fault lockout
- Role assignment by configuration
- Load priority assignment by configuration
- Safe default-off state during boot, reset, firmware update, and fault recovery

Detailed PB-100 requirements are tracked in
`docs/requirements/pb-100-requirements.md`.

## 6. Vehicle network

- CAN1: vehicle CAN, read-only by default
- CAN2: expansion / bench / accessory CAN
- LIN footprint
- RS485 footprint
- UART expansion

CAN1 requirements:

- CAN1 is physically listen-only by default.
- CAN1 TX must be disabled by solder jumper, hardware gate, or transceiver
  silent/listen-only mode.
- Rev.1 firmware must not transmit on vehicle CAN.
- Any future CAN TX support requires a new ADR and an explicit hardware-enable
  action.

CAN2 is the only CAN interface intended for bench, expansion, or accessory
transmit use in the v1.0 architecture.

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

Required software boundaries:

- Drivers expose hardware state and commands.
- Services own debouncing, filtering, diagnostics, and state transitions.
- The event bus is the only cross-feature notification path.
- The rule engine consumes events and configuration.
- The output manager is the only module that applies output state changes.
- Logging/API modules observe events and state; they do not bypass services.

## 9. Configuration

Configuration is separate from firmware and contains:
- channel role mapping
- current limits
- board-level total current budget
- PWM limits
- profiles
- IF/THEN rules
- battery thresholds
- vehicle profile
- CAN database selection

Configuration storage requirements:

- Firmware updates must not erase user configuration.
- Vehicle profiles define default role mappings and CAN database selection.
- Hardware capability discovery must use board identifiers and capabilities, not
  accessory role assumptions.
- Invalid configuration must fail safe with outputs disabled or held in the last
  explicitly safe state.

The current example configuration is
`firmware/configs/config-example.json`.

## 10. Manufacturing

- SMD parts assembled by PCBWay/JLCPCB.
- User installs only connectors, fuses, enclosure hardware, wiring.
- Components should preferably be available through LCSC/JLCPCB assembly.
- Critical components must have alternatives.
- Component-family selection must be verified before schematic freeze.
- Factory BOM and garage BOM remain separate production artifacts.
- Initial component-family shortlist is tracked in
  `docs/production/component-family-shortlist.md`.

## 11. Reference vehicle

BMW R1200GS K25 2007 is the first integration target.

Vehicle Profile #001 requirements:

- BMW CAN remains read-only.
- Accessory roles map to OUT1..OUT10 through configuration.
- Fog light, brake-light, and accessory behavior must be implemented through
  events, rules, and output manager actions.
- The platform must remain vehicle-agnostic after applying the BMW K25 profile.

## 12. Board-to-board interface contract

The PB-100 to LB-100 interface must carry these signal classes:

- Power: protected battery sense, logic supply, power-good, grounds.
- Output control: enable/PWM command signals for each generic output.
- Measurement: per-output current telemetry, input voltage/current telemetry,
  and temperature telemetry.
- Faults: per-output fault indication and board-level fault indication.
- Expansion: spare GPIO/ADC/I2C/SPI/UART capacity for future PB-100 revisions.
- Safety: CAN1 TX disable control/status when applicable.

The exact pin map is a schematic-freeze artifact. The interface must keep PB-100
usable with future LB-100 revisions without changing PB-100 connectors or output
stage design.

## 13. Freeze checklist

Architecture v1.0 is frozen because all items are true:

- ADR-0001 through ADR-0009 are accepted.
- PB-100 requirements are reviewed and accepted.
- CAN1 read-only hardware policy is preserved in schematic requirements.
- Output role mapping remains configuration-driven.
- Board-level current budget and priority shedding are defined.
- Critical component families have at least two viable alternatives.
- Initial component-family shortlist is complete.
- Factory and garage BOM split remains valid.
- No KiCad layout work has started before requirements acceptance.

## 14. Review outcome

This review authorizes PB-100 schematic planning. It does not authorize PCB
layout or Power Board requirement changes without a follow-up ADR.
