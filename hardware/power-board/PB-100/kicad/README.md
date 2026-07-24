# PB-100 KiCad Project

Status: `EVT-LAYOUT-AUTHORIZED`; connectivity-complete layout; fabrication blocked

This directory contains the controlled Rev.1 EVT KiCad project for PB-100.

## Current boundary

- `PB-100.kicad_pro`: project metadata scaffold.
- `PB-100.kicad_sch`: value-bearing top-level schematic with linked child
  sheets.
- `sheets/*.kicad_sch`: child sheets with role-agnostic `OUT1`..`OUT10` nets
  and the reviewed CAN1 DNP/open safety path.
- `sym-lib-table`: project-local symbol library table.
- `fp-lib-table`: project-local footprint library table.
- `lib/PB100.kicad_sym` and `lib/PB100Gen.kicad_sym`: controlled project-local
  symbols.
- `lib/PB100.pretty/`: controlled project-local footprints.
- `PB-100-routing.csv`: complete deterministic routing manifest.

The controlled `PB-100.kicad_pcb` places all 414 footprint-bound schematic
parts plus eight mechanical holes on the reviewed 150 mm x 90 mm, eight-layer
outline. It contains 5,677 segments, 910 conventional through vias, 39
adjacent-layer microvias and 38 zones. KiCad 10.0.4 refill reports zero
unconnected items; schematic parity contains only the eight intentional
board-only mounting holes.

The 39 `0.30/0.10 mm` microvias are explicit HDI manufacturing constraints.
They include stacked F.Cu-to-In3.Cu and B.Cu-to-In5.Cu transitions. U3 pads 2
and 9 also contain filled/capped conventional through via-in-pad features.
Supplier sequential-lamination, aspect-ratio, registration, filling/capping,
inspection, yield and quote acceptance remain mandatory.

ADR-0019 and ADR-0020 permit controlled board import, placement, routing,
copper pours and extraction while the final EVT schematic review remains open.
There are no manufacturing outputs; Gerber, drill, pick-and-place, BOM/CPL and
zipped manufacturing outputs remain blocked until
`EVT-FAB-AUTHORIZED` after DRC, parity, 40 A electrothermal/clamp-loop review,
DFM, connector fit and laboratory safety review.

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
- `../PB-100-footprint-binding-inventory.csv`
- `../PB-100-symbol-mpn-readiness.csv`
- `../PB-100-symbol-capture-worklist.csv`
- `../PB-100-symbol-pin-evidence.csv`
- `../PB-100-symbol-open-items.md`
- `../PB-100-schematic-freeze-checklist.md`
- `../PB-100-pcb-layout-start-checklist.csv`
- `../PB-100-mechanical-envelope-inventory.csv`
- `../PB-100-schematic-freeze-gap-register.csv`
- `../PB-100-validation-traceability.csv`
- `../PB-100-test-point-plan.csv`
- `../PB-100-fault-response-matrix.csv`
- `../PB-100-can1-safety-verification.csv`
- `../../../../production/bom/pb100_assembly_sourcing_recheck.csv`
- `../../../../production/bom/pb100_sourcing_evidence_snapshot.csv`
- `../../../../production/board-order/three_board_footprint_binding_status.csv`
- `../../../../production/board-order/three_board_mechanical_envelope_status.csv`
- `../../../../firmware/configs/hardware/pb-100-capabilities.json`

## Next controlled work

1. Review `../PB-100-evt-fab-review-checklist.csv`, ADR-0020 and
   `../PB-100-layout-progress.md`.
2. Open `PB-100.kicad_pro` in KiCad.
3. Perform the 40 A electrothermal, switch/clamp-loop, Kelvin, rail, CAN1,
   connector and safety review against the tracked layout.
4. Obtain supplier HDI stack/DFM acceptance and filled/capped via-in-pad
   confirmation before any fabrication authorization.
5. Preserve all generic outputs, option footprints and DNP variants during
   review changes.
6. Do not create Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP files,
   fabrication packages or PCBA orders until `EVT-FAB-AUTHORIZED`.

## Validation

Run from repository root:

```bash
python3 tools/validate_pb100.py
python3 tools/validate_pb100_layout.py
```

The validator intentionally fails if manufacturing artifacts appear before
layout review and order evidence close.

The validator requires `kicad-cli` version `10.0.4`. It fails if KiCad is
missing or a different version is installed.

The validator also rejects `sheet-placeholder`/`Placeholder sheet` markers,
runs schematic ERC, requires zero reported violations, exports a temporary KiCad
S-expression netlist, checks that all child sheets in
`PB-100-kicad-sheet-manifest.csv` are linked from the top-level schematic, and
requires at least 20 schematic components plus 20 electrical nets in the exported
netlist. Empty child sheets are therefore not allowed to pass CI.

The current child sheets use passive preliminary class-symbol pins so ERC checks
hierarchy, net continuity, and capture completeness without treating abstract
planning symbols as final electrical models. Schematic freeze must replace those
abstract instances with reviewed final pin electrical types, values, footprints,
and MPN selections.

KiCad schematic and symbol files are also checked for accessory-role tokens such
as `FOG`, `USB`, `SEAT`, `CHIGEE`, `DVR`, and `BRAKE`. PB-100 output artifacts
must use generic `OUT1`..`OUT10` naming only. The protected manual-request inputs
`FOG_A_SW_IN` and `FOG_B_SW_IN` are the only explicit exceptions; they do not
assign roles to outputs and cannot bypass Output Manager authorization.

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
instance map, JPB1 pin map, net-domain plan, and freeze policy. Layout-start
work is now controlled by `../PB-100-pcb-layout-start-checklist.csv`.
