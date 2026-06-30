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
| High-side output controller | TI TPS4811-Q1 | TI TPS1211-Q1; TI TPS4810-Q1 | VSSOP/HTSSOP class | For high-current outputs with external N-MOSFETs |
| Smart high-side switch | TI TPS2HB16-Q1 | TI TPS2HB35-Q1; TI TPS1H100-Q1 | HTSSOP class | Candidate for lower-current channels after thermal review |
| Output MOSFET | Infineon OptiMOS automotive 40-60 V | Vishay SQJQ automotive; onsemi F085 automotive | TDSON/PowerPAK/DPAK | Must pass SOA and thermal review per channel |
| Current monitor | TI INA226 | TI INA228/INA229; integrated IMON from high-side controller | VSSOP/SOIC class | External monitor may be unnecessary on channels with accurate IMON |
| Logic buck regulator | TI LM5164-Q1 | TI TPS54360B-Q1/TPS54360-Q1 | SOIC/HSOIC PowerPAD | LM5164-Q1 for low-IQ 1 A rail; TPS54360 family for higher 5 V current |
| Input reverse protection | TI LM74700-Q1/LM74502-Q1 class | ADI/LTC ideal diode controller families | MSOP/SOIC class | External MOSFET sizing remains open |
| Input TVS/load dump | SM8S automotive TVS class | SMBJ/SMCJ automotive TVS class | DO-218/SMC/SMA as needed | Final clamp voltage depends on MOSFET and buck ratings |
| FRAM | Fujitsu/Infineon MB85 I2C/SPI FRAM | Cypress/Infineon Excelon FRAM | SOIC/TSSOP/DFN | Configuration and black-box storage |
| RTC | Microchip MCP7940 class | NXP PCF8523/PCF8563; DS3231 class | SOIC/TSSOP/DFN/module | Prefer low-IQ SMD IC over hobby module |
| IMU | Bosch BMI270/BMI323 | TDK ICM-42688 class | LGA | Optional for Rev.1 if layout risk is high |
| Ambient light | Vishay VEML7700 | TI OPT3001 | SMD optical | Placement and window design required |

## Evidence links

- STM32H563VI is active and in volume production at ST: https://www.st.com/en/microcontrollers-microprocessors/stm32h563vi.html
- STM32H563VIT6 was listed in stock at LCSC on the snapshot date: https://www.lcsc.com/product-detail/C6937834.html
- STM32H573 family is active at ST: https://www.st.com/en/microcontrollers-microprocessors/stm32h573ii.html
- STM32H573VIT3Q had low LCSC stock on the snapshot date: https://www.lcsc.com/product-detail/C27164413.html
- NXP TJA1051T/3 variants were listed at LCSC: https://www.lcsc.com/product-detail/C58988.html
- TI TCAN1042-Q1 was listed at LCSC: https://www.lcsc.com/product-detail/can-transceivers_texas-instruments-tcan1042hgvdrbrq1_C2671243.html
- TI TPS4811-Q1 is active as an automotive high-side driver with protection and diagnostics: https://www.ti.com/product/TPS4811-Q1
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
