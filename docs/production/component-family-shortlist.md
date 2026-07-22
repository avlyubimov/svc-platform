# Component Family Shortlist

Status: PB-100 critical power selections synchronized; remaining families are shortlist items

Evidence snapshot date: 2026-07-21

This document selects component families for schematic planning. It is not a
final MPN lock. LCSC/JLCPCB/PCBWay availability, assembly class, price, and
substitution risk must be rechecked before schematic freeze and before each PCBA
order.

## Selection rules

- Prefer automotive-qualified or automotive-targeted parts.
- Prefer packages suitable for factory SMD assembly.
- Prefer LCSC/JLCPCB availability where possible.
- Keep at least two viable alternatives for critical functions.
- Do not choose BGA for Rev.1 unless a later ADR accepts the tradeoff.

## Shortlist

| Function | Preferred family | Alternatives | Package direction | Notes |
|---|---|---|---|---|
| LB-100 MCU | STM32H563 | STM32H573; STM32F407 for prototypes only | LQFP-100 preferred | STM32H5 target accepted in ADR-0005 |
| Vehicle CAN transceiver | NXP TJA1051/TJA1057 | TI TCAN1042-Q1 | SOIC-8 or VSON/HVSON | CAN1 TX remains physically disabled by default |
| Expansion CAN transceiver | TI TCAN1042-Q1 | NXP TJA1051/TJA1057 | SOIC-8 or VSON/HVSON | CAN2 may transmit for bench or accessory use |
| High-side output controller | TI TPS4811-Q1 | TI TPS1211-Q1; TI TPS4810-Q1 | VSSOP/HTSSOP class | Rev.1 baseline for all PB-100 outputs with external N-MOSFETs |
| Smart high-side switch | TI TPS2HB16-Q1 | TI TPS2HB35-Q1; TI TPS1H100-Q1 | HTSSOP class | Deferred low-current alternate after ADR-0011; requires lower-clamp strategy |
| Output MOSFET | Infineon IAUT300N08S5N012ATMA2 80 V TOLL selected | Infineon IAUT300N08S5N014ATMA1 same-footprint TOLL; Nexperia BUK7J2R4-80MX 80 V LFPAK56E non-drop-in | PG-HSOF-8-1 TOLL selected with segmented paste | Generated per-class SOA and pre-layout sourcing pass; exact sheet-value promotion and physical acceptance remain gates |
| Current monitor | TPS48110 IMON for outputs; TI INA228/INA229 or INA226 for input | External analog monitor; firmware-calibrated ADC path | VSSOP/SOIC class | Per-output telemetry uses controller IMON; total input current uses dedicated shunt monitor |
| Total current shunt | Bourns CSS4J-4026R-L500F-class 0.5 mΩ four-terminal shunt | Bourns CSS4J-4026R-1L00F-class 1.0 mΩ; Isabellenhuette BVN/BAS or equivalent AEC-Q200 four-terminal family | CSS4J-4026 or reviewed power shunt | 0.5 mΩ gives 30 mV at 60 A and 1.8 W; compatible with INA228 ±40.96 mV range candidate |
| Temperature sensor | TDK NTCGS103JF103FT8-class 10 kΩ AEC-Q200 NTC | Vishay NTCS0402E3 10 kΩ AEC-Q200 150 °C class; Murata NCU18XH103D6SRB-class 10 kΩ 0603 AEC-Q200 150 °C; TI TMP117/TMP112-class digital sensor optional | 0402 preferred for NTC; SOT/DFN only for optional digital sensor | PB-100 uses PCB reference plus two power-zone thermal points; divider values and calibration remain schematic-freeze items |
| Logic buck regulator | TI LM5164-Q1 | TI LM5013-Q1; TI TPS54360B-Q1/TPS54360-Q1 | SOIC/HSOIC PowerPAD | LM5164-Q1 for 1 A 100 V rail; LM5013-Q1 preferred over 60 V family if more current is needed |
| Input active cutoff and reverse protection | TI LM74930QRGERQ1 selected | TI LM74800-Q1 family; TI LM74900-Q1 family after full cutoff/timing revalidation | VQFN-24 RGE selected | Common-source hard cutoff must remain no higher than 55 V |
| Raw-side surge cutoff MOSFET | Infineon IAUTN15S6N025ATMA1 150 V TOLL selected | 150 V automotive TOLL family; 150 V automotive LFPAK family after SOA/footprint revalidation | PG-HSOF-8-1 TOLL selected | Generated transition-energy screen passes; extracted dynamic SOA remains post-layout |
| Input reverse MOSFET | Infineon IAUT300N08S5N012ATMA2 80 V TOLL selected | Infineon IAUT300N08S5N014ATMA1 same-footprint TOLL; Nexperia BUK7J2R4-80MX 80 V LFPAK56E non-drop-in | PG-HSOF-8-1 TOLL selected with segmented paste | Generated 40 A thermal bound and pre-layout sourcing pass; plane/polygon/bus and prototype thermal acceptance remain gates |
| Legacy input TVS | Vishay SM8S33AHM3/I DNP only | Littelfuse SLD8S33A; Diodes DM8W33AQ-13; Bourns SM8S33A-Q retained as rejected comparisons | DO-218AC footprint retained unpopulated | A single TVS is not the approved load-dump solution under ADR-0018 |
| PB-100/LB-100 board-to-board connector | Hirose FX18-100P-0.8SV10 plus FX18-100S-0.8SV10 selected pair | Samtec Q Strip/high-density mezzanine class; Molex SlimStack 100-position class | 100-position 0.8 mm FX18 official 20 mm stack | Six-land footprints, MF ownership, four-spacer retention, fixture, and pre-layout mechanics are closed; live stock, factory handling, and PB-BENCH-014/015 remain release gates |
| FRAM | Fujitsu/Infineon MB85 I2C/SPI FRAM | Cypress/Infineon Excelon FRAM | SOIC/TSSOP/DFN | Configuration and black-box storage |
| RTC | Microchip MCP7940 class | NXP PCF8523/PCF8563; DS3231 class | SOIC/TSSOP/DFN/module | Prefer low-IQ SMD IC over hobby module |
| IMU | Bosch BMI270/BMI323 | TDK ICM-42688 class | LGA | Optional for Rev.1 if layout risk is high |
| Ambient light | Vishay VEML7700 | TI OPT3001 | SMD optical | Rev.1 LB placement accepted for EVT; external/window placement moves to production/Rev.2 |

