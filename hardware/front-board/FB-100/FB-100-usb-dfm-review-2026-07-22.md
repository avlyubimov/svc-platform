# FB-100 USB and DFM Review — 2026-07-22

Status: board geometry reviewed; supplier impedance and physical FFC fit remain open

## KiCad evidence

KiCad 10.0.4 checks the regenerated FB-100 after zone refill with:

- 44 schematic footprints plus H1-H4;
- 457 routed segments and 48 through vias;
- four GND zones, one per copper layer;
- zero unconnected items;
- zero DRC violations;
- schematic parity containing only the four board-only mounting holes.

The raw library audit contains only the intentional generated transforms for
J1 and JFB1. Their pad sets, layers and net assignments are validator-covered.

## USB routing precheck

The committed stack model is the JLCPCB-style 1.6 mm four-layer construction:

- outer copper `0.035 mm`;
- `F.Cu`/`In1.Cu` and `In2.Cu`/`B.Cu` 3313 RC57% dielectric
  `0.0994 mm`, nominal `Er=4.1`;
- inner copper `0.0152 mm`;
- `1.265 mm` FR-4 core.

The long B.Cu portion of `USB_D_P`/`USB_D_N` is `0.154 mm` wide with
`0.2032 mm` edge gap and continuous In2.Cu GND reference. Total routed lengths
are `96.9368 mm` and `96.9519 mm`, giving `0.0151 mm` skew. An IPC-style
edge-coupled microstrip precheck gives approximately `91.5 ohm` differential.
This is a regression calculation, not a supplier field-solver result.

Three return vias were added at `(2.2,17.75)`, `(11.8,3.5)` and `(66.5,5.5)`.
Together with the existing GND vias, every grouped USB layer transition has a
GND via within 4 mm. The validator locks width, gap, skew, analytical impedance
range and return-via proximity.

JLCPCB's official calculator guide confirms the 3313 nominal dielectric data
and requires the chosen stack, width and conductor spacing to be submitted to
its impedance calculator/order review. The exact manufacturing field-solver
result and tolerance therefore remain open until the actual supplier and stack
are selected:

- <https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator>
- <https://jlcpcb.com/help/article/multi-layer-pcb-standard-laminated-structures>

## JFB1 orientation

The generated board explicitly places JFB1 on the back side at
`(75.2,17.5)`, rotation `-90 degrees`; its pads, paste, mask, fab, silk and
courtyard are all on back layers. Pin 1 is at `(76.47,11.75)` and pin 24 at
`(76.47,23.25)`. The LB mating connector remains top-side at `(6,35)`,
rotation `+90 degrees`, with the same electrical pin numbering.

Electrical orientation and D+/D- polarity are closed by exported-netlist and
PCB validation. Mechanical closure still requires the actual FFC contact-side
type, insertion direction, bend radius and latch access to be checked with an
LB/FB mock stack. Do not order a same-side or reverse-contact cable from the PCB
coordinates alone.

## Remaining fab-review gates

- supplier field-solver/impedance-order confirmation for the selected stack;
- physical JFB1/JFB1 cable and latch-fit inspection;
- USB shell stake and panel opening inspection against enclosure CAD;
- assembly-house DFM for edge connector soldering, bottom JFB1 access, DNP
  OLED population and five-board serialization;
- Product Owner `EVT-FAB-AUTHORIZED` approval.

No Gerber, drill, position, BOM/CPL or manufacturing package is created by
this review.
