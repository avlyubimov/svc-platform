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
