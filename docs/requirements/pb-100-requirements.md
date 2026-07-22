# PB-100 Power Board Requirements

Status: Baseline candidate

PB-100 is the stable power-stage board for the SVC platform. It must remain
vehicle-agnostic and must not encode accessory roles in hardware.

## 1. Lifecycle

- Target lifecycle: 10-15 years where practical.
- New features must prefer configuration, plugins, firmware, or LB-100 changes
  before PB-100 changes.
- PB-100 requirement changes require an ADR.

## 2. Electrical input

- Normal operating input target: 6-18 V.
- Must tolerate motorcycle cranking dips where practical.
- Requires main fuse near the battery in the harness.
- Requires reverse-polarity protection.
- Requires automotive transient/load-dump protection strategy before schematic
  freeze.
- Requires battery voltage and total input current measurement.

### 2.1 Load-dump design envelope

- ISO 16750-2 Test A design evidence must cover `Us = 79-101 V`,
  `Ri = 0.5-4 ohm`, and `td = 40-400 ms` at cold and hot initial junction
  conditions.
- The final qualification plan must cover ten pulses with 60 s spacing.
- Evidence must calculate cutoff tolerance, source current, switch transition
  energy, MOSFET dynamic SOA, transient thermal impedance, junction
  temperature, self-heating, and layout/measurement uncertainty. Any populated
  suppression device also requires current, power, energy, and thermal proof.
- The selected Rev.1 branch must disconnect the load at no more than `55 V`;
  load interruption during load dump is explicitly permitted. Post-layout
  extraction must keep `VBAT_PROT` below the 60 V protected-domain limit.
- Passing a peak clamp-voltage check alone does not satisfy the requirement.
- See ADR-0016 and ADR-0018.

## 3. Generic outputs

PB-100 must provide at least 10 generic protected outputs.

| Output | Reference default role | Target fuse | Target current limit | PWM |
|---|---|---:|---:|---|
| OUT1 | Cigarette socket / future compressor | 15 A | 12 A | yes |
| OUT2 | High-current reserve | 20 A | 18 A | optional |
| OUT3 | Fog primary left | 10 A | 8 A | yes |
| OUT4 | Fog primary right | 10 A | 8 A | yes |
| OUT5 | Low-current reserve 1 | 5 A | 4 A | yes |
| OUT6 | Fog secondary left | 10 A | 8 A | yes |
| OUT7 | Fog secondary right | 10 A | 8 A | yes |
| OUT8 | Low-current reserve 2 | 5 A | 4 A | yes |
| OUT9 | Low-current reserve 3 | 5 A | 4 A | yes |
| OUT10 | Medium-current reserve | 10 A | 8 A | yes |

Reference default roles are initial configuration defaults for BMW K25 Vehicle
Profile #001. Physical outputs remain generic.

The stock headlamp remains on factory wiring. The LOBOO C36 is the separate
`C36_BIDIRECTIONAL` battery branch defined by ADR-0020 and is not OUT1 through
OUT10. The four auxiliary-lamp nameplate values are provisional until EVT
measurement. `FOG_A_SW_IN` and `FOG_B_SW_IN` are independent configurable user
requests for the reference OUT3/OUT4 and OUT6/OUT7 pairs; Output Manager retains
all budget, voltage, telemetry, thermal and fault authority.

The reference fuse ratings total 100 A and the reference current limits total
82 A. This is intentionally higher than the board-level continuous-current
budget. See ADR-0008.

## 4. Per-output requirements

Each output must support:

- User-serviceable fuse.
- High-side electronic switching.
- PWM where listed.
- Current measurement.
- Overcurrent protection.
- Thermal derating.
- Fault lockout.
- Configuration-based role assignment.
- Configuration-based current limit and priority.
- Safe default-off state during boot, reset, update, and fault recovery.

## 5. Board-level current budget

- Main harness fuse target: 50 A.
- Board continuous-current design target: at least 40 A after thermal validation.
- Default firmware/configuration total-current limit: 40 A.
- Outputs are allowed to be over-subscribed relative to the board budget.
- Firmware must refuse startup or shed lower-priority loads when the configured
  board-level budget would be exceeded.
- Total input current measurement is required for budget enforcement.
- `IIN_SENSE`, rather than only the sum of channel IMON readings, enforces the
  40 A managed-board budget.
- Mutually exclusive loads are evaluated through the configured operating-mode
  matrix and are not treated as simultaneously permitted.

## 6. Thermal and diagnostics

- Requires PCB temperature measurement.
- Requires power-zone temperature measurement.
- Must expose output fault status to LB-100.
- Must support firmware-visible diagnostic state for overcurrent, thermal
  derating, fuse/open-load suspicion where practical, and lockout.

## 7. Vehicle network safety

- PB-100 must not require vehicle CAN TX for any core function.
- If CAN1 routing or transceiver support crosses PB-100, CAN1 TX disable must be
  physically enforced by default.
- Any CAN1 TX enable path requires a new ADR and an explicit hardware action.

## 8. Board interface

PB-100 must expose a stable board-to-board interface to LB-100 for:

- Power and ground.
- Output enable/PWM commands.
- Current, voltage, and temperature telemetry.
- Fault/status signals.
- Board identity or revision identification where practical.
- Reserved expansion capacity.

The exact pin map is deferred to schematic freeze.

## 9. Manufacturing

- Fine-pitch and small SMD parts are factory assembled.
- User-installed parts are limited to connectors, fuses, enclosure hardware, and
  wiring.
- Critical component selections require at least two alternatives.
- Component availability for JLCPCB/PCBWay assembly must be checked before
  schematic freeze.
- Initial component-family shortlist is tracked in
  `docs/production/component-family-shortlist.md`.

## 10. Acceptance criteria

PB-100 requirements are ready for schematic planning when:

- ADR-0006 is accepted.
- ADR-0007 is accepted.
- ADR-0008 is accepted.
- Output count and protection model are stable.
- CAN read-only policy is preserved.
- Board-level current budget is documented.
- Factory/garage BOM split is still valid.
- Component-family shortlist exists with alternatives for critical parts.
