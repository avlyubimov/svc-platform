# LB-100 Controlled Layout Progress

Status: `EVT-FAB-AUTHORIZED` — one segregated five-board bare-PCB Rev.1 EVT package is authorized

## Completed milestone

- The deterministic six-layer `kicad/LB-100.kicad_pcb` implements the frozen
  104-component/199-net schematic on the reviewed 100 mm x 70 mm outline.
- The route manifest contains 2,274 segments and 409 conventional
  `0.50/0.30 mm` F.Cu-to-B.Cu plated through vias. No blind, buried or
  microvias are used.
- KiCad 10.0.4 zone-refill DRC reports zero errors and zero unconnected items.
  Schematic parity contains only H1-H8, the intentional board-only mounting
  holes.
- The six-layer `JLC06161H-3313` model is committed: F.Cu and B.Cu signal,
  In1.Cu and In3.Cu signal, and continuous GND references on In2.Cu and
  In4.Cu. GND pours are also present on F.Cu and B.Cu.
- U7 faces the +Y edge. Its rule area covers all six copper layers and forbids
  tracks, vias, pads and pours beyond the terminal end.
- The E73 SWDIO, SWDCLK, reset, switched target reference and GND recovery
  pads are accessible and routed.
- The USB Full-Speed pair uses 0.20 mm traces on In3.Cu above the In2.Cu GND
  plane. Its parallel section has approximately 0.157 mm edge gap, total route
  skew is 1.112 mm, and the analytical regression estimate is approximately
  85 ohm differential. Supplier field-solver confirmation remains an order
  preflight requirement, not a claimed qualification result.
- The two TF-015 locating features are now 1.00 mm NPTH holes, matching the
  official SOFNG mechanical drawing instead of electrically plated pads.

## Reviewed DRC warnings

The refill report contains 27 warnings and no errors:

- 10 silk-over-mask-pad clips on small footprints;
- 6 silk-to-edge clips at the intentional E73 and TF-015 board-edge entries;
- 8 missing-library notices for generated board-only H1-H8 footprints;
- 3 known generated local footprint transforms for JPB1, JSD1 and JBT1.

These findings affect legend/library comparison only. None changes copper,
mask openings, drill geometry, connectivity or courtyard clearance. The
fabricator may clip the affected silkscreen. The validator locks the exact
warning set so a new electrical or mechanical finding cannot hide in it.

## Remaining EVT order controls

- Select the exact `JLC06161H-3313` stack in the supplier order and accept only
  a field-solver result inside the USB 90-ohm order tolerance; otherwise return
  the board for a width/gap update.
- JFB1 is JUSHUO `AFC07-S24ECA-00`: 24 positions, 0.5 mm pitch, top contact,
  slide lock, 0.3 mm FFC. Verify cable contact side, insertion direction, bend
  radius and latch access on the first unpowered LB/FB stack.
- Treat the 0.15 mm E73 keepout margin as a Rev.1 experiment. Measure BLE range
  in the actual enclosure before production/Rev.2.
- Run the supplier's automated DFM on the segregated LB-only package before
  payment. Any stack, drill, outline, clearance or impedance substitution
  requires review; it is not an automatic waiver.
- The first five units remain `LB-100 REV.1 EVT - NOT FOR PRODUCTION` and may
  be used only for bench bring-up and measurements before motorcycle testing.

PB-100 and the combined three-board order remain `NO-GO`; this milestone does
not authorize PB or production outputs.
