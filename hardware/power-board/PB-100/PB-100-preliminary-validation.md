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
- SIDR626LDP-T1-RE3: 60 V N-MOSFET, 2.1 mOhm max at VGS = 4.5 V, PowerPAK
  SO-8DC.
- IAUTN06S5N008: 60 V automotive N-MOSFET, 0.76 mOhm max at VGS = 10 V, TOLL.
- BUK7S1R2-80M: 80 V automotive N-MOSFET, 1.2 mOhm class, LFPAK88.
- Active AEC-Q101 SM8S33AHE3-class TVS: 33 V standoff, 53.3 V clamp at
  rated pulse current. MCC SM8S33A is EOL evidence only and must not be locked.

## Preliminary findings

- TPS48110AQDGXRQ1 plus external 60 V MOSFET remains the preferred path for
  all Rev.1 output channels.
- SIDR626LDP-class MOSFET conduction losses are acceptable as a starting point,
  but SOA and thermal validation are still required for compressor inrush and
  heated-seat steady state.
- OUT2 compressor/inrush planning uses the envelope in
  `hardware/power-board/PB-100/PB-100-out2-soa.md`; SIDR626LDP remains a
  candidate only if detailed SOA review passes.
- LM74700QDBVRQ1-class reverse protection is compatible with the 12 V input
  target and cold-crank requirement when paired with a dedicated low-Rds input
  MOSFET strategy.
- Active SM8S33AHE3-class input TVS is compatible with 60 V MOSFET planning but leaves
  limited voltage margin against 60 V absolute maximum ratings.
- Active SM8S33AHE3-class input TVS is not automatically compatible with 40 V integrated
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
