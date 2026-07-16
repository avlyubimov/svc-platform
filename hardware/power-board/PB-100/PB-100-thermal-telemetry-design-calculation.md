# PB-100 Thermal Telemetry Design Calculation

Status: Candidate values for schematic review; not final

This note defines the first value-bearing NTC divider candidate for `TEMP_PCB`,
`TEMP_PWR_A`, and `TEMP_PWR_B`. It does not authorize PCB layout, sensor
placement, thermal copper, or manufacturing output.

## Inputs

- Sensor class: `NTCGS103JF103FT8`-class 10 kΩ AEC-Q200 NTC.
- Nominal NTC: 10 kΩ at 25 °C.
- B25/85: 3435 K.
- ADC domain: `LB_3V3_IO`.
- Default thresholds: 85 °C warn, 105 °C cutoff, 75 °C recovery.
- Divider topology: pull-up resistor to `LB_3V3_IO`, NTC to `GND`, ADC reads
  the divider midpoint. Hotter temperature lowers ADC voltage.

## Candidate divider

| Item | Candidate | Rationale | Still open |
|---|---:|---|---|
| Pull-up resistor | 4.7 kΩ 1% AEC-Q200 | Improves hot-threshold ADC span versus 10 kΩ pull-up | ADC source impedance review |
| NTC | 10 kΩ B25/85 3435 K | Matches TDK preferred class and alternates | Exact suffix sourcing |
| ADC series resistor | 1 kΩ 1% | Limits ADC/input transient current and isolates filter cap | LB-100 ADC sample timing |
| ADC filter capacitor | 10 nF X7R to GND | Local noise filter without heavy response delay | ADC settling and leakage |
| Calibration | Per-board config/calibration table | Keeps thresholds out of firmware constants | Bench calibration |

## Calculated divider points

Approximate NTC resistance uses the beta equation with B = 3435 K. ADC voltage
uses `VADC = 3.3 V × RNTC / (4.7 kΩ + RNTC)`.

| Temperature | Approx RNTC | Approx VADC |
|---:|---:|---:|
| -40 °C | 248 kΩ | 3.24 V |
| 0 °C | 28.7 kΩ | 2.84 V |
| 25 °C | 10.0 kΩ | 2.25 V |
| 75 °C recovery | 1.91 kΩ | 0.95 V |
| 85 °C warn | 1.45 kΩ | 0.78 V |
| 105 °C cutoff | 874 Ω | 0.52 V |
| 125 °C | 554 Ω | 0.35 V |
| 150 °C | 333 Ω | 0.22 V |

## Self-heating check

With 4.7 kΩ pull-up, divider current is about 224 µA at 25 °C. NTC dissipation
is roughly 0.50 mW at 25 °C and about 0.31 mW at 105 °C. This is acceptable for
schematic review, but final approval still requires the selected NTC package
dissipation constant, airflow/enclosure assumptions, and bench calibration.

## Freeze blockers

- Verify LB-100 ADC input leakage and sample/hold settling with 1 kΩ + 10 nF.
- Confirm whether `TEMP_PWR_A` and `TEMP_PWR_B` need different placement rules
  or thermal coupling pads.
- Recheck TDK, Vishay, and Murata NTC orderability and assembly handling.
- Store calibration constants outside firmware binaries.
- Keep PCB layout blocked until schematic freeze closes.
