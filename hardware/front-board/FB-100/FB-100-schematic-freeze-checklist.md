# FB-100 Schematic Freeze Checklist

Status: Open

This checklist gates FB-100 schematic planning before PCB layout. It does not
authorize KiCad PCB layout, Gerbers, drills, pick-place, BOM/CPL order packages,
or PCBA orders.

## Completion Rule

FB-100 schematic freeze is allowed only when every required gate is `Closed`.
Changes to the service connector power model, UI signal ownership, or mechanical
interface require an ADR before this checklist can close.

## Required Gates

| Gate | Status | Evidence | Close condition |
|---|---|---|---|
| Architecture baseline | Closed | `docs/architecture/Architecture-Review-v1.0.md`, `docs/adr/ADR-0009-architecture-v1-freeze.md` | Three-board architecture remains frozen |
| FB-100 requirements | Closed | `hardware/front-board/FB-100/FB-100-requirements.md`, `docs/adr/ADR-0014-lb-fb-baseline-requirements.md` | Rev.1 FB-100 baseline remains unchanged |
| LB-100 interface | Conditional | `hardware/front-board/FB-100/FB-100-requirements.md`, `hardware/front-board/FB-100/FB-100-interface-signal-plan.csv`, `hardware/logic-board/LB-100/LB-100-requirements.md` | Cable or board-to-board signal ownership, reset/service button behavior, and channel/status LED signals are reviewed |
| USB service and ESD | Conditional | `hardware/front-board/FB-100/FB-100-requirements.md`, `hardware/front-board/FB-100/FB-100-interface-signal-plan.csv` | USB-C service role, CC behavior, ESD protection, shield/chassis policy, and no-back-power behavior are reviewed |
| Indicators and controls | Conditional | `hardware/front-board/FB-100/FB-100-requirements.md`, `hardware/front-board/FB-100/FB-100-interface-signal-plan.csv` | RGB LED, channel LEDs, SERVICE/RESET button, and optional OLED footprint are selected without accessory role hard-coding |
| Mechanical and enclosure interface | Conditional | `hardware/front-board/FB-100/FB-100-requirements.md`, `hardware/front-board/FB-100/FB-100-ui-mechanical-precheck.csv` | Board outline, mounting, button/LED alignment, display keep-out, connector access, and service sealing are reviewed |
| Factory assembly readiness | Conditional | `docs/production/component-family-shortlist.md` | Critical FB-100 components have preferred parts, alternatives where critical, and current JLCPCB/PCBWay sourcing review |
| KiCad schematic scaffold | Conditional | `hardware/front-board/FB-100/kicad/FB-100.kicad_sch`, `hardware/front-board/FB-100/kicad/FB-100.kicad_pro` | Non-layout KiCad schematic scaffold exists, validates, and contains no PCB layout or manufacturing artifacts |

## Active Blockers

Active FB-100 release blockers are tracked in
`hardware/front-board/FB-100/FB-100-board-release-blocker-register.csv`.
PCB layout and manufacturing output remain blocked until this checklist is
`Closed` and the blocker register is empty.
