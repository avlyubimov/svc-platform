# PB-100 Footprint Binding Closeout 2026-07-20

Status: Footprint-binding evidence update

Historical scope note: the package rows listed as remaining at the end of this
2026-07-20 record were subsequently closed. The current selected MOSFET is
`IAUT300N08S5N012ATMA2` PG-HSOF-8-1 TOLL; the current footprint status is
authoritative in `PB-100-footprint-binding-progress.csv`.

This closeout binds two package-specific PB-100 footprint rows without changing
architecture and without creating `PB-100.kicad_pcb`, Gerbers, drill files,
pick-place files, BOM/CPL order packages, manufacturing ZIP files, fabrication
packages, panel outputs, or PCBA orders.

## Scope

| Item | Close result |
|---|---|
| Logic buck alternate | `LM5013-Q1` remains an alternate only and reuses the existing reviewed `PB100:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL-EP2.9` SO PowerPAD-8 footprint evidence |
| CAN1 TX disable hardware | `JP_CAN1` gets a local 0603 DNP/open link footprint and `U_CAN1` gets a local TI DBV SOT-23-5 gate footprint candidate while the default TX route remains physically open |

## Logic Buck Alternate

- Why the blocker existed: `LM5013-Q1` was listed as a higher-current 100 V logic-power alternate but the footprint inventory did not yet prove that its package could use the local SO PowerPAD footprint already imported for `LM5164QDDATQ1`.
- Candidate comparison: `LM5164QDDATQ1` remains the preferred 100 V 1 A synchronous buck because it is already selected for the protected 5 V budget. `LM5013-Q1` is a higher-current 100 V non-synchronous alternate and is not selected by this footprint closeout. `TPS54360B-Q1` remains a conditional 60 V alternate and does not close this SO PowerPAD-8 footprint row.
- Recommended solution: keep `LM5164QDDATQ1` as the default and bind `LM5013-Q1` only as a package-compatible DDA SO PowerPAD-8 alternate using `hardware/power-board/PB-100/kicad/lib/PB100.pretty/SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL-EP2.9.kicad_mod`.
- Datasheet evidence: TI documentation identifies `LM5013-Q1` as an AEC-Q100 Grade 1 device in 8-pin SO PowerPAD with 1.27 mm pitch and identifies `LM5164-Q1` as AEC-Q100 Grade 1 in 8-pin DDA SO PowerPAD with 1.27 mm pitch.
- Why this component: it preserves a high-current 100 V escape path without changing the Rev.1 logic-power architecture.
- Why not alternative A: do not switch the default from `LM5164QDDATQ1` because the current 5 V budget does not require the higher-current non-synchronous alternate.
- Why not alternative B: do not bind `TPS54360B-Q1` for this row because it is the 60 V conditional escape path and has different package and transient-margin implications.
- Expected lifetime: unchanged from the selected TI automotive regulator class because this closeout is footprint binding only.
- Operating margin: no electrical margin is claimed by this footprint closeout; logic-power current ripple inductor and thermal margin remain separate schematic/layout gates.
- Maximum junction temperature: no new `Tj` claim is made here. Junction-temperature margin remains part of logic-power thermal review.
- Availability: TI product pages remain primary source evidence. JLCPCB/LCSC and authorized-distributor availability still require recheck before BOM lock.
- Automotive qualification: both preferred and alternate TI Q1 regulator paths are automotive-qualified evidence classes.
- LCSC availability: `LM5164QDDATQ1` has the existing JLCPCB/LCSC evidence row. `LM5013-Q1` remains an alternate and must be rechecked before population.
- PCBWay/JLC compatibility: SO PowerPAD-8 is factory-assembly compatible in principle but exposed-pad paste thermal-via and inspection notes remain layout/DFM gates.
- Cost impact: no prototype BOM increase because the alternate is not selected or populated by this closeout.
- Thermal impact: none until the alternate is selected. If selected later it needs its own efficiency and exposed-pad thermal review.
- Production impact: schematic symbol promotion may use the same local SO PowerPAD footprint for the alternate row but must not change the selected regulator without evidence.
- Field reliability: preserving a documented alternate improves sourcing resilience while avoiding an unreviewed regulator swap.
- Known risks: package similarity does not close inductor compensation EMI switch-node or thermal layout review.

