# ADR-0019: Authorize PB-100 EVT development before production qualification

## Status

Accepted — Product Owner direction on 2026-07-22

## Context

PB-100 cannot obtain board-level copper, thermal, parasitic, connector, fault
and enclosure evidence without a routed and assembled board. The dedicated
Q2-C100 coupon isolates the surge-stopper Q2 trajectory, but completing it as a
mandatory predecessor to PB-100 has started to create a second hardware project
and still cannot replace full-board evidence.

ADR-0017 correctly separated layout, prototype and production evidence, but its
aggregate least-authorized-state rule allowed the unresolved PBREL-007
production evidence to block PB-100 board import and EVT fabrication. That
prevents the measurements needed to improve the design.

This ADR changes the PB-100 development release process. It does not change the
three-board architecture, generic outputs, 40 A board target, CAN1 read-only
default, selected LM74930-Q1/Q1/Q2 power-path architecture, or production
acceptance limits.

## Decision

PB-100 uses these ordered release states:

1. `EVT-LAYOUT-AUTHORIZED`: controlled `PB-100.kicad_pcb` board import,
   placement, routing, copper pours and iterative post-layout extraction are
   allowed. Manufacturing and energized hardware remain prohibited.
2. `EVT-FAB-AUTHORIZED`: a reviewed package for exactly five Rev.1 EVT boards
   may be fabricated and assembled. Every artifact must be marked
   `PB-100 REV.1 EVT — NOT FOR PRODUCTION`.
3. `BENCH-VALIDATION`: assembled and inspected EVT boards may be energized only
   on controlled bench fixtures under the approved safety plan.
4. `MOTORCYCLE-VALIDATION`: an undamaged, bench-passed EVT board may be
   installed on the reference motorcycle. Intentional load-dump, short-circuit
   or destructive fault generation on the motorcycle is prohibited.
5. `PRODUCTION-RELEASE`: production is allowed only after bench and motorcycle
   evidence is complete, all Rev.1 findings are dispositioned into Rev.2, the
   Rev.2 design is reviewed, and the normal production gates close.

`BLOCKED` remains the state below `EVT-LAYOUT-AUTHORIZED` for a future design
conflict that makes even controlled layout unsafe or architecturally invalid.

PB-100 advances immediately to `EVT-LAYOUT-AUTHORIZED`. PBREL-007 and the
Q2Q-010 through Q2Q-015 calculation/empirical evidence remain mandatory for
`PRODUCTION-RELEASE`, but they do not block Rev.1 EVT layout or fabrication.
Q2-C100 is retained unchanged as an optional diagnostic coupon. Further coupon
development is paused unless a later reviewed failure investigation needs it.

ADR-0019 supersedes the PB-100 release-authorization portions of ADR-0013,
ADR-0016, ADR-0017 and ADR-0018 wherever they prohibit PB-100 layout or EVT
fabrication solely because PBREL-007/Q2 qualification is incomplete. Their
electrical limits, evidence requirements and production restrictions remain
active.

## Mandatory Rev.1 EVT Design Hooks

The routed PB-100 shall include:

- Accessible test points for `VBAT_RAW`, protected input/output nodes, Q1/Q2
  `VDS`, Q1/Q2 `VGS`, controller gate pins, current-sense nodes, logic rails,
  temperatures, output faults and representative output nodes.
- DNP or isolated sites for reviewed alternative MOSFET/TVS strategies without
  removing the selected baseline footprints or creating an uncontrolled
  populated branch.
- Replaceable gate resistors and reviewed DNP damping/snubber experiment sites.
- Physical jumpers or removable links that isolate the input power stage and
  prevent an unsafe power node from energizing the remainder of the board.
- Current-limited bring-up access and hardware safe-off control independent of
  normal firmware operation.
- Silkscreen `PB-100 REV.1 EVT — NOT FOR PRODUCTION` and a durable serial field
  for `EVT-01` through `EVT-05`.

CAN1 TX remains physically DNP/open by default. EVT status does not authorize
vehicle-CAN transmit.

## EVT Fabrication Gate

`EVT-FAB-AUTHORIZED` requires all of the following:

- Final value-bearing schematic review for the EVT population and synchronized
  BOM/variant/DNP records.
- PCB DRC, schematic-to-board parity and unconnected-item checks at zero.
- Reviewed 40 A copper, via, connector and thermal calculations plus extracted
  clamp-loop/parasitic evidence appropriate to the routed board.
