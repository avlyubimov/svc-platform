# PB-100 to LB-100 Pin-Binding Precheck

Status: Candidate resource constraints for LB-100 schematic review; not final

This precheck converts the `JPB1` 100-pin PB-100 interface into the minimum
LB-100 MCU resource budget that must be proven on the STM32H563 LQFP-100 target.
It does not assign exact STM32H5 package pins, alternate functions, or PCB
placement. Exact pin binding remains an LB-100 schematic-freeze item.

The execution checklist for this precheck is
`hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`. That
checklist keeps the STM32H563 LQFP-100 exact pinout audit, FX18 footprint
drawing, stack height, vibration retention, assembly handling, CAN1 read-only
crossing, and no-layout boundary explicit.

## Non-goals

- No STM32 pin numbers are assigned here.
- No timer alternate-function mapping is frozen here.
- No ADC channel order or sampling schedule is frozen here.
- No reserve or future expansion pin is consumed by default.
- No CAN1 TX enable path is created.

## Core resource budget

| JPB1 group | Pins | Signals | Minimum LB-100 resource reservation | Freeze check |
|---|---:|---|---|---|
| Power-good and wake status | 19-20 | `PB_PWR_GOOD`, `PB_WAKE_REQ` | 2 GPIO inputs with wake or interrupt review | Verify power-good polarity and wake source before LB schematic freeze |
| Output control commands | 21-30 | `OUT1_CTL`..`OUT10_CTL` | 10 GPIO outputs with PWM-capable timer channels preferred | Verify default-low reset and timer AF conflicts |
| Output fault inputs | 31-40 | `OUT1_FLT`..`OUT10_FLT` | 10 GPIO inputs, direct EXTI only where latency requires it | Verify pull-up domain and fault aggregation policy |
| Per-output current telemetry | 41-50 | `OUT1_IMON`..`OUT10_IMON` | 10 ADC-capable inputs | Verify ADC channel count, impedance, filtering, and sampling time |
| Board analog telemetry and ID | 51-55, 60, 66 | `VBAT_SENSE`, `IIN_SENSE`, `TEMP_PCB`, `TEMP_PWR_A`, `TEMP_PWR_B`, `PB_ID_ADC`, `ADC_REF` | 6 ADC-capable inputs plus optional reference strategy | Verify ADC reference, scaling, calibration, and sample sequencing |
| Board fault summary | 56 | `PB_FAULT` | 1 GPIO input or interrupt-capable input | Verify safe-default fault behavior |
| PB-side monitor bus | 57-59 | `PB_I2C_SCL`, `PB_I2C_SDA`, `PB_I2C_INT` | 1 I2C bus plus 1 GPIO interrupt input | Verify pull-ups, address plan, and monitor fallback |
| Future SPI monitor bus | 61-65 | `PB_SPI_SCK`, `PB_SPI_MISO`, `PB_SPI_MOSI`, `PB_SPI_CS0`, `PB_SPI_CS1` | Reserved SPI plus 2 chip-select GPIOs | Keep DNP/reserved unless a future review consumes it |
| CAN1 safety crossing | 67-70 | `CAN1_TX_DISABLE_CMD`, `CAN1_TX_DISABLED_STATUS`, `CAN1_RX_ROUTE`, `CAN1_TX_ROUTE` | 2 GPIOs plus FDCAN RX; FDCAN TX remains future/DNP | Keep CAN1 TX DNP/open and future-ADR gated |
| Future CAN2 route | 71-72 | `CAN2_RX_ROUTE`, `CAN2_TX_ROUTE` | Reserved FDCAN RX/TX | Keep expansion DNP until accepted |
| Future serial expansion | 73-79 | `LIN_TX`, `LIN_RX`, `RS485_DE`, `RS485_RX`, `RS485_TX`, `UART_TX`, `UART_RX` | Reserved UART resources plus direction GPIO | Keep DNP/reserved until accepted |
| External/manual IO | 80-84 | `EXT_ADC1`, `EXT_ADC2`, `FOG_A_SW_IN`, `FOG_B_SW_IN`, `EXT_5V_EN` | PA8 and PA9 protected GPIO inputs through U18/U19; ADC and 5 V enable allocations unchanged | Preserve independent active-low safe defaults and mutually exclusive dry/12 V assembly variants |

## LB-100 internal reservations

LB-100 schematic review must reserve internal MCU resources before accepting an
exact `JPB1` pin map:

- SWD/JTAG debug.
- Boot and reset pins.
- HSE/LSE or accepted clock source pins.
- USB-C service interface.
- microSD interface.
- BLE module UART or SPI.
- RTC, FRAM, IMU, lux sensor, and any onboard sensor buses.
- Watchdog, wake, and sleep/deep-sleep pins required by ADR-0012.

These internal reservations compete with `JPB1` ADC, timer, FDCAN, UART, SPI,
and interrupt resources. If STM32H563 LQFP-100 cannot satisfy the budget with
clean alternate-function mapping, LB-100 must add an external ADC/mux, change
the MCU package, or update the architecture through review before PB-100
schematic freeze.

## Freeze blockers

- Run an STM32H563 LQFP-100 pinout audit with all LB-100 internal peripherals
  and `JPB1` resource reservations included.
- Verify at least 16 ADC-capable external measurement inputs or approve a
  reviewed ADC mux/external ADC strategy.
- Verify 10 output-control pins can be timer/PWM-capable without role-specific
  hard-coding.
- Verify `PB_WAKE_REQ`, `PB_FAULT`, and time-critical output faults have
  interrupt or wake-capable routing where required.
- Verify `PB_I2C` pull-up ownership and address plan against current telemetry.
- Verify CAN1 read-only default: `CAN1_TX_ROUTE` remains DNP/open and cannot be
  enabled by configuration.
- Keep connector placement and PCB layout blocked until exact LB-100 pin
  binding, stack-height, footprint, and vibration evidence close.
