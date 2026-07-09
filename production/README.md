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

Do not treat Excel as source of truth. CSV/Markdown files are the source; Excel is generated for convenience.
