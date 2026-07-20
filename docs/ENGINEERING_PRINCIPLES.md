# Engineering Principles

Status: Active
Last updated: 2026-07-20

This document defines how engineering execution is done after architecture
freeze. It does not change architecture, requirements, or board release gates.

## Philosophy

- Execute the accepted architecture; do not invent a replacement architecture.
- Optimize for reliability, automotive environment, long lifecycle,
  availability, thermal margin, serviceability, and manufacturability.
- Treat cost as secondary during prototype work. The prototype target budget is
  `<=500 USD`; production cost optimization happens later.
- Prefer evidence over opinion. Do not claim "this should work" without
  datasheet evidence, calculation, simulation, worst-case analysis,
  manufacturing impact, and reliability impact.
- Preserve platform compatibility and avoid technical debt.

## Decision Authority

- Architecture decisions: ChatGPT + Product Owner.
- Engineering implementation: Codex.
- Final approval: Product Owner.

Codex proposes engineering changes, documents evidence, and implements approved
work. Codex must not independently change architecture.

## Design Rules

- Do not redesign Power Board architecture.
- Do not remove capabilities.
- Do not simplify architecture for convenience.
- Do not replace generic outputs with dedicated functions.
- Do not bind hardware to BMW-specific logic.
- Do not start PCB layout before all engineering gates are closed.
- Do not create KiCad PCB layout, Gerbers, drills, pick-place files, BOM/CPL
  order packages, manufacturing ZIPs, or PCBA order artifacts before schematic
  freeze authorizes them.
- Preserve backward compatibility unless the Product Owner explicitly approves
  an ADR-backed change.

## Hardware Rules

Every hardware decision must document:

- Why this component.
- Why not alternative A.
- Why not alternative B.
- Expected lifetime.
- Operating margin.
- Maximum junction temperature.
- Availability.
- Automotive qualification.
- LCSC availability.
- PCBWay/JLCPCB compatibility.
- Known risks.

Component selection rules:

- Prefer automotive-qualified parts, including AEC-Q100/AEC-Q101/AEC-Q200,
  where practical.
- Prefer JLCPCB/PCBWay assembly-compatible packages and sourcing paths.
- Every critical component must have at least two qualified alternatives.
- Do not optimize for lowest cost when it reduces reliability, lifecycle,
  thermal margin, serviceability, or manufacturability.
- Do not remove DNP footprints without Product Owner approval.
- Keep CAN1 vehicle-bus transmit physically disabled unless an ADR explicitly
  changes that boundary.

## PB-100 Blocker Closeout Rules

For every remaining PB-100 engineering blocker, document:

- Why the blocker exists.
- Candidate solution comparison.
- Recommended solution.
- Risks.
- Alternatives.
- Cost impact.
- Thermal impact.
- Production impact.
- Field reliability impact.
- Updated documentation.

Close a PB-100 blocker only when the required evidence exists. If the evidence
requires an assembled board, keep the item in the post-prototype validation gate
instead of falsifying pre-layout closure.

## Firmware Rules

- Firmware must remain hardware-capability driven.
- Missing hardware is not an error; it means the related capability is
  unavailable.
- One firmware image must support every approved assembly variant.
- Keep configuration separate from firmware.
- Do not hard-code accessory roles or physical output roles.
- Do not access GPIO directly outside the HAL.
- Avoid hidden state.
- Avoid magic numbers; use named constants, configuration, or documented
  calibration values.
- Keep services testable through interfaces.
- Every service must have tests.
- Plugins and optional modules must remain independent.
- The Rule Engine must remain generic.

## Manufacturing Rules

- Schematic freeze must precede PCB layout.
- PCB layout must precede fabrication and assembly output generation.
- BOM, CPL, pick-place, Gerber, drill, and manufacturing ZIP outputs are release
  artifacts, not planning artifacts.
- JLCPCB/PCBWay compatibility must be checked for selected parts and meaningful
  alternatives before BOM lock.
- Package-specific handling, orientation, DNP/open inspection, and rework risks
  must be documented before PCBA order release.
- User-installed garage items must remain off-board unless an approved ADR
  changes the manufacturing boundary.

## Cost Rules

- Prototype cost target is `<=500 USD`.
- Prototype reliability and safety margins take priority over lowest component
  price.
- Cost reductions are production-optimization work and must not compromise the
  frozen architecture.
- Record cost impact for every blocker closeout and component selection.

## Testing Rules

- Everything must be testable.
- Prefer unit tests for firmware services and deterministic host tests for
  safety behavior.
- Hardware claims require datasheet evidence, calculations, simulations,
  inspection evidence, or bench evidence, depending on the gate.
- Physical bench checks that require assembled hardware belong in
  post-prototype validation and must not block first prototype PCB fabrication
  unless the schematic gate explicitly requires pre-layout evidence.
- Gate status must reflect evidence state, not intent.

## Safety Rules

- Safe default is outputs off unless explicit validated conditions enable them.
- BMW/vehicle CAN1 is read-only by default.
- CAN1 transmit must require explicit hardware action plus ADR approval.
- Runtime behavior must fail safe when telemetry is stale, invalid, missing, or
  unavailable.
- Configuration must not be able to bypass Output Manager safety controls.
- Board variants must degrade by capability availability, not by firmware forks.

## Commit Gate

Before committing, verify:

- The change preserves platform architecture.
- The change preserves Power Board compatibility.
- The change improves maintainability.
- The change reduces or does not add technical debt.
- The change is backed by evidence appropriate to the engineering gate.

If these checks fail, do not commit.
