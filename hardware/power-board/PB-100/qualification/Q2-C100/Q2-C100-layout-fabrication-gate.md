# Q2-C100 Layout and Fabrication Gate

Status: `LAYOUT MILESTONE / FABRICATION BLOCKED`

## Preliminary stackup contract

- four copper layers, 2.0 mm finished thickness;
- F.Cu and B.Cu: 70 um finished copper target;
- In1.Cu and In2.Cu: 35 um copper target;
- high-Tg FR-4, Tg at least 170 degC;
- terminal finished press-fit holes per Würth `786202073`: 1.60 mm drill,
  1.475 +/-0.05 mm finished hole, 25-60 um hole-wall copper;
- REDCUBE insertion occurs after all soldering, with recorded insertion force
  and board support. Rework or soldering after insertion is prohibited;
- 2.0 mm RAW_101V copper clearance outside QDUT and the reviewed resistor
  component bodies. The TOLL package's internal drain/source land spacing is
  controlled by the official package land pattern, not widened by invention.

The high-current segments on both outer layers and their via stitching are a
geometry prototype, not a validated 40 A continuous rating. Fabrication review
must calculate/extract DC resistance, current density, via sharing, local
heating, loop inductance and connector/interface temperature. Initial QDUT
150 degC is created by the controlled heater/calibration method, not by assuming
the coupon's unverified steady-state thermal impedance.

## Current machine-checked milestone

- schematic ERC findings: 0;
- board DRC rule violations: 0;
- open low-energy fixture connections: exactly 36;
- schematic-parity differences: four board-only M3 mounting holes only;
- routed critical nets: RAW_101V, COMMON_SOURCE, SYSTEM_OUT, Q2_HGATE,
  QREV_DGATE and separate UCTRL A/OUT Kelvin returns;
- manufacturing outputs: none.

## Required before `FAB-REVIEW`

1. Route every remaining fixture/control connection and obtain zero
   unconnected items without weakening DRC.
2. Complete creepage/clearance, field-solver/loop-inductance and 40 A thermal
   review using the selected supplier stackup.
3. Close exact MPNs for fixture headers, probe loops and the external safety
   enclosure/interlock interfaces.
4. Prove effective CTRL_VS capacitance is at least 1.0 uF at 56 V across the
   accepted temperature range.
5. Review controller/passive placement against the TI layout guidance and the
   QDUT land against Infineon assembly guidance.
6. Commit current-limit, fuse, dump/discharge, emergency stop, remote trigger,
   shield and laboratory safety evidence.
7. Obtain independent electrical, layout and safety sign-off.

Only then may a separate reviewed change generate coupon Gerber/drill files.
That change still cannot generate or authorize PB-100 manufacturing output.
