# PB-100 Engineering Blocker Closeout

Status: Closed for PBREL pre-layout evidence
Review date: 2026-07-20

This closeout closes PBREL-001 through PBREL-012 as release-blocker evidence
items. It does not close the PB-100 schematic-freeze checklist and does not
authorize PCB layout, `PB-100.kicad_pcb`, Gerbers, drills, pick-place files,
BOM/CPL order packages, manufacturing ZIP files, fabrication packages, or PCBA
orders.

## Closeout Boundary

- PBREL blockers are closed when pre-layout engineering evidence exists.
- Schematic-freeze gates can remain `Conditional` until reviewed value-bearing
  schematic sheets, final values, and Product Owner approval close them.
- Post-prototype PB-BENCH execution remains deferred under
  `PB-100-post-prototype-validation-gate.csv` and blocks first motorcycle power,
  field use, and production release.

## PBREL-001 — CAN1 safety policy

- Closeout status: Conditional.
- Why blocker existed: vehicle CAN1 must remain read-only by hardware default,
  not only by firmware policy, and reset or unpowered states must not create a
  transmit path.
- Candidate comparison: DNP/open `CAN1_TX_ROUTE` plus SN74LVC1G125-Q1-class
  default-disabled gate and status readback is preferred; firmware-only disable
  is rejected because it fails during firmware fault or reset; populated TX
  routing with a simple jumper is rejected because production can accidentally
  ship a transmit-capable path without a future ADR.
- Recommended solution: keep `CAN1_TX_ROUTE` DNP/open by default, use
  `CAN1_TX_DISABLE_CMD` and `CAN1_TX_DISABLED_STATUS` as physical safety/status
  signals, retain future ADR plus explicit hardware action for any CAN1 TX.
- Risks: production DNP inspection, gate polarity review, reset default, and
  status readback interpretation remain schematic-review details.
- Alternatives: SN74LV1T125-Q1 translator gate, transceiver silent-mode-only
  path, or no routed TX option; the selected path keeps a physical open circuit
  plus an active gate instead of relying on software.
- Cost impact: low, one small automotive logic gate, DNP link, pull resistors,
  and inspection step.
- Thermal impact: negligible; logic-gate dissipation is not a power-path thermal
  limiter.
- Production impact: factory BOM must mark the default TX route DNP/open and
  first-article inspection must verify no default-populated vehicle-CAN TX path.
- Field reliability impact: fail-safe default is no transmit path; field
  service cannot enable CAN1 TX by configuration alone.
- Engineering decision: Why this component/solution: SN74LVC1G125-Q1-class
  output disable is high-impedance when OE is high and supports automotive
  qualified variants; Why not alternative A: firmware-only control has no
  physical safety barrier; Why not alternative B: transceiver silent mode alone
  depends on transceiver configuration and does not prove an open TX route;
  Expected lifetime: 10-15 year platform target with automotive logic family;
  Operating margin: logic path is outside high-current load path and defaults
  disabled; Maximum junction temperature: use AEC-Q100 temperature-grade device
  limits from selected exact suffix; Availability: TI family plus alternates;
  Automotive qualification: AEC-Q100 candidate; LCSC availability: local
  sourcing snapshot records JLCPCB componentSearch risk; PCBWay/JLCPCB
  compatibility: small SMD factory assembly plus DNP inspection; Known risks:
  exact suffix stock and DNP handling.
- Evidence and calculations:
  `PB-100-can1-default-disable-freeze-checklist.csv`,
  `PB-100-can1-default-disable-derivation-precheck.csv`,
  `PB-100-can1-default-disable-closeout-precheck.csv`,
  `PB-100-can1-production-dnp-review.csv`, and
  `PB-100-can1-tx-disable-design-calculation.md`.
- Datasheet and sourcing evidence:
  https://www.ti.com/lit/ds/symlink/sn74lvc1g125-q1.pdf and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-012 verifies CAN1 listen-only/no vehicle-
  CAN transmit frame after hardware exists.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-002 — Board current budget

- Closeout status: Closed.
- Why blocker existed: output current limits are intentionally over-subscribed,
  so the board needs a defensible 40 A continuous budget, 50 A main-fuse path,
  total-current telemetry, and firmware shedding behavior before layout.
- Candidate comparison: 40 A continuous with 50 A near-battery fuse is preferred;
  sizing the PCB for all channel limits simultaneously is rejected as physically
  oversized and contrary to ADR-0008; reducing channel capability is rejected
  because it removes generic output capability.
- Recommended solution: keep ADR-0008 40 A firmware/config budget, 50 A main
  fuse path, 0.5mΩ four-terminal total-current shunt, and stale-current denial.
- Risks: copper cross-section, shunt Kelvin routing, connector/gland derating,
  and enclosure temperature still require schematic/layout and post-prototype
  validation.
- Alternatives: 1.0mΩ shunt for stronger signal at higher loss, Hall sensor
  total-current monitor, or lower configured board budget if thermal validation
  fails.
