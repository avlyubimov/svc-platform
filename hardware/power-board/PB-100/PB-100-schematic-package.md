# PB-100 Schematic Package

Status: Started after Architecture v1.0 freeze

This package converts frozen PB-100 requirements into schematic-planning inputs.
It is not a PCB layout package.

## Governing documents

- `docs/architecture/Architecture-Review-v1.0.md`
- `docs/requirements/pb-100-requirements.md`
- `docs/adr/ADR-0006-pb-100-baseline-requirements.md`
- `docs/adr/ADR-0007-pb-100-high-side-output-switching.md`
- `docs/adr/ADR-0008-pb-100-current-budget.md`
- `docs/adr/ADR-0010-pb-100-power-path-candidate-strategy.md`
- `docs/production/component-family-shortlist.md`
- `hardware/power-board/PB-100/PB-100-preliminary-validation.md`
- `hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md`

## Electrical baseline

- Battery input: 6-18 V normal target.
- Main harness fuse target: 50 A.
- Board continuous-current target: at least 40 A after thermal validation.
- Default configuration total-current limit: 40 A.
- Outputs: 10 generic high-side protected channels.
- CAN1: read-only by default; TX physically disabled.

## Output classes

| Class | Outputs | Target fuse | Target current limit | Initial implementation direction |
|---|---|---:|---:|---|
| High current | OUT2 | 20 A | 18 A | TPS48110AQDGXRQ1-class controller plus external 60 V N-MOSFET |
| Medium current | OUT1, OUT3, OUT4, OUT6, OUT7, OUT10 | 10-15 A | 8-12 A | TPS48110AQDGXRQ1-class controller plus external 60 V N-MOSFET |
| Low current | OUT5, OUT8, OUT9 | 5 A | 4 A | TPS2HB35BQPWPRQ1-class smart high-side switch |

## Required schematic blocks

- Battery input protection: main input connector, reverse protection, TVS/load
  dump clamp, input current measurement, battery voltage measurement.
- Logic power: protected 5 V/3.3 V rails for LB-100 interface and telemetry.
- Output channels: fuse, high-side switch/controller, current sense, fault
  signal, flyback/inductive-load handling where required.
- Thermal sensing: PCB sensor and power-zone sensor.
- Board identity: revision or resistor-coded identity where practical.
- Board-to-board interface: stable PB-100 to LB-100 connector.
- Safety interlocks: CAN1 TX disable status/control if CAN1 routing crosses
  PB-100.

## Board-to-board signal budget

Logical pin-budget CSV:
`hardware/power-board/PB-100/PB-100-b2b-pin-budget.csv`.

| Signal group | Count target | Direction | Notes |
|---|---:|---|---|
| Power and grounds | 20-30 pins | PB-100/LB-100 | Multiple grounds and supply pins for current return and signal integrity |
| Output enable/PWM | 10 pins | LB-100 to PB-100 | One control signal per output minimum |
| Output fault/status | 10 pins | PB-100 to LB-100 | Can be direct or multiplexed if diagnostic latency is acceptable |
| Current telemetry | 10 signals | PB-100 to LB-100 | Analog, I2C/SPI monitors, or high-side IMON strategy |
| Board telemetry | 4-8 signals | PB-100 to LB-100 | Input voltage/current, PCB temp, power-zone temp, power-good |
| Configuration/ID | 2-4 signals | PB-100 to LB-100 | Revision ID, EEPROM, or resistor-coded identity |
| Expansion reserve | 10-20 pins | Mixed | Spare GPIO/ADC/I2C/SPI/UART capacity |

The initial 100-pin mezzanine target remains plausible, but final pin assignment
requires schematic-level tradeoff between direct signals, multiplexed telemetry,
and digital monitor buses.

## Output channel matrix

Output matrix CSV:
`hardware/power-board/PB-100/PB-100-output-channel-matrix.csv`.

The matrix keeps hardware outputs generic while carrying the BMW K25 reference
defaults needed for sizing and bench tests.

## Power-path candidates

Candidate MPN CSV:
`hardware/power-board/PB-100/PB-100-power-path-candidates.csv`.

These candidates are allowed for schematic planning only. Final MPN lock still
requires SOA, thermal, clamp-voltage, and assembly-class validation.

Preliminary validation tables:

- `hardware/power-board/PB-100/PB-100-thermal-estimates.csv`
- `hardware/power-board/PB-100/PB-100-protection-validation.csv`

## Net naming rules

- Use neutral output identifiers: `OUT1` through `OUT10`.
- Do not name nets after accessory roles such as fog, seat, USB, or CHIGEE.
- Use role names only in configuration and vehicle-profile documents.
- Mark CAN1 TX-disable hardware clearly in schematic notes.

## Schematic freeze blockers

- Track schematic-freeze readiness in
  `hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md`.
- Validate candidate MPNs in `PB-100-power-path-candidates.csv`.
- Resolve SM8S33A-class TVS clamp compatibility with 40 V smart switches.
- Confirm high-side switch/controller thermal limits.
- Confirm MOSFET SOA for OUT2 compressor startup/inrush.
- Confirm TVS clamp voltage against high-side controller, MOSFET, and buck
  absolute maximum ratings.
- Confirm connector current ratings and derating.
- Confirm JLCPCB/PCBWay assembly class for selected MPNs.
