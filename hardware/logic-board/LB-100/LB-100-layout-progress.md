# LB-100 Controlled Layout Progress

Status: `EVT-LAYOUT-AUTHORIZED` — full placement exists; routing open

## Completed Milestone

- Generated the controlled four-layer `kicad/LB-100.kicad_pcb` from the
  reviewed 100-component schematic and project-local footprints.
- Applied the 100 mm x 70 mm outline, four local M2.5 holes and four shared
  PB/LB stack holes around the centered back-side JPB1 connector.
- Placed MCU, rail conversion, JFB1, service interfaces, microSD, BLE, IMU,
  lux sensor, ten-channel control/IMON support and the independent
  `FOG_A_SW_IN`/`FOG_B_SW_IN` protection chains in the reviewed functional
  zones.
- Added deterministic generation, preliminary USB rules and CI validation.
  KiCad reports no copper shorts, clearance violations, edge violations,
  courtyard overlaps or mounting-hole conflicts.
- Schematic parity is exact apart from H1-H8, which are board-only mechanical
  holes. The 384 unconnected findings are the explicit routing backlog.

## EVT-FAB Blockers

- Route all 384 remaining connections and add reviewed reference planes.
- Close USB, SD, clocks, CAN/serial, ADC, I2C and BLE signal-integrity review.
- Implement the BLE antenna copper keepout from the exact module requirement.
- Review ten IMON ADC paths, INA228 I2C/addressing, `VBAT_SENSE`, both protected
  fog inputs, boot safe-state, connector orientation, DNP exclusivity and
  supplier DFM.
- Clear the existing library/silkscreen footprint findings before fabrication.

No manufacturing outputs exist. Gerber, drill, BOM/CPL, pick-place,
manufacturing ZIP and order artifacts remain blocked until
`EVT-FAB-AUTHORIZED`.