- Cost impact: moderate, dominated by the four-terminal shunt, current monitor,
  copper/connector margin, and high-current harness parts.
- Thermal impact: CSS4J-4026R-L500F-class 0.5mΩ shunt dissipates 0.8 W at 40 A,
  1.25 W at 50 A, and 1.8 W at 60 A; a 5 W part gives pre-layout electrical
  headroom before PCB copper and enclosure derating.
- Production impact: factory must support Kelvin shunt footprint and AOI; garage
  input wiring must preserve the 50 A fuse and serviceable high-current path.
- Field reliability impact: board survives realistic simultaneous accessory use
  by enforcing total-current budget and shedding by configuration priority.
- Engineering decision: Why this component/solution: independent total-current
  shunt plus firmware limit closes the oversubscription safety gap; Why not
  alternative A: all-channels-at-max sizing inflates board area, connectors, and
  heat without matching real use; Why not alternative B: no total-current
  measurement leaves load shedding blind; Expected lifetime: 10-15 year platform
  target with derated passive shunt; Operating margin: 5 W shunt versus 1.25 W
  at 50 A fuse current; Maximum junction temperature: passive shunt terminal
  temperature replaces semiconductor junction and is post-prototype validated;
  Availability: Bourns CSS4J plus 1.0mΩ and Isabellenhuette/BAS-class
  alternates; Automotive qualification: AEC-Q200 shunt class; LCSC availability:
  local snapshot records JLCPCB pre-order risk; PCBWay/JLCPCB compatibility:
  factory assembly requires package/stock review; Known risks: copper heating
  and zero-stock shunt sources.
- Evidence and calculations:
  `PB-100-board-current-budget-design-calculation.md`,
  `PB-100-board-current-budget-value-freeze-checklist.csv`,
  `PB-100-board-current-budget-value-derivation-precheck.csv`,
  `PB-100-board-current-budget-closeout-precheck.csv`, and
  `firmware/configs/config-example.json`.
- Datasheet and sourcing evidence:
  https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-006 verifies total current budget and
  PB-BENCH-010 verifies sustained thermal behavior.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-003 — Board-to-board interface

- Closeout status: Closed.
- Closure boundary: pre-layout evidence under ADR-0013; PB-BENCH-014/015 still
  gate motorcycle power, field use, and production release.
- Why blocker existed: PB-100 and LB-100 need a stable 100-pin interface before
  schematic/layout work can preserve power, telemetry, safety, and expansion.
- Candidate comparison: Hirose FX18 100-position mezzanine pair is preferred;
  Samtec Q Strip class remains an alternate with sourcing and footprint review;
  Molex SlimStack class remains an alternate but needs equivalent stack-height
  and retention proof.
- Recommended solution: keep `JPB1` as the role-free PB/LB interface using the
  corrected FX18-100P-0.8SV10 plus FX18-100S-0.8SV10 pair, four shared M2.5
  stack holes, four 20.3 +/-0.127 mm spacers, and the closed STM32H563VITx
  LQFP100 resource binding from LB-100.
- Risks: physical continuity, vibration, tray/reel handling, and service damage
  remain post-prototype/production risks; PB-BENCH-014 and PB-BENCH-015 are
  mandatory before motorcycle power, field use, or production release.
- Alternatives: Samtec Q Strip/high-density mezzanine family and Molex SlimStack
  100-position family.
- Cost impact: moderate, expected to be one of the more expensive board-level
  connector choices, but cheaper than redesigning PB-100 later.
- Thermal impact: negligible for signals; power pins and grounds are paralleled
  and remain current/temperature reviewed with the board budget.
- Production impact: connector orientation, coplanarity, and mating-height
  inspection become factory assembly and first-article checks.
- Field reliability impact: high-retention mezzanine and explicit spare pins
  protect future LB revisions without changing PB-100 power architecture.
- Engineering decision: Why this component/solution: FX18 provides 0.8 mm pitch,
  100 positions, guides, and high-density board-to-board architecture; Why not
  alternative A: Samtec path needs a full footprint/current/mating review before
  substitution; Why not alternative B: Molex path needs equivalent vibration and
  stack-height evidence; Expected lifetime: 10-15 year platform target with
  connector family alternates; Operating margin: 100 pins cover required power,
  output control, telemetry, fault, CAN, expansion, and spare reserves; Maximum
  junction temperature: not semiconductor-specific, connector operating
  temperature and contact resistance are the controlling limits; Availability:
  Hirose plus Samtec/Molex alternates; Automotive qualification: connector
  family is not claimed AEC, so vibration/first-article evidence is mandatory;
  LCSC availability: local snapshot records low JLCPCB stock; PCBWay/JLCPCB
  compatibility: factory placement and handling must be reviewed; Known risks:
  low stock, mating tolerance, and service damage.
