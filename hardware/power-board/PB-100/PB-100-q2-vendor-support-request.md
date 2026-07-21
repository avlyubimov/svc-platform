# PB-100 Q2 Maximum-Bound Qualification Request

Status: `SENT` 2026-07-21 — awaiting response

## Purpose

Obtain manufacturer-supported maximum-bound turn-off evidence for
`IAUTN15S6N025ATMA1` before PBREL-007 may authorize `LAYOUT-ONLY`. The request
does not change the accepted LM74930-Q1 hard-cutoff architecture, selected
MOSFET, passive cooling decision, schematic, or post-layout/prototype gates.

## Public Evidence Audit

- The Infineon datasheet gives maximum `Qgd = 40 nC` and `Qgs = 52 nC`, but
  specifies the gate-charge condition at 75 V / 123 A and marks the dynamic
  values as specified by design rather than production tested.
- The public SOA plot supports a preliminary screen, but does not provide a
  guaranteed time-correlated `VDS(t)` / `ID(t)` envelope from an initial
  junction temperature of 150 degC.
- Infineon's official power-MOSFET simulation guidance says its simulation
  models represent typical devices and cannot replace hardware evaluation.
  A typical SPICE run therefore cannot be promoted to a production maximum.
- The TI LM74930-Q1 model can evaluate controller behavior, but cannot qualify
  the selected Infineon Q2 across Infineon process and temperature corners.
- AEC-Q101 qualification or a product qualification report alone does not
  establish the requested switching trajectory.

## Circuit and Corner

- Q2 orderable part: `IAUTN15S6N025ATMA1`, 150 V TOLL.
- Controller: `LM74930QRGERQ1`, hard overvoltage cutoff.
- Q2 orientation: drain at `VBAT_RAW`, source at `INPUT_COMMON_SOURCE`, gate
  connected directly to `HGATE`; no external gate resistor or CdV/dt capacitor
  is populated in the current pre-layout schematic.
- Conservative qualification corner: raw drain supply 101 V, drain current
  initially 40 A, and initial Q2 junction temperature 150 degC.
- Initial `VGS` range: 10.0-14.5 V from the LM74930-Q1 specified HGATE drive
  range. The bound must cover the gate-charge maximum over that range.
- Turn-off drive: at least the LM74930-Q1 minimum 128 mA HGATE sink current.
- The maximum 7 us OV deglitch is a separate fully-enhanced interval and must
  not be added to the linear-mode switching interval.
- Repetition: ten load-dump events with 60 s spacing. The application permits
  complete load disconnection during the surge.

## Requested Infineon Evidence

Please provide one of the following for the exact orderable device and corner:

1. A written maximum-bound time-correlated `VDS(t)` and `ID(t)` turn-off
   trajectory, including maximum Miller `VDS`-rise time and maximum
   post-Miller `ID`-fall time; or
2. An Infineon-approved corner model and qualification procedure that produces
   the same maximum-bound trajectory.

The response needs to identify:

- the time origin and initial electrical state;
- maximum gate-discharge charge or equivalent bound at 101 V / 40 A /
  150 degC initial `Tj` and 10.0-14.5 V initial `VGS`;
- the residual-current criterion defining completion of `ID` fall;
- process, temperature, and lot coverage and any applied guardband;
- confirmation that the complete trajectory is inside linear-mode SOA at
  150 degC initial `Tj`, including the acceptable repeated-pulse condition;
- the document, case, model revision, or FAE-response identifier that may be
  cited as application qualification evidence.

A typical-only SPICE result, a charge value at another operating point without
a valid scaling bound, an avalanche-energy comparison, or an SOA plot without
a time-correlated trajectory will remain supporting evidence only.

## Acceptance Contract

PBREL-007 pre-layout can close only after Q2Q-010 through Q2Q-016 in
`PB-100-q2-maximum-bound-qualification.csv` are populated from a traceable
Infineon artifact and independently reviewed. The accepted artifact must prove
the full paired trajectory, not merely separate scalar timing estimates.

If Infineon cannot provide a production maximum, the Product Owner must approve
a separate component-level qualification plan defining sample count, lot
coverage, instrumentation bandwidth, 150 degC preconditioning, guardband, and
post-stress parametric acceptance. Such testing would be empirical project
qualification, not a manufacturer production-maximum claim.

Until acceptance, PBREL-007 remains `Conditional`, aggregate PB-100 remains
`BLOCKED`, and no `PB-100.kicad_pcb`, prototype manufacturing package,
production release, or field release is authorized.

## Email Draft

**To:** `support@infineon.com`

**Subject:** IAUTN15S6N025ATMA1 maximum turn-off trajectory / hot SOA qualification request

Hello Infineon Automotive MOSFET Applications team,

We are evaluating IAUTN15S6N025ATMA1 as the raw-side cutoff MOSFET in an
LM74930-Q1 automotive surge-stopper. We need manufacturer-supported
maximum-bound turn-off evidence for a pre-layout safety review.

The conservative corner is 101 V raw drain supply, 40 A initial drain current,
150 degC initial junction temperature after continuous-current heating,
10.0-14.5 V initial VGS, and at least 128 mA gate sink. The controller's maximum
7 us overvoltage deglitch is treated separately while the MOSFET remains fully
enhanced. The use case permits complete load disconnection and requires ten
events at 60 s spacing.

Could you provide either a maximum-bound time-correlated VDS(t)/ID(t)
trajectory, including maximum Miller VDS-rise and post-Miller ID-fall time, or
an Infineon-approved corner model and qualification method for this exact
condition? Please identify process/temperature/lot coverage, guardband, the
residual-current criterion, and whether the resulting trajectory is within
linear-mode SOA from 150 degC initial Tj.

The public maximum Qgd/Qgs values are specified at 75 V / 123 A and are marked
as design values, so we do not want to misuse them as a qualified maximum at
101 V / 40 A. A traceable case, document, model revision, or FAE statement that
we can cite in the design evidence would be appreciated.

Please route this request to the Automotive MOSFET applications or product
engineering team if needed.

Best regards,
SVC Platform project

## Official Sources

- Infineon Q2 datasheet:
  https://www.infineon.com/assets/row/public/documents/10/49/infineon-iautn15s6n025-datasheet-en.pdf
- Infineon power-MOSFET simulation-model application note:
  https://www.infineon.com/assets/row/public/documents/24/42/infineon-applicationnote-powermosfet-simulationmodels-applicationnotes-en.pdf
- Infineon support entry point: https://www.infineon.com/support
- TI LM74930-Q1 datasheet: https://www.ti.com/lit/ds/symlink/lm74930-q1.pdf
