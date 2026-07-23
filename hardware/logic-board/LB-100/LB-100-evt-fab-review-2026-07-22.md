# LB-100 Rev.1 EVT Fabrication Review — 2026-07-22

Status: technical routing review complete; five-board bare-PCB package may be
released only through the recorded EVT controls below

## Release scope

This review covers one segregated batch of five bare LB-100 Rev.1 EVT boards
for bench bring-up and measurements. It does not authorize PB-100, a combined
three-board order, production use, motorcycle installation, BOM/CPL release or
assembled PCBA procurement.

The Product Owner explicitly requested completion of LB-100 and preparation of
test boards on 2026-07-22. That instruction is recorded as authorization for
the limited LB-only fabrication package after repository checks pass. The
supplier upload must still be stopped if DFM changes the stack, copper, drill,
outline, impedance or connector geometry.

## Electrical and fabrication evidence

- 104 schematic footprints plus H1-H8; 199 nets.
- 2,274 deterministic segments and 409 standard 0.50/0.30 mm plated through
  vias; no blind/buried vias or HDI process.
- Four GND zones on F.Cu, In2.Cu, In4.Cu and B.Cu.
- KiCad 10.0.4 after refill: zero errors and zero unconnected items.
- Schematic parity: H1-H8 only, all intentional board-only NPTH mounting holes.
- Stack: JLCPCB `JLC06161H-3313`, six layers, 1.6 mm, ENIG. In2.Cu and In4.Cu
  are uninterrupted reference planes; no routing rows are allowed on them.
- The exact six-layer E73 no-copper rule is validator-covered.
- All five E73 recovery pads and every frozen ADC, I2C, FOG, SD, clock, USB,
  UART, SWD, safety-control and JPB1 net are connected. Existing schematic and
  exported-netlist validators continue to enforce the safe-boot, Ioff,
  read-only CAN1 and mutually-exclusive FOG population contracts.

## USB review

`USB_D_P` and `USB_D_N` use 0.20 mm traces on In3.Cu over the In2.Cu GND
reference through the central 0.1088 mm 2116 dielectric. The long parallel
segments have approximately 0.157 mm edge gap. Total routed lengths are
37.643 mm and 38.754 mm, so skew is 1.112 mm. Each grouped layer transition has
a GND via within 4 mm.

An IPC-style regression estimate is approximately 85 ohm differential. This
is not supplier field-solver evidence. During JLCPCB upload select
`JLC06161H-3313`, request 90-ohm differential control, and accept the order
only if the supplier calculator/engineering review keeps the pair within its
stated process tolerance without an unreviewed geometry change:

- <https://jlcpcb.com/resources/6-layer-pcbs>
- <https://jlcpcb.com/impedance>
- <https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator>

## Connector and storage review

JFB1 is JUSHUO `AFC07-S24ECA-00` / LCSC `C262643`: 24 positions, 0.5 mm pitch,
top contact, slide lock, right angle and 0.3 mm FFC. LB places it on F.Cu at
`(6,35)`, rotation +90 degrees, with the cable opening at the left edge. The FB
mate is on B.Cu with the opposite edge entry. Electrical pin numbering is
validator-covered; actual cable contact face, fold, bend radius and both latch
accesses remain a first-article unpowered fit inspection:

- <https://www.lcsc.com/product-detail/C262643.html>

The SOFNG TF-015 drawing specifies two 1.00 mm mechanical locating holes. They
are NPTH in the local footprint; the socket signal/shell lands remain SMT:

- <https://www.sofng.com/Memory/T_Flash_CARD_SOCKETS/list_58_4.html>
- <https://xonstorage.z8.web.core.windows.net/pdf/sofng_tf015_apr22_xonlink.pdf>

## Warning disposition and first-article controls

The 27 KiCad warnings are limited to reviewed silkscreen clips, generated
board-hole library notices and three known local footprint transforms. There
are no copper, mask, drill, courtyard, clearance or connectivity errors.

Before payment:

1. Run supplier DFM and confirm the exact six-layer stack and 90-ohm request.
2. Confirm all Gerber layers, NPTH/PTH drill split, 100 mm x 70 mm outline and
   five-piece quantity in the preview.
3. Do not approve any automatic reroute, layer reduction or drill substitution.

Before powering the first assembly:

1. Inspect JPB1 pin 1, all six FX18 mechanical lands and the four GND MF nets.
2. Dry-fit the actual FFC and microSD card; record contact side and latch access.
3. Inspect polarity, DNP selections and shorts; power from a current-limited
   bench supply.
4. Measure BLE range in the intended enclosure. RF evidence remains a
   production/Rev.2 gate.

The combined platform remains `NO-GO` until PB-100 is completed and each board
passes its own release gate.
