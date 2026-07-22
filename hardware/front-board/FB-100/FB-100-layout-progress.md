# FB-100 Controlled Layout Progress

Status: `EVT-LAYOUT-AUTHORIZED` — connectivity routing complete; fab review open

## Completed Milestone

- Created the deterministic `kicad/FB-100.kicad_pcb` board import from the
  frozen 44-component schematic and project-local footprints.
- Applied the reviewed 80.0 mm x 35.0 mm outline and four 2.7 mm NPTH M2.5
  holes at `(5,5)`, `(75,5)`, `(5,30)`, and `(75,30)`.
- Placed the USB-C receptacle at the X=0 service edge and kept USB ESD plus CC,
  shield, and defined-low VBUS-detect passives in the connector-side zone.
- Placed the rear/internal JFB1 FFC connector on the back side at the X=80
  cable edge and retained pins 4/5 for `USB_D_P` / `USB_D_N`.
- Applied the role-free STATUS and CH1..CH10 optical grid, SERVICE/RESET
  actuator targets, optional OLED DNP window, panel openings, and cable-bend
  review graphics.
- Added board-specific minimum clearance, track-width, and USB differential-
  pair rules in `kicad/FB-100.kicad_dru`.
- Repositioned the USB ESD/passive cluster and RGB driver support parts to
  provide manufacturable fan-out without changing the outline, optical grid,
  USB panel datum, FFC datum, or mounting holes.
- Routed every electrical connection with 457 straight segments and 48
  through vias, then added one filled GND zone per copper layer. The routing is
  stored in `kicad/FB-100-routing.csv` and remains deterministic under CI
  regeneration.
- KiCad 10.0.4 reports zero unconnected items and zero DRC violations after
  refill. A separate raw library audit accepts only the generated J1/JFB1
  transforms. Three additional GND vias bound USB reference-layer transitions.
- Locked the committed USB analytical precheck at 0.154 mm width, 0.2032 mm
  edge gap, 0.0151 mm routed skew and approximately 91.5 ohm differential on
  the selected 0.0994 mm 3313 reference spacing. Supplier field-solver
  confirmation is still required.
- Schematic parity is exact apart from H1-H4, which are board-only mechanical
  mounting holes.

## Open Layout Work

- Review JFB1 mating-side/reverse FFC orientation against the future LB-100
  placement before any prototype package is authorized.
- Submit the selected 1.6 mm/3313 stack, width and spacing to the actual PCB
  supplier impedance calculator/field solver; the analytical precheck is not
  manufacturing acceptance.
- Review the routed CC, VBUS detect-only, RGB, buttons, OLED-DNP, indicator,
  power, ground, shield and ESD return paths together with the four filled GND
  zones; revise zone keepouts if the USB/no-back-power review requires it.
- Complete enclosure, cable, assembly-orientation and supplier DFM review; the
  current KiCad DRC, courtyard and silkscreen check is clean.

## Release Boundary

This milestone is a controlled layout artifact only. It does not authorize or
create Gerbers, drill files, BOM/CPL, pick-and-place, panel files,
manufacturing ZIPs, fabrication packages, PCBA orders, production release, or
field use. FB-100 remains `EVT-LAYOUT-AUTHORIZED` and order state remains
`NO-GO` until a separate `EVT-FAB-REVIEW` closes.
