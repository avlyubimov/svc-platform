# PB-100 Validator Structure

`tools/validate_pb100.py` is the stable command-line entrypoint. The validation
implementation is grouped here by engineering responsibility so that a change
to one design area does not require editing a monolithic validator.

| Module | Ownership |
|---|---|
| `common.py` | Repository paths, CSV/schema contracts, shared parsing and failure helpers |
| `runner.py` | Ordered check registry and CLI orchestration |
| `kicad.py` | KiCad scaffold, ERC, exported netlist, layout-artifact boundary |
| `symbols.py` | Symbol, footprint, pin evidence, instance maps and capture readiness |
| `release.py` | Schematic-freeze, blocker-register and board-print state consistency |
| `release_evidence.py` | Generated five-blocker SOA, transient, Q1, factory, selected-part and freshness invariants |
| `pin_contracts.py` | Controller, input-protection and logic-power pin contracts |
| `outputs.py` | Generic output classes, values, SOA/freeze and closeout traces |
| `input_power.py` | Input protection and reverse-MOSFET evidence |
| `logic_power.py` | Protected logic rails, regulator values and closeout evidence |
| `can.py` | CAN1 physical-disable, readback, DNP and capture contracts |
| `budget.py` | Board-current budget, shunt and high-current path evidence |
| `current_telemetry.py` | Total/per-output current telemetry contracts |
| `thermal_telemetry.py` | NTC, temperature scaling and thermal telemetry contracts |
| `factory.py` | Factory assembly, sourcing snapshots and critical-key ownership |
| `garage.py` | Garage-installed connectors, fuses, wire and tooling evidence |
| `protection.py` | TVS/load-dump source, margin, overshoot and closeout evidence |
| `interface.py` | FX18/JPB1, LB resource binding and validation traceability |
| `review.py` | Test points, faults, review manifest and capture/release packet |

## Adding a check

1. Put the check in the module that owns the engineering decision.
2. Reuse contracts and helpers from `common.py`; do not duplicate file paths or
   CSV schemas in a domain module.
3. Add the top-level check to `CHECKS` in `runner.py` at the dependency-correct
   location. Helper checks called by another registered check do not need a
   second registry entry.
4. Keep `python3 tools/validate_pb100.py` and `make check` passing.

The runner also registers every callable `validate_*` hook exposed by these
modules so `PB-100-review-release-manifest.csv` retains the same hook validation
semantics as the former single-file implementation.
