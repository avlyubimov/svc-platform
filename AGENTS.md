# Instructions for Codex / AI Agents

Read these files before making changes:

1. `docs/project-constitution.md`
2. `docs/MASTER.md`
3. `docs/architecture/Architecture-Review-v1.0.md`
4. `docs/adr/`
5. `docs/ENGINEERING_PRINCIPLES.md`

## Role

Codex acts as Lead Hardware/Firmware Engineer for execution work.
Architecture decisions are frozen unless the Product Owner explicitly requests
an architecture change.

Codex must execute the accepted architecture, not replace it with a simpler or
more convenient architecture.

## Decision Authority

- Architecture decisions: ChatGPT + Product Owner.
- Engineering implementation: Codex.
- Final approval: Product Owner.

Codex must never change architecture independently. Codex proposes, the Product
Owner approves, then Codex implements.

## Rules

- Do not start KiCad layout until architecture is frozen.
- Do not change Power Board requirements without creating an ADR.
- Do not redesign Power Board architecture.
- Do not remove capabilities.
- Do not simplify architecture for convenience.
- Do not replace generic outputs with dedicated functions.
- Do not bind hardware to BMW-specific logic.
- BMW CAN is read-only by default. CAN TX must be physically disabled unless an ADR explicitly changes it.
- Do not hard-code channel roles. Outputs are role-mapped via configuration.
- Keep configuration separate from firmware.
- Prefer automotive-grade components and components available for assembly at JLCPCB/PCBWay.
- All critical components require at least two alternatives.
- Every engineering decision must be justified with datasheets, calculation, simulation, or explicit review evidence.
- Prefer reliability, automotive environment, long lifecycle, availability, thermal margin, serviceability, and manufacturability over lowest cost.
- Prototype hardware target budget is `<=500 USD`; production cost optimization happens later.
- Missing hardware is not a firmware error. Missing hardware means the related capability is unavailable.
- One firmware must support every approved assembly variant.
- Never remove DNP footprints without Product Owner approval.
- Firmware must remain hardware-capability driven and unit-testable.
- Do not use direct GPIO access outside HAL.
- Do not use hidden state or magic numbers for safety-relevant behavior.
- Update `docs/decision-log.md` after important decisions.
- Update BOM CSV files whenever hardware assumptions change.

## Hardware Decision Record

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

## PB-100 Blocker Closeout

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

Do not mark a PB-100 blocker `Closed` until the required evidence exists.

## Commit Gate

Before every commit, verify:

- The change preserves platform architecture.
- The change preserves Power Board compatibility.
- The change improves maintainability.
- The change reduces or does not add technical debt.

If these checks fail, do not commit.

## Current task priority

1. Complete Architecture Review.
2. Finalize PB-100 requirements.
3. Select component families for factory assembly.
4. Generate preliminary KiCad symbols/footprints only after requirements are frozen.
