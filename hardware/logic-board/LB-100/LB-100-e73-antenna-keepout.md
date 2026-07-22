# LB-100 E73 Antenna Keepout

Status: implemented for Rev.1 EVT layout; RF validation remains open

## Source boundary

The selected module is Ebyte `E73-2G4M08S1C`. The official product page and
user manual identify the 2.4 GHz ceramic-antenna variant and give the module,
terminal and antenna-end geometry:

- <https://www.ebyte.com/product/444.html>
- <https://www.ebyte.com/Uploadfiles/Files/2018-8-7/2018871547597144.pdf>

The manual does not specify a numeric host-PCB antenna keepout. The LB-100
boundary below is therefore a conservative, project-derived Rev.1 rule based
on the official terminal drawing and the reviewed local footprint. It must not
be represented as an Ebyte-certified keepout.

## Implemented geometry

- U7 datum: `(72.0 mm, 59.0 mm)`, rotation `0 degrees`.
- The ceramic-antenna end faces the `+Y` board edge.
- The closest terminal copper ends at board `Y=66.46 mm` after placement.
- The keepout starts at `Y=66.61 mm`, adding `0.15 mm` beyond that terminal
  land, and continues to the board edge at `Y=70.00 mm`.
- X boundary: `65.35..78.65 mm`, which covers the 13 mm module width with
  `0.15 mm` lateral margin on both sides.
- Layers: `F.Cu`, `In1.Cu`, `In2.Cu`, and `B.Cu`.
- Forbidden inside the boundary: tracks, vias, pads and copper pours.
- Footprints are not globally forbidden by the KiCad rule so U7 itself remains
  legal; no other component may be accepted in the antenna end without a new
  RF review.

The keepout is emitted deterministically by `tools/generate_lb100_layout.py`.
Four separate GND-zone intents stop at the keepout during KiCad refill.

## Verification and residual risk

KiCad 10.0.4 accepts the multilayer rule area and reports no
`items_not_allowed`, short, clearance or track-crossing findings after refill.
The rule prevents accidental copper placement but does not qualify RF range.

Before `EVT-FAB-AUTHORIZED`:

- inspect the actual module antenna orientation and pin 1 on the first fitted
  assembly;
- keep battery cells, shields, standoffs, enclosure metallization and cable
  bundles out of the antenna volume;
- review the final enclosure material and air gap;
- run conducted-current and over-the-air range checks on EVT hardware;
- widen or reshape the keepout in Rev.2 if the measured margin requires it.

No Gerber, drill, assembly or order artifact is authorized by this closeout.
