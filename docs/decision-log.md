# Decision Log

## 2026-06-30 — Project start

SVC Platform started from BMW R1200GS K25 OEM+ accessory power project.

## 2026-06-30 — Power Board long lifecycle

Decision: Power Board must be stable for 10–15 years and not redesigned for normal feature additions.

Reason: High-current vehicle wiring and connectors are the most expensive and risky parts to change.

## 2026-06-30 — Three-board architecture

Decision: Split hardware into Power Board, Logic Board, and Front Panel Board.

Reason: Allows future MCU/connectivity upgrades without redesigning the power stage.

## 2026-06-30 — CAN read-only default

Decision: BMW CAN is read-only by default. TX is physically disabled.

Reason: Avoid any risk to ZFE/ABS/DME/KOMBI operation.

## 2026-06-30 — Factory SMD assembly

Decision: All fine-pitch and small SMD parts must be assembled by the PCB manufacturer.

Reason: User has only a soldering iron, no working hot-air/rework station.

## 2026-06-30 — Architecture Review v1.0 freeze candidate

Decision: Architecture Review v1.0 is promoted from draft to freeze candidate.

Reason: Core platform boundaries are defined: PB-100 remains stable, outputs are
generic and configuration-mapped, CAN1 is read-only by default, and factory/garage
assembly responsibilities are separated.

## 2026-06-30 — PB-100 baseline requirements

Decision: PB-100 baseline requirements are captured in ADR-0006 and
`docs/requirements/pb-100-requirements.md`.

Reason: Power Board requirements must be explicit before schematic planning and
must not change later without ADR review.

## 2026-06-30 — STM32H5 product target accepted

Decision: ADR-0005 is accepted. LB-100 product target is STM32H563/H573 class,
with STM32H563 LQFP-100 preferred for Rev.1 schematic planning.

Reason: STM32H5 provides FDCAN, flash/RAM headroom, modern security features,
and current supplier availability suitable for the product baseline.

## 2026-06-30 — PB-100 high-side output switching

Decision: PB-100 outputs use high-side switching, captured in ADR-0007.

Reason: Automotive accessories normally share vehicle ground. High-side
switching gives safer wiring behavior and clearer fault handling.

## 2026-06-30 — Component-family shortlist

Decision: Initial factory-assembly component families are documented in
`docs/production/component-family-shortlist.md`.

Reason: Architecture freeze needs at least two viable alternatives for critical
components before schematic planning starts.

## 2026-06-30 — PB-100 board-level current budget

Decision: PB-100 outputs are intentionally over-subscribed relative to the main
fuse and board continuous-current budget. ADR-0008 sets the initial Rev.1 target
at 50 A main fuse and 40 A continuous board/configuration budget.

Reason: The reference channel limits total more than the input fuse, so firmware
and configuration must enforce total current and load priorities as safety
features.

## 2026-06-30 — Architecture v1.0 frozen

Decision: Architecture Review v1.0 is frozen by ADR-0009 after owner approval to
continue implementation.

Reason: The required platform decisions are accepted, PB-100 baseline
requirements are stable enough for schematic planning, and component families
have initial alternatives.

## 2026-06-30 — PB-100 power-path candidate strategy

Decision: ADR-0010 selects external smart high-side controller plus external
60 V N-MOSFET for high/medium outputs, integrated smart high-side switches for
low-current outputs, LM74700-class reverse protection, and SM8S33A-class input
TVS sizing. The low-current integrated-switch part is later superseded by
ADR-0011 for the Rev.1 baseline.

Reason: This keeps thermal and SOA margin for compressor, heated-seat, and
lighting loads while retaining simpler integrated switches for low-current
channels.

## 2026-06-30 — PB-100 TVS clamp compatibility risk

Decision: SM8S33A-class input TVS remains a candidate for 60 V or higher
power-path devices, but it is not accepted for any direct 40 V smart-switch rail.

Reason: Its clamp voltage class can exceed 40 V device limits. Low-current
smart-switch channels need a lower-clamp protection strategy or must move to the
external-controller architecture.

## 2026-06-30 — PB-100 schematic freeze gate

Decision: PB-100 schematic freeze is gated by
`hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md` before any
PCB layout work.

Reason: Architecture v1.0 authorizes schematic planning, but PCB layout must
remain blocked until unresolved protection, thermal, pin-map, BOM, and CAN1
listen-only implementation evidence is closed.

