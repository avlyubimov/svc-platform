# Q2-C100 Fixture Interface Selection

Status: `EXACT BOARD INTERFACE PARTS SELECTED / FIT, PROBES, SAFETY AND FAB-REVIEW OPEN`

This record selects the parts mounted on Q2-C100 and the matching loose
harness parts. It does not select the oscilloscope, differential probe,
current probe, isolated driver, heater controller, enclosure or safety
interlock. It does not authorize fabrication or energized use.

## Connector kits

| Interface | Board header | Harness housing | Contacts | Conductors | Deliberate differentiation |
|---|---|---|---|---|---|
| `JHEAT` | Molex `436500228`, two-position vertical TH, 0.38 um gold | `436450208` | `430300039`, gold, 18 AWG | HEAT+, HEAT- | only two-position harness |
| `JTEMP` | Molex `436500328`, three-position vertical TH, 0.38 um gold | `436450308` | two `430300002`, gold, 20-24 AWG | T+, T-; position 3 physically empty | only three-position harness; empty position is not a guard or shield |
| `JDRIVE` | Molex `436500428`, four-position vertical TH, 0.38 um gold | `436450408` | four `430300002`, gold, 20-24 AWG | gate, source Kelvin, trigger, interlock | only four-position harness |

The three circuit counts prevent a complete wrong-interface mate. This is not
a claim of manufacturer key coding: the 43645 housings state no optional keying
to the mating part. Each connector remains shrouded, polarized and latched.
Labels, conductor colors and a point-to-point harness test remain mandatory.

Molex rates the selected headers up to 600 V and 8.0-8.5 A per contact and
-40..125 degC, while the selected 43645 harness housings are limited to
-40..105 degC. These catalog values are not a coupon system rating and do not
make a disconnected or exposed connector touch-safe. The fixture design must
use the lower rating of every header/contact/housing/wire combination and keep
each housing below its validated temperature limit with an approved margin.
No connector may be touched or changed while the energy sources are enabled.

## Exact land-pattern boundary

The generated footprints follow Molex drawing `SD-43650-010`:

- 3.00 mm non-accumulating signal pitch;
- 1.05 mm generated signal drill within the drawing's 1.02 +/-0.05 mm
  recommended hole;
- 1.30 mm NPTH polarizing-peg drill against the drawing's 1.27 +/-0.05 mm
  recommendation;
- square pad 1 and component-side pin order;
- two locator pegs; the selected `...28` variants have no snap retention.

The drawing recommends a 1.57 mm PCB, but Q2-C100 is frozen at 2.0 mm. The
3.18 mm terminal tails do not by themselves prove seating, solder-fillet,
locator or enclosure fit. Supplier DFM plus a physical sample/section review
must accept the 2.0 mm stackup, or a reviewed change must select a compatible
part. This mismatch alone keeps `FAB-REVIEW` open.

## Probe attachment hardware

All nine board probe points use Harwin `S1751-46R`: a tape-and-reel SMT test
point with a 3.25 x 1.63 x 2.00 mm body and the official 3.45 x 1.85 mm land.
Harwin specifies 2 A maximum, -55..125 degC operation and use with standard
probes, clips and hooks. The part is factory-reflowable.

Harwin does not specify a working-voltage or measurement-bandwidth rating for
this test point. Therefore its selection closes only the PCB hardware suffix
and land. It does not close the 101 V VDS measurement chain, 100 MHz bandwidth,
probe loading, common-mode range, insulation or accidental-short risk. Attach
all probes with every source discharged and verified de-energized; then close
and interlock the shielded enclosure before remote energization. A grounded
oscilloscope lead remains forbidden on RAW_101V or the floating VDS path.

## Alternatives and rejection reasons

- Molex Micro-Fit+ increases mating-cycle capability but changes to a dual-row
  footprint and does not solve the unverified 2.0 mm board fit as a drop-in.
- Generic 2.54 mm headers have no latch, shroud or wrong-harness resistance and
  remain prohibited for energized work.
- Harwin `S2751-46R` and `S2761-46R` reduce pad and loop size, but require
  miniature attachment hardware and are less suitable for the present
  controlled clip workflow. They remain layout alternatives only after the
  actual probe adapters are selected.
- Large color-keyed TH loops increase loop area and require two drilled lands;
  they are not the default high-bandwidth interface.

## Lifecycle, production and open evidence

The Micro-Fit interface is specified for 30 mating cycles, so it is a
replaceable laboratory harness interface, not a 10-15 year vehicle connector.
There is no semiconductor junction temperature for these passive interfaces;
their component temperature limits are stated above. Exact distributor lots,
LCSC availability, crimp applicator/tooling, pull-force samples, contact
resistance, header manual-solder process, JLCPCB/PCBWay handling and order-date
quotes remain open. `S1751-46R` may be factory placed; all three TH headers are
post-reflow manual operations.

The selected family is expected to remain inside the 500 USD prototype budget,
but no cost or availability claim is frozen before quotes. The dominant risks
are the 2.0 mm board mismatch, only 30 mating cycles, heater-housing
temperature, operator miswiring, probe-loop loading and the absence of an
intrinsic touch-safe boundary.

Primary evidence:

- [Molex SD-43650-010 customer drawing](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/436/43650/436500827_sd.pdf)
- [Molex Micro-Fit 3.0 single-row product specification](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/436/43650/PS-43650-001.pdf)
- [Molex 43645 receptacle family](https://www.molex.com/en-us/products/series-chart/43645)
- [Molex 43030 female crimp-terminal family](https://www.molex.com/en-us/products/series-chart/43030)
- [Harwin S1751-46R](https://www.harwin.com/products/S1751-46R)
- [Harwin S1751-46R drawing](https://cdn.harwin.com/pdfs/S1751R.pdf)