## PB-100 power-path candidates

Detailed candidate MPNs for PB-100 schematic planning are tracked in
`hardware/power-board/PB-100/PB-100-power-path-candidates.csv`.

The current strategy is:

- All Rev.1 outputs: TPS48110AQDGXRQ1 high-side controller plus selected
  IAUT300N08S5N012ATMA2 80 V PG-HSOF-8-1 TOLL N-MOSFET.
- Low-current integrated smart switches: deferred alternatives only.
- Input active cutoff: LM74930QRGERQ1 with common-source external MOSFETs.
- Raw-side cutoff MOSFET: IAUTN15S6N025ATMA1 150 V TOLL selected for Q2.
- Input reverse and output MOSFET: IAUT300N08S5N012ATMA2 80 V TOLL selected,
  with IAUT300N08S5N014ATMA1 as the same-footprint controlled alternative and
  BUK7J2R4-80MX 80 V LFPAK56E as a non-drop-in production escape path.
- Input transient handling: hard cutoff at no more than 55 V; load disconnect
  is allowed. SM8S33AHM3/I remains DNP and no single-TVS branch may be credited
  as the Rev.1 load-dump solution.
- Total current shunt: 0.5 mΩ four-terminal AEC-Q200 shunt candidate for the
  0-60 A telemetry range. At 60 A the candidate produces 30 mV and about 1.8 W;
  at the 40 A board-budget point it produces 20 mV and about 0.8 W.
- Thermal telemetry: TDK `NTCGS103JF103FT8`-class 10 kΩ AEC-Q200 NTC candidate
  for `TEMP_PCB`, `TEMP_PWR_A`, and `TEMP_PWR_B`. The schematic must still
  close divider values, ADC scaling, placement, and calibration.
- Board-to-board interface: Hirose `FX18-100P-0.8SV10` plus
  `FX18-100S-0.8SV10` selected pair for `JPB1`. The official 20 mm stack,
  footprint drawings, MF ownership, LB-100 MCU binding, four-spacer retention,
  fixture, and inspection plan are closed for pre-layout work. Live stock,
  factory handling, and post-prototype continuity/vibration execution remain.

## Evidence links

- STM32H563VI is active and in volume production at ST: https://www.st.com/en/microcontrollers-microprocessors/stm32h563vi.html
- STM32H563VIT6 was listed in stock at LCSC on the snapshot date: https://www.lcsc.com/product-detail/C6937834.html
- STM32H573 family is active at ST: https://www.st.com/en/microcontrollers-microprocessors/stm32h573ii.html
- STM32H573VIT3Q had low LCSC stock on the snapshot date: https://www.lcsc.com/product-detail/C27164413.html
- NXP TJA1051T/3 variants were listed at LCSC: https://www.lcsc.com/product-detail/C58988.html
- TI TCAN1042-Q1 was listed at LCSC: https://www.lcsc.com/product-detail/can-transceivers_texas-instruments-tcan1042hgvdrbrq1_C2671243.html
- TI TPS4811-Q1 is active as an automotive high-side driver with protection and diagnostics: https://www.ti.com/product/TPS4811-Q1
- TI TPS48110AQDGXRQ1 was listed at LCSC on the snapshot date: https://www.lcsc.com/product-image/C17556513.html
- TI TPS2HB35BQPWPRQ1 was listed at LCSC on the snapshot date: https://www.lcsc.com/product-detail/power-distribution-switches_texas-instruments-tps2hb35bqpwprq1_C3230080.html
- Vishay SIDR626LDP-T1-RE3 sourcing and data-sheet evidence is retained only as
  rejected 60 V history, not as a Rev.1 assembly substitute:
  https://www.lcsc.com/product-detail/C3279576.html and
  https://www.vishay.com/docs/77277/sidr626ldp.pdf
