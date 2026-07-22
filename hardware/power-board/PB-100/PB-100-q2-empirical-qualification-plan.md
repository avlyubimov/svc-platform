# PB-100 Q2 Empirical Qualification Plan

Status: `PAUSED DIAGNOSTIC OPTION / RESULTS PENDING`

Date: 2026-07-21

## Purpose and Classification

This plan retains `IAUTN15S6N025ATMA1` as the raw-side 150 V Q2 selected by
ADR-0018 and obtains the missing Q2Q-010 through Q2Q-015 evidence by controlled
measurement. The results will be project-specific empirical qualification;
they must never be described as an Infineon production maximum.

ADR-0019 removes this coupon from the PB-100 Rev.1 EVT critical path. Q2-C100
is retained unchanged as an optional diagnostic artifact and further design or
fabrication work is paused unless a reviewed PB-100 failure investigation
requires isolated Q2 evidence.

The Product Owner allowed replacement only if a replacement closes the
evidence gap, otherwise physical qualification of the selected device. The
replacement audit found no credible automotive 150 V candidate with the
required public maximum-bound paired hot trajectory. The engineering route is
therefore to retain and test the selected device.

## Authorization Boundary

The following temporary state is defined:

`QUALIFICATION-COUPON-ONLY`

When explicitly resumed it permits schematic capture, PCB layout, fabrication and bench use of a
dedicated Q2 qualification coupon whose only purpose is generating the evidence
defined here. It does not authorize a `PB-100.kicad_pcb`, PB-100 placement or
routing, PB-100 manufacturing output, production release or field use. ADR-0019
separately authorizes PB-100 Rev.1 EVT layout and a later reviewed five-board
EVT package. Coupon results cannot waive the later PB-100 extracted-loop,
thermal-path or PB-BENCH-004 production gates.

## Frozen Qualification Corner

- DUT: exact orderable `IAUTN15S6N025ATMA1`.
- Application controller: `LM74930QRGERQ1` in hard overvoltage cutoff.
- Raw drain supply during the qualification trajectory: `101 V`.
- Initial drain current: `40 A`.
- Initial Q2 junction temperature: `150 degC`.
- Initial VGS endpoint coverage: `10.0 V` and `14.5 V`.
- Gate discharge: no populated external series resistor and no populated
  CdV/dt capacitor; the worst-case discharge stimulus must be no stronger than
  the LM74930-Q1 guaranteed `128 mA` minimum HGATE sink.
- Controller OV deglitch: evaluated separately at its `7 us` maximum while Q2
  remains fully enhanced; it is not added to the linear-mode interval.
- Repetition: ten accepted events per qualification DUT with `60 s` between
  events.
- Complete load disconnection is allowed.

Any change to these conditions requires a reviewed plan revision. Testing a
less severe corner cannot close the gate.

## Coupon Electrical and Mechanical Contract

The qualification coupon shall provide:

1. The exact Q2 TOLL footprint and the exact LM74930-Q1 RGE footprint.
2. A direct baseline HGATE-to-Q2-gate path with no populated Rg or CdV/dt.
   Optional DNP experiment sites must be isolated from the accepted baseline
   configuration and their use cannot qualify the production path.
3. Short, low-inductance drain/source and gate loops with documented copper,
   stackup and connector geometry. The coupon is not allowed to hide ringing
   with unrecorded snubbers or bandwidth limiting.
4. Kelvin probe points for Q2 gate, source and drain; controller HGATE and OUT;
   raw supply; protected/source node; and the trigger/fault signal.
5. Drain-current measurement outside the common-source gate-return path using a
   calibrated wideband current probe or low-inductance coaxial shunt.
6. A local controllable Q2 heating interface while LM74930-Q1 remains within
   its specified temperature range.
7. Per-DUT temperature-sensitive electrical-parameter calibration, preferably
   low-current body-diode forward voltage, so the initial 150 degC junction
   condition is measured rather than inferred only from heater temperature.
8. Hardware current limiting, discharge paths, interlock, shield and remote
   trigger suitable for the stored energy. Fixture operation requires a
   written laboratory safety review; this repository approval is not an
   authorization to energize unsafe equipment.

The coupon schematic, layout, stackup, BOM, assembly variant and calibration
record must be committed before test data is accepted.

## Instrumentation Contract