- Evidence and calculations:
  `PB-100-b2b-pin-map.csv`, `PB-100-b2b-lb100-resource-binding.csv`,
  `PB-100-b2b-lb100-pin-audit-checklist.csv`, and
  `hardware/logic-board/LB-100/LB-100-stm32h563-pin-binding-precheck.csv`, plus
  `PB-100-fx18-paired-stack-closeout.md`.
- Datasheet and sourcing evidence:
  https://www.hirose.com/en/product/series/FX18 and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-014 verifies assembled-stack continuity
  and PB-BENCH-015 verifies vibration/retention after hardware exists.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-004 — High/medium output stage

- Closeout status: Conditional.
- Why blocker existed: OUT2 and medium-current outputs need high-side switching,
  current sense, fault handling, PWM, fuse coordination, and SOA margin before
  output-stage placement or copper can start.
- Candidate comparison: TPS48110AQDGXRQ1 external-controller architecture is
  preferred; integrated smart switches are rejected for Rev.1 voltage-margin
  risk; the Product Owner selected BUK7S1R2-80M 80 V LFPAK88 and rejected the
  former 60 V assembly paths.
- Recommended solution: keep TPS48110AQDGXRQ1 for all output channels and use
  BUK7S1R2-80M 80 V LFPAK88 for Q101-Q110, while keeping IAUTN08S5N012L
  80 V TOLL and BUK7J2R4-80M 80 V LFPAK56E as controlled non-drop-in
  alternatives.
- Risks: OUT2 compressor inrush SOA, gate resistor tuning, inductive clamp
  energy, and thermal copper still require schematic/layout/post-prototype
  validation.
- Alternatives: IAUTN08S5N012L 80 V TOLL or BUK7J2R4-80M 80 V LFPAK56E after
  pin-map, SOA, thermal, footprint, sourcing and assembly review. SIDR626LDP
  and IAUTN06S5N008 remain rejected 60 V history.
- Cost impact: high relative to integrated switches because every channel keeps
  a controller and external MOSFET, but it preserves thermal/service margin.
- Thermal impact: MOSFET conduction loss scales with output current squared;
  80 V MOSFET selection reduces voltage-margin risk but does not remove copper,
  SOA, and enclosure derating work.
- Production impact: factory must handle VSSOP controller and power MOSFET
  packages, with stencil/thermal-pad review and AOI on power pads.
- Field reliability impact: external MOSFET/controller architecture isolates
  roles from hardware and supports serviceable fuses, telemetry, and fault
  lockout per generic output.
- Engineering decision: Why this component/solution: TPS4811-Q1 provides 100 V
  high-side driver capability, diagnostics, IMON, UV/OV, overcurrent, and
  thermal-fault hooks; Why not alternative A: direct 40 V smart switch conflicts
  with SM8S33 clamp margin; Why not alternative B: 60 V MOSFET path leaves less
  overshoot margin unless simulation/bench proves it; Expected lifetime: 10-15
  year platform target with automotive controller and MOSFET families; Operating
  margin: 80 V MOSFET class against 53.3 V TVS clamp point before overshoot;
  Maximum junction temperature: use 175 °C MOSFET class and 150 °C/grade device
  controller limits where selected; Availability: TI/Nexperia plus Vishay/
  Infineon alternates; Automotive qualification: AEC-Q100 controller and
  AEC-Q101 MOSFET candidates; LCSC availability: local snapshot records JLCPCB
  controller and MOSFET source paths; PCBWay/JLCPCB compatibility: power package
  assembly review required; Known risks: OUT2 SOA and package heating.
- Evidence and calculations:
  `PB-100-out2-soa.md`, `PB-100-high-medium-output-freeze-review.csv`,
  `PB-100-output-stage-value-freeze-checklist.csv`,
  `PB-100-output-stage-value-derivation-precheck.csv`, and
  `PB-100-output-stage-closeout-precheck.csv`.
- Datasheet and sourcing evidence:
  https://www.ti.com/lit/ds/symlink/tps4811-q1.pdf,
  https://assets.nexperia.com/documents/data-sheet/BUK7Y3R1-80M.pdf, and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-003, PB-BENCH-004, PB-BENCH-006, and
  PB-BENCH-010 verify output switching, fault response, current budget, and
  thermal behavior.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-005 — Low-current output stage

- Closeout status: Closed.
- Why blocker existed: OUT5, OUT8, and OUT9 previously allowed integrated smart
  switches, but TVS/load-dump margin made direct 40 V smart-switch rails unsafe
  without another protection domain.
- Candidate comparison: external TPS48110 plus MOSFET is preferred by ADR-0011;
  integrated 40 V smart switches are rejected for Rev.1; a lower-clamp rail is
  rejected because it adds another protection domain and architecture risk.
- Recommended solution: use the same TPS48110 external-controller architecture
  for OUT5, OUT8, and OUT9, keeping all outputs generic and no direct 40 V smart
  switch rail.
- Risks: low-current channels pay a cost/area penalty and still need exact
  threshold/timer/gate/filter values in reviewed schematic sheets.
