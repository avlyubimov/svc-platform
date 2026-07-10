# PB-100 Thermal Telemetry Strategy

Status: Schematic-planning input

This document defines PB-100 thermal telemetry for schematic planning. It does
not freeze final divider values or calibration constants.

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

Initial schematic-planning sensor direction is a TDK
`NTCGS103JF103FT8`-class 10 kΩ NTC:

- 0402 body, 10 kΩ at 25 °C, ±1% resistance tolerance.
- B25/85 value of 3435 K.
- AEC-Q200 automotive grade with 150 °C maximum operating temperature.
- Same NTC class for `TEMP_PCB`, `TEMP_PWR_A`, and `TEMP_PWR_B` unless
  schematic review proves a mixed sensor set is needed.

The ADC divider value is still a schematic-freeze item. It must keep thermistor
self-heating low, preserve useful ADC resolution around the default thermal
thresholds, and include calibration constants outside firmware binaries.

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
- Default configuration thresholds are currently 85 °C warn, 105 °C cutoff, and
  75 °C recovery for each thermal zone until bench thermal validation updates
  board calibration.

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
- TDK `NTCGS103JF103FT8` product page: https://product.tdk.com/en/search/sensor/ntc/chip-ntc-thermistor/info?part_no=NTCGS103JF103FT8
- Vishay NTCS0402E3 automotive alternate family: https://www.vishay.com/en/product/29003/
- Murata NCU automotive alternate family list: https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/static-model/component-list-ntc-2508.ashx?cvid=20250930011345000000&la=en
