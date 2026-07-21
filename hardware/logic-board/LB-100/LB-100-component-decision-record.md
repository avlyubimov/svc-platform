# LB-100 Value-Bearing Component Decision Record

Status: Accepted for Rev.1 schematic and prototype layout input
Decision date: 2026-07-21

This record implements the frozen LB-100 architecture. It does not change
ADR-0014 or ADR-0015 and does not authorize fabrication or production release.

## TCA9539-Q1 UI I/O Expander (U3)

- Decision: use `TCA9539QPWRQ1` in TI PW TSSOP-24. It supplies the 16 role-free
  front-panel GPIOs that do not fit on the MCU after the approved JPB1 binding.
  Reset and power-on configure every port as an input, so all channel LEDs
  remain inactive until firmware configures them. The timing-critical
  `STATUS_RGB_DATA` path is not routed through this I2C expander.
- Why this part: automotive AEC-Q100 Grade 1, -40 to +125 degrees C, 1.65 to
  3.6 V supply, interrupt and reset pins, and current-sink capability suitable
  for the 1 kOhm FB-100 LED paths. JLCPCB lists `C201627` as an extended
  TSSOP-24 assembly part.
- Alternative A: NXP `PCA9539PW/Q900`. Automotive-qualified and functionally
  similar; retain as a BOM alternate only after exact register/reset and
  footprint compatibility review.
- Alternative B: TI `TCA9535-Q1`. Automotive 16-bit I2C expansion, but lacks
  the selected reset behavior and is not approved as a drop-in substitution.
- Operating margin: each channel LED is externally limited below 2 mA versus
  an 8 mA guaranteed low-output test point. Ten simultaneous indicators use
  less than 20 mA versus 100 mA allowed per octal bank. With 0.5 V conservative
  VOL, port dissipation is below 10 mW; using 108.8 degrees C/W for PW gives
  less than 1.1 degrees C rise from the LED sink load.
- Maximum junction temperature: 150 degrees C absolute maximum; the design
  target is below 125 degrees C and must be checked again after placement.
- Lifetime: expected platform service life is at least 10 years when operated
  inside the stated temperature/current limits; procurement status and PCNs
  are rechecked before every production lot.
- Availability and assembly: TI marks the family active; JLCPCB `C201627` is a
  standard SMT extended part. The local PW footprint is drawing-bound and its
  gull-wing joints are optically inspectable.
- Risks: an I2C fault can remove UI indication. UI state is not a PB output
  safety interlock; firmware must report expander failure and must never infer
  output safety from LED state.

## SN74LVC1G17-Q1 USB VBUS Detector (U14)

- Decision: use `SN74LVC1G17QDBVRQ1` as a 3.3 V Schmitt-input digital detector
  between current-limited `USB_VBUS_DETECT_RAW` and STM32 PD10.
- Why this part: AEC-Q100 qualification, 5.5 V-tolerant input at 3.3 V VCC,
  Ioff partial-power-down protection, Schmitt thresholds, and inspectable
  SOT-23-5 packaging prevent both the invalid ADC claim and back-power.
- Alternative A: Nexperia `74LVC1G17-Q100`; automotive-qualified but requires
  exact threshold, Ioff, pin-map, and sourcing review.
- Alternative B: automotive onsemi `NC7SZ17`; non-drop-in sourcing and
  electrical review are required before substitution.
- Operating margin: FB R13 3.9 kOhm and R14 15 kOhm produce at least 3.723 V
  at 4.75 V VBUS after resistor and input-leakage tolerance, above even the
  3.43 V maximum positive threshold in the complete TI table. After disconnect,
  R14 holds the input below 0.152 V and discharges the worst-case 130 nF node
  below the 0.77 V minimum falling threshold within 3.81 ms. The output is limited to `LB_3V3_IO`; PD10
  is used only as a digital input.
- Maximum junction temperature and lifetime: use the selected datasheet limits
  and the 10-year platform target; static detector dissipation is negligible,
  but enclosure temperature remains a prototype check.
- Availability and assembly: DBV SOT-23-5 is compatible with JLCPCB/PCBWay;
  exact LCSC/JLC stock and PCN status require an order-date recheck.
- Known risks: threshold variation during low VBUS ramps and ESD coupling;
  firmware must debounce presence and layout must keep the raw 5 V path short.

## SN74LVC1G125-Q1 E73 Isolation (U15-U17)

- Decision: use three `SN74LVC1G125QDBVRQ1` gates powered by
  `RADIO_SENSOR_3V3` to isolate STM32 UART TX, UART RX, and reset from the E73
  while its switched rail is off. R18/R19 are 22 kOhm module-side idle pull-ups
  to the quick-output-discharged switched rail; R9 is a switched-domain reset
  pull-up; R20/R22 hold both isolated STM32 UART sides idle-high; R21 keeps the
  reset command asserted until firmware deliberately releases it after rail
  settling.
