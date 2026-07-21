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

The first committed arithmetic screen is
`Q2-C100-pre-fab-screening.md` / `.csv`. It records a 1.9033 mOhm and 3.0453 W
lower bound for five straight correlation-path corridors at 150 degC copper,
plus source-fanout/via cross-sections and a waveform-derived 194.75 nH absolute
loop ceiling. Package lands, spreading, via resistance, contacts, unequal layer
sharing and fixture conductors are excluded, so these values are inputs to the
required field solutions and cannot close 40 A or loop behavior.

## Current machine-checked milestone

- schematic ERC findings: 0;
- board DRC rule violations: 0;
- unconnected items: 0;
- schematic-parity differences: four board-only M3 mounting holes only;
- all required pad-to-pad connections are routed, including RAW_101V,
  COMMON_SOURCE, SYSTEM_OUT, Q2_HGATE, QREV_DGATE, controller support,
  probe and fixture paths;
- the direct F.Cu-only HGATE path, separate In1/In2 sense/Kelvin routes,
  outer-layer power-spine widths and power-via stitching are pinned by CI;
- every TOLL source pad has its own 0.8 mm spoke into a 4.0 mm collection bus;
  the common-source spine is 6.0 mm on both outer layers and has two five-via
  transfer rows at each package-side boundary;
- RVS, ROV1/2, ROV3 and CCAP exact primary MPNs and independent alternatives
  are recorded; their remaining application calculations stay open;
- exact Molex 2/3/4-position board interfaces and Harwin `S1751-46R` test
  points are bound to generated footprints; 2.0 mm header fit and the actual
  rated measurement instruments remain open;
- manufacturing outputs: none.

`FAB-REVIEW` remains open. Zero DRC and zero unconnected items prove electrical
completion of this controlled source milestone; they do not prove 40 A thermal
capacity, transient loop behavior, safety-system completion or fabricability.

## Required before `FAB-REVIEW`

1. Use the committed arithmetic screen to complete creepage/clearance,
   field-solver/loop-inductance and 40 A electrothermal review with the selected
   supplier stackup and complete fixture.
2. Obtain written/supplier DFM and physical-sample acceptance for the selected
   Molex headers on the 2.0 mm board; close the exact rated probes, adapters,
   instruments and external safety enclosure/interlock interfaces.
3. Prove effective CTRL_VS capacitance is at least 1.0 uF at 56 V across the
   accepted temperature range.
4. Close RVS Zener-tolerance/startup-pulse/local-temperature derating, review
   controller/passive placement against TI layout guidance, and review the
   QDUT land against Infineon assembly guidance.
5. Commit current-limit, fuse, dump/discharge, emergency stop, remote trigger,
   shield and laboratory safety evidence.
6. Obtain independent electrical, layout and safety sign-off.

Only then may a separate reviewed change generate coupon Gerber/drill files.
That change still cannot generate or authorize PB-100 manufacturing output.
