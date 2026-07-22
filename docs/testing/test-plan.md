# Test Plan

## Phase boundary

PB-100 bench tests that require an assembled board are EVT validation gates.
Per ADR-0020, all three boards may enter controlled layout at
`EVT-LAYOUT-AUTHORIZED`; completed routing then enters `EVT-FAB-REVIEW`.
Reviewed DRC, parity, electrothermal/clamp-loop extraction, DFM and safety
evidence permit a five-board package at `EVT-FAB-AUTHORIZED`. Build inspection permits
`BENCH-VALIDATION`; physical bench records then gate
`MOTORCYCLE-VALIDATION` and production remains closed until reviewed Rev.2.
This flow preserves the validation intent of
`docs/adr/ADR-0013-pb-100-prelayout-vs-postprototype-validation.md` and the
staged evidence model of
`docs/adr/ADR-0017-pb-100-staged-release-authorization.md`; ADR-0020 controls
which release boundary those gates block. PBREL-007 blocks only production.

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

Do not run motorcycle first-power, field use, or production release before the
post-prototype validation gate in
`hardware/power-board/PB-100/PB-100-post-prototype-validation-gate.csv` is
complete.

PBREL-006/PBREL-007 EVT transition sequencing is tracked in
`hardware/power-board/PB-100/PB-100-staged-release-readiness.csv`.

Unit roles are fixed by
`hardware/power-board/PB-100/PB-100-evt-unit-allocation.csv`. `EVT-03` receives
fault/surge testing and must never be installed on the motorcycle. `EVT-04` is
reserved for motorcycle validation after its nondestructive bench pass.

### Ordered EVT bench sequence

1. Inspect DNP populations, polarity, isolation links and shorts.
2. Current-limited bring-up with all outputs disabled.
3. Verify each output and calibrate `OUT1_IMON` through `OUT10_IMON`.
4. Measure the four real auxiliary lamps and verify open-load, overload and
   short-circuit diagnosis with logged trip reasons.
5. Controlled 10 A, 20 A, 30 A and 40 A total-current load steps.
6. Calibrate INA228 and compare summed channel current with `IIN_SENSE`.
7. Verify `FOG_A_SW_IN` and `FOG_B_SW_IN` independently in both configurable
   behaviors: boot/reset-off, simultaneous requests, contact bounce, isolated
   stuck-input diagnosis, immediate pair-off and delayed channel start inside
   OUT3/OUT4 and OUT6/OUT7.
8. Verify OUT1 socket/compressor safeguards and both external C36 current
   directions; C36 uses an external clamp or shunt and remains unmanaged.
9. Verify mode masks, undervoltage response and shedding order: second fog pair,
   first fog pair, remaining managed outputs, then all outputs.
10. Record MOSFET, copper, via, shunt, connector and enclosure temperatures.
11. Run controlled overvoltage/load disconnect while recording synchronized
   `VBAT_RAW`, protected output, Q1/Q2 `VDS`, Q1/Q2 `VGS`, current and
   temperature.
12. Repeat inspection and parametric checks after abnormal-stress testing.

## PB-100 bench validation matrix

