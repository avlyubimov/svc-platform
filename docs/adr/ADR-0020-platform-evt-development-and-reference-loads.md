# ADR-0020: Platform EVT development and reference vehicle loads

## Status

Accepted — final Product Owner direction on 2026-07-22

## Context

The project must obtain board-level electrical, thermal, EMC, mechanical and
vehicle evidence without confusing development authorization with production
qualification. PB-100, LB-100 and FB-100 are mature enough for controlled EVT
layout work, but none is ready for production. Several remaining values can be
confirmed only on routed or assembled hardware and therefore cannot remain
preconditions for creating that hardware.

The BMW K25 reference configuration also needs correction. The LOBOO C36 is a
bidirectional battery accessory, not a normal one-way PB-100 output. Four
additional lamps require two independent manual request inputs and controlled
per-pair sequencing. The physical outputs must nevertheless remain generic
`OUT1` through `OUT10`; vehicle roles remain configuration data.

This ADR changes the accepted release process and reference configuration. It
does not change the three-board platform architecture, the 40 A PB-100 product
target, CAN1 read-only default, generic-output rule or capability-driven
firmware architecture.

## Decision

### Unified release states

All main boards use the same ordered states:

1. `EVT-LAYOUT-AUTHORIZED`: schematic import, placement, routing, copper pours
   and layout iteration are allowed.
2. `EVT-FAB-REVIEW`: routing is complete and DRC, connectivity, schematic-board
   parity, safety, DFM and EVT-package review are in progress. Fabrication is
   not yet allowed.
3. `EVT-FAB-AUTHORIZED`: reviewed EVT Gerber, drill, BOM/CPL and assembly
   packages may be generated and a limited prototype order may be placed.
4. `BENCH-VALIDATION`: inspected EVT hardware may be energized on controlled
   bench fixtures.
5. `MOTORCYCLE-VALIDATION`: an undamaged, bench-passed unit may be installed on
   the reference motorcycle.
6. `PRODUCTION-BLOCKED`: EVT validation is complete enough for Rev.2
   disposition, but production remains prohibited while findings,
   qualification or corrected-design review remain open.
7. `PRODUCTION-RELEASE`: the corrected revision has passed required critical
   retests and the Product Owner has accepted production release.

An earlier state always implies `PRODUCTION-BLOCKED` as an independent safety
boundary. The workflow state describes allowed development work; it never
silently authorizes production.

Current board states are:

- PB-100: `EVT-LAYOUT-AUTHORIZED`.
- LB-100: `EVT-LAYOUT-AUTHORIZED`.
- FB-100: `EVT-LAYOUT-AUTHORIZED`, continuing the existing placed-board route.

Calculations or measurements that require a routed or assembled physical board
do not block EVT layout or the limited EVT build. Pre-fabrication checks that
can be completed from the schematic, routed geometry, selected stackup,
datasheets and supplier DFM remain mandatory at `EVT-FAB-REVIEW`.

ADR-0020 supersedes the release-state definitions in ADR-0017 and ADR-0019 and
any active readiness text that uses `BLOCKED`, `LAYOUT-ONLY`, `PROTO-ONLY` or
`PRODUCTION-READY` for a main board. Historical decision records remain
unchanged as history.

### PBREL-007 and Q2-C100

PBREL-007 is a production-release blocker only. It does not prohibit:

- creating `PB-100.kicad_pcb`;
- component placement, routing or copper iteration;
- an EVT Gerber/package after the separate `EVT-FAB-REVIEW` closes;
- fabrication of five PB-100 Rev.1 EVT prototypes;
- controlled bench validation; or
- motorcycle validation after the bench gate.

Q2-C100 remains a paused diagnostic coupon. Its fabrication is optional and is
not a prerequisite for PB-100 EVT layout, EVT fabrication or validation. The
primary qualification vehicle is the complete PB-100 Rev.1 EVT. Qualified Q2
maximum-bound evidence, accepted PB-100 measurements and corrected Rev.2
disposition remain required before `PRODUCTION-RELEASE`.

### PB-100 electrical budget

- Continuous product target: 40 A after EVT validation.
- Main harness fuse target: 50 A near the battery.
- Total-current measurement range: 0-60 A using a 0.5 mOhm four-terminal shunt
  and INA228-class monitor through `IIN_SENSE`/the PB I2C monitor path.
- 50 A and 60 A are fuse/measurement headroom, not continuous product ratings.
- Copper, vias, MOSFETs, fuses, connectors and thermal paths receive design
  margin, but PB-100 is not promoted to a 60 A product without a future ADR and
  accepted EVT evidence.
