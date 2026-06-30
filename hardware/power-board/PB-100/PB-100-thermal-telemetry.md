# PB-100 Thermal Telemetry Strategy

Status: Schematic-planning input

This document defines PB-100 thermal telemetry for schematic planning. It does
not freeze final thermistor values or digital sensor MPNs.

## Decision

Use three PB-100 thermal measurement points:

- `TEMP_PCB`: board-level reference temperature.
- `TEMP_PWR_A`: high-current hot zone near OUT2 and input reverse-protection
  MOSFET.
- `TEMP_PWR_B`: secondary power zone near medium-current outputs and logic buck.

Rev.1 preferred implementation is automotive/AEC-Q200 NTC dividers routed to
LB-100 ADC inputs. A TMP117/TMP112-class digital sensor may be used as an
additional board-temperature reference on `PB_I2C` if schematic space and
assembly sourcing allow it.

## Measurement map

Detailed map CSV:
`hardware/power-board/PB-100/PB-100-thermal-telemetry-map.csv`.

The map is tied to thermal zones, not accessory roles.

## Firmware behavior

- Temperature thresholds are configuration/calibration values, not hard-coded
  role assumptions.
- Missing, saturated, or implausible temperature telemetry is a safe fault.
- Output Manager must derate or shut down outputs based on board and power-zone
  thermal state.
- Thermal faults must be logged with the affected generic output or board zone.
- Firmware now has a host-testable Thermal Protection service for initial
  allow/derate/cutoff decisions before driver integration.

## Schematic requirements

- Place `TEMP_PWR_A` close to the OUT2/input high-current thermal path.
- Place `TEMP_PWR_B` close to the medium-output MOSFET cluster or logic buck hot
  zone.
- Place `TEMP_PCB` away from direct heat sources enough to represent board
  ambient/reference temperature.
- Route analog thermistor dividers to `LB_3V3_IO` ADC domain.
- Keep divider current low enough to avoid self-heating.
- Provide calibration constants through configuration or board identity data.
- Recheck JLCPCB/PCBWay assembly support for selected sensors before schematic
  freeze.

## Evidence links

- TI TMP117 data sheet: https://www.ti.com/lit/gpn/TMP117
- TDK automotive SMD NTC thermistor overview: https://www.tdk-electronics.tdk.com/download/1642324/f93f281b350e066d0869c5c77be5189b/smd-ntc-presentation-multilayer-smd-ntc-thermistors-pdf.pdf
- TDK NTCG automotive NTC data sheet: https://www.farnell.com/datasheets/3920346.pdf
