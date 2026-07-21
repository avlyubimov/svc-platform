# LB-100 / FB-100 Electrical Corrective Review — 2026-07-21

Status: Closed for schematic evidence; layout and manufacturing remain blocked

This review corrects five electrical defects without changing ADR-0014 board
ownership or the 24-pin JFB1 contract.

## Electrical pin types and ERC

The deterministic generator now assigns `input`, `output`, `bidirectional`,
`power_in`, and `power_out` pin types to IC and rail-source pins. Connector and
passive-component pins remain passive. The validator rejects any passive pin on
U1-U17 LB IC symbols or U1 FB and requires a power input on every checked IC.
KiCad ERC therefore checks driver/power semantics instead of accepting an
all-passive library.

## ADC reference and ground

`ADC_REF` is sourced from `LB_3V3_ANALOG` through R16 0 ohm and decoupled at
VREF+ by C28 1 uF plus C29 100 nF to AGND as required by the STM32H563 supply
scheme. R17 0 ohm creates one explicit AGND-to-GND return. The validator checks
the complete VREF+ net and both sides of the single-point return.

## USB VBUS presence

FB-100 no longer creates a 100 kOhm / 27 kOhm analog divider. R13 limits
current from `USB_VBUS` to `USB_VBUS_DETECT_RAW`; R14 provides the mandatory
defined pulldown and C1 supplies bounded filtering. LB U14
`SN74LVC1G17QDBVRQ1` provides a 5 V-tolerant input with Ioff and a 3.3 V digital
output `USB_VBUS_PRESENT` to STM32 PD10. PD10 is treated as a digital input and
is not claimed as ADC-capable.

Why selected: the Q1 Schmitt buffer provides automotive qualification,
5.5 V-tolerant input operation at 3.3 V VCC, Ioff partial-power-down behavior,
and a small inspectable SOT-23-5 package. Alternative A is Nexperia
`74LVC1G17-Q100`; alternative B is onsemi `NC7SZ17` automotive grade. Either
alternative requires threshold, Ioff, pin-map, sourcing, and footprint review.
The buffer dissipates only leakage/static current for this slow signal; maximum
junction and operating limits remain those of the selected datasheet. Order-
date LCSC/JLCPCB/PCBWay availability remains a production recheck. The final
`3.9 kOhm / 15 kOhm / 100 nF` network and its Schmitt-threshold, leakage, and timing proof
are recorded in `LB-100-fb-powered-off-corrective-review-2026-07-21.md`.

## LTC3212 timing source

`STATUS_RGB_DATA` is driven directly by STM32 PD7. TCA9539-Q1 P12 is unused.
This removes the 400 kHz I2C expander transaction from the LTC3212 LEDEN timing
path; firmware can now generate the datasheet-defined high/low pulses and
enable/shutdown intervals directly.

## Switched-sensor back-power

BMI270 VDD remains on switched `RADIO_SENSOR_3V3`, while BMI270 VDDIO and CSB
are on always-on `LB_3V3_IO`, matching the always-on I2C pull-up domain. The
VEML7700 interface supply is also always-on. This prevents SDA/SCL from rising
above an unpowered VDDIO domain and violating the BMI270 `VDDIO + 0.3 V`
absolute input limit. Firmware must not access BMI270 until switched VDD is
settled. The E73 on the same switched rail is separately isolated from STM32
UART and reset by three `SN74LVC1G125-Q1` gates as documented in
`LB-100-fb-powered-off-corrective-review-2026-07-21.md`.

## Evidence

- STM32H563 datasheet: https://www.st.com/resource/en/datasheet/stm32h563vi.pdf
- SN74LVC1G17-Q1 datasheet: https://www.ti.com/lit/ds/symlink/sn74lvc1g17-q1.pdf
- TCA9539-Q1 datasheet: https://www.ti.com/lit/ds/symlink/tca9539-q1.pdf
- LTC3212 datasheet: https://www.analog.com/media/en/technical-documentation/data-sheets/3212fb.pdf
- BMI270 datasheet: https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf
- `tools/validate_board_schematics.py`

No `LB-100.kicad_pcb`, `FB-100.kicad_pcb`, Gerbers, drills, pick-place,
BOM/CPL manufacturing package, or manufacturing ZIP is authorized by this
review.