## 2026-06-30 — PB-100 low-current output stage

Decision: PB-100 Rev.1 uses TPS48110-class external-controller output stages for
OUT5, OUT8, and OUT9 instead of direct 40 V integrated smart switches.

Reason: This removes the SM8S33A-class TVS clamp conflict with 40 V smart
switches while keeping low-current channel fuse and current-limit requirements
unchanged.

## 2026-06-30 — PB-100 board-to-board pin map

Decision: PB-100 to LB-100 schematic planning uses `JPB1` with the logical
100-pin map captured in `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`.

Reason: Schematic freeze needs a concrete interface contract for power, grounds,
output control, telemetry, faults, board identity, expansion, and CAN1 TX-disable
signals before KiCad layout can be considered.

## 2026-06-30 — CAN1 TX-disable schematic input

Decision: PB-100 Rev.1 schematic planning requires CAN1 TX to be DNP/open and
hardware-disabled by default, with `CAN1_TX_DISABLED_STATUS` visible to LB-100
when the safety gate crosses PB-100.

Reason: This preserves the ADR-0002 vehicle-CAN read-only policy even if
firmware is faulty, LB-100 is reset, or a future board revision routes CAN1
through PB-100.

## 2026-06-30 — PB-100 input reverse MOSFET strategy

Decision: PB-100 Rev.1 schematic planning uses a dedicated low-Rds input MOSFET
strategy for LM74700-class reverse protection instead of a single 2.1 mOhm
PowerPAK output MOSFET.

Reason: A single 2.1 mOhm MOSFET dissipates about 6.72 W at the 40 A board
budget with the conservative thermal multiplier. The preferred 0.76 mOhm TOLL
class reduces the estimate to about 2.43 W, with an 80 V LFPAK88 alternate and a
dual-PowerPAK fallback retained for sourcing and assembly risk.

## 2026-06-30 — OUT2 startup/inrush SOA envelope

Decision: OUT2 schematic planning uses a defined startup/inrush envelope and
keeps a larger or parallel MOSFET escape path if SIDR626LDP-class SOA is not
confirmed.

Reason: OUT2 is the highest-risk output because the reference compressor load
can create startup and fault pulses beyond the 18 A continuous current limit.
The schematic must bound these pulses before PCB layout.

## 2026-06-30 — PB-100 bench validation matrix

Decision: PB-100 bench validation is tracked in `docs/testing/test-plan.md` with
explicit bring-up, protection, telemetry, thermal, current-budget, B2B, and CAN1
listen-only tests.

Reason: Schematic freeze requires a testable design, not only a component list.
The test matrix ties the schematic inputs to bench evidence before any motorcycle
installation.

## 2026-06-30 — PB-100 logic power rail strategy

Decision: PB-100 Rev.1 schematic planning uses a protected `PB_5V_OUT` rail
based on an LM5164-Q1-class 100 V 1 A buck, with LM5013-Q1-class 100 V higher
current fallback before considering 60 V buck families.

Reason: The logic rail must tolerate the same transient strategy as the power
path and must not be confused with accessory USB power. The 1 A budget is enough
for initial planning but keeps a 100 V higher-current escape path.

## 2026-06-30 — PB-100 current telemetry strategy

Decision: PB-100 Rev.1 uses TPS48110-class `IMON` outputs for per-channel
current telemetry and a dedicated input shunt monitor for total board current.

Reason: Per-output telemetry supports diagnostics and per-channel limits, while
the board-level 40 A budget must be enforced from an independent total input
current measurement.

## 2026-06-30 — PB-100 thermal telemetry strategy

Decision: PB-100 Rev.1 schematic planning uses three thermal points:
`TEMP_PCB`, `TEMP_PWR_A`, and `TEMP_PWR_B`.

Reason: One board reference and two power-zone measurements are needed to derate
OUT2, the input reverse-protection path, medium-output MOSFET clusters, and the
logic buck before sustained overheating.

## 2026-06-30 — PB-100 schematic planning ready for review

Decision: PB-100 schematic planning inputs are ready for schematic review, but
schematic freeze and PCB layout remain blocked until all conditional gates in
`hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md` are closed.

Reason: The package now has no active planning blockers and includes output,
power, telemetry, thermal, CAN safety, B2B, BOM, and bench-validation inputs.

