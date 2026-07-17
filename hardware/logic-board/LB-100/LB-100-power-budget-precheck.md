# LB-100 Power Budget Precheck

Status: Schematic-review input; not final

This precheck defines the load-budget contract that LB-100 must satisfy before
PB-100 can freeze the protected `PB_5V_OUT` buck regulator. It does not select
LB-100 regulators, power switches, sleep hardware, or exact MCU pins.

## Contract With PB-100

- PB-100 Rev.1 currently reserves 500 mA of the 1 A `PB_5V_OUT` budget for
  LB-100 logic-board use.
- PB-100 reserves another 500 mA for PB-side controllers, telemetry, expansion,
  and design margin.
- If LB-100 schematic review needs more than 500 mA sustained from
  `PB_5V_OUT`, PB-100 must keep the LM5013-Q1-class higher-current 100 V buck
  fallback active before schematic freeze.
- `PB_5V_OUT` must not power accessory loads.
- `LB_3V3_IO` is a logic reference and pull-up domain for PB-side interfaces,
  not a PB-100 load supply.

## LB-100 Loads To Budget Before Freeze

| Load group | Budget status | Notes |
|---|---|---|
| STM32H563/H573 MCU and clocks | Required | Include active current and reset/startup behavior |
| CAN1/CAN2 transceivers | Required | CAN1 remains listen-only by default |
| BLE module or radio module | Required | Include peak current during advertising or connection |
| microSD socket | Required | Include write-current peak and inrush |
| RTC FRAM IMU lux and other sensors | Required | Include always-on or sleep-domain leakage |
| USB/service interface | Required | Clarify when USB powers LB-100 versus only signals service presence |
| PB-side pull-ups and status inputs | Required | Include `PB_I2C`, `PB_PWR_GOOD`, and CAN1 disabled-status pull-ups |
| Expansion reserve | Should | Keep future sensors and debug adapters out of the guaranteed 500 mA until reviewed |

## Freeze Checks

- Produce an LB-100 rail tree with active, sleep, and deep-sleep current states.
- Prove ADR-0012 sleep and deep-sleep current targets at the battery input.
- Define whether LB-100 can back-power PB-100 through `LB_3V3_IO`, USB, SWD, or
  communication interfaces.
- Define power-good interpretation and reset sequencing for `PB_PWR_GOOD`.
- Keep PB-100 outputs default-off while `PB_5V_OUT` or `LB_3V3_IO` is invalid.
- Keep the PB-100 LM5013-Q1 fallback if the 500 mA LB allocation is exceeded.

## Related Artifacts

- PB-100 budget table: `hardware/power-board/PB-100/PB-100-logic-power-budget.csv`.
- PB-100 logic calculation: `hardware/power-board/PB-100/PB-100-logic-power-design-calculation.md`.
- PB-100 logic freeze review: `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`.
- Sleep and parking-current ADR: `docs/adr/ADR-0012-system-sleep-wake-and-parking-current.md`.