- Alternatives: TPS2HB16-Q1/TPS2HB35-Q1 direct smart switches after a future
  lower-clamp ADR, local clamp network, or the same 80 V MOSFET class as medium
  outputs.
- Cost impact: moderate increase versus integrated switch, acceptable for
  prototype reliability and architecture consistency.
- Thermal impact: improved thermal margin versus integrated switch package
  heating at 4 A; MOSFET losses remain lower and easier to spread into copper.
- Production impact: common controller/MOSFET pattern reduces schematic review
  variance across all 10 outputs at the cost of more placements.
- Field reliability impact: uniform output behavior simplifies diagnostics,
  spare-channel behavior, and firmware capability discovery.
- Engineering decision: Why this component/solution: external-controller path
  keeps voltage margin and common diagnostics; Why not alternative A: integrated
  smart switch creates 40 V absolute-maximum conflict behind SM8S33 clamp; Why
  not alternative B: local clamp/lower rail adds new failure modes; Expected
  lifetime: 10-15 year platform target with common automotive output family;
  Operating margin: no direct 40 V path on transient-clamped rail; Maximum
  junction temperature: use selected MOSFET/controller datasheet limits and
  derating; Availability: TPS48110 and MOSFET alternates retained; Automotive
  qualification: AEC-Q100/AEC-Q101 candidate families; LCSC availability: local
  snapshot records preferred/alternate source paths; PCBWay/JLCPCB
  compatibility: same assembly review as medium outputs; Known risks: added
  BOM cost and board area.
- Evidence and calculations:
  `docs/adr/ADR-0011-pb-100-low-current-output-stage.md`,
  `PB-100-low-current-output-freeze-review.csv`,
  `PB-100-output-stage-value-freeze-checklist.csv`,
  `PB-100-output-stage-value-derivation-precheck.csv`, and
  `PB-100-output-stage-closeout-precheck.csv`.
- Datasheet and sourcing evidence:
  https://www.ti.com/lit/ds/symlink/tps4811-q1.pdf and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-003, PB-BENCH-004, and PB-BENCH-005 cover
  low-current output switching, fault behavior, and current telemetry.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-006 — Input reverse protection

- Closeout status: Conditional.
- Why blocker existed: the 40 A protected input path needs reverse-battery
  protection with low loss, load-dump voltage margin, gate control, and package
  thermal evidence.
- Candidate comparison: LM74700QDBVRQ1 ideal-diode controller plus 80 V
  BUK7S1R2-80M-class LFPAK88 MOSFET is selected; IAUTN08S5N012L 80 V TOLL
  and BUK7J2R4-80M 80 V LFPAK56E are non-drop-in alternatives. The 60 V
  IAUTN06S5N008 and SIDR626LDP paths are rejected for Rev.1 assembly.
- Recommended solution: lock the schematic-review direction to LM74700-Q1 plus
  Q1 80 V LFPAK88 BUK7S1R2-80M-class path, with gate clamp/turn-off values
  derived in schematic review.
- Risks: LFPAK88 assembly support, copper thermal model, gate clamp values, and
  negative transient behavior still need footprint and bench validation.
- Alternatives: IAUTN08S5N012L 80 V TOLL, BUK7J2R4-80M 80 V LFPAK56E, or the
  LM74502-Q1 controller family after controlled electrical and package review.
- Cost impact: moderate; the 80 V LFPAK88 path may cost more than a 60 V TOLL
  path but buys voltage margin and package current density.
- Thermal impact: 1.2mΩ nominal class gives 1.92 W at 40 A before temperature
  multiplier and copper derating; this is lower than a 2.1mΩ single PowerPAK
  class and must be validated in enclosure.
- Production impact: power package footprint, stencil, AOI, and rework limits
  need first-article review before PCB release.
- Field reliability impact: ideal-diode behavior reduces reverse-battery loss
  and avoids a series diode heat source on the main input path.
- Engineering decision: Why this component/solution: LM74700-Q1 supports
  low-loss external NMOS reverse protection and BUK7S1R2-80M adds 80 V headroom;
  Why not alternative A: 60 V TOLL has excellent RDS(on) but insufficient
  transient margin without overshoot evidence; Why not alternative B: dual
  PowerPAK path adds current sharing and placement complexity; Expected
  lifetime: 10-15 year platform target with automotive controller/MOSFET; 
  Operating margin: 80 V MOSFET class against 53.3 V TVS clamp point before
  overshoot; Maximum junction temperature: 175 °C MOSFET class and selected
  controller temperature limits; Availability: TI/Nexperia plus Infineon/Vishay
  alternates; Automotive qualification: AEC-Q100 controller and AEC-Q101 MOSFET;
  LCSC availability: local snapshot tracks stock risk; PCBWay/JLCPCB
  compatibility: LFPAK88/TOLL assembly review required; Known risks: package
  soldering and input copper heating.
