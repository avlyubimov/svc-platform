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
- SM8S33A-class TVS: 33 V standoff, 53.3 V clamp at rated pulse current.

## Preliminary findings

- TPS48110AQDGXRQ1 plus external 60 V MOSFET remains the preferred path for
  high-current and medium-current channels.
- SIDR626LDP-class MOSFET conduction losses are acceptable as a starting point,
  but SOA and thermal validation are still required for compressor inrush and
  heated-seat steady state.
- LM74700QDBVRQ1-class reverse protection is compatible with the 12 V input
  target and cold-crank requirement.
- SM8S33A-class input TVS is compatible with 60 V MOSFET planning but leaves
  limited voltage margin against 60 V absolute maximum ratings.
- SM8S33A-class input TVS is not automatically compatible with 40 V integrated
  smart switches. Low-current TPS2HB-class channels require a lower-clamp input
  protection strategy, local protection, or fallback to the external-controller
  output architecture.

## Schematic blockers added

- Resolve input TVS clamp voltage for any 40 V smart switch connected to the
  protected battery rail.
- Confirm whether OUT5/OUT8/OUT9 stay on TPS2HB-class smart switches or move to
  the external TPS48110 plus MOSFET architecture.
- Confirm MOSFET SOA for OUT2 with compressor startup/inrush assumptions.
- Confirm thermal stack-up for all output classes in the intended enclosure.

## Related tables

- `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`
- `hardware/power-board/PB-100/PB-100-thermal-estimates.csv`
- `hardware/power-board/PB-100/PB-100-protection-validation.csv`