| ID | Area | Test | Pass condition |
|---|---|---|---|
| PB-BENCH-001 | Bring-up | Power PB-100 from current-limited supply at 6 V, 12 V, and 18 V with outputs disabled | No abnormal current draw; logic rail and `PB_PWR_GOOD` behave as expected |
| PB-BENCH-002 | Safe default | Hold LB-100 reset or disconnected and check `OUT1` through `OUT10` | All outputs remain off |
| PB-BENCH-003 | Reverse protection | Apply reverse polarity only through a current-limited fixture | No downstream rail energizes and no damage occurs |
| PB-BENCH-004 | Active cutoff/load dump | Apply the ADR-0016 surge envelope to the assembled engineering prototype while recording VBAT_RAW, VBAT_PROT, DGATE, HGATE, current, and Q2 temperature | LM74930-Q1 disconnects the load, VBAT_PROT peak stays below 60 V, Q2 remains inside extracted dynamic SOA, and repeated-pulse recovery has documented margin |
| PB-BENCH-005 | Per-output current telemetry | Measure each output at 0%, 25%, 50%, and 100% of configured current limit | Telemetry error is inside the schematic-defined calibration target |
| PB-BENCH-006 | Total input current telemetry | Load multiple outputs up to the 40 A board-budget target | Input current telemetry follows independent measurement inside calibration target |
| PB-BENCH-007 | OUT2 inrush envelope | Exercise the `PB-100-out2-soa-envelope.csv` pulse cases on a fused bench fixture | Controller does not exceed validated MOSFET SOA or fault timing |
| PB-BENCH-008 | Overcurrent and short fault | Apply controlled overcurrent and short-circuit tests per output class | Output faults and latches off inside the selected controller/FET SOA |
| PB-BENCH-009 | Thermal derating | Run representative high, medium, and low-current load combinations in enclosure conditions | Firmware sees PCB and power-zone temperature and derates before unsafe temperature |
| PB-BENCH-010 | Board current budget and passive Q1 cooling | Run the 40 A path at the qualified ambient while recording Q1 junction estimate, case, PCB copper, thermal pad, metal enclosure, and ambient temperatures | Firmware enforces the 40 A budget, Q1 stays at or below 150 °C, and the measured full passive path agrees with the extracted limit of 6.20 °C/W or better |
| PB-BENCH-011 | Fuse behavior | Open and overload fused outputs under controlled load | Fault state is visible and output is isolated by fuse behavior |
| PB-BENCH-012 | CAN1 listen-only | Connect CAN analyzer and attempt any Rev.1 CAN1 TX path with TX disable defaulted | No vehicle-CAN transmit frame is observed; disabled status is visible |
| PB-BENCH-013 | CAN2 expansion | Exercise CAN2 on bench only | CAN2 can transmit without affecting CAN1 listen-only policy |
| PB-BENCH-014 | B2B interface | Check `JPB1` control, fault, telemetry, ID, and reserve pins against the pin map | Pin behavior matches `PB-100-b2b-pin-map.csv` |
| PB-BENCH-015 | Vibration inspection | Inspect fuses, connectors, and harness strain relief after vibration exposure | No intermittent power, signal, or connector fault is observed |
| PB-BENCH-016 | Dual manual FOG requests | Exercise A-only, B-only, both inputs, simultaneous press, short/repeat press, maintained position, contact bounce, boot/reset, one stuck input, invalid configuration, undervoltage, overcurrent and thermal fault | Requests boot off; A controls only OUT3/OUT4; B controls only OUT6/OUT7; each pair sequences its two channels independently; pair-off is immediate; one stuck input does not block the other; safety denial clears both requests and no safety gate is bypassed |
| PB-BENCH-017 | Reference lamp currents | Measure each nominal 80 W and 70 W auxiliary lamp on its configured output | Actual steady and inrush current are stored and remain inside channel/fuse/SOA limits |
| PB-BENCH-018 | C36 bidirectional branch | Measure accessory-source and battery-charge directions with PB/LB both on and off using external current measurement | Both vendor-defined directions work through the separately fused branch; no current is attributed to `IIN_SENSE`; C36 is not used for starter current |
| PB-BENCH-019 | Operating modes and shedding | Exercise DAY NIGHT SERVICE_COMPRESSOR C36_RESCUE_CHARGE ENGINE_OFF and increasing generator deficit | Mutually exclusive loads are never admitted together; second fog pair sheds first, then first pair, then other managed outputs, and critical undervoltage disables OUT1 through OUT10 |

### Three-wire button identification

Perform this check with the switch disconnected from the motorcycle and from
PB-100/LB-100. Do not finalize the external harness until the record is complete.

1. Find the common conductor by continuity testing.
2. Verify common-to-each-remaining-conductor closure separately.
3. Record resistance in every pressed and released state.
4. Use diode mode to identify LEDs or other internal electronics.
5. Record wire colours, the complete state table and all measurements without
   assigning colour-based pin names beforehand.
6. Select exactly one assembly variant per input: active-low dry contact or the
   protected 12 V DNP option. Never populate incompatible variants together.

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
Repository validation also compares the compiled PB-100 capability constant with
the JSON hardware capability manifest.
Configuration acceptance tests verify startup rejects invalid configuration,
invalid hardware capability data, and configurations exceeding PB-100 limits.
Runtime boot tests verify rejected configuration leaves outputs off and runtime
services uninitialized. Store-backed runtime boot tests verify persisted records
are loaded before hardware capability acceptance.
Configuration store tests verify persisted user configuration is selected ahead
of firmware defaults after an update, including reserved-field rejection and
wrap-aware two-slot sequence selection.
Configuration update tests verify unsafe or hardware-incompatible configurations
are not prepared for persistence.
CAN RX log tests verify CAN1/CAN2 receive-only frame capture, invalid-frame
rejection, ring-buffer overwrite accounting, and saturating diagnostic counters.
CAN decode tests verify received frames publish internal state-change events
through the Event Bus without repeating unchanged states, and retry dropped edges
when the Event Bus is full.
Rule Event Bridge tests verify condition events drain into rule state, CAN-derived
events can reach rule evaluation, and non-rule events remain available for safety
dispatch.
Manual FOG control tests verify boot-off, debounce, stuck-input safe-off,
toggle behavior, safety denial and delayed second-pair requests. Rule condition
and rule text tests continue to verify the generic configuration grammar.
Rule Engine rule-set tests verify ordered multi-rule execution, skipped-rule
accounting, stop-on-first-failure behavior, and stale-telemetry denial through
the Output Manager budget path.
Rule Text tests verify multi-action `then[]` compilation into ordered
`svc_rule_t` arrays using caller-owned storage, canonical PWM action grammar,
and side-effect-free rejection before caller-owned buffers are modified.
Event Log tests verify fixed-size overwrite behavior and saturating dropped-entry
accounting.
System Safety tests verify battery cutoff, thermal cutoff, runtime current-budget
shedding, stale/invalid telemetry safe-off behavior, overflow-safe battery
elapsed-time conversion, and retry of dropped power-budget shed events.
Repository config validation checks schema rule string patterns, rule grammar,
non-empty `then[]`, mapped rule-action roles, and partial-PWM compatibility
against the configured outputs.
Rule Runtime tests verify CAN-derived condition events, retained fault dispatch,
ordered rule execution, and stale-telemetry denial in one processing step.