## 2026-06-30 — PB-100 KiCad preparation boundary

Decision: PB-100 KiCad work may proceed only as preliminary symbol and footprint
preparation tracked in `hardware/power-board/PB-100/PB-100-kicad-prep.md`.

Reason: Schematic capture needs package preparation, but PCB layout, placement,
routing, and Gerber generation remain blocked until schematic freeze.

## 2026-06-30 — PB-100 schematic capture contract

Decision: PB-100 schematic capture now has a sheet plan, net naming contract,
and component instance plan under `hardware/power-board/PB-100/`.

Reason: The project needs a deterministic bridge from requirements and planning
tables to schematic capture while preserving generic outputs, CAN1 TX safety, and
the no-layout boundary.

## 2026-06-30 — PB-100 KiCad schematic scaffold

Decision: PB-100 now has a project-local KiCad scaffold under
`hardware/power-board/PB-100/kicad/` with a top schematic, local symbol table,
local footprint table, and empty local libraries.

Reason: This creates a concrete schematic workspace while intentionally omitting
`PB-100.kicad_pcb` so PCB layout remains blocked until schematic freeze.

## 2026-06-30 — PB-100 KiCad child sheet placeholders

Decision: PB-100 KiCad scaffold now includes placeholder child sheets for input
protection, logic power, outputs, telemetry, B2B interface, and CAN1 safety.

Reason: The schematic workspace now mirrors the capture plan and can be filled
incrementally without starting PCB layout.

## 2026-06-30 — PB-100 preliminary abstract symbols

Decision: PB-100 local KiCad symbol library now includes abstract preliminary
symbols for input protection, logic power, generic output channels, JPB1, and
CAN1 TX-disable scaffolding.

Reason: Schematic capture can proceed at block level before final vendor pinouts
and footprints are locked, while keeping these symbols explicitly non-final and
excluded from BOM/on-board status.

## 2026-06-30 — PB-100 repository validator

Decision: PB-100 schematic-planning and KiCad scaffold artifacts are validated by
`tools/validate_pb100.py`.

Reason: The project now has enough generated CSV and KiCad text artifacts that
basic structural checks must be automated before commits and pushes.

## 2026-06-30 — PB-100 garage connector and fuse families

Decision: PB-100 garage planning uses DEUTSCH DTP class for OUT1/OUT2,
DEUTSCH DT class for OUT3-OUT10, DEUTSCH DTM class for signal/CAN connectors,
and Littelfuse MAXI-class sealed inline holder for the main battery fuse.

Reason: DT contacts are too close for the 15 A and 20 A fuse output classes,
while DTP provides the needed high-current connector class. DTM remains a signal
connector family, not a power-output family.

## 2026-06-30 — Project validation baseline

Decision: Top-level project validation is `make check`, which runs
`python3 tools/validate_pb100.py` plus `make -C firmware test`. GitHub Actions
runs the same root command on push and pull request.

Reason: Hardware planning artifacts and firmware safety services now change
together, so project status must be verified from the repository root.

## 2026-06-30 — Firmware power budget service

Decision: Firmware now has a host-testable power budget service that denies
output startup on invalid telemetry, already-active outputs, invalid
configuration, or projected total-current overrun.

Reason: ADR-0008 makes board-level current-budget enforcement a safety feature,
so it needs executable tests before hardware is available.

## 2026-06-30 — Firmware output manager core

Decision: Firmware now has a host-testable Output Manager core that keeps all
outputs off by default, enables outputs only through generic `OUT1`..`OUT10`
IDs, checks the power budget before enabling, and locks outputs off after faults.

Reason: Output control must be centralized and role-agnostic so CAN/rules cannot
directly manipulate GPIO/PWM hardware.

## 2026-06-30 — Firmware battery protection service

Decision: Firmware now has a host-testable battery protection service with warn,
cutoff latch, recovery threshold, and invalid-telemetry cutoff behavior.

Reason: Low-voltage shutdown is a safety requirement and must fail safe before
vehicle integration.

## 2026-06-30 — Firmware event bus core

Decision: Firmware now has a host-testable fixed-size Event Bus with FIFO order,
overflow rejection, and empty-pop protection.

Reason: The architecture requires CAN, sensors, rules, logging, and output
control to communicate through events instead of direct feature-to-feature calls.

