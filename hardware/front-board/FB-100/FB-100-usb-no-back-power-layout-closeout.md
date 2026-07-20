# FB-100 USB And No-Back-Power Layout Model Closeout

Status: Closed for layout-start input
Review date: 2026-07-20

This closeout defines how the FB-100 USB-C service path must be placed and
routed once footprint binding permits KiCad board import. It does not create
`FB-100.kicad_pcb`, Gerbers, drill files, pick-place files, BOM/CPL order
packages, manufacturing ZIP files, fabrication packages, or PCBA orders.

## Why The Blocker Existed

The schematic freeze already closed USB device-only behavior, CC `Rd`
behavior, VBUS sense-only behavior, ESD family selection, JFB1 pinout, and
no-back-power policy. Board import was still blocked because layout-specific
constraints were not captured for USB ESD placement, D+/D- routing, VBUS copper
handling, CC routing, shield/ESD return, and JFB1 FFC transition.

## Candidate Comparison

| Area | Candidate A | Candidate B | Selection |
|---|---|---|---|
| ESD location | Near USB-C receptacle | Near JFB1/LB cable | Near USB-C receptacle |
| USB routing | Short coupled pair with GND reference | Loose single-ended traces | Short coupled pair |
| VBUS use | Sense-only plus ESD reference | Power FB/LB rails from USB | Sense-only only |
| CC behavior | Device-only `Rd` | Source/dual-role `Rp` | Device-only `Rd` |
| Shield return | Local ESD/chassis return strategy | Use shield as normal return | Local ESD/chassis return strategy |
| JFB1 pinout | Preserve adjacent D+/D- pins | Remap for routing convenience | Preserve pinout |

## Recommended Solution

Use `FB-100-usb-no-back-power-layout-rules.csv` as the layout model:

- Place USB ESD on FB-100 between the USB-C receptacle and JFB1.
- Route `USB_D_P` and `USB_D_N` as a short coupled pair with continuous ground
  reference and no avoidable stubs or vias.
- Keep `USB_VBUS_SENSE` as a sense-only net; do not pour VBUS and do not
  connect it to `FB_3V3_OR_IO`, `PB_5V_OUT`, `LB_3V3_IO`, PB-100, or outputs.
- Keep `USB_CC1` and `USB_CC2` device-role only; no source-power behavior.
- Treat shell and ESD return as a reviewed ESD/chassis return network, not as
  a high-current or signal-return substitute.
- Preserve JFB1 pins 4 and 5 for `USB_D_P` and `USB_D_N`.

## Engineering Impact

- Cost impact: small; ESD, CC resistors, VBUS sense passives, and optional
  shell-network passives are already in the FB-100 sourcing model.
- Thermal impact: negligible; USB service and sense nets do not carry board
  load current.
- Production impact: improves DFM by making ESD placement, polarity, pinout,
  and no-back-power inspection explicit before board import.
- Field reliability: ESD near the connector and explicit shield/return policy
  reduce service-port ESD and cable-stress risk.

## Risks And Open Follow-Ups

- Exact USB-C footprint shell stake geometry remains open until footprint
  binding.
- Final stackup can change differential impedance; keep the USB pair short and
  referenced even if exact impedance is prototype-limited.
- The selected ESD part determines whether VBUS is used as an ESD reference;
  VBUS still cannot become a power rail.
- The FFC cable path must be reviewed with LB-100 mating placement before
  board-order release.

## Source Evidence

- `FB-100-usb-no-back-power-layout-rules.csv`
- `FB-100-usb-service-closeout-precheck.csv`
- `FB-100-interface-pinout-closeout.csv`
- `FB-100-interface-signal-plan.csv`
- `FB-100-mechanical-layout-inputs.csv`
- ST USBLC6-2 datasheet:
  `https://www.st.com/resource/en/datasheet/usblc6-2.pdf`
- TI TPD2EUSB30 datasheet:
  `https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf`

## Boundary

FB-100 USB/no-back-power layout model is closed as a layout-start input only.
FB-100 KiCad board import remains blocked until footprint binding closes.
JLCPCB/PCBWay order state remains `NO-GO`.
