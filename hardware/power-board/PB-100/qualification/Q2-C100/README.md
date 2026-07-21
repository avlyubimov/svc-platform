# Q2-C100 Qualification Coupon

Status: `CONTROLLED ROUTING IN PROGRESS / NOT FOR FABRICATION`

Q2-C100 is the dedicated laboratory coupon authorized by
`PB-100-q2-empirical-qualification-plan.md`. It is not PB-100, is not a vehicle
assembly and does not authorize `PB-100.kicad_pcb`.

The committed KiCad milestone contains:

- the exact `IAUTN15S6N025ATMA1` QDUT and `LM74930QRGERQ1` UCTRL footprints;
- the selected `IAUT300N08S5N012ATMA2` QREV correlation path;
- separate RAW drain, common-source and system-output REDCUBE terminals;
- a direct UCTRL HGATE-to-QDUT gate connection with no Rg or CdV/dt element;
- Kelvin and fixture probe interfaces, isolated heater and TSEP interfaces;
- the routed high-current path, direct HGATE path, DGATE path and controller
  A/OUT Kelvin returns;
- a four-layer, 2.0 mm preliminary stackup boundary and a 2.0 mm RAW_101V
  clearance rule outside the unavoidable reviewed QDUT/RVS/ROV component
  geometries.

KiCad 10.0.4 ERC has zero findings. Board DRC has zero rule violations. The
board deliberately retains exactly 36 unconnected low-energy fixture items;
the validator treats any change to that number as a reviewed milestone change,
not as permission to fabricate.

## Build variants

`CORRELATION-A` populates UCTRL and QREV. UCTRL drives QDUT directly and the
input rise/OV-deglitch behavior is measured.

`FORCED-B` does not populate UCTRL or QREV. The isolated external driver is
connected to JDRIVE pins 1 (gate) and 2 (source Kelvin). Its complete discharge
waveform must be demonstrated to be no stronger than the LM74930-Q1 worst-case
corner before Phase B. The copper between the QDUT gate, JDRIVE and probe points
does not contain a selector, zero-ohm resistor or hidden damping part.

Population differences are controlled by `Q2-C100-assembly-variants.csv`.

## Hard safety boundary

Do not energize or fabricate this revision. Before the status can change to
`FAB-REVIEW`, all 36 low-energy connections, interlock behavior, external
current limiting, stored-energy discharge, enclosure/shield, remote trigger,
instrument ratings, heater control and laboratory safety review must close.
Gerber, drill, pick-and-place and manufacturing ZIP files are prohibited in
the current state.
