# FB-100 Mechanical Layout Input Closeout

Status: Closed for FB-100 mechanical board-import inputs
Review date: 2026-07-20

This closeout converts the FB-100 schematic-freeze mechanical envelope into
reviewed layout-input dimensions. It does not create `FB-100.kicad_pcb`,
Gerbers, drill files, pick-place files, BOM/CPL order packages, manufacturing
ZIP files, fabrication packages, panel CAD, enclosure CAD, or PCBA orders.

## Why The Blocker Existed

FB-100 had a closed 80 mm x 35 mm planning envelope, role-free UI policy, USB
service policy, and JFB1 pinout, but board import still lacked reviewed
coordinates for the outline, mounting holes, USB edge, JFB1 cable exit, LED
optical grid, button actuator targets, optional OLED keepout, and panelization
edge clearances.

## Candidate Comparison

| Area | Candidate A | Candidate B | Selection |
|---|---|---|---|
| Outline | 80 mm x 35 mm rectangular prototype | Wait for final enclosure CAD | 80 mm x 35 mm prototype outline |
| Mounting | Four M2.5 holes | Two holes plus edge support | Four M2.5 holes for prototype stiffness |
| USB access | Left short-edge USB-C | Long-edge USB-C | Left short-edge USB-C |
| JFB1 exit | Rear/internal right-edge FFC | Same-side/front FFC | Rear/internal FFC |
| LEDs | Single role-free row | Role-specific grouped LEDs | Single role-free row |
| Buttons | Separate SERVICE/RESET targets | Shared multifunction button | Separate targets |
| OLED | DNP optional keepout | Mandatory display | DNP optional keepout |
| Panel | Tab-route-first prototype | V-score-first prototype | Tab-route-first unless DFM approves V-score |

## Recommended Solution

Use `FB-100-mechanical-layout-inputs.csv` as the FB-100 mechanical source for
the first KiCad board-import outline after footprint binding closes:

- Board outline: `80.0 mm x 35.0 mm`.
- Mounting: four `2.7 mm` finished NPTH M2.5 clearance holes at `(5,5)`,
  `(75,5)`, `(5,30)`, and `(75,30)`.
- USB-C: left short edge, centerline `Y=17.5 mm`, VBUS sense-only.
- JFB1: rear/internal side near right cable edge, 24-pin 0.5 mm FFC.
- LEDs: role-free `STATUS` plus `CH1..CH10` optical positions.
- Buttons: separate `SERVICE` and `RESET` actuator targets.
- OLED: optional DNP window keepout only.
- Panel: tab-route-first prototype assumption with conservative edge clearance.

## Engineering Impact

- Cost impact: negligible for electronics BOM; board area is fixed at
  `28 cm²`, so prototype PCB cost is predictable and remains within the
  project prototype budget target.
- Thermal impact: negligible for FB-100 because it carries service USB,
  indicators, buttons, and optional OLED rather than power switching.
- Production impact: improves JLCPCB/PCBWay layout readiness by defining
  outline, mounting, optical, actuator, connector, and panel assumptions before
  board import; actual panel rails and tooling holes still close during
  manufacturing-package review.
- Field reliability: four-corner mounting, rear/internal FFC exit, separated
  buttons, and tab-route-first depanel assumptions reduce service-panel flex,
  cable strain, accidental reset, and depanel stress.

## Risks And Open Follow-Ups

- Final enclosure CAD can still move the service-panel cutout or mounting
  points, causing a prototype respin.
- USB shell datum and JFB1 FFC same-side/reverse orientation must be confirmed
  during footprint binding and LB-100 mating layout.
- LED brightness, current-limit values, common-anode/common-cathode strategy,
  diffuser geometry, and light-pipe material remain footprint/electrical
  binding inputs.
- Button cap height, gasket compression, and service-cover stack remain
  enclosure CAD inputs.
- Optional OLED remains DNP by default; omitting it must be treated by firmware
  as capability unavailable.

## Source Evidence

- `FB-100-mechanical-layout-inputs.csv`
- `FB-100-mechanical-envelope-precheck.csv`
- `FB-100-ui-mechanical-precheck.csv`
- `FB-100-usb-service-closeout-precheck.csv`
- `FB-100-ui-control-closeout-precheck.csv`
- `FB-100-interface-pinout-closeout.csv`
- `production/board-order/three_board_layout_rules.md`
- GCT USB4105 product page: `https://gct.co/connector/usb4105`
- JLCPCB AFC07-S24ECA-00 source:
  `https://jlcpcb.com/partdetail/AFC07-S24ECA-00/C262643`
- JLCPCB Panasonic EVPBB4A9B000 source:
  `https://jlcpcb.com/partdetail/PANASONIC-EVPBB4A9B000/C140848`
- JLCPCB panelization guidance: `https://jlcpcb.com/blog/pcb-panelization`
- PCBWay panel requirements:
  `https://www.pcbway.com/pcb_prototype/Panel_Requirements_for_Assembly.html`
- PCBWay manufacturing tolerances:
  `https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html`

## Boundary

FB-100 mechanical envelope is closed as a layout input only. KiCad board import
remains blocked until FB-100 footprint binding closes. JLCPCB/PCBWay order
state remains `NO-GO`.