- Simultaneous acquisition of `VDS(t)`, `ID(t)` and `VGS(t)` from one trigger.
- Oscilloscope analog bandwidth at least `200 MHz` and sample rate at least
  `1 GS/s` on every active channel.
- Differential VDS probe rated at least `200 V`, bandwidth at least `100 MHz`,
  and verified common-mode behavior at the test edge rate.
- Current channel bandwidth at least `50 MHz`, range at least `50 A`, and total
  uncertainty/resolution sufficient to distinguish `1.0 A` residual current.
- Gate probe bandwidth at least `100 MHz` with capacitance included in the
  recorded fixture loading budget.
- Probe deskew to the current channel and end-to-end amplitude calibration
  before and after each test day.
- Raw waveform export in a lossless numeric format with calibration IDs,
  sample ID, lot/date code, controller ID, fixture revision, temperatures,
  supply setting and software revision. Screenshots alone are not evidence.
- Measurement uncertainty must be propagated into every reported timing,
  voltage, current, energy and SOA margin. Uncertainty may not be subtracted
  from a worst-case result.

## Sample and Lot Plan

### Phase A — engineering characterization

- Five Q2 devices from one authorized-distributor lot/date code.
- Characterize both VGS endpoints, the 128 mA sink representation, probe
  loading, fixture ringing and temperature calibration.
- Correlate the controlled sink representation with actual LM74930-Q1 HGATE
  turn-off over controller temperature. If the 128 mA specification cannot be
  shown to conservatively represent the complete discharge waveform, Phase B
  is blocked until the fixture uses a demonstrated slower controller corner or
  a reviewed equivalent.
- Phase A can refine the test procedure but cannot close Q2Q-010 through
  Q2Q-015 and its devices cannot be counted in Phase B.

### Phase B — qualification

- Thirty new Q2 devices: ten devices from each of at least three independent
  semiconductor lot/date codes obtained through authorized distribution.
- In each lot, five devices are tested from 10.0 V initial VGS and five from
  14.5 V initial VGS. Each device receives ten events at 60 s spacing.
- Controller coverage uses at least three LM74930-Q1 lot/date codes across the
  thirty pairings where sourcing permits. If three controller lots cannot be
  obtained, the missing coverage is recorded and separately approved before
  Phase B begins.
- No failed sample may be replaced, omitted or retested into a pass. Any test
  interruption is dispositioned before continuing and all raw acquisitions
  remain in the evidence set.

If three independent Q2 lots are unavailable, the gate remains blocked. A
reduced-lot program requires an explicit Product Owner exception and cannot be
silently treated as equivalent production coverage.

## Event Sequence

For every Phase B DUT:

1. Record identity, package marking, source, lot/date code and incoming visual
   inspection.
2. Measure baseline V(BR)DSS, IDSS, IGSS, VGS(th) and pulsed RDS(on) using the
   datasheet conditions where practical; record any justified equivalent.
3. Calibrate the DUT temperature-sensitive parameter at 25, 125 and 150 degC.
4. Establish 40 A fully-enhanced current and verify the initial 150 degC
   junction condition immediately before the event.
5. Establish the required 101 V raw-drain condition and initial VGS endpoint,
   then trigger the reviewed conservative gate-discharge stimulus.
6. Capture synchronized VDS, ID and VGS from before the trigger until current
   reaches the residual-current criterion and all relevant ringing has settled.
7. Calculate transition intervals, peak VDS, time-correlated SOA locus and
   integral of VDS multiplied by ID. Energy is supporting information, not a
   replacement for SOA acceptance.
8. Confirm safe discharge, wait 60 s, and repeat for ten total events.
9. Repeat baseline parametric measurements after the tenth event and inspect
   the device/coupon for damage.

Separate controller-correlation runs shall apply the realistic 5-10 ms input
rise and verify the maximum 7 us OV deglitch while Q2 is fully enhanced. These
runs do not substitute for the 101 V / 40 A paired-trajectory qualification.

## Waveform Definitions

- Time zero: first sustained downward crossing of 90% of initial VGS after the
  turn-off command, with a documented debounce/noise rule.
- VDS-rise completion: first sustained crossing of 90% of the final settled
  VDS.
- Miller VDS-rise interval: from the start of sustained VDS rise above 10% to
  VDS-rise completion.
