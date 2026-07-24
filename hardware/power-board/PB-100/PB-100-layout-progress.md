# PB-100 Controlled Layout Progress

Status: `EVT-LAYOUT-AUTHORIZED` — connectivity-complete routed baseline;
`EVT-FAB-REVIEW` remains blocked

## Completed milestone

- The deterministic eight-layer `kicad/PB-100.kicad_pcb` retains the reviewed
  150 mm x 90 mm outline, four local M3 holes and four shared M2.5 PB/LB stack
  holes. In2.Cu remains the continuous GND reference and In5.Cu remains the
  protected-battery distribution plane.
- All 414 footprint-bound schematic parts and eight intentional board-only
  mounting holes are placed. Schematic parity contains only H1-H8.
- The accepted architecture is unchanged: ten generic configuration-mapped
  outputs, the 40 A board target, removable input isolation, all factory/DNP
  alternatives and the physically default-disabled CAN1 TX path remain
  present.
- `kicad/PB-100-routing.csv` now contains 6,481 deterministic manifest items:
  5,644 segments, 798 conventional `0.60/0.30 mm` through vias and 39
  `0.30/0.10 mm` adjacent-layer microvias. With the generator-owned
  high-current copper, the board contains 5,677 segments, 910 conventional
  through vias, 39 microvias, 949 total vias and 38 zones.
- A clean regeneration reproduces the accepted copper item-for-item. KiCad
  10.0.4 zone-refill DRC reports zero unconnected items and no errors. The
  locked 188-warning baseline is limited to 136 silk-over-copper findings, 27
  project-library footprint mismatches, 17 silkscreen overlaps and eight
  project-library footprint issues.
- Connectivity fell from the original 499 open items, through the former
  36-item checkpoint, to zero. The closeout includes the dense TPS48110
  fan-outs, all switched-output and FET-drain clusters, protected-battery
  attachments, input-controller pins and ten isolated GND pour fragments.
- Broad generated segments, zones and `1.00/0.50 mm` power-via fields remain
  the only copper credited to high-current capacity. The `0.20 mm`
  attachments and HDI transitions are connectivity evidence only.

## HDI manufacturing decision record

This is a layout/manufacturing constraint under ADR-0020, not a Power Board
requirements or architecture change.

- **Why this construction:** ordinary through vias cannot fit the 0.50 mm
  controller fan-out or pass between overlapping F.Cu/B.Cu power zones without
  clearance or shorting violations. Adjacent-layer `0.30/0.10 mm` laser
  microvias preserve the frozen placement, nets, variants and DNP footprints.
- **Why not alternative A:** continuing with `0.60/0.30 mm` through vias
  produced hole, pad-pitch or opposite-side power-zone conflicts.
- **Why not alternative B:** moving controller/power-stage placement or
  changing the layer/functional architecture would invalidate reviewed
  mechanical, thermal and interface work and is not authorized.
- **Construction:** 21 B.Cu-In6.Cu, five In6.Cu-In5.Cu, eight F.Cu-In1.Cu,
  three In1.Cu-In2.Cu and two In2.Cu-In3.Cu microvias. The deepest stacks are
  F.Cu-to-In3.Cu and B.Cu-to-In5.Cu. The nominal annular ring is 0.10 mm.
  Dielectric traversal is 0.10 mm or 0.18 mm, so the nominal laser-via aspect
  ratio is 1.0:1 or 1.8:1 and requires explicit supplier acceptance.
- **Lifetime and operating margin:** prototype lifetime is not yet qualified.
  Stacked-microvia fatigue, voiding, registration and thermal-cycle margin
  remain supplier/EVT evidence items. No microvia receives high-current
  capacity credit.
- **Thermal and junction limit:** junction temperature is not applicable to a
  passive interconnect. Local current/temperature-rise extraction remains
  open, and the board may not be fabricated from connectivity evidence alone.
- **Availability and qualification:** component availability, automotive
  qualification and LCSC availability are not applicable. Actual
  JLCPCB/PCBWay process compatibility, sequential-lamination count, filled and
  capped via-in-pad capability, inspection plan, lead time and quote are open.
- **Assembly requirement:** U3 pads 2 and 9 contain conventional through
  via-in-pad features and require filled/capped processing. All stacked
  microvias require supplier DFM plus first-article registration/void
  inspection; solder-wicking disposition is mandatory.
- **Cost and risk:** sequential lamination and via filling will increase PCB
  cost. A supplier quote must demonstrate that the complete prototype remains
  within the project `<=500 USD` target. No cost, yield or lifecycle claim is
  accepted until that evidence exists.

## Remaining EVT-FAB blockers

- Complete 40 A current-density, temperature-rise and margin extraction for
  the input path, protected bus, shunts, MOSFET fields, output exits and
  connector transitions.
- Review the buck switch loop, clamp-current returns, Kelvin paths, protected
  5 V/3.3 V rails, CAN1 coupled-pair geometry and all safety/probe access.
- Obtain supplier stack/HDI DFM acceptance, impedance/process limits, filled
  and capped via-in-pad confirmation, microsection/inspection plan, yield and
  prototype quote.
- Close connector fit, enclosure/thermal-interface extraction, solder-void
  controls, laboratory safety review and Product Owner pre-fabrication
  approval.
- Disposition the locked non-electrical library/silkscreen warning set during
  fabrication review.

This connectivity-complete routed baseline is not yet suitable for
fabrication. No Gerbers, drills, pick-place, manufacturing ZIP or order package
is authorized or generated. `PBREL-007` remains a separate
`PRODUCTION-RELEASE` blocker.

ADR-0020 authorizes placement, routing, pours and extraction, but not
fabrication. Zero unconnected items closes the routing-connectivity milestone;
it does not replace electrothermal, EMC, DFM, safety or Product Owner evidence.