## PB-100 schematic-review traceability

- Bring-up and logic-rail tests trace to
  `hardware/power-board/PB-100/PB-100-logic-power-rail-trace.csv` and
  `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`, and
  `hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`
  plus
  `hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`
  and `hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv`.
- OUT2 pulse tests trace to
  `hardware/power-board/PB-100/PB-100-high-medium-output-baseline-trace.csv`
  `hardware/power-board/PB-100/PB-100-high-medium-output-freeze-review.csv`
  `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`
  `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`
  `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`
  and `hardware/power-board/PB-100/PB-100-out2-soa.md`.
- Output overcurrent, fuse, and class-limit tests trace to
  `hardware/power-board/PB-100/PB-100-high-medium-output-baseline-trace.csv`
  `hardware/power-board/PB-100/PB-100-high-medium-output-freeze-review.csv`
  and
  `hardware/power-board/PB-100/PB-100-low-current-output-baseline-trace.csv`
  plus `hardware/power-board/PB-100/PB-100-low-current-output-freeze-review.csv`
  plus `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`
  `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`
  and `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`.
- CAN1 listen-only tests trace to
  `hardware/power-board/PB-100/PB-100-can1-tx-disable-trace.csv`,
  `hardware/power-board/PB-100/PB-100-can1-tx-disable.md`, and
  `hardware/power-board/PB-100/PB-100-can1-safety-verification.csv`, plus
  `hardware/power-board/PB-100/PB-100-can1-production-dnp-review.csv` and
  `hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv`, and
  `hardware/power-board/PB-100/PB-100-can1-default-disable-freeze-checklist.csv`
  plus
  `hardware/power-board/PB-100/PB-100-can1-default-disable-derivation-precheck.csv`,
  and `hardware/power-board/PB-100/PB-100-can1-default-disable-closeout-precheck.csv`.
- Input reverse-protection tests trace to
  `hardware/power-board/PB-100/PB-100-input-reverse-package-trace.csv`,
  `hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv`,
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`,
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv`,
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv`, and
  `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`.
- TVS/load-dump tests trace to
  `hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv` and
  `hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv`, and
  `hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv` plus
  `hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv`
  and `hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv`.
- Current telemetry and current-budget tests trace to
  `hardware/power-board/PB-100/PB-100-current-telemetry-trace.csv`,
  `hardware/power-board/PB-100/PB-100-current-telemetry-freeze-review.csv`,
  `hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv`,
  `hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv`,
  `hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv`,
  `hardware/power-board/PB-100/PB-100-board-current-budget-trace.csv`,
  `hardware/power-board/PB-100/PB-100-board-current-budget-freeze-review.csv`,
  `hardware/power-board/PB-100/PB-100-board-current-budget-design-calculation.md`,
  `hardware/power-board/PB-100/PB-100-board-current-budget-value-freeze-checklist.csv`,
  `hardware/power-board/PB-100/PB-100-board-current-budget-value-derivation-precheck.csv`,
  `hardware/power-board/PB-100/PB-100-board-current-budget-closeout-precheck.csv`,
  and
  `docs/adr/ADR-0008-pb-100-current-budget.md`.
- Thermal derating tests trace to
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-trace.csv` and
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-freeze-review.csv`, and
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`
  plus
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`,
  and `hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`.
- B2B interface tests trace to
  `hardware/power-board/PB-100/PB-100-b2b-interface-trace.csv`,
  `hardware/power-board/PB-100/PB-100-b2b-lb100-resource-binding.csv`,
  `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`,
  `hardware/power-board/PB-100/PB-100-b2b-interface-freeze-checklist.csv`,
  `hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv`, and
  `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`.
- Vibration, connector, fuse, and harness ownership tests trace to
  `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv` and
  `hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`,
  `hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`,
  `hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`,
  plus
  `hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv` and
  `hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv` and
  `hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`.

## Motorcycle test

Do not intentionally generate load dump, short circuit, overcurrent or another
destructive corner on the motorcycle. Use only an undamaged board that has
passed the required bench evidence.

1. Record battery voltage without additional loads, then install undamaged
   bench-passed `EVT-04`.
2. Verify DAY with auxiliary lamps off and no CAN errors.
3. Verify manual FOG toggle, NIGHT and each lamp pair separately.
4. Verify C36 powering an accessory and charging the battery from the approved
   power bank according to the C36 manufacturer procedure.
5. Verify cranking, idle and manual-defined control RPM while recording battery
   voltage and generator load.
6. Add only mode-permitted real loads in reviewed steps; test the compressor
   only after its purchase and current/fuse review.
7. Record board, wire and connector temperatures, vibration and fault logs.
8. Log CAN without transmitting and confirm the physical CAN1 TX-disabled
   status.
9. Disposition every Rev.1 finding into the Rev.2 review package.
