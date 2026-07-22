# ADR-0013: Split PB-100 pre-layout closure from post-prototype validation

## Status
Accepted — PB-100 release authorization superseded in part by ADR-0019

ADR-0019 permits controlled PB-100 Rev.1 EVT layout before every production
qualification item closes and requires the routed-board pre-fab review before
the five-board EVT order. The evidence-class split in this ADR remains active.

## Context
Some PB-100 checks need an assembled board or board stack. Examples include
current-telemetry calibration, thermal calibration, CAN1 no-transmit observation
with physical reset/unpowered states, output fault timing, fuse behavior, and
vibration inspection.

The board-print readiness artifacts previously mixed two different evidence
classes:

- Pre-layout evidence: schematic values, calculations, simulations, source
  evidence, assembly-process review, package/footprint review, test-point hooks,
  and bench procedures.
- Post-prototype evidence: measurements that require fabricated PB-100 hardware
  or the PB-100/LB-100 stack.

Requiring physical bench execution before the first PCB fabrication package is a
process deadlock.

## Decision
PB-100 schematic freeze requires only pre-layout evidence. First engineering-
prototype board-print authorization additionally requires the post-layout
verification defined by ADR-0017. Bench tests that need physical PB-100
hardware are deferred to a post-prototype validation gate.

Pre-layout closure may use:

- Datasheet calculations and design-value review.
- SPICE/surge/thermal simulation where applicable.
- Manufacturer, distributor, JLCPCB, and PCBWay process/source evidence.
- Package drawings, footprint review inputs, pin-map audits, and assembly notes.
- Test-point hooks and bench procedures that make later measurements possible.

Post-prototype validation requires actual bench records for PB-BENCH-001 through
PB-BENCH-015 before first motorcycle power, field use, or production release.
Those records do not block generation of the first prototype PCB fabrication
package after schematic freeze.

CAN1 remains safety-critical: ADR-0002 still requires CAN1 TX to be physically
DNP/open by default, and any vehicle-CAN TX path still requires a future ADR plus
explicit hardware action. ADR-0013 only moves physical no-transmit measurement
execution to the post-prototype gate; it does not permit a populated TX path.

## Consequences
PBREL blocker wording must distinguish pre-layout evidence from post-prototype
bench execution. Board-print gates may require bench plans, test hooks, and
simulation evidence, but not measurements that require a board that does not yet
exist.

Post-prototype validation is tracked separately in
`hardware/power-board/PB-100/PB-100-post-prototype-validation-gate.csv`.

ADR-0017 supersedes the former two-state authorization wording with explicit
`BLOCKED`, `LAYOUT-ONLY`, `PROTO-ONLY`, and `PRODUCTION-READY` transitions. It
does not change which evidence belongs before layout or after prototype build.
