# PB-100 Power And Telemetry Footprint Binding Closeout 2026-07-20

Status: Footprint-binding evidence update

Historical scope note: the two MOSFET package rows listed at the end of this
2026-07-20 record were subsequently closed. The current selected path is
`IAUT300N08S5N012ATMA2` PG-HSOF-8-1 TOLL and the current footprint inventory is
authoritative.

This closeout binds three PB-100 package rows from manufacturer package drawings.
It does not create `PB-100.kicad_pcb`, Gerbers, drill files, pick-place files,
BOM/CPL order packages, manufacturing ZIP files, fabrication packages, panel
outputs, or PCBA orders.

## Scope

| Item | Local footprint | Close result |
|---|---|---|
| Input TVS | `PB100:DO-218AC_Vishay_SM8S` | Vishay DO-218AC mounting pad layout is captured locally |
| Total input current shunt | `PB100:CSS4J-4026_Bourns` | Bourns CSS4J-4026 recommended pad layout is captured locally with separate force and sense pads |
| Optional digital temperature sensor | `PB100:SOT-563-6_DRL_TI` | TMP112-Q1 DRL SOT-563 footprint exists for a DNP optional digital sensor variant |

## Engineering Closeout

- Input TVS: Vishay document 98647 shows the DO-218AC package and mounting pad
  layout for the SM8S automotive TVS class. The local footprint captures the
  9.80 mm by 10.70 mm heatsink pad, 2.15 mm by 2.60 mm lead pad, and 3.35 mm
  pad gap. Polarity, protected-battery creepage, surge heating, large-pad paste,
  and rework remain layout and production gates.
- Total input current shunt: Bourns CSS4J-4026 documentation shows AEC-Q200
  compliance, -55 °C to +170 °C operation, L500 0.5 mΩ / 10 W rating, 2000 h
  load life at 130 °C terminal temperature, and a recommended pad layout with
  10.60 mm overall width, 7.30 mm height, 5.50 mm force-pad gap, 5.60 mm
  force-pad height, and separated sense terminals. At 40 A the 0.5 mΩ class
  dissipates about 0.8 W by I²R before copper-temperature derating.
- Optional digital temperature sensor: TI TMP112-Q1 keeps an automotive DNP
  digital temperature option in SOT-563 DRL. This does not replace the required
  analog NTC thermal points and does not select the optional population variant.

## Decision Rationale

- Why these components: the footprints preserve the accepted TVS, total-current
  telemetry, and optional digital-telemetry capabilities without changing PB-100
  architecture.
- Why not alternatives: alternate TVS, shunt, and TMP117-class packages remain
  valid only after their own package drawings, sourcing, thermal, and production
  reviews.
- Cost impact: no default BOM change; the optional digital sensor remains DNP.
- Thermal impact: no copper or thermal-via sizing is closed. TVS surge heating
  and shunt terminal temperature remain layout and post-prototype gates.
- Production impact: these are factory SMT packages. Polarity, paste strategy,
  solder voiding, high-mass shunt handling, and first-article inspection remain
  PCBA-order gates.
- Field reliability: local manufacturer-derived footprints reduce board-import
  ambiguity while preserving Kelvin sensing and default optional-DNP behavior.
- Known risks: TVS polarity, shunt force/sense polarity, pulse power, solder
  voiding, sourcing stock risk, optional I2C address ownership, and calibration
  are not closed by this footprint-only update.

## Historical state at this closeout

At the time of this record these rows still required package selection; they
are not current blockers:

- TOLL / PG-HSOF-8-1 input-reverse and OUT2 escape MOSFET path.
- Historical LFPAK88 package-evidence path.

Those rows were later closed by exact symbol/footprint and generated evidence.
No PCB layout or manufacturing output is authorized by this historical record.