- TI LM74930QRGERQ1 is the selected active surge-stopper controller:
  https://www.ti.com/product/LM74930-Q1/part-details/LM74930QRGERQ1
- Infineon IAUTN15S6N025ATMA1 is the selected 150 V raw-side Q2:
  https://www.infineon.com/assets/row/public/documents/10/49/infineon-iautn15s6n025-datasheet-en.pdf
- Infineon IAUTN06S5N008 is retained only as rejected 60 V TOLL history:
  https://www.infineon.com/part/IAUTN06S5N008
- Infineon IAUT300N08S5N012 is the selected 80 V automotive
  PG-HSOF-8-1 TOLL MOSFET for Q1 and Q101-Q110:
  https://www.infineon.com/part/IAUT300N08S5N012
- Infineon IAUT300N08S5N014 is the controlled same-footprint alternative:
  https://www.infineon.com/part/IAUT300N08S5N014
- Nexperia BUK7J2R4-80M is the controlled non-drop-in 80 V LFPAK56E
  alternative: https://www.nexperia.com/product/BUK7J2R4-80M
- MCC SM8S33A reference now shows EOL/obsolete status and is retained only as a
  cautionary sourcing note: https://www.mccsemi.com/products/esd-protection-and-power-tvs/tvs/SM8S33A
- Vishay SM8S HM3 AEC-Q101 DO-218AC data was checked as the active TVS class
  direction: https://www.vishay.com/docs/98647/sm8s85ahm3.pdf
- Vishay SM8S HE3 data is now treated as NFD stock-only evidence:
  https://www.vishay.com/doc/?88387=
- TI TPS2HB16-Q1 datasheet is available through LCSC: https://datasheet.lcsc.com/datasheet/pdf/5e972c8f510fd1d0477aeb85de68fc2f.pdf
- TI INA226AIDGST was listed at LCSC: https://www.lcsc.com/product-detail/current-sense-amplifiers_texas-instruments-ina226aidgst_C2653870.html
- TI INA228-Q1 supports the shunt-voltage range needed for the 0.5 mΩ current
  shunt candidate: https://www.ti.com/lit/ds/symlink/ina228-q1.pdf
- Bourns CSS4J-4026 0.5 mΩ four-terminal AEC-Q200 shunt data was checked:
  https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf
- TI TMP117 data sheet was checked for optional digital board-temperature sensing: https://www.ti.com/lit/gpn/TMP117
- TDK NTCGS103JF103FT8 10 kΩ 150 °C AEC-Q200 NTC product page was checked for
  PB-100 thermal sensing: https://product.tdk.com/en/search/sensor/ntc/chip-ntc-thermistor/info?part_no=NTCGS103JF103FT8
- Vishay NTCS0402E3 0402 150 °C NTC family was checked as an alternate:
  https://www.vishay.com/en/product/29003/
- Murata NCU automotive NTC part list was checked as an alternate:
  https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/static-model/component-list-ntc-2508.ashx?cvid=20250930011345000000&la=en
- Hirose FX18-100P-0.8SV10 product page was checked for the PB-100/LB-100
  candidate plug: https://www.hirose.com/product/p/CL0579-0034-1-00
- Hirose FX18-100S-0.8SV10 product page was checked for the PB-100/LB-100
  candidate receptacle: https://www.hirose.com/product/p/CL0579-0058-0-00
- Hirose FX18 series catalog was checked for 0.8 mm pitch, 100-position, and
  power/MF-contact planning evidence:
  https://www.hirose.com/product/series/catalogdownload?category=FX18
- TI LM5164QDDATQ1 was listed at LCSC: https://www.lcsc.com/product-detail/C1850350.html
- TI LM5164-Q1 is active as a 6-100 V 1 A automotive buck regulator: https://www.ti.com/product/LM5164-Q1
- TI LM5013-Q1 is active as a 6-100 V 3.5 A automotive buck regulator: https://www.ti.com/product/LM5013-Q1
- TI TPS54360B-Q1 is active as an automotive 60 V 3.5 A buck regulator: https://www.ti.com/product/TPS54360B-Q1

## Remaining gates before schematic freeze

- Synchronize remaining passive and clamp values into value-bearing sheets.
- Carry the generated output SOA and hot-loss limits into layout and prototype
  thermal acceptance.
- Keep the generated 59.45 V transient bound below the 20 nH layout escape
  limit and confirm it in PB-BENCH-004.
- Confirm high-side controller availability through at least two suppliers.
- Confirm selected PG-HSOF-8-1 TOLL handling at actual JLCPCB/PCBWay quote;
  IAUT300N08S5N014ATMA1 and BUK7J2R4-80MX remain controlled alternatives.
