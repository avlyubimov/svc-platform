# Test Plan

## Bench test before motorcycle

Required equipment:

- Current-limited lab power supply.
- Electronic load or fused dummy-load bank.
- Clamp meter or calibrated shunt.
- Oscilloscope or logic analyzer.
- CAN analyzer/logger.
- Thermal camera or thermocouples.
- Fused high-current harness fixture.

Do not run first-power, short-circuit, inrush, thermal, or CAN safety tests on
the motorcycle.

## PB-100 bench validation matrix

| ID | Area | Test | Pass condition |
|---|---|---|---|
| PB-BENCH-001 | Bring-up | Power PB-100 from current-limited supply at 6 V, 12 V, and 18 V with outputs disabled | No abnormal current draw; logic rail and `PB_PWR_GOOD` behave as expected |
| PB-BENCH-002 | Safe default | Hold LB-100 reset or disconnected and check `OUT1` through `OUT10` | All outputs remain off |
| PB-BENCH-003 | Reverse protection | Apply reverse polarity only through a current-limited fixture | No downstream rail energizes and no damage occurs |
| PB-BENCH-004 | TVS/load dump | Validate clamp behavior by simulator or suitable surge test fixture | Clamp remains below selected device limits with documented margin |
| PB-BENCH-005 | Per-output current telemetry | Measure each output at 0%, 25%, 50%, and 100% of configured current limit | Telemetry error is inside the schematic-defined calibration target |
| PB-BENCH-006 | Total input current telemetry | Load multiple outputs up to the 40 A board-budget target | Input current telemetry follows independent measurement inside calibration target |
| PB-BENCH-007 | OUT2 inrush envelope | Exercise the `PB-100-out2-soa-envelope.csv` pulse cases on a fused bench fixture | Controller does not exceed validated MOSFET SOA or fault timing |
| PB-BENCH-008 | Overcurrent and short fault | Apply controlled overcurrent and short-circuit tests per output class | Output faults and latches off inside the selected controller/FET SOA |
| PB-BENCH-009 | Thermal derating | Run representative high, medium, and low-current load combinations in enclosure conditions | Firmware sees PCB and power-zone temperature and derates before unsafe temperature |
| PB-BENCH-010 | Board current budget | Configure load priorities and request loads above the 40 A budget | Firmware refuses startup or sheds lower-priority loads |
| PB-BENCH-011 | Fuse behavior | Open and overload fused outputs under controlled load | Fault state is visible and output is isolated by fuse behavior |
| PB-BENCH-012 | CAN1 listen-only | Connect CAN analyzer and attempt any Rev.1 CAN1 TX path with TX disable defaulted | No vehicle-CAN transmit frame is observed; disabled status is visible |
| PB-BENCH-013 | CAN2 expansion | Exercise CAN2 on bench only | CAN2 can transmit without affecting CAN1 listen-only policy |
| PB-BENCH-014 | B2B interface | Check `JPB1` control, fault, telemetry, ID, and reserve pins against the pin map | Pin behavior matches `PB-100-b2b-pin-map.csv` |
| PB-BENCH-015 | Vibration inspection | Inspect fuses, connectors, and harness strain relief after vibration exposure | No intermittent power, signal, or connector fault is observed |

## Repository validation

Run the PB-100 artifact validator before committing schematic-planning or KiCad
scaffold changes:

```bash
python3 tools/validate_pb100.py
```

The validator checks CSV structure, KiCad scaffold syntax, the no-PCB-layout
boundary, preliminary symbol-library status, output instance coverage, and PB-100
net-naming safety rules.

Run firmware host tests after changing configuration, hardware-capability, or
safety-service contracts:

```bash
make -C firmware test
```

The hardware-capability tests verify that PB-100 generic output limits,
safe-default behavior, board current budget, and CAN1 read-only defaults are
accepted without binding accessory roles to physical outputs.

## PB-100 schematic-review traceability

- OUT2 pulse tests trace to
  `hardware/power-board/PB-100/PB-100-out2-soa.md`.
- CAN1 listen-only tests trace to
  `hardware/power-board/PB-100/PB-100-can1-tx-disable.md`.
- Input reverse-protection tests trace to
  `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`.
- Current-budget tests trace to `docs/adr/ADR-0008-pb-100-current-budget.md`.
- B2B interface tests trace to
  `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`.

## Motorcycle test

1. Install with only low-current loads.
2. Verify no CAN errors.
3. Verify ACC behavior.
4. Verify low-voltage shutdown.
5. Add fog lights.
6. Add CHIGEE/nav.
7. Log CAN without transmitting.
