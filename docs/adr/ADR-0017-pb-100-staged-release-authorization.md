# ADR-0017: Stage PB-100 layout, prototype, and production authorization

## Status

Accepted — Product Owner directed the release-gate correction on 2026-07-21

## Context

ADR-0013 correctly separates pre-layout evidence from measurements that need an
assembled board, but the current PBREL-006 and PBREL-007 wording still requires
layout extraction and prototype bench results before it permits PCB layout.
That creates a process deadlock: copper, thermal, and clamp-loop extraction need
a routed board, while PB-BENCH-004 and PB-BENCH-010 need an engineering
prototype.

The electrical architecture and the PR #36 LB-100/FB-100 corrections are not
changed by this decision.

## Decision

Use four monotonically increasing release states:

- `BLOCKED`: pre-layout design evidence is incomplete; no PCB layout or
  fabrication output is authorized.
- `LAYOUT-ONLY`: pre-layout calculation, component selection, schematic freeze,
  and normal layout-start gates are closed; controlled PCB layout is authorized,
  but Gerber/BOM prototype output is not.
- `PROTO-ONLY`: post-layout copper/current/thermal and clamp-loop extraction is
  reviewed; engineering-prototype Gerber, drill, BOM/CPL, assembly, and order
  output is authorized and must be marked prototype-only. Production and field
  use remain prohibited.
- `PRODUCTION-READY`: required prototype qualification is complete. For
  PBREL-006 this includes PB-BENCH-010; for PBREL-007 this includes
  PB-BENCH-004. Overall PB-100 production and field release additionally
  requires every applicable row in `PB-100-post-prototype-validation-gate.csv`
  and the normal production package gates to be closed.

PBREL-006 and PBREL-007 each use three evidence stages:

1. Pre-layout design closes component selection and analytical evidence and may
   advance the blocker to `LAYOUT-ONLY`.
2. Post-layout verification closes extracted copper, current density, thermal,
   parasitic, and clamp-loop evidence and may advance it to `PROTO-ONLY`.
3. Prototype qualification closes the applicable PB-BENCH evidence and may
   advance that blocker to `PRODUCTION-READY`.

Stages must close in order. A later stage cannot compensate for a failed or
open earlier stage. The aggregate PB-100 state is the least-authorized state of
the staged blockers and the remaining board-wide release gates.

No second-developer review is required. Codex review evidence and Product Owner
approval remain sufficient for these project-owner workflows.

## Current state

- PBREL-006 pre-layout design is closed for the selected 80 V Q1 and passive
  thermal target; its post-layout extraction and PB-BENCH-010 remain blocked.
- PBREL-007 pre-layout design is Conditional under ADR-0018: the corrected
  150 degC initial-junction screen is provisional until a qualified
  maximum-bound Q2 turnoff trajectory exists. Extracted-loop review and
  PB-BENCH-004 remain blocked.
- PBREL-006 is individually `LAYOUT-ONLY`, but PBREL-007 is `BLOCKED`.
  Aggregate PB-100 authorization is therefore `BLOCKED` and layout may not
  begin.
- Production and field use remain `NO-GO`.

## Consequences

- A passing pre-layout protection selection no longer needs impossible
  extracted-layout or bench evidence before controlled layout can begin.
- Engineering-prototype manufacturing files become legal only at
  `PROTO-ONLY`; they are not production-release artifacts.
- `PBREL-006` may remain Conditional and `PBREL-007` may remain Open as overall
  blockers while their individual evidence stages accurately report what is
  authorized.
- Readiness CSV files and consistency validation must use only `BLOCKED`,
  `LAYOUT-ONLY`, `PROTO-ONLY`, and `PRODUCTION-READY` for release authorization.
- No `.kicad_pcb`, Gerber, drill, BOM/CPL, pick-place, manufacturing ZIP, or
  PCBA order is created by this ADR.
