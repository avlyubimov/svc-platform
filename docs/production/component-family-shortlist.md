# Component Family Shortlist

Status: Initial factory-assembly shortlist

Evidence snapshot date: 2026-06-30

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
| Output MOSFET | Infineon OptiMOS automotive 40-60 V | Vishay SQJQ automotive; onsemi F085 automotive | TDSON/PowerPAK/TOLL/LFPAK | Must pass SOA and thermal review per channel; OUT2 keeps larger/parallel escape path |
| Current monitor | TPS48110 IMON for outputs; TI INA228/INA229 or INA226 for input | External analog monitor; firmware-calibrated ADC path | VSSOP/SOIC class | Per-output telemetry uses controller IMON; total input current uses dedicated shunt monitor |
| Total current shunt | Bourns CSS4J-4026R-L500F-class 0.5 mΩ four-terminal shunt | Bourns CSS4J-4026R-1L00F-class 1.0 mΩ; Isabellenhuette BVN/BAS or equivalent AEC-Q200 four-terminal family | CSS4J-4026 or reviewed power shunt | 0.5 mΩ gives 30 mV at 60 A and 1.8 W; compatible with INA228 ±40.96 mV range candidate |
| Temperature sensor | Automotive NTC thermistor | TI TMP117/TMP112-class digital sensor | 0603/0805 or SOT/DFN class | PB-100 uses PCB reference plus two power-zone thermal points |
| Logic buck regulator | TI LM5164-Q1 | TI LM5013-Q1; TI TPS54360B-Q1/TPS54360-Q1 | SOIC/HSOIC PowerPAD | LM5164-Q1 for 1 A 100 V rail; LM5013-Q1 preferred over 60 V family if more current is needed |
| Input reverse protection | TI LM74700-Q1/LM74502-Q1 class | ADI/LTC ideal diode controller families | MSOP/SOIC class | Controller family only; MOSFET is tracked separately |
| Input reverse MOSFET | Infineon OptiMOS 5 60 V TOLL low-Rds class | Nexperia LFPAK88 80 V; parallel Vishay SIDR626 PowerPAK | TOLL/LFPAK88/PowerPAK | Single 2.1 mOhm MOSFET is rejected for 40 A input thermal |
| Input TVS/load dump | Vishay SM8S33AHM3/I active HM3 TVS | Vishay SM8S33AHE3_A/I NFD stock-only; Littelfuse SLD8S33A; Diodes DM8W33AQ-13; Bourns SM8S33A-Q class | DO-218AC/SMC as needed | MCC SM8S33A source is EOL and HE3 is NFD evidence only; final clamp voltage depends on MOSFET and buck ratings |
| FRAM | Fujitsu/Infineon MB85 I2C/SPI FRAM | Cypress/Infineon Excelon FRAM | SOIC/TSSOP/DFN | Configuration and black-box storage |
| RTC | Microchip MCP7940 class | NXP PCF8523/PCF8563; DS3231 class | SOIC/TSSOP/DFN/module | Prefer low-IQ SMD IC over hobby module |
| IMU | Bosch BMI270/BMI323 | TDK ICM-42688 class | LGA | Optional for Rev.1 if layout risk is high |
| Ambient light | Vishay VEML7700 | TI OPT3001 | SMD optical | Placement and window design required |

## PB-100 power-path candidates

Detailed candidate MPNs for PB-100 schematic planning are tracked in
`hardware/power-board/PB-100/PB-100-power-path-candidates.csv`.

The current strategy is:

- All Rev.1 outputs: TPS48110AQDGXRQ1-class high-side controller plus
  external 60 V N-MOSFET.
- Low-current integrated smart switches: deferred alternatives only.
- Input reverse protection: LM74700QDBVRQ1-class ideal-diode controller.
- Input reverse MOSFET: IAUTN06S5N008ATMA1-class low-Rds TOLL device, with
  BUK7S1R2-80M-class LFPAK88 and dual SIDR626LDP fallback alternatives.
- Input transient clamp: Vishay SM8S33AHM3/I active HM3 load-dump TVS or
  reviewed equivalent. MCC SM8S33A is treated as EOL evidence only, and Vishay
  HE3 is treated as NFD stock-only evidence; neither may be locked.
- Total current shunt: 0.5 mΩ four-terminal AEC-Q200 shunt candidate for the
  0-60 A telemetry range. At 60 A the candidate produces 30 mV and about 1.8 W;
  at the 40 A board-budget point it produces 20 mV and about 0.8 W.

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
- Vishay SIDR626LDP-T1-RE3 was listed at LCSC on the snapshot date: https://www.lcsc.com/product-detail/C3279576.html
- Vishay SIDR626LDP data sheet was checked for OUT2 SOA planning: https://www.vishay.com/docs/77277/sidr626ldp.pdf
- TI LM74700QDBVRQ1 was listed at LCSC on the snapshot date: https://www.lcsc.com/product-detail/C2941042.html
- Infineon IAUTN06S5N008 is active/preferred as a 60 V 0.76 mOhm automotive TOLL MOSFET: https://www.infineon.com/part/IAUTN06S5N008
- Nexperia BUK7S1R2-80M data sheet lists an 80 V 1.2 mOhm automotive LFPAK88 MOSFET: https://assets.nexperia.com/documents/data-sheet/BUK7S1R2-80M.pdf
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
- TDK automotive NTC thermistor data was checked for PB-100 power-zone sensing: https://www.farnell.com/datasheets/3920346.pdf
- TI LM5164QDDATQ1 was listed at LCSC: https://www.lcsc.com/product-detail/C1850350.html
- TI LM5164-Q1 is active as a 6-100 V 1 A automotive buck regulator: https://www.ti.com/product/LM5164-Q1
- TI LM5013-Q1 is active as a 6-100 V 3.5 A automotive buck regulator: https://www.ti.com/product/LM5013-Q1
- TI TPS54360B-Q1 is active as an automotive 60 V 3.5 A buck regulator: https://www.ti.com/product/TPS54360B-Q1

## Open checks before schematic freeze

- Confirm JLCPCB/PCBWay assembly class for each selected MPN.
- Confirm thermal budget for each output current class.
- Confirm MOSFET SOA for compressor and heated-seat inrush cases.
- Confirm TVS clamp voltage against buck, MOSFET, and high-side controller limits.
- Confirm high-side controller availability through at least two suppliers.
- Confirm TOLL/LFPAK88 assembly support at JLCPCB/PCBWay or use the documented
  parallel PowerPAK fallback for input reverse protection.