- `IIN_SENSE` controls the 40 A board budget. Summed `OUTn_IMON` is diagnostic
  cross-check evidence, not the sole budget measurement.

The ten TPS48110 channels retain their accepted electrical limits and current
ranges:

| Output class | Limit | Measurement range |
|---|---:|---:|
| OUT2 | 18 A | 0-30 A |
| OUT1 | 12 A | 0-20 A |
| OUT3, OUT4, OUT6, OUT7, OUT10 | 8 A | 0-15 A |
| OUT5, OUT8, OUT9 | 4 A | 0-8 A |

Every IMON path requires ADC-safe scaling, RC filtering, configuration-owned
zero/gain calibration, stale/plausibility handling, open-load/overload/short
diagnostics and current/trip-reason logging. Missing, stale or implausible
telemetry produces safe-off behavior.

### Reference vehicle role mapping

Hardware and PCB net names remain `OUT1` through `OUT10`. The BMW K25 reference
configuration maps:

- OUT1: cigarette socket and a future compressor limited to 10-12 A.
- OUT2: reserved high-current output up to 18 A.
- OUT3/OUT4: first auxiliary-light pair, marked 80 W pending EVT measurement.
- OUT6/OUT7: second auxiliary-light pair, marked 70 W pending EVT measurement.
- OUT10: reserved medium-current output up to 8 A.
- OUT5/OUT8/OUT9: reserved low-current outputs up to 4 A.

The stock motorcycle headlamp remains on the factory wiring and is not a
PB-100 load. Nameplate lamp wattages are planning data only; actual current is
recorded on EVT hardware.

### Dual manual fog-light requests

Amended by final Product Owner direction on 2026-07-22: replace the single
request with `FOG_A_SW_IN`, `FOG_B_SW_IN` and common `SW_GND` for the owner's
unverified double three-wire handlebar switch. JPB1 pins 82/83 bind through two
independent protected LB paths to STM32H563 PA8/PA9. A sealed three-position
DTM harness connector uses contact 1 `SW_GND`, contact 2 `FOG_A_SW_IN` and
contact 3 `FOG_B_SW_IN`; wire colors remain unassigned until offline
multimeter measurement.

Each input has its own pull-up, series impedance, RC filter, voltage clamp,
automotive Schmitt buffer, debounce and stuck-input diagnostic. The default
assembly is an active-low dry contact. Mutually exclusive DNP components retain
a protected 12 V active-high transistor option if measurement proves the
switch contains electronics or illumination. No external wire connects
directly to an MCU input, and incompatible variants may not be populated
together.

Input A independently requests the configured OUT3/OUT4 reference pair; input
B independently requests the configured OUT6/OUT7 reference pair. The two
requests may coexist. Each pair sequences its two channels with a configurable
delay and disables both channels immediately after a valid off command. Each
input supports `momentary_toggle` and `maintained`; the unverified default is
`momentary_toggle`. Boot, reset, invalid configuration or safety denial clears
requests and requires a held input to return OFF before rearming. A fault or
stuck contact on one input does not suppress the other input's state machine.

The switches create requests only. Output Manager resolves configured roles
and retains current, undervoltage, thermal, telemetry, fault and safe-off
authority. Load shedding removes the OUT6/OUT7 reference pair before OUT3/OUT4.
`SERVICE` and `RESET` are not normal fog controls, and the stock headlamp stays
on the factory loom.

### C36 bidirectional branch

Create capability class `C36_BIDIRECTIONAL`. The LOBOO C36 uses its
manufacturer-defined bidirectional branch directly at the battery/`VBAT_RAW`
through a dedicated near-battery fuse and the required C36 cable. It does not
pass through TPS48110, OUT1 through OUT10, the PB-100 input shunt or a one-way
load switch. Reverse charging must work with PB-100, LB-100 and the MCU off.

C36 is excluded from PB-100 output-current accounting but remains part of the
motorcycle generator-energy budget. Firmware may warn from battery-voltage and
engine-state evidence but cannot claim guaranteed C36 disconnection. EVT shall
measure current in both directions with an external clamp or shunt. Optional
bidirectional C36 monitoring is a Rev.2 consideration and is not a Rev.1
fabrication blocker. C36 is not a starter-current source.

### Operating modes and load shedding

The reference configuration defines `DAY`, `NIGHT`, `SERVICE_COMPRESSOR`,
`C36_RESCUE_CHARGE` and `ENGINE_OFF`. Allowed-role masks prevent mutually
exclusive loads from being summed as a simultaneously permitted operating
case.

- `DAY`: auxiliary lamps off; normal low-power managed loads may operate; C36
  may source a USB device.
