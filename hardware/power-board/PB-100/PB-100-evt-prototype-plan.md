# PB-100 Rev.1 EVT Prototype Plan

Status: `EVT-LAYOUT-AUTHORIZED / FABRICATION NOT YET AUTHORIZED`

Authority: ADR-0019, Product Owner direction 2026-07-22

## Scope

PB-100 Rev.1 is an engineering-validation vehicle for board-level measurement
and design correction. It is not a production design and must not be sold,
distributed as a finished product or treated as production-representative.

The planned batch is five boards. Every board and every manufacturing package
must state:

`PB-100 REV.1 EVT — NOT FOR PRODUCTION`

## Required Layout Provisions

- Test points for input/output voltage, Q1/Q2 `VDS`, Q1/Q2 `VGS`, controller
  gates, current sense, logic rails, fault lines and temperature nodes.
- Replaceable gate resistors and DNP damping/snubber experiment sites.
- Retained baseline Q1/Q2/TVS footprints plus isolated DNP alternative sites.
- Removable links for input-stage isolation and hardware safe-off.
- Current-limited low-voltage bring-up connection.
- Accessible thermocouple/thermal-camera targets at MOSFETs, shunts, connectors,
  high-current vias and representative copper bottlenecks.
- Serial field accepting exactly `EVT-01` through `EVT-05`.
- Physical CAN1 TX DNP/open default preserved.

Alternative sites may not create an energized stub or parallel current path in
the baseline EVT population. Population changes require a recorded assembly
variant and pre-power review.

## Pre-Fabrication Evidence

Before `EVT-FAB-AUTHORIZED`:

- Final EVT schematic review, netlist parity, DRC and unconnected checks pass.
- 40 A copper/via/connector electrothermal review and power-loop extraction are
  reviewed against the routed board.
- Stackup, clearance, board thickness, footprints, paste, voiding, component
  height, connector seating and supplier DFM are accepted.
- EVT BOM/CPL, DNP variant, assembly drawing and serial-label process are
  complete.
- The laboratory plan identifies current limiting, fuse, discharge, emergency
  disconnect, shield, remote trigger and rated instruments/probes.
- The release package is segregated from production output.

## Bench Sequence

1. Inspect assembly, DNP links, polarity, shorts and isolation jumpers.
2. Bring up from a current-limited supply with outputs disabled.
3. Exercise controlled 5 A, 10 A, 20 A and 40 A steps.
4. Record MOSFET, trace, via, shunt, connector and enclosure temperatures.
5. Verify telemetry, fuse coordination, current limiting and safe shutdown.
6. Exercise controlled short-circuit and overcurrent cases on the assigned unit.
7. Exercise controlled overvoltage/load disconnect on the surge fixture while
   recording input, output, `VDS`, `VGS`, current and temperature.
8. Repeat post-stress inspection and parametric checks.

The motorcycle is not a load-dump or destructive-fault generator.

## Motorcycle Sequence

Only an undamaged, bench-passed unit assigned to motorcycle validation may be
installed. Validate cranking, alternator behavior, real accessory loads, CAN1
listen-only behavior, vibration, connector retention and enclosure temperature.
Start with low-current loads and add loads in reviewed steps.
Never install on motorcycle a unit used for limit, destructive or abnormal-
stress testing.

## Exit Criteria

- All evidence and failures are recorded by unit serial.
- Rev.1 findings are dispositioned into a Rev.2 change list.
- Rev.2 schematic and layout receive a fresh review.
- PBREL-007 calculation/empirical evidence and all production gates close.
- Rev.1 remains permanently `NOT FOR PRODUCTION` regardless of test outcome.

Q2-C100 is retained as a paused diagnostic option and is not a prerequisite for
Rev.1 EVT layout or fabrication.
