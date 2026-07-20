# PB-100 Preliminary Electrical Validation

Status: Schematic-planning input

This document records first-pass validation for PB-100 power-path candidates. It
does not approve schematic freeze or PCB layout.

## Source assumptions

- TPS4811-Q1: 3.5-80 V operating input, 100 V smart high-side driver family,
  external N-MOSFET control, protection and diagnostics.
- TPS2HB35-Q1: 40 V dual-channel smart high-side switch for 12 V automotive
  systems.
- LM74700-Q1: 3.2-65 V automotive ideal-diode controller with external
  N-MOSFET.
- BUK7S1R2-80M: selected 80 V automotive N-MOSFET, 1.2 mOhm class,
  LFPAK88, for Q1 and Q101-Q110.
- IAUTN08S5N012L 80 V TOLL and BUK7J2R4-80M 80 V LFPAK56E are
  non-drop-in alternatives. SIDR626LDP and IAUTN06S5N008 60 V evidence is
  historical and rejected for the Rev.1 assembly baseline.
- Active AEC-Q101 SM8S33AHM3-class TVS: 33 V standoff, 53.3 V clamp at
  rated pulse current in the HM3 DO-218AC branch. MCC SM8S33A is EOL evidence
  only and Vishay HE3 is NFD stock-only evidence; neither may be locked.

## Preliminary findings

- TPS48110AQDGXRQ1 plus selected external BUK7S1R2-80M 80 V MOSFET is the
  Rev.1 path for all output channels.
- Selected LFPAK88 conduction loss is acceptable as a planning input, but SOA
  and thermal validation are still required for compressor inrush and
  steady-state loads.
- OUT2 compressor/inrush planning uses the envelope in
  `hardware/power-board/PB-100/PB-100-out2-soa.md`; the selected BUK7S1R2-80M
  still requires detailed SOA review.
- LM74700QDBVRQ1-class reverse protection is compatible with the 12 V input
  target and cold-crank requirement when paired with a dedicated low-Rds input
  MOSFET strategy.
- Active SM8S33AHM3-class input TVS has 26.7 V nominal datasheet-clamp
  headroom to the selected 80 V MOSFET rating; actual loop overshoot still
  requires reproducible validation.
- Active SM8S33AHM3-class input TVS is not automatically compatible with 40 V integrated
  smart switches. ADR-0011 resolves the Rev.1 conflict by moving OUT5, OUT8,
  and OUT9 to the external-controller output architecture.

## Schematic blockers added

- Validate the low-current TPS48110 plus MOSFET implementation for OUT5, OUT8,
  and OUT9.
- Confirm detailed MOSFET SOA for OUT2 against the defined startup/inrush
  envelope before PCB layout.
- Confirm thermal stack-up for all output classes and the input
  reverse-protection MOSFET in the intended enclosure.

## Related tables

- `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`
- `hardware/power-board/PB-100/PB-100-out2-soa.md`
- `hardware/power-board/PB-100/PB-100-out2-soa-envelope.csv`
- `hardware/power-board/PB-100/PB-100-thermal-estimates.csv`
- `hardware/power-board/PB-100/PB-100-protection-validation.csv`