- ID-fall completion: first sustained crossing below
  `max(1.0 A, 3 x current-channel uncertainty)`.
- Complete linear transition: from the start of sustained VDS rise above 10%
  until ID-fall completion.
- Every threshold is calculated from raw numeric data using a versioned script;
  hand-positioned oscilloscope cursors are supporting evidence only.

## Acceptance Criteria

All thirty Phase B devices and all 300 qualification events must pass:

1. Complete transition plus timing uncertainty must be `<= 0.80 us`, so a
   `1.25x` project timing guardband remains within the existing 1 us hot-SOA
   reference screen.
2. Peak VDS plus measurement uncertainty must be `<= 120 V`, retaining at
   least 30 V to the 150 V absolute rating in the coupon test.
3. The uncertainty-expanded and 1.25x-guardbanded time-correlated VDS/ID locus
   must remain inside the temperature-derated datasheet SOA with at least
   `1.5x` current margin at every evaluated sample. The exact digitization and
   temperature-derating algorithm must be committed and independently checked.
4. No event may show thermal instability, secondary-breakdown signature,
   uncontrolled oscillation, avalanche entry, or failure to reach the residual
   current criterion.
5. Post-stress V(BR)DSS, IDSS and IGSS remain within datasheet limits.
6. Post-stress pulsed RDS(on) remains within the datasheet limit and increases
   no more than 5% from that DUT's temperature-corrected baseline.
7. VGS(th) remains within its datasheet range and shifts no more than 0.10 V
   from that DUT's baseline after measurement uncertainty.
8. No package, solder-joint or coupon damage is visible, and pre/post
   calibration checks remain valid.

Any single failure keeps Q2Q-010 through Q2Q-015 open, blocks PBREL-007 and
triggers failure analysis. Acceptance criteria are not relaxed after observing
the data; a revision requires a documented engineering rationale and Product
Owner approval followed by a new qualification population.

## Required Evidence Package

- Coupon KiCad source, fabrication outputs, assembly record and photographs.
- Authorized-distributor and lot/date-code traceability for every DUT and
  controller.
- Instrument model, serial number, calibration date and probe deskew record.
- Temperature calibration data and initial Tj evidence for every event.
- Raw numeric VDS/ID/VGS acquisitions for all events.
- Versioned analysis script and immutable result manifest with file hashes.
- Per-event result CSV plus worst-case overlay and SOA calculation.
- Incoming and post-stress parametric data.
- Deviation, interruption and failure-analysis records.
- Documented Codex independent technical review sign-off and Product Owner
  acceptance; no second developer is required.

### Independent Technical Review Authority

For `Q2E-012`, a documented Codex review of the committed evidence package is
the required independent technical review for this owner-operated project. The
review record must cover the setup, calibration, lot trace, raw-data integrity,
analysis script, result reproducibility, deviations and acceptance criteria
before Product Owner acceptance. No second developer or external reviewer is
required. Machine validation and Product Owner acceptance remain mandatory and
are not replaced by the Codex review.

Only after this package passes may Q2Q-010 through Q2Q-015 be changed to
`PASS EMPIRICAL`, Q2Q-018 be closed, and PBREL-007 advance toward
`PRODUCTION-RELEASE`. It does not control `EVT-LAYOUT-AUTHORIZED` or
`EVT-FAB-AUTHORIZED`. MyCases may remain active in parallel; a later qualifying
Infineon artifact may supersede or reduce future lot testing only after review.

## Current State

The paused Q2-C100 diagnostic schematic, preliminary four-layer PCB, complete pad-to-
pad electrical routing, BOM, assembly variants, probe interfaces and
fabrication gate now exist under `qualification/Q2-C100`. KiCad 10.0.4 ERC and
board DRC have zero violations and zero unconnected items. Exact board headers
and board test points are selected, but fabrication review, 2.0 mm header fit,
the manufacturing package, rated instrument/probe hardware, remaining fixture
hardware and the complete laboratory safety system remain open. No DUT lot
population, calibrated setup or test
result exists yet. Q2Q-010 through Q2Q-015 therefore remain
`PENDING EMPIRICAL` and PBREL-007 remains `Conditional` for production. ADR-0019
places PB-100 at `EVT-LAYOUT-AUTHORIZED`; Q2-C100 fabrication remains paused
and production/general field use remain `NO-GO`.
