# PB-100 Garage Connector and Fuse Plan

Status: Schematic-planning input

This document selects garage-installed connector and fuse families for PB-100
schematic planning. It does not freeze exact connector MPNs or enclosure
placement.

## Decision

Use DEUTSCH connector families by current class:

- DTP 2-pin class for high-current outputs OUT1 and OUT2.
- DT 2-pin class for medium and low-current outputs OUT3 through OUT10.
- DTM class for CAN, service, and signal connectors.

Use Littelfuse MAXI-class sealed inline fuse holder for the 50 A main harness
fuse near the battery.

Use MINI/ATO blade fuse families for per-channel user-serviceable fuses, with
final holder style decided during enclosure and schematic review.

## Current rationale

- DEUTSCH DTM uses size 20 contacts around the 7.5 A class and is therefore
  suitable for signal/CAN/service and low-current control, not 8-18 A outputs.
- DEUTSCH DT uses size 16 contacts around the 13 A class and is suitable for
  4-8 A output classes with margin, but not the 15 A/20 A fuse classes.
- DEUTSCH DTP uses size 12 contacts around the 25 A class and is the preferred
  family for OUT1 and OUT2.

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
- Littelfuse MAXI 152 inline fuse holder: https://www.littelfuse.com/products/fuses-overcurrent-protection/fuse-holders-fuse-blocks-accessories/fuse-holders/in-line-fuse-holders/maxi-152/01520003u
- Littelfuse ATO/MINI sealed fuse holders: https://www.littelfuse.com/products/fuses-overcurrent-protection/fuse-holders-fuse-blocks-accessories/fuse-holders/in-line-fuse-holders/ato-mini-sealed-fuse-holders
