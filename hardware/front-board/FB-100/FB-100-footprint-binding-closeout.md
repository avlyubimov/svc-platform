# FB-100 Footprint Binding Closeout

Status: Closed for local footprint binding
Review date: 2026-07-20

This closeout binds FB-100 footprint classes to project-local KiCad footprints
created from JLCPCB/LCSC/EasyEDA footprint evidence and conservative local
0603/0805 passive land patterns. It does not create `FB-100.kicad_pcb`,
Gerbers, drill files, pick-place files, BOM/CPL order packages, manufacturing
ZIP files, fabrication packages, panel outputs, or PCBA orders.

## Why The Blocker Existed

FB-100 had package-source evidence for every on-board item, but no reviewed
project-local KiCad footprints existed in `kicad/lib/FB100.pretty`. Board import
from footprint-free schematic evidence would create false layout readiness.

## Candidate Comparison

| Area | Candidate A | Candidate B | Selection |
|---|---|---|---|
| Vendor-specific footprints | Use JLCPCB/LCSC EasyEDA-derived footprints | Draw every footprint manually from PDFs | Use EasyEDA-derived footprints then normalize with KiCad |
| Generic passives | Use local 0603/0805 conservative land patterns | Depend on missing system KiCad libs | Use local 0603/0805 footprints |
| Optional OLED | Keep DNP but bind footprint keepouts | Remove display footprint | Keep DNP footprints bound |
| USB-C alternate | Bind only preferred connector | Bind preferred plus alternate | Bind preferred plus alternate |

## Recommended Solution

Use the footprints listed in `FB-100-footprint-binding-closeout.csv`:

- USB-C: `TYPE-C-SMD_SBC-160S1A-20-S412` preferred and
  `USB-C_SMD-TYPE-C-31-M-12_1` alternate.
- USB ESD: `SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL` preferred and
  `SOT-9X3-3_L1.0-W0.8-P0.35-LS1.0-BR` alternate.
- RGB/status LED: `LED-ARRAY-SMD_4P-L1.6-W1.6-BL_1`.
- Channel LEDs: `LED0805-R-RD` preferred and
  `LED-SMD_L1.6-W0.8-R-RD` alternate.
- JFB1 FPC connector: `FPC-SMD_AFC07-S24ECA-00`.
- Buttons: `KEY-SMD_L2.6-W1.6-P0.75-LS3.0` preferred and
  `SW-SMD_4P-L5.1-W5.1-P3.70-LS6.5-TL_H3.5` alternate.
- Optional OLED DNP: `OLED-SMD_QG-2864XXX` preferred and
  `OLED-SMD_N091-2832TSWFG02-H14` alternate.
- Passives: local `R_C_0603_1608Metric` and `R_C_0805_2012Metric`.

## Engineering Impact

- Cost impact: no material BOM increase; binding footprints only improves
  layout readiness.
- Thermal impact: negligible for FB-100 because these are service/UI parts.
- Production impact: improves JLCPCB/PCBWay reviewability by placing all
  candidate SMT footprints in a project-local library.
- Field reliability: keeps USB ESD, connector shell, button actuator, FFC, LED,
  and DNP OLED orientation risks explicit for layout review.

## Risks And Open Follow-Ups

- EasyEDA-derived footprints still require visual review in KiCad/EasyEDA Pro
  against package drawings before PCBA order release.
- USB-C shell stake, shield, and panel-edge clearance must be reviewed in the
  actual board layout.
- LED polarity/current values are closed in the value-bearing schematic;
  optical alignment remains a placement review item.
- OLED remains DNP by default; population needs Product Owner approval.
- FB-100 now has a reviewed 44-component/46-net value-bearing schematic, so
  controlled board import is ready; manufacturing packages remain unauthorized
  until layout and fabrication review close.

## Tooling Evidence

- EasyEDA Pro installed locally at `~/.local/opt/easyeda-pro-3.2.149`.
- `easyeda-pro --version` reports app `3.2.149.88089769`.
- `easyeda2kicad.py v1.0.1` converted JLCPCB/LCSC footprint sources.
- `kicad-cli fp upgrade --force` normalized FB-100 footprints to KiCad 10
  footprint format.

## Boundary

FB-100 footprint binding and symbol promotion are closed as local KiCad
evidence. Controlled board import is ready. Gerbers, drills, pick-place,
BOM/CPL order packages, manufacturing ZIPs, fabrication packages, and PCBA
orders remain blocked until the full layout review and project order gates
allow them.