## 2026-06-30 — Firmware CAN safety guard

Decision: Firmware now has a host-testable CAN safety guard that denies CAN1
vehicle transmit attempts in Rev.1 and allows CAN2 expansion transmit.

Reason: Vehicle CAN must remain read-only by default even if higher-level code
attempts to transmit.

## 2026-06-30 — Firmware system safety coordinator

Decision: Firmware now has a host-testable System Safety Coordinator that
connects battery protection, Event Bus notification, and Output Manager shutdown
behavior.

Reason: Low-battery cutoff must disable physical outputs even if event
publication fails, and recovery must not automatically restore previous loads.

## 2026-06-30 — Firmware event dispatcher

Decision: Firmware now has a host-testable Event Dispatcher that drains fault
events from the Event Bus and applies output overcurrent/fault events through the
Output Manager fault path.

Reason: Safety events need an executable Event Bus to Output Manager path, while
preserving the rule that no feature code directly controls physical outputs.

## 2026-06-30 — Firmware host-test header dependencies

Decision: Firmware host-test targets now depend on `core/*.h` and `services/*.h`
headers and compile only C sources from each target dependency list.

Reason: Interface changes must force host-test binary rebuilds; otherwise local
checks can pass stale binaries after service header edits.

## 2026-06-30 — Firmware configuration validator

Decision: Firmware now has a host-testable configuration validator for battery
settings, power budget constraints, output ID continuity, and output role enum
bounds.

Reason: Accessory roles must remain configuration data. Firmware services should
reject invalid role values without hard-coding any role-to-output assignment.

## 2026-06-30 — Firmware config JSON repository validator

Decision: `make check` now runs `tools/validate_config.py`, which validates
`firmware/configs/config-example.json` against firmware role enums, electrical
limits, shed priority order, and C default configuration values.

Reason: The JSON vehicle/profile example and C default config must not drift
apart while configuration remains separate from firmware logic.

## 2026-06-30 — Firmware config JSON schema

Decision: Firmware now has `firmware/configs/svc-config.schema.json` for the
device configuration shape, output IDs, output roles, load priorities, fog logic,
and rule entries.

Reason: SVC Studio, SVC Mobile, and CI need a shared schema artifact before UI
configuration editing and import/export flows are implemented.

## 2026-06-30 — Firmware role resolver and rule engine skeleton

Decision: Firmware now has a host-testable Role Resolver and Rule Engine action
executor that apply enable/disable actions by configured accessory role and then
call the Output Manager by generic output ID.

Reason: Rule logic must not hard-code physical output numbers. Missing or
ambiguous role mappings must fail closed instead of guessing a channel.

## 2026-06-30 — Firmware rule condition state

Decision: Firmware now has host-testable rule condition state tracking for
engine running, high beam, and left indicator events, plus all-conditions-match
evaluation.

Reason: Rule execution needs an event-derived state layer before JSON rule
parsing and vehicle-specific logic are added.

## 2026-06-30 — Firmware in-memory rule runner

Decision: Firmware Rule Engine now evaluates in-memory rules by checking
conditions first and applying role-based actions only when all conditions match.

Reason: The firmware now has an executable path from event-derived state to
configured role action to Output Manager, without adding JSON parsing or direct
channel assumptions prematurely.

## 2026-06-30 — Firmware initial rule text grammar

Decision: Firmware now has a host-testable rule text parser for
`engine_running`, `high_beam`, and `left_indicator` boolean conditions plus
`ROLE.pwm = 0..100` actions. Repository config validation checks JSON rules
against the same limited grammar.

Reason: Configuration examples must not accept rule strings that firmware cannot
understand. The initial grammar established the safe rule-action boundary before
full duty-cycle output control was added.

## 2026-06-30 — Firmware PWM ownership in Output Manager

Decision: Output Manager now owns per-output PWM duty-cycle state. Rule actions
can request `0..100` duty; duty `0` disables the output, duty `1..100` enables
the output, and partial duty is denied when `pwm_allowed` is false.

Reason: PWM requests must remain behind the same safety boundary as on/off
output state, budget checks, lockout, and role mapping.

## 2026-06-30 — Firmware rule text compile helper

Decision: Rule text parsing can now compile condition/action strings into an
in-memory `svc_rule_t` using caller-provided condition storage, and tests execute
that compiled rule through the Rule Engine and Output Manager.

