# Instructions for Codex / AI Agents

Read these files before making changes:

1. `docs/project-constitution.md`
2. `docs/MASTER.md`
3. `docs/architecture/Architecture-Review-v1.0.md`
4. `docs/adr/`

## Rules

- Do not start KiCad layout until architecture is frozen.
- Do not change Power Board requirements without creating an ADR.
- BMW CAN is read-only by default. CAN TX must be physically disabled unless an ADR explicitly changes it.
- Do not hard-code channel roles. Outputs are role-mapped via configuration.
- Keep configuration separate from firmware.
- Prefer automotive-grade components and components available for assembly at JLCPCB/PCBWay.
- All critical components require at least two alternatives.
- Update `docs/decision-log.md` after important decisions.
- Update BOM CSV files whenever hardware assumptions change.

## Current task priority

1. Complete Architecture Review.
2. Finalize PB-100 requirements.
3. Select component families for factory assembly.
4. Generate preliminary KiCad symbols/footprints only after requirements are frozen.
