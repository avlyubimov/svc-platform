# PB-100 Five-Blocker Closeout — 2026-07-21

Status: Historical record; PBREL-006 is Conditional and PBREL-007 is reopened by ADR-0016

This record preserves the reasoning used by PR #34. ADR-0016 supersedes its
PBREL-006/PBREL-007 conclusions after corrective review found that the
10/1000 us model did not cover ISO 16750-2 load-dump duration, TVS energy, or
transient thermal behavior. PBREL-001, PBREL-004, and PBREL-011 remain closed.

## PBREL-001 — CAN1 safety policy

Closed by `PB-100-can1-physical-closeout.md` plus exported-netlist topology
validation. The PB-owned TJA1051, ESD, optional 120 ohm termination, physical
OE pull/readback, dual DNP links, silent-mode default, RX-only independence,
and exact DTM04-4P/DTM06-4S harness kit are defined. PB-BENCH-012 remains the
post-prototype release test.

## PBREL-004 — high/medium output stage

Closed by generated `PB-100-output-soa-evidence.csv`,
`PB-100-output-stage-design-values.csv`, and `PB-100-out2-soa.md`.
Q101-Q110 use active/preferred `IAUT300N08S5N012ATMA2` 80 V TOLL. The accepted
per-fuse-class Rsense, RIWRN, RISCP, CTMR, RIMON, bootstrap, OV/UVLO, gate, and
local `STPS40170CGY-TR` clamp values are explicit. OUT2 uses 30 A / 100 ms and
80 A / 4 ms fully-enhanced envelopes; the 95.91 A short threshold is below the
conservative 10 us / 60 V SOA current bound. Gate waveform, case temperature,
and actual load pulse measurements remain post-layout/prototype acceptance.

## PBREL-006 — input reverse protection

Conditional by generated `PB-100-input-q1-evidence.csv` and
`PB-100-mosfet-voltage-margin-review.md`. Q1 uses the same exact 80 V TOLL
part. The 2.52 mOhm hot bound gives 4.032 W at 40 A. A 125 degC case ceiling
predicts 126.61 degC junction and 48.39 degC margin to the 175 degC absolute
maximum, but that calculation assumes rather than proves a 125 degC case.
PBREL-006 remains Conditional overall. Its pre-layout stage is closed and may
advance this blocker to `LAYOUT-ONLY`; layout copper/thermal extraction must
close the `PROTO-ONLY` transition and PB-BENCH-010 must close its prototype-
qualification transition. No trace-only 40 A production claim is accepted.

## PBREL-007 — TVS/load-dump protection

Open by ADR-0016. The former 100 V, 10/1000 us, 0.3766 ohm calculation produced
59.45 V and only 0.55 V to the LM74700 recommended ceiling; it is retained as
rejected historical evidence, not a closeout. The replacement model covers
ISO 16750-2 `79-101 V`, `0.5-4 ohm`, and `40-400 ms`, and calculates TVS
current, energy, transient thermal impedance, tolerances, and self-heating.
The current SM8S33AHM3/I candidate fails multiple corners, including the
101 V / 0.5 ohm / 400 ms hot corner, so PBREL-007 remains `BLOCKED` at its
pre-layout stage. A passing protection selection permits only `LAYOUT-ONLY`;
clamp-loop extraction then permits `PROTO-ONLY`, and PB-BENCH-004 closes the
blocker-specific prototype qualification.

## PBREL-011 — factory assembly readiness

Closed for pre-layout source/process evidence by
`PB-100-factory-production-evidence.csv` and synchronized BOM/source tables.
The exact orderable MOSFET is tape-and-reel MSL1 and planned active availability
through at least 2038. The source path is JLC global/preorder/private-part
consignment or PCBWay kitted/consigned assembly; no live-stock claim is made.
TOLL segmented paste, SPI/AOI, polarity, MSL, solder-void/rework, DNP-link and
first-article controls are specified. Actual quote, job-specific DFM response,
stencil approval, order-date stock/lifecycle recheck, and FAI remain production
release gates.

## Alternatives and rejection evidence

- Same-footprint alternative: `IAUT300N08S5N014ATMA1`, active/preferred 80 V
  TOLL, subject to repeated electrical/thermal review.
- Non-drop-in alternative: production `BUK7J2R4-80MX`, 80 V LFPAK56E, subject
  to footprint/thermal/factory review.
- Rejected: preliminary `BUK7S1R2-80M` LFPAK88 and all former 60 V paths.

## Boundary

This historical record does not itself authorize layout or manufacturing. The
board-release register has two active PBREL rows after corrective review:
PBREL-006 is Conditional and PBREL-007 is Open. ADR-0017 and
`PB-100-staged-release-readiness.csv` remove the process deadlock, but aggregate
PB authorization remains `BLOCKED` because PBREL-007 has no passing pre-layout
branch. No `.kicad_pcb`, Gerber, drill, CPL, fabrication ZIP, or PCBA order
package is authorized by the current state.
