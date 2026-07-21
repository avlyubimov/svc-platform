# FB-100 Value-Bearing Component Decision Record

Status: Accepted for Rev.1 schematic and prototype layout input
Decision date: 2026-07-21

This record implements the frozen 24-pin JFB1 contract. It does not authorize
fabrication or production release.

## LTC3212 One-Wire RGB Driver (U1)

- Decision: use `LTC3212EDDB#TRPBF` to translate the single approved
  `STATUS_RGB_DATA` signal into three regulated cathode currents for the
  common-anode Everlight RGB LED.
- Why this part: it accepts 2.7 to 5.5 V, supports one-wire pulse programming,
  provides three current sinks plus a 1x/2x charge pump, and remains in
  production. It preserves the frozen JFB1 pinout without adding I2C or three
  direct RGB signals.
- Alternative A: a one-wire smart RGB LED such as a WS2812/SK6805 class part.
  It reduces part count but is not automotive-qualified, has protocol and
  quiescent-current variation, and would replace the already sourced discrete
  LED footprint; it is not an approved substitution.
- Alternative B: an automotive multi-channel I2C LED driver such as a
  `LP5562`-class device. It offers richer diagnostics but needs SDA/SCL across
  JFB1 and therefore requires an ADR and connector-contract change.
- Operating margin: `R16 = 35.7 kOhm` programs green near 4.97 mA. With ISETR
  and ISETB tied to VIN as the datasheet permits, worst white-mode current is
  approximately 13.2 mA total. This is far below the 25 mA continuous rating
  per output and is included in the 35 mA FB UI rail allocation.
- Maximum junction temperature: 125 degrees C; specified operation is only
  -40 to +85 degrees C and theta-JA is 76 degrees C/W. This is not an
  automotive-qualified part. At less than 0.12 W conservative dissipation the
  estimated rise is below 10 degrees C, but prototype enclosure temperature
  must be measured before field release.
- Lifetime: expected prototype service target is at least 10 years only if the
  measured FB enclosure temperature remains within the 85 degrees C operating
  limit. Production use requires annual lifecycle/PCN review or qualification
  of an automotive replacement.
- Availability and assembly: ADI marks the part Production. LCSC `C684295`
  identifies the exact DFN-12-EP package but was out of stock at the 2026-07-21
  review; JLCPCB direct-library availability was not proven. Consignment or
  distributor sourcing is required for prototypes. The exposed-pad footprint
  uses segmented paste and requires AOI/X-ray process review.
- Known risks: non-automotive qualification, 85 degrees C operating ceiling,
  single-source lifecycle, and one-wire timing. These do not remove the status
  function; they remain explicit prototype/production release risks.

## Discrete Indicators, USB, and Controls

- Channel indicators use `KT-0805Y` with 1 kOhm series resistors. At 3.6 V and
  a conservative 1.7 V LED drop, current remains below 1.9 mA. Alternative
  0603/0805 colors remain allowed only after brightness and light-pipe review.
- Status LED is `19-237/R6GHBHC-A01/2T`, common anode. Alternatives are other
  pin-compatible Everlight 19-237 common-anode bins or a reviewed smart RGB
  implementation; polarity must never be inferred from package size.
- USB-C remains device-only with two independent 5.1 kOhm Rd resistors,
  USBLC6-2SC6 ESD protection, and a 100 kOhm/27 kOhm VBUS sense divider.
  `USB_VBUS` has no connection to `FB_3V3_OR_IO`.
- SERVICE and RESET use the sourced Panasonic switch class with 10 kOhm pulls
  and 100 nF debounce capacitors. RESET reaches LB `NRST` through the reviewed
  0 Ohm link; neither button can enable PB outputs.
- The OLED connector is DNP by default and uses a replaceable four-wire module
  header. Direct-solder OLED footprints remain alternatives only after window,
  pinout, and assembly review.

## Production and Field Boundary

USB, UI, and connector topology is closed for schematic/layout input. LTC3212
temperature and sourcing, optical fit, button actuator stack, FFC orientation,
and actual enclosure temperature remain prototype or manufacturing-release
checks. No manufacturing output is authorized by this decision record.
