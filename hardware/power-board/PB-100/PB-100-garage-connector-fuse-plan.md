# PB-100 Garage Connector and Fuse Plan

Status: Schematic-planning input

This document selects garage-installed connector and fuse families for PB-100
schematic planning. It does not freeze exact connector MPNs or enclosure
placement.

Last source recheck: 2026-07-20 kit-candidate refresh; 2026-07-17 class
baseline retained.

## Decision

Use DEUTSCH connector families by current class:

- DTP 2-pin class for high-current outputs OUT1 and OUT2.
- DT 2-pin class for medium and low-current outputs OUT3 through OUT10.
- DTM class for CAN, service, and signal connectors.

Use Littelfuse MAXI-class sealed inline fuse holder for the 50 A main harness
fuse near the battery.

Use MINI/ATO blade fuse families for per-channel user-serviceable fuses, with
final holder style decided during enclosure and schematic review.

## Rev.1 garage boundary

- Battery input stays off-board and conditional: use a battery ring-lug lead to
  a near-battery MAXI fuse holder, then a high-current sealed harness entry or
  serviceable cable gland class into the enclosure. Do not use DT or DTP as the
  50 A battery input connector class.
- Use 6 mm2 / 10 AWG or larger candidate battery-input wire until harness
  length, temperature, bundling, and fuse-holder terminals are reviewed.
- Use DTP 2-pin housings with size 12 contacts for OUT1 and OUT2. The current
  class covers the 15 A and 20 A fuse classes, but final contacts, seals,
  boots, backshells, and crimp tooling still need a purchase-ready review.
- Use DT 2-pin housings with size 16 contacts for OUT3 through OUT10. Keep DT
  only for 10 A fuse classes or lower; move any future higher-fuse output to
  DTP by ADR or release review.
- Use DTM only for CAN, service, and signal wiring. Do not use DTM for PB-100
  output power.
- Keep per-channel blade fuses user-serviceable from outside the sealed
  electronics volume or from a removable service cover.
- Keep crimping garage-realistic: each selected contact family must have an
  available crimp tool, insertion/removal tool, wedgelock, seal, and spare
  contact set before schematic freeze.

## Purchase-kit candidate evidence

Candidate garage kit MPNs are tracked in
`hardware/power-board/PB-100/PB-100-garage-purchase-kit-candidates.csv`.
That file narrows the current evidence to candidate DTP06/DTP04, DT06/DT04,
DTM06/DTM04 housings, matching size 12/16/20 contacts, wedgelocks, Littelfuse
MAXI and MINI/ATO fuse-holder classes, and HDT-48-00-class tooling. This still
does not freeze exact connector MPNs: final lock requires supplier stock,
boots/backshells, seals, insertion/removal tools, wire gauge, enclosure entry,
heat/service access, and vibration inspection evidence.

## Current rationale

- DEUTSCH DTM uses size 20 contacts around the 7.5 A class and is therefore
  suitable for signal/CAN/service and low-current control, not 8-18 A outputs.
- DEUTSCH DT uses size 16 contacts around the 13 A class and is suitable for
  4-8 A output classes with margin, but not the 15 A/20 A fuse classes.
- DEUTSCH DTP uses size 12 contacts around the 25 A class and is the preferred
  family for OUT1 and OUT2.
- Battery input remains a separate 50 A path and must not borrow the DTP output
  connector decision.

## Detailed output map

Detailed map CSV:
`hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.csv`.

## Open schematic/enclosure checks

- Battery input connector remains conditional and must be derated for the 50 A
  main fuse and 40 A board current budget.
- OUT1 and OUT2 DTP connector variants need final plug/receptacle, contact, wedge
  lock, backshell, and boot selections.
- DT output connectors need final pin count and enclosure-entry strategy.
- Per-channel fuse holders must remain user-serviceable after enclosure design.
- Wire gauge must be checked against connector contacts, fuse rating, harness
  length, and motorcycle installation route.
- Crimp tooling, contact insertion/removal tools, strain relief, and service
  access must remain feasible for garage installation.

## Evidence links

- TE DEUTSCH DT series: https://www.te.com/en/products/connectors/automotive-connectors/intersection/deutsch-dt-series-connectors.html
- TE DEUTSCH DT housings: https://www.te.com/en/product-CAT-D487-CH8172.html
- TE DEUTSCH DTM series: https://www.te.com/en/products/connectors/automotive-connectors/intersection/deutsch-dtm-connectors.html
- TE DEUTSCH DTM housings: https://www.te.com/en/product-CAT-D485-CH8172.html
- TE DEUTSCH family overview with DTP current class: https://www.te.com/en/videos/transportation/deutsch-dt-te-logos.html
- TE DEUTSCH DTP06-2S housing: https://www.te.com/en/product-DTP06-2S.html
- TE DEUTSCH DTP04-2P housing: https://www.te.com/en/product-DTP04-2P.html
- TE DEUTSCH DT06-2S housing: https://www.te.com/en/product-DT06-2S.html
- TE DEUTSCH DT04-2P housing: https://www.te.com/en/product-DT04-2P.html
- TE DEUTSCH DTM06-4S housing: https://www.te.com/en/product-DTM06-4S.html
- TE DEUTSCH DTM04-4P housing: https://www.te.com/en/product-DTM04-4P.html
- TE DEUTSCH HDT-48-00 crimp tool: https://www.te.com/en/product-HDT-48-00.html
- Littelfuse MAXI 152 inline fuse holder: https://www.littelfuse.com/products/fuses-overcurrent-protection/fuse-holders-fuse-blocks-accessories/fuse-holders/in-line-fuse-holders/maxi-152/01520003u
- Littelfuse ATO/MINI sealed fuse holders: https://www.littelfuse.com/products/fuses-overcurrent-protection/fuse-holders-fuse-blocks-accessories/fuse-holders/in-line-fuse-holders/ato-mini-sealed-fuse-holders