- Evidence and calculations:
  `PB-100-input-reverse-protection.md`,
  `PB-100-input-reverse-package-trace.csv`,
  `PB-100-input-reverse-q1-freeze-checklist.csv`,
  `PB-100-input-reverse-q1-derivation-precheck.csv`, and
  `PB-100-input-reverse-q1-closeout-precheck.csv`.
- Datasheet and sourcing evidence:
  https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf,
  https://assets.nexperia.com/documents/data-sheet/BUK7S1R2-80M.pdf, and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-001, PB-BENCH-002, PB-BENCH-006, and
  PB-BENCH-010 verify input polarity, transient behavior, current budget, and
  thermal behavior.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-007 — TVS/load-dump protection

- Closeout status: Conditional.
- Why blocker existed: SM8S33-class TVS clamp can stress 60 V downstream parts
  after overshoot, so schematic freeze needed a voltage-margin escape path.
- Candidate comparison: Vishay SM8S33AHM3/I HM3 DO-218AC TVS is preferred for
  active AEC-Q101 load-dump class; obsolete MCC/NFD HE3 paths are rejected for
  lock; 80 V downstream MOSFET and 100 V buck selections are preferred over
  accepting unproven 60 V overshoot margin.
- Recommended solution: keep the SM8S33AHM3/I TVS branch and the selected
  80 V MOSFET baseline while retaining 100 V TPS4811 and LM5164/LM5013-class
  devices. Voltage-class choice is closed; the blocker remains Conditional
  until actual clamp-loop overshoot and TVS pulse-energy evidence closes.
- Risks: board-level overshoot, TVS heating, trace inductance, and pulse energy
  still require simulation/bench validation after physical design.
- Alternatives: Littelfuse SLD8S33A, Diodes DM8W33AQ-13, Bourns SM8S33A-Q
  class, or lower-clamp strategy after future review.
- Cost impact: low to moderate; the HM3 TVS and 80 V MOSFET choices cost more
  than lowest-cost 60 V paths but reduce load-dump risk.
- Thermal impact: TVS pulse heating is not a continuous dissipation item, but
  copper, pulse spacing, and enclosure heating must be validated; 80 V MOSFETs
  may increase RDS(on) versus 60 V candidates.
- Production impact: DO-218AC placement/stencil/inspection must be reviewed and
  obsolete/NFD sources must not be used for BOM lock.
- Field reliability impact: active TVS plus downstream 80 V/100 V headroom
  reduces latent damage during motorcycle load dump and jump-start transients.
- Engineering decision: Why this component/solution: SM8S33AHM3/I gives active
  automotive TVS evidence and 53.3 V clamp-class data; Why not alternative A:
  obsolete MCC/NFD sources are not lifecycle-safe; Why not alternative B: keeping
  60 V-only downstream paths requires unproven overshoot margin; Expected
  lifetime: 10-15 year platform target with active-source TVS alternates;
  Operating margin: 80 V MOSFET/100 V regulator classes above 53.3 V clamp
  point before overshoot; Maximum junction temperature: TVS/package pulse
  derating and MOSFET/regulator junction limits remain reviewed separately;
  Availability: Vishay HM3 plus Littelfuse/Diodes/Bourns alternates; Automotive
  qualification: AEC-Q101 TVS branch; LCSC availability: local snapshot records
  JLCPCB source path; PCBWay/JLCPCB compatibility: DO-218AC handling review
  required; Known risks: trace inductance overshoot and TVS pulse energy.
- Evidence and calculations:
  `PB-100-tvs-load-dump-margin-trace.csv`,
  `PB-100-tvs-load-dump-freeze-review.csv`,
  `PB-100-tvs-overshoot-escape-checklist.csv`,
  `PB-100-tvs-overshoot-validation-precheck.csv`, and
  `PB-100-tvs-overshoot-closeout-precheck.csv`.
