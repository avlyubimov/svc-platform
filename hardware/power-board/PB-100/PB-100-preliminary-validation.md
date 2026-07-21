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
- IAUT300N08S5N012ATMA2: selected 80 V automotive N-MOSFET, 1.2 mOhm class,
  PG-HSOF-8-1 TOLL, for Q1 and Q101-Q110.
- IAUT300N08S5N014ATMA1 80 V TOLL is the controlled same-footprint
  alternative and BUK7J2R4-80MX 80 V LFPAK56E is deliberately non-drop-in.
  SIDR626LDP and IAUTN06S5N008 60 V evidence is historical and rejected for
  the Rev.1 assembly baseline.
- Active AEC-Q101 SM8S33AHM3-class TVS: 33 V standoff, 53.3 V clamp at
  rated pulse current in the HM3 DO-218AC branch. MCC SM8S33A is EOL evidence
  only and Vishay HE3 is NFD stock-only evidence; neither may be locked.

## Preliminary findings

- TPS48110AQDGXRQ1 plus selected external IAUT300N08S5N012ATMA2 80 V MOSFET is the
  Rev.1 path for all output channels.
- Generated class envelopes close pre-layout SOA and thermal calculations;
  layout extraction and prototype thermal validation remain physical gates.
- OUT2 compressor/inrush planning uses the envelope in
  `hardware/power-board/PB-100/PB-100-out2-soa.md`; the selected IAUT300N08S5N012ATMA2
  is bounded by 30 A for 100 ms, 80 A for 4 ms, and 95.91 A for 5 us.
- LM74700QDBVRQ1-class reverse protection is compatible with the 12 V input
  target and cold-crank requirement when paired with a dedicated low-Rds input
  MOSFET strategy.
- The SM8S33AHM3/I input TVS remains a candidate only. ADR-0016 generated
  `79-101 V`, `0.5-4 ohm`, and `40-400 ms` evidence exposes energy/thermal
  failures and only 2.40 V minimum LM74700 recommended margin. PBREL-007 is
  Open pending a passing protection branch and PB-BENCH-004.
- Active SM8S33AHM3-class input TVS is not automatically compatible with 40 V integrated
  smart switches. ADR-0011 resolves the Rev.1 conflict by moving OUT5, OUT8,
  and OUT9 to the external-controller output architecture.

## Remaining physical gates

- Promote reviewed values into the final value-bearing schematic sheets.
- Confirm extracted clamp-loop inductance does not exceed 20 nH during layout.
- Confirm output and input-MOSFET case temperatures do not exceed 125 degC in
  the intended enclosure during prototype validation.

## Related tables

- `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`
- `hardware/power-board/PB-100/PB-100-out2-soa.md`
- `hardware/power-board/PB-100/PB-100-out2-soa-envelope.csv`
- `hardware/power-board/PB-100/PB-100-thermal-estimates.csv`
- `hardware/power-board/PB-100/PB-100-protection-validation.csv`
