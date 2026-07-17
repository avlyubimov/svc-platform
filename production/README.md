# Production

This folder contains production artifacts:

- BOM drafts in `production/bom/factory_bom_draft.csv` and
  `production/bom/garage_bom_draft.csv`.
- Symbol-to-BOM ownership in `production/bom/pb100_symbol_bom_map.csv`.
- Assembly sourcing recheck tracking in
  `production/bom/pb100_assembly_sourcing_recheck.csv`.
- Current sourcing evidence snapshots in
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Future Gerber, Pick&Place, assembly notes, and JLCPCB/PCBWay settings after
  schematic freeze and layout authorization.

Use `make pb100-release-status` from the repository root before any PB-100 board
order discussion. It reports the schematic-freeze state, active board-release
blockers, KiCad PCB presence, and manufacturing output presence. Use
`make pb100-release-gate` when a failing shell status is required for a release
job.

Do not treat Excel as source of truth. CSV/Markdown files are the source; Excel is generated for convenience.
