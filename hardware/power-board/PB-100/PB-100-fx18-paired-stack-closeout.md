# PB-100/LB-100 FX18 Paired-Stack Mechanical Closeout

Status: Closed for pre-layout evidence; physical validation is post-prototype
Review date: 2026-07-21

This closeout resolves PBREL-003 and LBREL-003 under ADR-0013. It does not
claim that a physical stack has been tested and does not authorize field use or
production release.

## Corrected 20 mm Pair

The previously listed `FX18-100P-0.8SV10` plus
`FX18-100S-0.8SV20` combination is not a 20 mm pair. Hirose's FX18 design
guide identifies it as a 30 mm two-piece stack. Rev.1 therefore uses:

- PB-100 plug: `FX18-100P-0.8SV10`, CL0579-0034-1-00, drawing
  `0000951879`, JLCPCB/LCSC `C3640134`.
- LB-100 receptacle: `FX18-100S-0.8SV10`, CL0579-0058-0-00, drawing
  `0000954081`, JLCPCB `C6048965`.
- Nominal connector stack: 20 mm.
- Hirose recommended two-board spacer height for this pair:
  `20.3 +/- 0.127 mm`.
- Maximum PCB thickness at each connector: 1.6 mm.

The LB receptacle change preserves the 100-position JPB1 electrical contract,
MF ownership, signal land pattern, and frozen architecture. It corrects only
the mechanical height variant.

## Footprint and Electrical Evidence

Both project-local footprints contain:

- exactly 100 SMD signal lands at 0.8 mm pitch;
- 4.9 mm signal-row center spacing and 0.5 mm by 2.1 mm signal lands;
- exactly six plated oval TH lands for four MF circuits;
- two physical poles sharing `MF_A_PIN1_51_END` and two sharing
  `MF_A_PIN50_100_END`;
- one land each for `MF_B_PIN1_51_END` and `MF_B_PIN50_100_END`;
- all four logical MF circuits connected to GND on both boards;
- mirrored plug/socket X geometry and preserved pin-1 ends.

The four MF identifiers remain distinct even though they share GND. They are
not connected to AGND, PB_5V_OUT, LB_3V3_IO, or VBAT. The board-schematic and
board-order validators check this topology and the six-land footprint shape.

## Datum, Retention, and Spacer Plan

JPB1 is centered on both boards. Four shared M2.5 stack holes surround the
connector at offsets `X +/-35.0 mm`, `Y +/-20.0 mm` from the JPB1 datum:

- PB-100 coordinates: X40/Y25, X110/Y25, X40/Y65, X110/Y65.
- LB-100 coordinates: X15/Y15, X85/Y15, X15/Y55, X85/Y55.
- Finished NPTH hole diameter: 2.7 mm.
- Spacer: four rigid 20.3 mm M2.5 spacers with dimensional tolerance no worse
  than +/-0.127 mm; one spacer at every shared hole.

The spacers and fasteners carry board and vibration loads. JPB1 is not the sole
structural member, and no enclosure or harness load may be reacted through its
solder joints. Final enclosure hardware must use prevailing-torque fasteners or
another documented anti-loosening method compatible with service removal.

## Assembly Fixture and Inspection

The prototype assembly fixture shall:

1. locate PB-100 by its four shared stack holes and support the PCB below JPB1;
2. locate LB-100 on the same four guide axes with pin 1 aligned to the reviewed
   plug/socket orientation;
3. keep the boards parallel and apply insertion load normal to the board over
   the connector body, never through a board corner;
4. install all four 20.3 mm spacers before final fastener torque so the
   connector solder joints are unloaded;
5. reject assemblies with rocking, visible partial engagement, damaged housing,
   bent MF poles, lifted signal lands, or a spacer that cannot seat without
   forcing board bow;
6. inspect all six TH lands on both boards and AOI the signal rows before the
   stack is hidden.

The first stack record shall capture connector lot codes, measured spacer
heights, board spacing at all four corners, pin-1 photographs, mating force
observations, continuity of all four MF GND circuits, and the JPB1 pin audit.

## Candidate Comparison

| Candidate | Result |
|---|---|
| Existing P-SV10 + S-SV20 | Rejected: official two-piece stack is 30 mm, contradicting the 20 mm envelope |
| P-SV10 + S-SV10 | Selected: preserves the PB part and gives the required 20 mm stack with official 20.3 +/-0.127 mm spacer guidance |
| Standard P-SV + S-SV20 | Valid 20 mm alternative but changes the PB plug and its mechanical height; retain only as a reviewed redesign option |
| Samtec/Molex mezzanine family | Non-drop-in alternative requiring new footprints, mating audit, sourcing, SI, and mechanical review |

## Engineering Impact and Risk

- Cost: four spacers and fasteners add small prototype cost but protect two
  expensive connectors and remain inside the 500 USD target.
- Thermal: no junction temperature applies. The connector is outside PB power
  device thermal zones; enclosure thermal testing must keep it within its
  -55 to +85 degrees C component range.
- Availability: both selected exact parts have JLCPCB/LCSC sourcing paths; the
  LB receptacle is an extended part. Live stock is rechecked before purchase.
- Automotive qualification: FX18 is not recorded here as AEC-qualified.
  Hirose instructs high-reliability automotive users to contact a company
  representative. This is a production-release risk, not hidden evidence.
- Lifetime: expected platform service target is at least 10 years with rare
  service mating, four-point structural retention, and passing post-prototype
  vibration inspection. Connector wear and fretting are verified on prototype
  and production-validation stacks.
- Field reliability: spacer retention, board parallelism, fretting, housing
  damage, solder fatigue, and enclosure resonance remain physical risks.

## ADR-0013 Validation Boundary

Package drawings, the official design guide, footprint review, datum definition,
fixture procedure, and inspection plan are sufficient pre-layout evidence.
Actual hardware remains mandatory later:

- `PB-BENCH-014`: assembled JPB1 stack behavior and pin-map record.
- `PB-BENCH-015`: vibration/retention and strain-relief inspection.

These tests block first motorcycle power, field use, and production release;
they do not deadlock creation of the first prototype PCB after all other board
gates close.

## Sources

- Hirose FX18 design guide `D86_en`, section 4-3 recommended spacer dimensions.
- Hirose drawings `0000951879` and `0000954081`.
- `PB-100-fx18-mf-contact-ownership-precheck.csv`.
- `PB-100-b2b-interface-closeout-precheck.csv`.
- `hardware/power-board/PB-100/kicad/lib/PB100.pretty/FX18-100P-0.8SV10_Hirose.kicad_mod`.
- `hardware/logic-board/LB-100/kicad/lib/LB100.pretty/FX18-100S-0.8SV10_Hirose.kicad_mod`.
- `docs/adr/ADR-0013-pb-100-prelayout-vs-postprototype-validation.md`.
