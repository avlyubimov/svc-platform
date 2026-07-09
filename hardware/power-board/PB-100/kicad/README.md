# PB-100 KiCad Project

Status: Schematic scaffold only; no PCB layout

This directory contains the preliminary KiCad project scaffold for PB-100.

## Current boundary

- `PB-100.kicad_pro`: project metadata scaffold.
- `PB-100.kicad_sch`: top-level schematic note sheet.
- `sheets/*.kicad_sch`: child schematic placeholder sheets for capture.
- `sym-lib-table`: project-local symbol library table.
- `fp-lib-table`: project-local footprint library table.
- `lib/PB100.kicad_sym`: preliminary abstract block symbols, first
  project-local concrete MPN symbols, and non-final class symbols for passive
  or garage-installed schematic elements.
- `lib/PB100.pretty/`: empty preliminary local footprint library.

There is intentionally no `PB-100.kicad_pcb` file. PCB layout remains blocked
until schematic freeze. Gerber, drill, pick-and-place, placement, and zipped
manufacturing outputs are also blocked by repository validation.

## Source documents

- `../PB-100-schematic-capture-plan.md`
- `../PB-100-schematic-capture-work-queue.csv`
- `../PB-100-review-release-manifest.csv`
- `../PB-100-schematic-readiness-dashboard.csv`
- `../PB-100-net-naming.md`
- `../PB-100-schematic-instance-plan.csv`
- `../PB-100-schematic-instance-symbol-map.csv`
- `../PB-100-schematic-sheet-reference-map.csv`
- `../PB-100-schematic-net-domain-plan.csv`
- `../PB-100-output-channel-pin-contract.csv`
- `../PB-100-output-controller-pin-template.csv`
- `../PB-100-output-net-expansion.csv`
- `../PB-100-output-stage-design-values.csv`
- `../PB-100-input-controller-pin-template.csv`
- `../PB-100-input-protection-pin-contract.csv`
- `../PB-100-input-power-design-values.csv`
- `../PB-100-current-monitor-pin-template.csv`
- `../PB-100-logic-buck-pin-template.csv`
- `../PB-100-logic-power-design-placeholders.csv`
- `../PB-100-logic-power-design-values.csv`
- `../PB-100-kicad-prep.md`
- `../PB-100-kicad-sheet-manifest.csv`
- `../PB-100-kicad-footprint-plan.csv`
- `../PB-100-symbol-mpn-readiness.csv`
- `../PB-100-symbol-capture-worklist.csv`
- `../PB-100-symbol-pin-evidence.csv`
- `../PB-100-symbol-open-items.md`
- `../PB-100-schematic-freeze-checklist.md`
- `../PB-100-schematic-freeze-gap-register.csv`
- `../PB-100-validation-traceability.csv`
- `../PB-100-test-point-plan.csv`
- `../PB-100-fault-response-matrix.csv`
- `../PB-100-can1-safety-verification.csv`
- `../../../../production/bom/pb100_assembly_sourcing_recheck.csv`
- `../../../../production/bom/pb100_sourcing_evidence_snapshot.csv`
- `../../../../firmware/configs/hardware/pb-100-capabilities.json`

## Next KiCad work

1. Open `PB-100.kicad_pro` in KiCad.
2. Let KiCad normalize project settings if needed.
3. Link or normalize child schematic sheets listed in
   `PB-100-schematic-capture-plan.md`.
4. Review preliminary concrete MPN symbols against the official data sheets
   listed in `PB-100-symbol-capture-worklist.csv`.
5. Replace abstract block symbols only after package drawings and pinouts are
   checked.
6. Do not create a PCB layout until the freeze checklist is closed.

## Validation

Run from repository root:

```bash
python3 tools/validate_pb100.py
```

The validator intentionally fails if layout/manufacturing artifacts appear before
the PB-100 schematic freeze checklist is closed.

If `kicad-cli` is installed, the validator also runs schematic ERC, requires
zero reported violations, and exports a temporary KiCad S-expression netlist. If
`kicad-cli` is not available, the text-level KiCad scaffold checks still run.

KiCad schematic and symbol files are also checked for accessory-role tokens such
as `FOG`, `USB`, `SEAT`, `CHIGEE`, `DVR`, and `BRAKE`. PB-100 artifacts must use
generic `OUT1`..`OUT10` naming only.

Rows in `PB-100-symbol-capture-worklist.csv` that say `preliminary symbol
created` are checked against `lib/PB100.kicad_sym`; those symbols must stay
excluded from BOM and board output until schematic freeze.

`PB-100-symbol-pin-evidence.csv` records the official data-sheet pin tables used
for concrete MPN symbols and the internal schematic-class pin contracts used for
non-final class symbols. Validation checks each recorded pin number/name against
the KiCad symbol library.

`PB100_JPB1_100PIN_PRELIM` is generated from
`PB-100-b2b-pin-map.csv`; validation checks all 100 connector pin names and
numbers directly against that map.

The readiness dashboard and pin/value contract CSVs are checked against the
instance map, JPB1 pin map, net-domain plan, and freeze policy. They are
schematic-capture contracts only and do not authorize layout or final values.