- Datasheet and sourcing evidence:
  https://www.vishay.com/docs/98647/sm8s85ahm3.pdf,
  https://www.digikey.com/en/products/detail/vishay-general-semiconductor-diodes-division/SM8S33AHM3-I/25675894,
  and `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-002 verifies transient/load-dump behavior
  on the assembled board before field use.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-008 — Logic power rails

- Closeout status: Closed.
- Why blocker existed: PB-100 must provide a protected `PB_5V_OUT` rail for
  LB-100/PB low-power circuits without tying logic reliability to accessory
  loads or 60 V-only buck families.
- Candidate comparison: LM5164QDDATQ1 100 V 1 A buck is preferred; LM5013-Q1
  100 V 3.5 A remains the high-current fallback; TPS54360B-Q1 60 V family is
  rejected unless TVS overshoot margin is explicitly accepted.
- Recommended solution: keep LM5164-Q1 100 V 1 A as Rev.1 baseline with
  LM5013-Q1 fallback if LB/PB budget exceeds 1 A after schematic review.
- Risks: inductor saturation, RON/frequency, feedback tolerance, UVLO, PGOOD,
  EMI filter, and switch-node ringing still require value-bearing schematic
  review.
- Alternatives: LM5013-Q1 for more current, LM5163-Q1 if current budget drops,
  or TPS54360B-Q1 only after voltage-margin evidence.
- Cost impact: moderate; 100 V automotive buck and shielded inductor cost more
  than commodity 60 V regulators but reduce transient risk.
- Thermal impact: 1 A rail requires buck efficiency and inductor loss review;
  thermal risk is lower than power outputs but close to logic reliability.
- Production impact: SO PowerPAD/inductor/capacitor package availability and
  orientation must be checked before BOM lock.
- Field reliability impact: 100 V input headroom and explicit PGOOD/UVLO improve
  cold-crank, load-dump, and fail-safe output-disable behavior.
- Engineering decision: Why this component/solution: LM5164-Q1 is an automotive
  6 V to 100 V 1 A synchronous buck; Why not alternative A: LM5013-Q1 adds
  current but also size/thermal cost until budget requires it; Why not
  alternative B: 60 V buck path conflicts with unproven TVS overshoot margin;
  Expected lifetime: 10-15 year platform target with TI 100 V family; Operating
  margin: 100 V input class on protected rail; Maximum junction temperature:
  selected regulator junction limit and inductor temperature rise reviewed in
  schematic/layout; Availability: TI LM5164/LM5013 plus alternates; Automotive
  qualification: AEC-Q100 regulator candidates; LCSC availability: local
  snapshot records LM5164 JLCPCB pre-order risk; PCBWay/JLCPCB compatibility:
  SO PowerPAD and inductor assembly review required; Known risks: stock and EMI.
- Evidence and calculations:
  `PB-100-logic-power-design-calculation.md`,
  `PB-100-logic-power-value-freeze-checklist.csv`,
  `PB-100-logic-power-value-derivation-precheck.csv`,
  `PB-100-logic-power-closeout-precheck.csv`, and
  `hardware/logic-board/LB-100/LB-100-power-budget-precheck.md`.
- Datasheet and sourcing evidence:
  https://www.ti.com/lit/ds/symlink/lm5164-q1.pdf,
  https://www.ti.com/product/LM5013-Q1, and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-001 and PB-BENCH-013 verify first power
  and rail behavior before motorcycle power.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-009 — Current telemetry

- Closeout status: Closed.
- Why blocker existed: per-output and total-current measurements are safety
  inputs for current limits, load shedding, diagnostics, and stale-telemetry
  fail-safe behavior.
- Candidate comparison: TPS48110 IMON plus INA228-Q1 total-current monitor is
  preferred; ADC-only total-current sensing is rejected for lower accuracy and
  calibration burden; INA226 remains an alternate with lower bus voltage/range
  tradeoffs.
- Recommended solution: use controller IMON for OUT1..OUT10 and INA228-Q1 with
  0.5mΩ four-terminal shunt for board total current, keeping calibration in
  configuration/firmware and stale telemetry as unavailable capability/fault.
- Risks: shunt Kelvin routing, input filters, I2C address/pullups, alert timing,
  and calibration constants still require schematic and firmware review.
- Alternatives: INA229-Q1, INA226, external analog monitor, or Hall sensor for
  total current.
- Cost impact: moderate; precision monitor plus four-terminal shunt adds cost
  but closes the safety budget requirement.
- Thermal impact: shunt loss is 0.8 W at 40 A and 1.25 W at 50 A; monitor IC
  heat is minor compared with shunt and copper.
- Production impact: Kelvin footprint orientation, shunt solder volume, AOI, and
  calibration hooks must be included in factory and bench process.
- Field reliability impact: independent total-current telemetry lets firmware
  deny unsafe loads when per-output telemetry is stale or missing.
- Engineering decision: Why this component/solution: INA228-Q1 supports 85 V
  common-mode and ±40.96 mV/±163.84 mV shunt ranges for the 0.5mΩ path; Why not
  alternative A: ADC-only path lacks digital monitor accuracy/alert features;
  Why not alternative B: INA226 has less voltage/range headroom; Expected
  lifetime: 10-15 year platform target with automotive monitor/shunt families;
  Operating margin: 20 mV at 40 A and 30 mV at 60 A fit ±40.96 mV range;
  Maximum junction temperature: monitor device temperature limit and shunt
  terminal temperature are reviewed separately; Availability: INA228/INA229/
  INA226 and shunt alternates; Automotive qualification: INA228-Q1 AEC-Q100 and
  shunt AEC-Q200 class; LCSC availability: local snapshot records JLCPCB monitor
  stock and shunt stock risk; PCBWay/JLCPCB compatibility: VSSOP and CSS4J
  assembly review required; Known risks: shunt source and calibration.
- Evidence and calculations:
  `PB-100-current-telemetry-design-calculation.md`,
  `PB-100-current-telemetry-value-freeze-checklist.csv`,
  `PB-100-current-telemetry-value-derivation-precheck.csv`,
  `PB-100-current-telemetry-closeout-precheck.csv`, and
  `PB-100-current-telemetry-map.csv`.
- Datasheet and sourcing evidence:
  https://www.ti.com/product/INA228-Q1,
  https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf, and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-005 covers current telemetry and
  PB-BENCH-006 covers board total-current enforcement.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-010 — Thermal telemetry

- Closeout status: Closed.
- Why blocker existed: PB-100 needs board and power-zone temperature sensing to
  derate outputs and detect stale or missing telemetry before field use.
- Candidate comparison: TDK NTCGS103JF103FT8-class 10k AEC-Q200 NTCs are
  preferred; Vishay NTCS0402E3 and Murata NCU automotive NTCs are alternates;
  digital sensors are deferred because they add bus/power dependencies near hot
  power zones.
- Recommended solution: use three NTC points, `TEMP_PCB`, `TEMP_PWR_A`, and
  `TEMP_PWR_B`, with divider/calibration values owned by schematic review and
  firmware configuration.
- Risks: sensor placement, self-heating, ADC acquisition time, divider tolerance,
  and calibration thresholds remain schematic/layout/post-prototype work.
- Alternatives: Vishay NTCS0402E3 10k AEC-Q200, Murata NCU18 automotive NTC,
  or optional TMP117/TMP112-class digital sensor for a future board variant.
- Cost impact: low, mostly three NTCs, resistors, ADC filtering, and test hooks.
- Thermal impact: NTC self-heating is low but must be bounded by divider current;
  thermal coupling to MOSFET zones is layout-dependent.
- Production impact: 0402 placement and orientation are routine factory SMT but
  need AOI and placement-zone review.
- Field reliability impact: derating can fail safe when a sensor is stale,
  missing, shorted, or open, preserving capability-driven firmware behavior.
- Engineering decision: Why this component/solution: TDK NTC class is small,
  AEC-Q200, and suitable for 150 °C-class sensing; Why not alternative A:
  digital sensor adds I2C/power dependency at hot zones; Why not alternative B:
  single board sensor cannot represent input and output power-zone gradients;
  Expected lifetime: 10-15 year platform target with AEC-Q200 passive sensors;
  Operating margin: 150 °C sensor class above normal enclosure targets;
  Maximum junction temperature: passive NTC maximum operating temperature
  replaces semiconductor junction; Availability: TDK/Vishay/Murata alternates;
  Automotive qualification: AEC-Q200 candidate families; LCSC availability:
  local snapshot records JLCPCB stock for TDK candidate; PCBWay/JLCPCB
  compatibility: 0402 SMT assembly review required; Known risks: placement and
  calibration.
- Evidence and calculations:
  `PB-100-thermal-telemetry-design-calculation.md`,
  `PB-100-thermal-telemetry-value-freeze-checklist.csv`,
  `PB-100-thermal-telemetry-value-derivation-precheck.csv`,
  `PB-100-thermal-telemetry-closeout-precheck.csv`, and
  `PB-100-thermal-telemetry-map.csv`.
- Datasheet and sourcing evidence:
  https://product.tdk.com/system/files/dam/doc/product/sensor/ntc/chip-ntc-thermistor/catalog/tpd_automotive_ntc-thermistor_ntcgs_en.pdf,
  https://www.vishay.com/en/product/29003/, and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-009 verifies thermal telemetry and
  derating behavior on assembled hardware.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-011 — Factory assembly readiness

- Closeout status: Conditional.
- Why blocker existed: critical factory-populated PB-100 parts needed dated
  manufacturer/distributor/JLCPCB/PCBWay evidence, package handling notes, DNP
  inspection, and alternatives before blocker closure.
- Candidate comparison: JLCPCB Extended plus authorized distributor sourcing is
  preferred for prototype; PCBWay remains a parallel assembly path; unsupported
  manual assembly of VSSOP, PowerPAK, TOLL, LFPAK88, DO-218AC, CSS4J, and FX18
  packages is rejected.
- Recommended solution: keep factory-owned critical keys in
  `production/bom/pb100_sourcing_evidence_snapshot.csv` and
  `pb100_assembly_sourcing_recheck.csv`, with at least two alternatives for
  critical functions and exact BOM lock deferred to schematic/layout release.
- Risks: low/zero stock items, consign/pre-order rows, package-specific
  inspection, rework limits, and DNP/open production instructions require
  recheck before PCBA order.
- Alternatives: authorized distributor consignment, PCBWay sourcing, or selected
  alternate MPNs from the component-family shortlist.
- Cost impact: moderate; Extended/consigned assembly and automotive-grade parts
  cost more but avoid garage rework risk.
- Thermal impact: factory assembly quality directly affects power-pad thermal
  impedance for output/input MOSFETs, TVS, shunt, and buck power components.
- Production impact: requires factory assembly notes, DNP/open inspection,
  stencil review, first-article review, and no BOM/CPL lock before schematic
  freeze.
- Field reliability impact: factory placement of critical SMDs reduces solder
  defects and keeps garage assembly limited to serviceable high-current items.
- Engineering decision: Why this component/solution: factory assembly matches
  ADR-0003 and avoids manual fine-pitch/power-package soldering; Why not
  alternative A: garage soldering VSSOP/power packages is not reliable; Why not
  alternative B: lowest-cost non-automotive substitutions reduce lifecycle and
  thermal margin; Expected lifetime: 10-15 year platform target with
  automotive-qualified critical families; Operating margin: package/thermal
  margins remain reviewed per power component; Maximum junction temperature:
  use each selected semiconductor/passive datasheet limit; Availability:
  manufacturer/distributor/JLCPCB/PCBWay evidence is date-stamped; Automotive
  qualification: AEC-Q100/Q101/Q200 preferred; LCSC availability: local snapshot
  records exact JLCPCB componentSearch results; PCBWay/JLCPCB compatibility:
  package-specific review is required; Known risks: stock churn and rework.
- Evidence and calculations:
  `PB-100-factory-assembly-platform-evidence.csv`,
  `PB-100-factory-assembly-sourcing-precheck.csv`,
  `PB-100-factory-assembly-freeze-checklist.csv`,
  `PB-100-factory-assembly-closeout-precheck.csv`,
  `production/bom/pb100_assembly_sourcing_recheck.csv`, and
  `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Datasheet and sourcing evidence:
  `docs/production/component-family-shortlist.md` plus the manufacturer and
  distributor links recorded in `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-014 verifies assembly inspection and
  production DNP/open handling before field use.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.

## PBREL-012 — Garage assembly readiness

- Closeout status: Closed.
- Why blocker existed: user-installed items must stay limited to connectors,
  fuses, enclosure hardware, and wiring, with exact current rating, wire gauge,
  crimp tooling, seals, and service access documented before purchase lock.
- Candidate comparison: TE DEUTSCH DTP/DT sealed connector classes and
  Littelfuse MAXI/MINI/ATO fuse-holder classes are preferred; PCB-mounted power
  connectors are rejected for serviceability and thermal strain; DTM is rejected
  for output power and kept only for signal-level paths.
- Recommended solution: keep input/main fuse and output connectors/fuse holders
  garage-installed, use DTP size-12 25 A class for high-current outputs, DT
  size-16 13 A class for medium/low outputs, and Littelfuse MAXI 152 near the
  battery input path.
- Risks: exact kit quantities, supplier stock, boots, backshells, insertion/
  removal tools, enclosure gland, heat, vibration, and service access still need
  purchase-lock review.
- Alternatives: sealed serviceable gland plus internal pigtail, Deutsch-compatible
  sealed connector families, or external fuse block where enclosure service is
  better.
- Cost impact: high for garage kit, likely tens to low hundreds of USD, but it
  avoids unsafe PCB-mounted high-current service items.
- Thermal impact: off-board fuse/connector heat is separated from PCB; crimp and
  wire gauge derating still control field temperature rise.
- Production impact: no factory placement for garage items; BOM split and build
  instructions must stay separate from PCBA outputs.
- Field reliability impact: sealed serviceable connectors and near-battery main
  fuse improve maintainability and reduce vehicle wiring risk.
- Engineering decision: Why this component/solution: sealed TE DEUTSCH and
  Littelfuse automotive fuse-holder classes are serviceable and current-rated;
  Why not alternative A: PCB-mounted high-current connectors put service heat
  and strain into PB-100; Why not alternative B: DTM signal connectors are not
  output-power rated; Expected lifetime: 10-15 year platform target with
  replaceable garage harness items; Operating margin: DTP 25 A contacts support
  high-current channel class and MAXI 152 holder covers 50 A near-battery path;
  Maximum junction temperature: connector/fuse-holder temperature rise replaces
  semiconductor junction and is bench validated; Availability: TE/Littelfuse
  plus compatible alternates; Automotive qualification: sealed automotive
  connector/fuse-holder classes; LCSC availability: not required for garage
  items; PCBWay/JLCPCB compatibility: off-board and excluded from PCBA; Known
  risks: crimp quality, seal fit, and service routing.
- Evidence and calculations:
  `PB-100-garage-purchase-kit-candidates.csv`,
  `PB-100-garage-install-sourcing-precheck.csv`,
  `PB-100-garage-install-freeze-checklist.csv`,
  `PB-100-garage-install-closeout-precheck.csv`, and
  `production/bom/garage_bom_draft.csv`.
- Datasheet and sourcing evidence:
  https://www.te.com/en/product-DTP06-2S.html,
  https://www.littelfuse.com/products/fuses-overcurrent-protection/fuse-holders-fuse-blocks-accessories/fuse-holders/in-line-fuse-holders/maxi-152,
  and `production/bom/pb100_sourcing_evidence_snapshot.csv`.
- Post-prototype validation: PB-BENCH-015 verifies garage assembly and service
  inspection before field use.
- No-layout boundary: Does not authorize PCB layout, `PB-100.kicad_pcb`,
  Gerbers, drills, pick-place, BOM/CPL, manufacturing ZIP, or PCBA order.