Reason: The firmware needs a deterministic bridge from configuration rule text
to executable in-memory rules without adding dynamic allocation or a full JSON
parser to the embedded layer yet.

## 2026-06-30 — PB-100 layout artifact blocker

Decision: `tools/validate_pb100.py` now blocks PB-100 PCB layout and
manufacturing artifacts, including `.kicad_pcb`, Gerber, drill, placement, and
zipped manufacturing outputs, before schematic freeze.

Reason: Architecture and project rules prohibit PCB layout before the PB-100
schematic freeze checklist is closed, so the repository validator must enforce
that boundary automatically.

## 2026-06-30 — Firmware telemetry snapshot service

Decision: Firmware now has a host-testable Telemetry Snapshot service for
battery voltage, total input current, and per-output current samples with
validity flags and stale-data checks.

Reason: Safety services need a single telemetry validity boundary before ADC,
I2C, or CAN drivers exist. Missing, invalid, or stale telemetry must propagate to
safe denial/cutoff behavior.

## 2026-06-30 — Firmware telemetry-backed safety wrappers

Decision: System Safety and Rule Engine now have wrapper APIs that consume
Telemetry Snapshot inputs directly. Stale battery telemetry forces cutoff, and
stale total-current telemetry denies matching rule actions through the Output
Manager budget path.

Reason: Callers should not duplicate telemetry freshness logic or pass raw
validity flags around once a central snapshot service exists.

## 2026-06-30 — Firmware event log ring buffer

Decision: Firmware now has a host-testable fixed-size Event Log ring buffer that
stores timestamped events, preserves the latest entries on overflow, and counts
dropped entries.

Reason: Diagnostics and future service APIs need deterministic logging without
dynamic allocation before persistent storage or transport-specific logging is
added.

## 2026-06-30 — Optional PB-100 KiCad ERC validation

Decision: `tools/validate_pb100.py` now runs KiCad schematic ERC for PB-100 when
`kicad-cli` is available and requires zero reported violations.

Reason: The repository now has a KiCad 10 schematic scaffold. Automated ERC
should be part of local final-readiness checks without making CI depend on KiCad
until the CI image explicitly installs it.

## 2026-06-30 — Firmware thermal protection service

Decision: Firmware now has a host-testable Thermal Protection service for
PB-100 `TEMP_PCB`, `TEMP_PWR_A`, and `TEMP_PWR_B` zones with allow, derate, and
cutoff actions plus per-zone cutoff latching.

Reason: PB-100 requirements treat missing, stale, or implausible thermal
telemetry as a safe fault. Thermal thresholds must remain configuration values
and must not encode accessory roles.

## 2026-06-30 — Firmware thermal cutoff safety path

Decision: System Safety now consumes Thermal Protection results from Telemetry
Snapshot, publishes thermal derate/cutoff events, and disables all active outputs
through the Output Manager on thermal cutoff or stale thermal telemetry.

Reason: Thermal decisions must be applied through the same centralized output
safety boundary as battery cutoff and output faults; recovery must not
automatically restore previous loads.

## 2026-06-30 — Project final readiness gates

Decision: `docs/product/final-readiness.md` now defines repository readiness
levels, automated gates, schematic-freeze requirements, PCB-layout blockers, and
prototype bring-up prerequisites.

Reason: The project now has enough hardware planning, KiCad scaffold, firmware
safety code, and validation tooling that “ready” must be explicit and separated
from PB-100 PCB layout authorization.

## 2026-06-30 — Optional PB-100 KiCad netlist export validation

Decision: `tools/validate_pb100.py` now exports a temporary PB-100 KiCad
S-expression netlist when `kicad-cli` is available and validates the exported
netlist syntax.

Reason: ERC proves the schematic has no reported violations, while netlist
export proves the scaffold can move into downstream schematic-review artifacts
without committing generated layout or manufacturing files.

## 2026-06-30 — PB-100 KiCad role-token guard

Decision: `tools/validate_pb100.py` now scans PB-100 KiCad schematic and symbol
files for accessory-role tokens such as `FOG`, `USB`, `SEAT`, `CHIGEE`, `DVR`,
`BRAKE`, and `CIGARETTE`.

Reason: PB-100 must remain vehicle-agnostic. KiCad artifacts must use generic
`OUT1`..`OUT10` naming and keep accessory roles in configuration only.
