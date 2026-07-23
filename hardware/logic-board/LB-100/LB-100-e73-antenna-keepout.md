# LB-100 E73 Antenna Keepout

Status: implemented for Rev.1 EVT; production RF qualification remains open

## Source boundary

The selected module is Ebyte `E73-2G4M08S1C`. The official product page and
user manual identify the 2.4 GHz ceramic-antenna variant and give the module,
terminal and antenna-end geometry:

- <https://www.ebyte.com/product/444.html>
- <https://www.ebyte.com/Uploadfiles/Files/2018-8-7/2018871547597144.pdf>

The manual does not specify a numeric host-PCB antenna keepout. The LB-100
boundary is therefore a project-derived Rev.1 rule based on the official
terminal drawing and reviewed local footprint. It is not an Ebyte-certified
keepout.

## Implemented geometry

- U7 datum: `(72.0 mm, 59.0 mm)`, rotation `0 degrees`.
- The ceramic-antenna end faces the `+Y` board edge.
- Terminal copper ends at board `Y=66.46 mm`; the keepout starts at
  `Y=66.61 mm` and continues to `Y=70.00 mm`.
- X boundary: `65.35..78.65 mm`, including 0.15 mm lateral margin.
- Layers: `F.Cu`, `In1.Cu`, `In2.Cu`, `In3.Cu`, `In4.Cu`, and `B.Cu`.
- Tracks, vias, pads and copper pours are forbidden inside the boundary.
- F.Cu, In2.Cu, In4.Cu and B.Cu GND zones stop at the keepout during refill.

The geometry is emitted by `tools/generate_lb100_layout.py` and verified by
`tools/validate_lb100_layout.py`.

## Verification and residual risk

KiCad 10.0.4 reports no `items_not_allowed`, short, clearance, crossing or
unconnected finding after refill. This proves the implemented no-copper rule,
not RF range.

For the five Rev.1 EVT units:

- inspect antenna orientation and pin 1 before power-up;
- keep cells, shields, standoffs, metallization and cable bundles out of the
  antenna volume;
- record enclosure material and air gap;
- measure current and over-the-air range during bench EVT.

Production/Rev.2 RF readiness remains blocked until the real enclosure and
range results justify retaining or enlarging the project-derived boundary.