- Why this part: AEC-Q100 Grade 1, -40 to +125 degrees C, 1.65-5.5 V supply,
  5.5 V-tolerant inputs, three-state output, `Ioff` back-drive protection, and
  the already reviewed DBV SOT-23-5 footprint.
- Alternative A: Nexperia `74LVC1G125-Q100`, also Grade 1 with partial-power-
  down `IOFF`, after package and order-code review.
- Alternative B: TI `SN74LVC1G125B-Q1`, after exact suffix, pin-map, and source
  review.
- Operating margin: maximum `Ioff` through each 22.22 kOhm UART clamp is
  0.222 V and through the 10.10 kOhm switched reset pull is 0.101 V, both below
  the nRF52840 powered-off `VDD + 0.3 V` limit. Driven-high pull current is at
  most 0.166 mA versus the buffer's 16 mA guaranteed 3 V drive test point.
- Maximum junction temperature and lifetime: 150 degrees C absolute maximum,
  125 degrees C maximum ambient, and 229 degrees C/W DBV theta-JA. Static
  self-heating is below 0.01 degrees C. The design target is at least 10 years
  with order-date lifecycle and PCN review.
- Availability and assembly: TI marks the family active; DBV SOT-23-5 is a
  normal JLCPCB/PCBWay SMT process. Exact Q1 stock remains a purchase-time or
  consignment recheck.
- Known risks: firmware must wait for rail settling, C32-C34 must be adjacent
  to their buffers, and no alternate may omit powered-off input/output `Ioff`.

## TPS22918-Q1 Switched Peripheral Rails (U12, U13)

- Decision: use two `TPS22918TDBVRQ1` switches for `MICROSD_3V3` and
  `RADIO_SENSOR_3V3`, each with a 1 nF CT capacitor and controlled QOD. BMI270
  VDD uses the switched rail while BMI270 VDDIO/CSB and the I2C pull-ups remain
  on `LB_3V3_IO` to avoid back-power.
- Why this part: AEC-Q100 Grade 2, 1 to 5.5 V input, 2 A rating, 53 mOhm
  typical at 3.3 V, adjustable slew rate, shutdown leakage, and an inspectable
  SOT-23-6 package. It implements the ADR-0012 sleep boundary without direct
  GPIO power switching.
- Alternative A: `TPS22919-Q1`; self-protected and automotive, but its package,
  current limit, timing, and pin map require a non-drop-in schematic review.
- Alternative B: `TPS22954-Q1`; higher-current automotive switch with
  diagnostics, but larger and unnecessary for the 100 mA microSD and 58 mA
  radio/sensor peaks.
- Operating margin: the worst reviewed branch is 100 mA, only 5% of the 2 A
  continuous rating. At 53 mOhm, switch loss is about 0.53 mW at 100 mA.
- Maximum junction temperature: 125 degrees C; qualified ambient operation is
  -40 to +105 degrees C. Placement must preserve the sensor/antenna keepouts.
- Lifetime: expected platform service life is at least 10 years under the
  reviewed current and temperature derating, subject to lot-level PCN review.
- Availability and assembly: TI marks the Q1 part active. JLCPCB/LCSC stock is
  a purchase-time recheck; DBV is supported by the local reviewed SOT-23-6
  footprint and is suitable for JLCPCB/PCBWay optical inspection.
- Risks: QOD configuration and CT value affect power-down and inrush. Firmware
  must wait for the rail settling interval; later bench tests must verify SD
  write interruption and radio reset behavior. QOD also provides the defined
  zero-volt return used by the switched E73 reset pull-up.

## Clock and Service Population

- `ABM8AIG-25.000MHZ-12-2Z-T3` and `ABS07AIG-32.768kHz-7-T` are the preferred
  automotive-temperature clock sources. STM32 internal HSI/LSI operation is
  the degraded-service alternative; qualified 3225 HSE and 3215 LSE crystals
  from another vendor are the second-source path after load-capacitance and ESR
  review.
- `JBT1` is DNP by default. No backup cell chemistry is approved by this
  schematic; only the protected `BACKUP_AON` interface is retained.
- `JDBG1` is a service-only 1.27 mm SWD header. It must not source LB power or
  bypass the no-back-power boundary.

## Production and Field Boundary

The selected parts fit the 229.2 mA sustained and 381.2 mA service-peak
`PB_5V_OUT` allocation. Exact stock, alternates, thermal images, sleep leakage,
and peripheral power-cycle behavior remain lot/prototype checks. No alternative
may be substituted solely because its package fits.
