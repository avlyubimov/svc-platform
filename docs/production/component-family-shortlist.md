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
| Current monitor | TI INA226 | TI INA228/INA229; integrated IMON from high-side controller | VSSOP/SOIC class | External monitor may be unnecessary on channels with accurate IMON |
| Logic buck regulator | TI LM5164-Q1 | TI TPS54360B-Q1/TPS54360-Q1 | SOIC/HSOIC PowerPAD | LM5164-Q1 for low-IQ 1 A rail; TPS54360 family for higher 5 V current |
| Input reverse protection | TI LM74700-Q1/LM74502-Q1 class | ADI/LTC ideal diode controller families | MSOP/SOIC class | Controller family only; MOSFET is tracked separately |
| Input reverse MOSFET | Infineon OptiMOS 5 60 V TOLL low-Rds class | Nexperia LFPAK88 80 V; parallel Vishay SIDR626 PowerPAK | TOLL/LFPAK88/PowerPAK | Single 2.1 mOhm MOSFET is rejected for 40 A input thermal |
| Input TVS/load dump | SM8S automotive TVS class | SMBJ/SMCJ automotive TVS class | DO-218/SMC/SMA as needed | Final clamp voltage depends on MOSFET and buck ratings |
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
- Input transient clamp: SM8S33A-class load-dump TVS.

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
- SM8S33A-class TVS reference data was checked for clamp-voltage planning: https://www.mccsemi.com/products/esd-protection-and-power-tvs/tvs/SM8S33A
- TI TPS2HB16-Q1 datasheet is available through LCSC: https://datasheet.lcsc.com/datasheet/pdf/5e972c8f510fd1d0477aeb85de68fc2f.pdf
- TI INA226AIDGST was listed at LCSC: https://www.lcsc.com/product-detail/current-sense-amplifiers_texas-instruments-ina226aidgst_C2653870.html
- TI LM5164QDDATQ1 was listed at LCSC: https://www.lcsc.com/product-detail/C1850350.html
- TI TPS54360B-Q1 is active as an automotive 60 V 3.5 A buck regulator: https://www.ti.com/product/TPS54360B-Q1

## Open checks before schematic freeze

- Confirm JLCPCB/PCBWay assembly class for each selected MPN.
- Confirm thermal budget for each output current class.
- Confirm MOSFET SOA for compressor and heated-seat inrush cases.
- Confirm TVS clamp voltage against buck, MOSFET, and high-side controller limits.
- Confirm high-side controller availability through at least two suppliers.
- Confirm TOLL/LFPAK88 assembly support at JLCPCB/PCBWay or use the documented
  parallel PowerPAK fallback for input reverse protection.