## CAN1 TX Disable Hardware

- Why the blocker existed: the CAN1 safety scaffold had `JP_CAN1` and `U_CAN1` with empty footprint properties while ADR-0002 requires a physical default-disabled vehicle-CAN TX path.
- Candidate comparison: a 0603 DNP/open link provides the physical missing-link barrier and visible production DNP inspection point. A normally-open solder bridge is simpler but less BOM-auditable for factory assembly. An `SN74LVC1G125-Q1` DBV gate adds reset/unpowered electrical disable and physical disabled-status readback but does not replace the DNP/open link.
- Recommended solution: bind both the default `JP_CAN1` 0603 DNP/open link and the `SN74LVC1G125-Q1` DBV gate candidate while keeping `JP_CAN1` DNP/open and keeping CAN1 TX impossible in the default assembly.
- Datasheet evidence: TI `SN74LVC1G125-Q1` identifies AEC-Q100 Grade 1 qualification, 1.65 V to 5.5 V operation, output disable when `OE` is high, `CLVC1G125QDBVRQ1` SOT-23-5 DBV package, and the DBV0005A land pattern with five 1.1 mm by 0.6 mm pads, 0.95 mm pitch, and 2.6 mm row spacing.
- Why this component: `SN74LVC1G125-Q1` gives a non-inverting 3-state buffer whose high `OE` state disables the output and matches the existing `CAN1_TX_DISABLE_CMD` default-disable concept.
- Why not alternative A: a solder bridge alone does not provide gate-state readback or an OE default-disabled electrical barrier.
- Why not alternative B: `SN74LV1T125-Q1` or transceiver silent-control-only can be valid future alternatives but they change level-shift or transceiver ownership details and need a separate review if selected.
- Expected lifetime: the default DNP/open link has no current stress. If the gate is populated it operates as a low-current logic device within the automotive Grade 1 temperature envelope.
- Operating margin: the gate supports the LB logic range because its supply range covers 1.65 V to 5.5 V. The TX route remains physically open by default so firmware cannot create vehicle-CAN TX.
- Maximum junction temperature: the datasheet absolute maximum junction temperature is 150 °C. The Rev.1 gate load is logic-level and should be reviewed against board ambient during layout.
- Availability: JLCPCB evidence exists for the `SN74LVC1G125-Q1` class but the current snapshot records a stock-zero consign risk. Authorized-distributor or PCBWay sourcing remains required before BOM lock.
- Automotive qualification: the selected class is AEC-Q100 qualified. A DNP 0 Ω link should use an AEC-Q200 0603 jumper class if a future ADR permits population.
- LCSC availability: `C9900262991` remains recorded as the JLCPCB/LCSC candidate for the gate footprint. The DNP 0603 link uses a generic factory passive footprint and is not a default-populated TX item.
- PCBWay/JLC compatibility: both SOT-23-5 and 0603 footprints are normal SMT assembly classes. Production notes must still preserve DNP/open inspection and no default-populated TX path.
- Cost impact: negligible for footprint binding. The default 0 Ω link is DNP and the gate adds only a low-cost logic device if retained.
- Thermal impact: negligible for logic signaling. No power-copper thermal claim is made.
- Production impact: adds clear local footprint evidence for symbol promotion while keeping the factory BOM default as DNP/open for `JP_CAN1`.
- Field reliability: improves safety because CAN1 TX remains blocked by both production DNP/open state and default-disabled gate behavior.
- Known risks: JLC stock-zero consign status, first-article DNP inspection, disabled-status readback polarity, and reset/unpowered bench verification remain BOM lock and post-prototype gates.

## Historical state at this closeout

At the time of this record the following rows still required review; they are
not current blockers:

- TOLL / PG-HSOF-8-1 input-reverse and OUT2 escape MOSFET path.
- Historical LFPAK88 package-evidence path.
- DO-218AC input TVS.
- CSS4J-4026 four-terminal current shunt.
- Optional digital temperature sensor if retained as DNP.

Those rows were later closed by exact symbol/footprint and generated evidence.
No PCB layout or manufacturing output is authorized by this historical record.
