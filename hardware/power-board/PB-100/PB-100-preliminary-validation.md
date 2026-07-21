# PB-100 Preliminary Electrical Validation

Status: Schematic-planning input

This document records first-pass validation for PB-100 power-path candidates. It
does not approve schematic freeze or PCB layout.

## Source assumptions

- TPS4811-Q1: 3.5-80 V operating input, 100 V smart high-side driver family,
  external N-MOSFET control, protection and diagnostics.
- TPS2HB35-Q1: 40 V dual-channel smart high-side switch for 12 V automotive
  systems.
- LM74930-Q1: automotive back-to-back ideal-diode/surge-stopper controller
  selected for hard overvoltage cutoff.
- IAUTN15S6N025ATMA1: selected 150 V automotive TOLL raw-side cutoff MOSFET.
- IAUT300N08S5N012ATMA2: selected 80 V automotive N-MOSFET, 1.2 mOhm class,
  PG-HSOF-8-1 TOLL, for Q1 and Q101-Q110.
- IAUT300N08S5N014ATMA1 80 V TOLL is the controlled same-footprint
  alternative and BUK7J2R4-80MX 80 V LFPAK56E is deliberately non-drop-in.
  SIDR626LDP and IAUTN06S5N008 60 V evidence is historical and rejected for
  the Rev.1 assembly baseline.
- SM8S33AHM3/I is retained DNP only. The earlier single-TVS model fails the
  ISO energy/thermal envelope and is not the approved Rev.1 protection branch.

## Preliminary findings

- TPS48110AQDGXRQ1 plus selected external IAUT300N08S5N012ATMA2 80 V MOSFET is the
  Rev.1 path for all output channels.
- Generated class envelopes close pre-layout SOA and thermal calculations;
  layout extraction and prototype thermal validation remain physical gates.
- OUT2 compressor/inrush planning uses the envelope in
  `hardware/power-board/PB-100/PB-100-out2-soa.md`; the selected IAUT300N08S5N012ATMA2
  is bounded by 30 A for 100 ms, 80 A for 4 ms, and 95.91 A for 5 us.
- LM74930QRGERQ1 drives common-source Q2/Q1 devices and hard-disconnects the
  load at a generated `48.99-54.89 V` threshold across tolerance and leakage.
- The raw-side IAUTN15S6N025ATMA1 model covers the `79-101 V`, `0.5-4 ohm`,
  and `40-400 ms` envelope at 25/125/150 degC initial junction temperature.
  Seven-microsecond deglitch is fully enhanced; the separate 0.31 us Qgd
  transition gives a provisional 2.08x SOA screen at 150 degC. Q2 hot
  conduction loss is 7.200 W and requires a post-layout full thermal path no
  worse than 3.47 K/W. A qualified maximum-bound trajectory is still required
  before layout; final loop overshoot and dynamic SOA remain post-layout, with
  PB-BENCH-004 later.
- A populated SM8S33AHM3-class input TVS is not automatically compatible with 40 V integrated
  smart switches. ADR-0011 resolves the Rev.1 conflict by moving OUT5, OUT8,
  and OUT9 to the external-controller output architecture.

## Remaining physical gates

- Promote reviewed values into the final value-bearing schematic sheets.
- Extract common-source loop inductance, protected-rail overshoot, Q2 dynamic
  SOA, and Q1 full passive thermal path during layout review.
- Confirm Q1 stays at or below 150 degC at 40 A and 125 degC ambient with a
  complete passive path no worse than 6.20 K/W during PB-BENCH-010.

## Related tables

- `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`
- `hardware/power-board/PB-100/PB-100-out2-soa.md`
- `hardware/power-board/PB-100/PB-100-out2-soa-envelope.csv`
- `hardware/power-board/PB-100/PB-100-thermal-estimates.csv`
- `hardware/power-board/PB-100/PB-100-protection-validation.csv`