- Reviewed creepage/clearance, stackup, controlled-impedance requirements where
  applicable, solder/paste/voiding assumptions, assembly DFM and connector fit.
- Current limiting, input fuse, discharge, emergency disconnect, shielding and
  remote-operation controls documented for the intended bench tests.
- Gerber, drill, BOM/CPL and assembly files segregated under an EVT-only release
  package and never reused as production artifacts without a new review.

The first order is exactly five boards because it is the smallest planned EVT
batch and matches the normal five-piece JLCPCB prototype quantity. Order-time
quantity, capability, sourcing and assembly acceptance still require a fresh
vendor quote and DFM review.

## Validation Sequence

Bench validation is mandatory before motorcycle validation:

1. Current-limited bring-up with outputs disabled.
2. Controlled 5 A, 10 A, 20 A and 40 A steps.
3. MOSFET, copper, via, connector, shunt and enclosure thermal measurements.
4. Overcurrent, short-circuit, fuse and current-limit behavior.
5. Controlled overvoltage/load-disconnect testing while recording synchronized
   input, output, `VDS`, `VGS`, current and temperature waveforms.
6. Safe-default, telemetry, CAN1 listen-only and recovery verification.

Only after the bench gate passes may a dedicated undamaged board be tested on
the motorcycle for cranking, alternator behavior, real loads, CAN1 listen-only,
vibration and temperature. A board used for destructive or limit testing must
never subsequently be installed on the motorcycle.

## Candidate Comparison

### Full PB-100 Rev.1 EVT first — selected

- Produces the board-level evidence needed for copper, connectors, thermal
  paths, enclosure coupling, faults and serviceability.
- Cost impact: one five-board EVT order plus fixtures and instrumentation.
- Thermal impact: measurable on the actual board and enclosure path.
- Production impact: Rev.1 is explicitly non-production; findings feed Rev.2.
- Field reliability impact: improves evidence before any production decision.
- Main risk: an EVT board may be damaged; unit roles isolate destructive tests
  from vehicle validation.

### Q2-C100 qualification before PB-100 — not selected as the active path

- Better isolates Q2 switching behavior but delays system evidence and creates
  a separate fixture/board program.
- Remains useful only if Rev.1 measurements require focused Q2 diagnosis.

### Motorcycle-first validation — rejected

- Cannot safely or repeatably generate worst-case load dump, short-circuit and
  thermal corners.
- Risks the motorcycle regulator, wiring and production ECUs and provides poor
  measurement repeatability.

## Safety and Evidence Basis

ISO 16750-2:2023 describes controlled electrical-load tests but explicitly says
the edition is not intended for motorcycles or mopeds. SVC therefore uses the
12 V Test A envelope as a conservative project engineering reference, not as a
claim of motorcycle certification. TI's LM74930-Q1 application brief lists the
unsuppressed 12 V envelope as 79-101 V, 0.5-4 ohm and 40-400 ms. TI rates the
LM74930-Q1 product input to 65 V and requires suitable external protection and
component sizing. These facts support controlled bench generation instead of
intentional vehicle generation.

Primary evidence:

- https://www.iso.org/standard/76119.html
- https://www.ti.com/lit/ab/snoaaa1/snoaaa1.pdf
- https://www.ti.com/lit/ds/symlink/lm74930-q1.pdf
- https://jlcpcb.com/help/article/how-do-i-place-an-order

## Lifetime, Availability and Manufacturing

The expected platform lifetime remains 10-15 years. This process decision does
not change selected component junction limits, qualification status or sourcing
claims. Alternative sites are diagnostic/DNP provisions, not approved
production substitutions. LCSC availability, JLCPCB/PCBWay compatibility,
component lifecycle, exact stackup, assembly source and quote must be rechecked
before the EVT order and again before any Rev.2 production release.

## Consequences

- PB-100 layout may start without completing Q2-C100.
- Rev.1 EVT fabrication is possible only after routed-board pre-fab evidence.
- Five EVT boards receive fixed, non-interchangeable validation roles.
- Bench validation remains mandatory before motorcycle validation.
- Rev.1 can never receive production release; Rev.2 review is mandatory.
- PBREL-007 remains Conditional and blocks `PRODUCTION-RELEASE` until its
  calculation/empirical and bench evidence is accepted.
- Production and general field use remain `NO-GO`.
