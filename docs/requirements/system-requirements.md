# System Requirements

## Environmental
- Operating voltage: 6–18 V normal target
- Must tolerate motorcycle cranking voltage dips
- Automotive transient protection required
- Target temperature range: -40°C to +85°C where practical
- Vibration-resistant connectors and mounting

## Safety
- Main fuse near battery
- Per-channel fuse
- MOSFET/eFuse protection
- Low battery shutdown
- Thermal derating
- Watchdog
- Recovery mode
- CAN read-only default
- Safe default-off output state during boot/reset/update/fault
- Board-level current budget enforcement
- Priority-based load shedding

## Sleep, wake, and parking current
- Device is permanently battery-connected and must define off-ignition current
  budgets before final LB-100 power selection.
- Sleep mode target current at battery input: ≤1.0 mA; hard maximum: ≤2.0 mA.
- Deep-sleep target current at battery input: ≤250 µA; hard maximum: ≤500 µA.
- Enter sleep within 60 seconds after ignition/accessory-off when no service
  session or configured delayed-output action is active.
- Enter deep sleep within 24 hours of continuous parking.
- Allowed Rev.1 wake sources: ignition/accessory sense, USB/service power,
  service button, RTC/maintenance timer, and listen-only CAN1 wake only if CAN1
  TX remains physically disabled.
- All PB-100 outputs remain off in sleep and deep sleep unless a future ADR
  explicitly defines a wake-safe always-on output class.
- Maximum parking drain budget: ≤0.35 Ah over the first parked week and ≤0.45 Ah
  over one parked month after deep sleep transition.

## Manufacturing
- SMD factory assembly
- THT/large connectors installed manually
- Production BOM and Garage BOM separated
- Critical components have alternatives

## Software
- FreeRTOS preferred
- Event bus architecture
- Rule engine
- JSON/CBOR configuration
- Separate firmware and configuration
- USB-C service mode
- BLE configuration
- microSD logging

## Power Board
- PB-100 requirements are tracked in `docs/requirements/pb-100-requirements.md`
- PB-100 requirement changes require ADR approval