- `NIGHT`: the manual request may enable both lamp pairs; the second pair sheds
  first, then the first pair; C36 remains unmanaged and may be used only with
  adequate generator margin.
- `SERVICE_COMPRESSOR`: motorcycle stopped, fog group off, C36 USB load removed,
  only the configured OUT1 socket/compressor role allowed; 10-12 A compressor,
  separate fuse, undervoltage protection and configurable 10-15 minute timer.
- `C36_RESCUE_CHARGE`: all managed PB outputs off while C36 charges the battery
  with PB/LB off.
- `ENGINE_OFF`: managed power outputs off; C36 remains physically available,
  with user guidance preventing unnoticed USB discharge.

Managed shedding order is second fog pair, first fog pair, other managed
outputs, then all OUT1-OUT10 at critical voltage. Inputs are `IIN_SENSE`, all
`OUTn_IMON`, `VBAT_SENSE` and available engine/ignition state. Exact voltage,
delay and RPM thresholds remain configuration values to be established from
the motorcycle manual and EVT logs.

## EVT fabrication and validation

After each required board reaches `EVT-FAB-AUTHORIZED`, order five prototypes.
PB-100 marking remains `PB-100 REV.1 EVT — NOT FOR PRODUCTION` with fixed unit
roles EVT-01 bring-up, EVT-02 current/thermal, EVT-03 destructive fault/surge,
EVT-04 motorcycle and EVT-05 reserve/repair. A stressed or damaged unit is never
installed on the motorcycle.

Bench validation covers ERC/DRC/parity/unconnected checks, current-limited
bring-up, safe-off, all outputs, real lamp currents, ten IMON calibrations,
INA228 calibration, channel-sum versus input-current comparison, both FOG inputs and
pair sequencing, undervoltage/fault shutdown, OUT1 socket, both C36 directions,
10/20/30/40 A thermal points, short/overload/overvoltage and priority shedding.

Motorcycle validation follows only after bench acceptance and covers DAY,
NIGHT, FOG, both lamp pairs, both C36 directions, cranking, idle, manual-defined
control RPM, generator loading, board/harness/connector temperatures,
vibration, fault logs and the compressor after selection. Intentional load dump
or destructive faults are forbidden on the motorcycle.

Rev.1 is permanently non-production. Measurements, waveforms, currents,
temperatures and failures feed Rev.2. Critical tests are repeated on Rev.2
before the Product Owner may approve `PRODUCTION-RELEASE`.

## Alternatives and rationale

### Keep all boards blocked until every value is frozen — rejected

This prevents the physical evidence required to close the remaining values and
turns analysis into a substitute for validation.

### Put C36 on a TPS48110 output — rejected

The one-way managed output can obstruct the required reverse-charge path and
makes rescue charging depend on PB/LB/MCU state.

### Use SERVICE or RESET as the fog control — rejected

It overloads safety/service semantics, creates ambiguous long-term behavior and
does not provide the requested weather-protected handlebar control.

### Hard-code lamp channels in firmware — rejected

It violates generic-output architecture and prevents one firmware image from
supporting approved assembly and vehicle-profile variants.

## Lifetime, margin, sourcing and risks

- Expected platform lifetime remains 10-15 years.
- Existing semiconductor junction limits and automotive qualifications remain
  governed by their component decision records; this ADR creates no new
  production qualification claim.
- Connector, switch, ESD, filter and harness selections require at least two
  documented alternatives and JLCPCB/PCBWay or garage-assembly review before
  their applicable EVT fab package closes.
- C36 vendor cable/fuse requirements and live availability must be rechecked at
  order and installation time.
- Main risks are generator overload, lamp inrush, false switch activation,
  telemetry saturation, unseen C36 drain and damage from abnormal tests. The
  mode matrix, staged pair start, safe-off rules, external C36 fuse and fixed
  EVT unit allocation mitigate them.

## Review authority

The project has one developer. Product Owner approval plus a documented Codex
technical review satisfies independent technical review gates. A second human developer is not required.
This does not waive calculations, machine checks,
bench evidence, raw data, reproducibility or final Product Owner approval.

## Consequences

- PB-100 and LB-100 layout may start immediately; FB-100 routing continues.
- Physical-board-only evidence moves to bench or production qualification.
- EVT manufacturing remains separately gated by `EVT-FAB-REVIEW`.
- Q2-C100 no longer controls the PB-100 prototype schedule.
- C36 remains bidirectional and outside the managed PB output current.
- Four auxiliary lamps receive two independent, safe, configurable manual requests.
- Production remains blocked until Rev.2 correction, critical retest and Product
  Owner approval.
