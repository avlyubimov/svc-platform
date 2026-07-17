# PB-100 Current Telemetry Design Calculation

Status: Candidate values for schematic review; not final

This note defines the first value-bearing total-current telemetry candidate for
`IIN_SHUNT_HI`, `IIN_SHUNT_LO`, `IIN_SENSE`, `PB_I2C_SCL`, `PB_I2C_SDA`, and
`PB_I2C_INT`. It does not authorize PCB layout, shunt copper, Kelvin routing,
footprint lock, or manufacturing output.

## Inputs

- Total-current range target: 0-60 A.
- Board-current budget: 40 A software limit with 50 A main-fuse target.
- Shunt candidate: 0.5 mΩ four-terminal AEC-Q200 shunt in the Bourns
  `CSS4J-4026R-L500F` class.
- Monitor candidate: `INA228-Q1` I2C monitor with `INA229-Q1` and `INA226`
  alternates retained until sourcing and interface review close.
- Monitor supply and I/O domain: `LB_3V3_IO`.
- Safety boundary: total-current telemetry can deny or derate outputs, but must
  not be required to enable outputs from the safe-off state.

## Datasheet anchors

- `INA228-Q1`/`INA228` supports an 85 V bus-voltage sense input, a 2.7 V to
  5.5 V supply, 16 pin-selectable I2C addresses, and selectable ±40.96 mV or
  ±163.84 mV shunt ranges.
- `CSS4J-4026R-L500F`-class shunts are four-terminal AEC-Q200 current-sense
  resistors. The 0.5 mΩ member is a 10 W class part at 70 °C terminal
  temperature in the manufacturer table.

## Shunt operating points

Formula basis:

- `Vshunt = I * Rshunt`
- `Pshunt = I^2 * Rshunt`

| Current | Shunt voltage | Shunt dissipation | Range use with ±40.96 mV |
|---:|---:|---:|---:|
| 40 A budget | 20 mV | 0.8 W | 49 % |
| 50 A main-fuse target | 25 mV | 1.25 W | 61 % |
| 60 A telemetry target | 30 mV | 1.8 W | 73 % |
| 81.92 A monitor full-scale | 40.96 mV | 3.36 W | 100 % |

With a 0.5 mΩ shunt, the ±40.96 mV monitor range gives ±81.92 A electrical
full-scale. The 60 A telemetry target leaves about 10.96 mV or 21.92 A of
headroom before the monitor range limit. This is enough for schematic review,
but final approval still requires shunt temperature rise, copper heat spreading,
and fuse/short-pulse validation.

## Candidate monitor network

| Item | Candidate | Rationale | Still open |
|---|---|---|---|
| Monitor range | ±40.96 mV shunt range | Uses 73 % full-scale at 60 A with a 0.5 mΩ shunt | Confirm final monitor family |
| Address straps | `A1 = GND`, `A0 = GND`, candidate address `0x40` | Matches INA228-style default high-side example | LB-100 bus collision review |
| I2C pull-ups | LB-owned 4.7 kΩ to 10 kΩ to `LB_3V3_IO`; PB-side pull-ups DNP by default | Avoids duplicate pull-ups across the B2B connector | Bus capacitance and exact LB pins |
| Alert pull-up | `PB_I2C_INT` open-drain with LB-owned pull-up or 47 kΩ PB DNP option | Keeps alert diagnostic-only and low-current | Interrupt polarity and firmware mapping |
| Shunt input filter | 10 Ω series in each `IN+`/`IN-` sense leg plus 1 nF C0G differential capacitor candidate | Provides an EMI/transient filter point without large DC error | INA228 error and surge review |
| VBUS sense | 1 kΩ series from `VBAT_PROT` to `VBUS` plus 1 nF 100 V local filter capacitor candidate | Keeps bus-voltage telemetry on the protected rail | Load-dump and leakage review |
| Analog fallback | `IIN_SENSE` remains LB-visible for fast firmware budget checks or monitor-derived fallback | Keeps board-budget enforcement independent of summed per-output IMON | Final ADC or I2C ownership |
| Calibration | `telemetry.total_current` and `telemetry.output_current` carry nominal shunt value, per-output ranges, zero offsets, gains, monitor range, stale timeouts, and plausible-current limits | Keeps calibration out of firmware constants | Bench calibration flow and ADC scaling |

## Calibration boundary

Firmware must not hard-code the shunt value or monitor gain. The calibration
record must include at least:

- selected shunt nominal resistance;
- measured shunt resistance or gain correction;
- zero-current offset;
- monitor range setting;
- conversion timing/averaging used for safety decisions;
- stale-data timeout and implausible-data limits.

The first firmware-facing configuration contract is `telemetry.total_current`
and `telemetry.output_current` in `firmware/configs/config-example.json` and
`svc_telemetry_config_t` in `firmware/core/svc_config.h`. The current
total-current defaults mirror this schematic-review candidate: 500 µΩ shunt
resistance, 40960 µV monitor range, 0 mA offset, 1000000 ppm gain, 1000 ms
stale timeout, and 60000 mA plausible maximum. Per-output IMON defaults mirror
the map ranges: OUT1 20000 mA, OUT2 30000 mA, OUT3/OUT4/OUT6/OUT7/OUT10
15000 mA, and OUT5/OUT8/OUT9 8000 mA.
`tools/validate_config.py` and `firmware/services/config_validator.c` verify
that plausible-current limits cover the configured current limits without
exceeding their monitor or IMON class ranges. Bench calibration and ADC scaling
remain schematic-freeze items.

## Freeze blockers

- Verify the exact `INA228-Q1` orderable suffix, address table, and package
  drawing before locking `U2`.
- Confirm LB-100 owns the `PB_I2C` pull-up values, bus capacitance, and MCU pins.
- Review `PB_I2C_INT` polarity, pull-up ownership, and fault handling.
- Validate the 10 Ω / 1 nF shunt filter against measurement error, step
  response, and transient robustness.
- Validate `VBUS` surge stress under the selected TVS/load-dump clamp.
- Close the four-terminal shunt footprint, Kelvin routing, and shunt copper
  heating before layout.
- Keep PCB layout blocked until schematic freeze closes.

## Evidence links

- TI INA228-Q1 product page: https://www.ti.com/product/INA228-Q1
- TI INA228 data sheet: https://www.ti.com/lit/ds/symlink/ina228.pdf
- Bourns CSS4J-4026 data sheet:
  https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf
