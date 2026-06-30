# PB-100 Net Naming Contract

Status: Schematic-capture input

This contract keeps PB-100 hardware generic and prevents accessory roles from
entering the schematic.

## Global rails

| Net | Purpose |
|---|---|
| `VBAT_RAW` | Battery input before reverse protection |
| `VBAT_PROT` | Protected battery rail after reverse protection and input protection |
| `PB_5V_OUT` | Protected 5 V logic rail exported to LB-100 |
| `LB_3V3_IO` | LB-100-provided 3.3 V logic reference for PB-side interfaces |
| `GND` | Power and digital ground |
| `AGND` | Analog reference ground where separated in schematic |

## Input protection local nets

| Net | Purpose |
|---|---|
| `INPUT_FET_GATE` | Local gate drive from ideal-diode/reverse-protection controller to input MOSFET |
| `VBAT_REV_PROT` | Intermediate node after reverse-protection FET before the final protected rail definition |
| `IIN_SHUNT_HI` | High-side Kelvin sense for total input current shunt |
| `IIN_SHUNT_LO` | Low-side Kelvin sense for total input current shunt |

## Output channel nets

Use `OUTn` where `n` is `1` through `10`.

| Pattern | Direction | Purpose |
|---|---|---|
| `OUTn_CTL` | LB-100 to PB-100 | Enable/PWM command |
| `OUTn_FLT` | PB-100 to LB-100 | Fault/status output |
| `OUTn_IMON` | PB-100 to LB-100 | Analog current telemetry |
| `OUTn_GATE` | Local | External MOSFET gate drive |
| `OUTn_SRC` | Local | High-side controller source/sense node |
| `OUTn_LOAD` | PB-100 output | Fused output to external load |
| `OUTn_FUSED` | Local | Node after user-serviceable fuse when needed |

Do not use names such as `FOG_LEFT`, `SEAT`, `USB`, `CHIGEE`, `DVR`, or
`BRAKE` in PB-100 schematic nets.

## Board telemetry nets

| Net | Purpose |
|---|---|
| `VBAT_SENSE` | Scaled battery voltage telemetry |
| `IIN_SENSE` | Total input current telemetry |
| `TEMP_PCB` | PCB reference temperature telemetry |
| `TEMP_PWR_A` | High-current power-zone temperature telemetry |
| `TEMP_PWR_B` | Secondary power-zone temperature telemetry |
| `PB_FAULT` | Board-level fault summary |
| `PB_PWR_GOOD` | Logic rail power-good |
| `PB_WAKE_REQ` | Wake/fault wake request |
| `PB_ID_ADC` | Resistor-coded board identity fallback |

## Digital bus nets

| Net | Purpose |
|---|---|
| `PB_I2C_SCL` | PB-side I2C clock |
| `PB_I2C_SDA` | PB-side I2C data |
| `PB_I2C_INT` | PB-side monitor interrupt |
| `PB_SPI_SCK` | Reserved SPI clock |
| `PB_SPI_MISO` | Reserved SPI MISO |
| `PB_SPI_MOSI` | Reserved SPI MOSI |
| `PB_SPI_CS0` | Reserved SPI chip select |
| `PB_SPI_CS1` | Reserved SPI chip select |

## CAN safety nets

| Net | Rev.1 default |
|---|---|
| `CAN1_TX_DISABLE_CMD` | Hardware pull asserts disable |
| `CAN1_TX_DISABLED_STATUS` | Asserted when physical TX path is disabled |
| `CAN1_RX_ROUTE` | DNP unless CAN1 routes through PB-100 |
| `CAN1_TX_ROUTE` | DNP/open and hardware-gated unless future ADR allows TX |

Any CAN1 TX enable path requires a new ADR and an explicit hardware action.

## Domain plan

Schematic net domains and safety rules are tracked in
`hardware/power-board/PB-100/PB-100-schematic-net-domain-plan.csv`.
