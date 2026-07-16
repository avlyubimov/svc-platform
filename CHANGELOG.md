# Changelog

## Unreleased

- Initial SVC platform architecture.
- Added project constitution.
- Added Architecture Review draft.
- Added ADRs.
- Added Factory/Garage BOM drafts.
- Added firmware safety enforcement for delayed battery cutoff, runtime
  load-shedding, thermal derate, and PWM increase revalidation.
- Added system sleep/wake and parking-current ADR plus requirements.
- Hardened PB-100 KiCad validation to require fixed KiCad CLI, reject
  placeholder sheets, and enforce ERC/netlist/component/net gates.
- Added preliminary PB-100 KiCad child-sheet capture content that passes ERC and
  netlist export while keeping PCB layout blocked until schematic freeze.
- Added a PB-100 board-release blocker register so every conditional schematic
  freeze gate explicitly blocks PCB layout until its close evidence is complete.
