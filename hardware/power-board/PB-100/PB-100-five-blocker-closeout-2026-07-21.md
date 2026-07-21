# PB-100 Five-Blocker Closeout — 2026-07-21

Status: Closed for the five PBREL pre-layout blockers; schematic freeze and PCB layout remain gated

This record supersedes the former conditional evidence for PBREL-001,
PBREL-004, PBREL-006, PBREL-007, and PBREL-011. It closes decisions and
calculations that can honestly be completed before hardware exists. It does not
claim that post-prototype measurements, assembler quotations, DFM feedback, or
first-article inspection have already happened.

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

Closed by generated `PB-100-input-q1-evidence.csv` and
`PB-100-mosfet-voltage-margin-review.md`. Q1 uses the same exact 80 V TOLL
part. The 2.52 mOhm hot bound gives 4.032 W at 40 A. A 125 degC case ceiling
predicts 126.61 degC junction and 48.39 degC margin to the 175 degC absolute
maximum. A reviewed plane/polygon/bus current path and PB-BENCH-010 are hard
later gates; no trace-only 40 A claim is accepted.

## PBREL-007 — TVS/load-dump protection

Closed by generated `PB-100-transient-margin-evidence.csv`. The bounded source
is 100 V open-circuit, 10/1000 us, 0.3766 ohm. `SM8S33AHM3/I` is adjusted from
53.3 V at 25 degC to 58.15 V at a 125 degC initial junction. A 20 nH loop at
15 A/us adds 0.30 V and a separate 1.00 V model/probe allowance produces
59.45 V stress. Margins are 0.55 V to the LM74700 recommended ceiling, 5.55 V
to its absolute maximum, 20.55 V to the MOSFETs, and 40.55 V to 100 V devices.
Any extracted loop above 20 nH or PB-BENCH-004 result at/above 60 V rejects the
layout/protection branch.

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

The board-release register may report zero active PBREL blockers after this
closeout. PCB layout nevertheless remains `NO-GO` until the separate schematic
freeze checklist, controlled promotion of all value-bearing symbols/passives,
Product Owner approval, and layout-start checklist close. No `.kicad_pcb`,
Gerber, drill, CPL, fabrication ZIP, or PCBA order package is authorized here.
