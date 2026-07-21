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

## 2026-06-30 — PB-100 symbol/MPN readiness gate

Decision: PB-100 schematic freeze now requires
`hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv`, with critical
symbol keys, preferred candidate MPNs/classes, at least two alternatives, source
links, footprint status, and explicit assembly/sourcing recheck notes.

Reason: Preliminary KiCad symbol work can proceed safely only if every critical
component remains source-aware, non-final, and traceable to schematic-freeze
evidence without starting PCB layout.

## 2026-06-30 — PB-100 symbol capture worklist

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-symbol-capture-worklist.csv`, mapping every
critical symbol key to a project-local `PB100_*_PRELIM` symbol target, source,
pin-evidence status, instance refs, allowed action, blocked action, and freeze
closure evidence.

Reason: The local KiCad installation does not provide reusable project-ready
symbols for the selected PB-100 candidates. A validated worklist lets schematic
symbol creation proceed in controlled steps while preserving the no-layout gate.

## 2026-06-30 — First PB-100 concrete preliminary symbols

Decision: `hardware/power-board/PB-100/kicad/lib/PB100.kicad_sym` now includes
preliminary concrete symbols for TPS48110AQDGXRQ1, LM74700QDBVRQ1,
LM5164QDDATQ1, and INA228-Q1, with pinouts extracted from official TI data
sheets and kept excluded from BOM/board output.

Reason: These are core schematic-capture dependencies for output control, input
reverse protection, protected 5 V power, and total input current telemetry. They
can be reviewed now without locking footprints or authorizing PCB layout.

## 2026-06-30 — PB-100 symbol pin evidence validation

Decision: Created PB-100 preliminary symbols now have
`hardware/power-board/PB-100/PB-100-symbol-pin-evidence.csv`, and
`tools/validate_pb100.py` checks every recorded pin number/name against
`PB100.kicad_sym`.

Reason: Schematic capture needs traceable pinout provenance. A machine check
prevents the worklist from claiming a symbol is created while the KiCad library
misses or renames pins.

## 2026-06-30 — PB-100 passive class symbols

Decision: PB-100 now has preliminary class symbols for input TVS, four-terminal
input shunt, thermal NTC, output connector class, and main fuse class. These
symbols remain excluded from BOM/board output and use internal schematic-class
pin evidence until final MPN/package selection.

Reason: Schematic capture can represent protection, telemetry, and
garage-installed interfaces without pretending that package drawings, PCB
footprints, or final sourcing are locked.

## 2026-06-30 — PB-100 MOSFET and CAN safety preliminary symbols

Decision: PB-100 now has preliminary symbols and pin evidence for
SIDR626LDP-class output MOSFETs, a Nexperia LFPAK88 escape MOSFET class, and
the CAN1 TX-disable schematic gate. Infineon TOLL input-reverse MOSFET symbol
work remains pending until package pin evidence is reviewed separately.

Reason: Output-channel schematic capture needs MOSFET symbols now, but the
input reverse-protection TOLL package and OUT2 escape decision must not be
locked before SOA, thermal, and assembly evidence closes.

## 2026-06-30 — PB-100 JPB1 preliminary symbol

Decision: PB-100 now has a preliminary `PB100_JPB1_100PIN_PRELIM` symbol
generated from `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`, and
`tools/validate_pb100.py` checks all 100 symbol pins against that pin map.

Reason: The PB-100/LB-100 interface can be captured schematically without
choosing or placing a final mezzanine connector footprint. The pin contract
remains source-controlled and machine-checked before connector MPN lock.

## 2026-06-30 — PB-100 pending symbol gate

Decision: PB-100 now tracks intentionally uncreated schematic symbols in
`hardware/power-board/PB-100/PB-100-symbol-open-items.md`, and
`tools/validate_pb100.py` fails if a pending symbol appears in `PB100.kicad_sym`
without its worklist status and evidence being updated.

Reason: The IAUTN06S5N008/TOLL input reverse MOSFET is high-risk for package and
assembly lock. It must remain explicit pending work until pin evidence, package
drawing, and factory assembly support are reviewed.

## 2026-06-30 — PB-100 output fuse class symbol

Decision: PB-100 now has `OUTPUT_FUSE_HOLDER` in symbol readiness, a
`PB100_OUTPUT_FUSE_CLASS_PRELIM` KiCad symbol, and pin evidence for the generic
per-output fuse path used by F101 through F110.

Reason: Output fuses are part of the schematic instance plan and garage
installation model. They need a schematic-class symbol without moving fuse
holders onto the PCB or locking a footprint.

## 2026-06-30 — PB-100 instance-symbol map

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-schematic-instance-symbol-map.csv`, linking
every row in the schematic instance plan to a symbol key and concrete
`PB100_*_PRELIM` symbol target. Validation checks one-to-one reference coverage,
worklist consistency, created/pending state, and the OUT2 escape-FET note.

Reason: Schematic capture needs a controlled path from planned references
(`U101`, `Q102`, `JPB1`, `TP1..TPn`) to project-local symbols before real
schematic placement starts.

## 2026-06-30 — PB-100 sheet-reference map

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-schematic-sheet-reference-map.csv`, assigning
every planned schematic reference to a KiCad child sheet or an explicit
cross-sheet review bucket. Validation checks reference coverage, sheet file
existence, symbol-key consistency, Q1 pending-symbol status, and `TP1..TPn`
review-defined handling.

Reason: Schematic capture should place references deliberately by block instead
of relying on ad hoc sheet edits. This preserves the no-layout boundary while
making the KiCad capture sequence reviewable.

## 2026-06-30 — PB-100 KiCad sheet manifest

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-kicad-sheet-manifest.csv`, and
`tools/validate_pb100.py` checks the manifest against the actual top-level and
child `.kicad_sch` files plus the sheet-reference map.

Reason: Schematic capture needs a stable file-level scaffold. The manifest
prevents child sheets from being added, removed, or renamed without updating
the review package and automated checks.

## 2026-06-30 — PB-100 schematic net-domain plan

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-schematic-net-domain-plan.csv`, defining
schematic-only net domains, default states, directions, primary sheets, and
safety rules. Validation requires key power, telemetry, output, and CAN1 safety
patterns and verifies `CAN1_TX_ROUTE` remains DNP/open unless a future ADR
changes policy.

Reason: Net naming alone is not enough for schematic capture. The design needs
machine-checkable intent for power, logic, analog telemetry, generic outputs,
and vehicle-CAN safety before any schematic freeze review.

## 2026-06-30 — PB-100 symbol-to-BOM synchronization

Decision: PB-100 now has `production/bom/pb100_symbol_bom_map.csv`, linking
every symbol readiness key to either the factory or garage BOM draft. The factory
BOM now includes input shunt, buck inductor, B2B connector, board ID resistor
network, test points, and CAN1 TX-disable DNP link rows. The garage BOM now
includes battery input connector and per-output fuse holder rows.

Reason: Schematic symbol planning changes hardware assumptions. BOM drafts must
stay synchronized with schematic artifacts so sourcing and assembly ownership do
not drift before schematic freeze.

## 2026-06-30 — PB-100 schematic readiness contracts

Decision: PB-100 now has a machine-checked readiness dashboard plus schematic
contracts for output-channel pins, input-protection pins, and logic-power design
placeholders. `tools/validate_pb100.py` checks these files against the instance
map, `JPB1` pin map, net-domain plan, pending Q1 reverse-FET state, CAN1
DNP/open policy, and the no-final-values-before-review rule.

Reason: The project is close enough to schematic capture that review status,
net intent, and unresolved close work must be synchronized automatically. These
contracts reduce manual drift without starting PCB layout or pretending that
Q1, logic-power values, SOA, footprints, or assembly sourcing are final.

## 2026-06-30 — PB-100 output controller pin template

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-output-controller-pin-template.csv`, mapping
the preliminary TPS48110 controller pins to generic `OUTn_*` schematic patterns.
Validation checks every template pin number/name against
`PB-100-symbol-pin-evidence.csv` for `PB100_TPS48110AQDGXRQ1_PRELIM`, keeps
local threshold/timing/bootstrap/gate-drive values non-final, and requires the
template to remain role-agnostic.

Reason: The output-channel schematic needs more detail than a controller symbol
and high-level channel contract. A checked pin template lets OUT1 through OUT10
share one reviewable pattern while preserving configuration-based role mapping
and blocking value/footprint lock before schematic review.

## 2026-06-30 — PB-100 input and power pin templates

Decision: PB-100 now has checked pin templates for the LM74700 input
ideal-diode controller, INA228 total-current monitor, and LM5164 logic buck:
`PB-100-input-controller-pin-template.csv`,
`PB-100-current-monitor-pin-template.csv`, and
`PB-100-logic-buck-pin-template.csv`. Validation compares each template against
`PB-100-symbol-pin-evidence.csv`, keeps all values and local networks
non-final, and verifies the templates remain tied to schematic-review close
work.

Reason: Input protection, total-current measurement, and the protected logic
rail are freeze-critical blocks. Capturing their pin-level intent now reduces
schematic-review ambiguity while keeping Q1 package evidence, shunt calibration,
UVLO, feedback, EMI, and sourcing decisions open until reviewed.

## 2026-06-30 — PB-100 schematic freeze gap register

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-schematic-freeze-gap-register.csv` with one
row for every `Conditional` gate in the schematic freeze checklist.
`tools/validate_pb100.py` parses the checklist table, verifies exact register
coverage, and keeps CAN1 DNP/open, Q1/TOLL/40 A, factory assembly alternatives,
and garage user-scope close work explicit.

Reason: The freeze checklist defines the gate, but the remaining work needs an
operational register that can be assigned, reviewed, and closed without losing
synchronization. Machine-checking the register prevents conditional gates from
being silently omitted before schematic freeze.

## 2026-06-30 — PB-100 design-value placeholders

Decision: PB-100 now has machine-checked design-value placeholder tables for
output stages, input power, and logic power:
`PB-100-output-stage-design-values.csv`,
`PB-100-input-power-design-values.csv`, and
`PB-100-logic-power-design-values.csv`. Validation requires complete class or
block coverage, rejects final/locked values, checks referenced nets against the
pin templates, preserves OUT2 SOA and low-current external-controller notes,
and keeps Q1/TOLL/40 A, four-terminal shunt, LM5013-Q1 fallback, and
configuration-based role mapping explicit.

Reason: Schematic capture needs concrete value positions for thresholds, timing,
gate drive, bootstrap, shunt, UVLO, feedback, EMI, and power-good networks, but
the actual values are not safe to lock before SOA, thermal, clamp, sourcing, and
assembly review. These tables make the remaining value work reviewable without
starting PCB layout.

## 2026-06-30 — PB-100 CAN1 safety verification matrix

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-can1-safety-verification.csv`, a dedicated
matrix for vehicle-CAN read-only behavior, DNP/open `CAN1_TX_ROUTE`, reset and
unpowered disable behavior, disabled-state readback, RX independence, DNP BOM
ownership, firmware listen-only policy, and the future-ADR plus hardware-action
process. `tools/validate_pb100.py` fails if the matrix omits any required CAN1
safety requirement or allows default-populated/default-enabled TX.

Reason: CAN1 safety is a constitutional rule, not a normal design preference.
A separate checked matrix keeps the physical TX-disable policy visible across
schematic, BOM, firmware safety, and future-change review before schematic
freeze.

## 2026-06-30 — PB-100 assembly sourcing recheck register

Decision: PB-100 now has
`production/bom/pb100_assembly_sourcing_recheck.csv`, covering every critical
symbol readiness key with factory or garage ownership, recheck source,
alternate coverage, owner-specific action, and schematic-freeze dependency.
`tools/validate_pb100.py` checks the register against critical symbol readiness
and `pb100_symbol_bom_map.csv`, requires factory/garage actions to match BOM
ownership, keeps recheck language explicit, and preserves CAN1 DNP/open plus
Q1/TOLL/40 A constraints.

Reason: Component availability and assembly support can change. The design
should not treat candidate MPNs as locked until JLCPCB/PCBWay, distributor,
connector, fuse-holder, wire-gauge, and serviceability checks are repeated near
schematic freeze.

## 2026-06-30 — PB-100 validation traceability register

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-validation-traceability.csv`, mapping every
conditional schematic-freeze gate to a schematic, bench, or production review
validation row. `tools/validate_pb100.py` parses the freeze checklist and fails
if any conditional gate lacks validation coverage or if CAN1 DNP/open/read-only,
Q1/40 A, factory sourcing recheck, or garage scope constraints are lost.

Reason: Freeze gaps are not closed by documentation alone. Each conditional
gate needs explicit validation evidence before it can move to `Closed`, and the
coverage must stay synchronized as the checklist changes.

## 2026-06-30 — PB-100 output net expansion

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-output-net-expansion.csv`, expanding every
generic `OUTn_*` output-controller and output-channel net pattern into concrete
`OUT1_*` through `OUT10_*` schematic nets. `tools/validate_pb100.py` checks the
expansion against the output matrix, controller template, sheet manifest, and
`JPB1` control/fault/current nets.

Reason: Schematic capture should not rely on hand-expanding repeated output
channel nets. A machine-checked expansion table keeps the ten-channel capture
role-agnostic, repeatable, and aligned with the board-to-board interface.

## 2026-06-30 — PB-100 test point plan

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-test-point-plan.csv`, assigning schematic
test-point references to rails, telemetry, CAN1 safety, and every output
control/fault/current/fused net. `tools/validate_pb100.py` checks contiguous
`TP###` refs, sheet ownership, required net coverage, JPB1-facing nets, CAN1 TX
safety, and the no-footprint/no-placement-lock boundary.

Reason: Bring-up and bench validation need planned measurement points before
schematic capture. The test-point plan makes validation access explicit without
starting layout or locking physical pads before schematic freeze.

## 2026-06-30 — PB-100 fault response matrix

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-fault-response-matrix.csv`, covering input,
logic-power, B2B, output, fuse, thermal, current telemetry, board-budget, CAN1,
and board-identity faults. `tools/validate_pb100.py` requires every fault ID,
safe hardware defaults, explicit firmware safe actions, logging, validation
artifacts, CAN1 DNP/open/future-ADR protection, OUT2 SOA linkage, and
role-agnostic board identity behavior.

Reason: Safety behavior must be traceable before schematic freeze. The matrix
keeps fault handling consistent across hardware defaults, firmware policy, test
planning, and validation artifacts without encoding accessory roles in PB-100.

## 2026-06-30 — PB-100 capture queue and release manifest

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-schematic-capture-work-queue.csv` and
`hardware/power-board/PB-100/PB-100-review-release-manifest.csv`.
`tools/validate_pb100.py` checks sheet-level capture work against the KiCad
sheet manifest, sheet-reference map, source artifacts, Q1/TOLL blocker, CAN1
DNP/open future-ADR policy, and explicit no-layout boundaries. It also checks
that required freeze-packet artifacts exist and are listed in the release
manifest with validation hooks.

Reason: The next execution step is schematic capture. The work queue prevents
ad hoc sheet edits, while the release manifest keeps the freeze packet complete
and auditable before any layout authorization.

## 2026-06-30 — PB-100 KiCad sheet work-queue markers

Decision: PB-100 KiCad schematic placeholder sheets now include `Work queue:
CAP-*` title-block markers. `tools/validate_pb100.py` checks each real KiCad
sheet listed in `PB-100-schematic-capture-work-queue.csv` for the matching
marker.

Reason: The spreadsheet work queue and the KiCad files must not drift. Embedding
the work item marker in each placeholder sheet makes the capture sequence
traceable inside KiCad while still avoiding schematic placement and PCB layout.

## 2026-06-30 — PB-100 role-free hardware capabilities

Decision: PB-100 now has
`firmware/configs/hardware/pb-100-capabilities.json`, a role-free hardware
capability manifest for generic outputs, telemetry, power budget, safe defaults,
and CAN1 read-only behavior. `tools/validate_config.py` checks it against the
PB-100 output matrix, current/thermal telemetry maps, firmware config defaults,
and CAN1 DNP/open future-ADR policy. The PB-100 release manifest includes the
capability file as a required freeze artifact.

Reason: Firmware and configuration need a machine-readable hardware capability
contract that does not encode vehicle accessory roles. Role mapping remains in
configuration and vehicle profiles, while hardware capability discovery uses
board identity and generic `OUT1`..`OUT10` capabilities.

## 2026-07-09 — Firmware hardware capability guard

Decision: Firmware now has a role-free hardware capability validation service in
`firmware/services/hardware_capability.c` with host tests in
`firmware/tests/test_hardware_capability.c`. The service validates generic board
output count, safe default-off behavior, per-output electrical limits, PWM
support, board current budget, and CAN1 read-only default policy before a device
configuration is accepted against a board capability contract.

Reason: The PB-100 capability manifest must become an executable firmware
boundary, not only a JSON artifact. The guard keeps hardware capability
discovery separate from vehicle role mapping and fails safe if a configuration
exceeds PB-100 electrical limits or weakens CAN1 read-only behavior.

## 2026-07-09 — PB-100 compiled capability baseline

Decision: Firmware now exposes `svc_pb100_hardware_capability` in
`firmware/services/pb100_capability.c` as the compiled PB-100 Rev.1 capability
baseline. `firmware/tests/test_hardware_capability.c` uses that constant instead
of a private fixture, and `tools/validate_config.py` compares the C constant
against `firmware/configs/hardware/pb-100-capabilities.json`.

Reason: The JSON capability manifest and the firmware capability contract must
stay synchronized. A checked compiled constant gives firmware a concrete
role-free board capability source while keeping accessory roles in configuration
and preserving CAN1 read-only defaults.

## 2026-07-09 — Configuration acceptance boundary

Decision: Firmware now has `svc_config_accept_for_hardware()` in
`firmware/services/config_acceptance.c`. The boundary composes generic
configuration validation with the discovered hardware capability contract and
classifies startup failures as invalid configuration, invalid hardware
capability data, or a valid configuration exceeding the connected board limits.

Reason: A configuration that is internally valid can still be unsafe for a
specific board capability set. Startup must reject that case before Output
Manager, System Safety, Rule Engine, or other services act on configuration
data.

## 2026-07-09 — Runtime boot safety boundary

Decision: Firmware now has `svc_runtime_boot()` in
`firmware/services/runtime_boot.c`. Runtime boot initializes the Event Bus,
accepts configuration against discovered hardware capability, and initializes
Output Manager plus System Safety only after acceptance succeeds. Rejected
configuration or invalid capability leaves the runtime uninitialized with zero
active outputs.

Reason: Safe default-off behavior must hold at startup, not only inside
individual services. A single boot boundary prevents services from being
initialized around an unsafe configuration/capability pairing.

## 2026-07-09 — Configuration store persistence contract

Decision: Firmware now has a storage-backend-neutral Configuration Store in
`firmware/services/config_store.c`. It builds versioned records with sequence
numbers and explicit checksums, validates records before use, selects the newest
valid record from two slots, and falls back to compiled defaults only when no
valid persisted record exists.

Reason: Configuration is separate from firmware. Firmware updates must not erase
or silently override valid user configuration with new compiled defaults.

## 2026-07-09 — Store-backed runtime boot

Decision: `svc_runtime_boot_from_store()` now loads the newest valid
configuration record from the two-slot Configuration Store, falls back to
compiled defaults only when no valid persisted record exists, and then runs the
runtime boot acceptance path. The caller owns the loaded configuration storage
for the runtime lifetime.

Reason: Persistence and startup safety need to be connected. Firmware must boot
from valid persisted user configuration after updates, but still reject the boot
if the loaded configuration exceeds the connected hardware capability.

## 2026-07-09 — Configuration update persistence gate

Decision: Firmware now has `svc_config_update_prepare_record()` in
`firmware/services/config_update.c`. New persisted configuration records are
created only after the candidate configuration is accepted against the target
hardware capability. Rejected configurations leave the output record empty.

Reason: Boot-time rejection is necessary but not sufficient. The service-tool or
future API path that writes configuration must also prevent unsafe or
hardware-incompatible configuration from becoming the persisted user record.

## 2026-07-09 — CAN receive-only log

Decision: Firmware now has a receive-only CAN frame log in
`firmware/services/can_log.c`. It stores CAN1/CAN2 received frames in a fixed
ring buffer, tracks dropped frames and per-port receive counts, and rejects
invalid ports or DLC values. It exposes no transmit API.

Reason: The firmware MVP needs CAN read-only logging while preserving the
vehicle-CAN safety policy. A receive-only logging boundary moves the CAN logger
forward without adding any path that can transmit on CAN1.

## 2026-07-09 — CAN receive-only event decode

Decision: Firmware now has `firmware/services/can_decode.c`, which maps
received CAN frames to internal Event Bus events using caller-provided rules. It
matches by port and CAN identifier mask, evaluates configured byte/bit
conditions, suppresses unchanged repeated states, and reports dropped events
when the Event Bus is full.

Reason: CAN-derived behavior must flow through the Event Bus and Rule Engine,
not directly to outputs. A receive-only decoder advances CAN-aware automation
without adding a vehicle-CAN transmit path or hard-coding BMW message IDs in the
service.

## 2026-07-09 — Product readiness status refresh

Decision: `docs/product/final-readiness.md` and `docs/product/roadmap.md` now
reflect the firmware configuration persistence, hardware capability, config
update, config acceptance, and runtime boot host-test coverage added on
2026-07-09.

Reason: Readiness documents should track the repository state used for planning
the next work. The update is status-only and does not change PB-100 requirements
or authorize PCB layout.

## 2026-07-09 — Rule Event Bridge

Decision: Firmware now has a host-tested Rule Event Bridge that drains
rule-condition events from the Event Bus into `svc_rule_state_t` while retaining
non-rule events for safety and diagnostic dispatchers.

Reason: CAN-derived state changes must reach the Rule Engine through the
documented Event Bus boundary without bypassing Output Manager, hard-coding
physical output roles, or dropping fault events.

## 2026-07-09 — Ordered Rule Set Runner

Decision: Firmware now has a host-tested ordered rule set runner that evaluates
arrays of `svc_rule_t`, continues past unmatched conditions, applies matching
role-based actions in order, and stops on the first denied action while
reporting the failed rule index.

Reason: The configuration model already allows multiple `then` actions per
logical rule. Representing those actions as ordered `svc_rule_t` entries with
shared conditions gives firmware a deterministic multi-action execution path
without hard-coding channel roles or bypassing Output Manager safety checks.

## 2026-07-09 — Multi-action Rule Text Compiler

Decision: Firmware rule text compilation now supports one condition list plus
multiple action strings, producing an ordered `svc_rule_t` array in caller-owned
storage.

Reason: The example configuration uses `then[]` arrays. Compiling those actions
into ordered in-memory rules closes the next gap between configuration grammar
and the rule-set runner while keeping configuration separate from firmware and
avoiding dynamic allocation in the firmware core.

## 2026-07-09 — Rule Configuration Validation Tightening

Decision: Repository config validation now requires non-empty `then[]` arrays,
checks that each rule action resolves to exactly one configured role mapping,
and rejects partial PWM requests when the mapped output is not PWM-capable.

Reason: The JSON schema and repository validator must match the firmware rule
compiler and Output Manager boundary. Catching unmapped, ambiguous, or
electrically impossible rule actions at validation time reduces runtime
surprises without hard-coding physical channel roles.

## 2026-07-09 — Rule Runtime Processing Step

Decision: Firmware now has a host-tested Rule Runtime step that runs Rule Event
Bridge, Event Dispatcher, and ordered Rule Engine evaluation in a fixed order.
Fault events are dispatched through Output Manager before matching rule actions
can request output state.

Reason: The firmware MVP needs a deterministic event-to-action loop, not just
separate services. Keeping the composition explicit preserves CAN receive-only
behavior, role-based output mapping, telemetry fail-safe denial, and the single
Output Manager boundary for physical outputs.

## 2026-07-09 — PB-100 sourcing evidence snapshot

Decision: PB-100 production planning now has
`production/bom/pb100_sourcing_evidence_snapshot.csv`, and
`tools/validate_pb100.py` requires it to cover every critical symbol key. The
snapshot captures current sourcing evidence and keeps open blockers explicit.

Reason: Factory assembly readiness must be evidence-driven before schematic
freeze. A separate sourcing snapshot makes external evidence auditable without
pretending that package assembly, reel availability, or distributor continuity
are already closed.

## 2026-07-09 — PB-100 TVS candidate source correction

Decision: The input TVS candidate direction is updated from MCC `SM8S33A` to an
active AEC-Q101 `SM8S33AHE3_A/I`-class DO-218AB TVS or reviewed equivalent.
The MCC page is retained only as EOL/obsolete evidence and must not be locked as
the schematic MPN.

Reason: Current sourcing review found the MCC `SM8S33A` source obsolete with a
2025 last-time-ship notice. Keeping it as the preferred candidate would make the
factory assembly plan fragile before schematic freeze.

## 2026-07-09 — PB-100 TVS artifact synchronization

Decision: PB-100 schematic-package, protection-validation, footprint-plan,
symbol-capture, and production README artifacts now use the active
`SM8S33AHE3`-class TVS wording. `tools/validate_pb100.py` rejects the old MCC
`SM8S33A` URL as an active TVS source and rejects stale `SM8S33A-class` wording
in active schematic-planning artifacts.

Reason: The TVS source correction must be enforceable across the schematic
freeze packet, not only in the sourcing snapshot. This prevents the obsolete
source from drifting back into active symbol, footprint, or protection inputs.

## 2026-07-09 — Ambient light rule conditions

Decision: Firmware rule condition state and rule text parsing now support
`ambient_day`, `ambient_dusk`, and `ambient_night` boolean conditions driven by
Event Bus ambient-light events. The example configuration expresses day, dusk,
night, and high-beam fog-light PWM behavior as role-based rules.

Reason: The reference vehicle requires fog light behavior to respond to ambient
light and CAN-derived state without hard-coding physical output channels.
Adding ambient-light conditions keeps the behavior in configuration and the Rule
Engine path, with Output Manager still owning physical output changes.

## 2026-07-09 — Rule Schema Pattern Enforcement

Decision: `firmware/configs/svc-config.schema.json` now constrains rule
condition and action strings with the same supported patterns checked by
`tools/validate_config.py`.

Reason: The schema is part of the configuration contract and should reject
unsupported rule-string shapes before firmware-specific validation runs. Keeping
the schema patterns machine-checked against the repository validator prevents
ambient-light rule support and future grammar changes from drifting.

## 2026-07-10 — PB-100 TVS HM3 sourcing correction

Decision: PB-100 input TVS planning now uses Vishay `SM8S33AHM3/I` as the
preferred active 33 V load-dump TVS candidate. The older Vishay
`SM8S33AHE3_A/I` evidence is retained only as NFD stock-only evidence, and the
MCC `SM8S33A` source remains EOL evidence only.

Reason: Vishay's current HE3-family datasheet marks that branch not for new
designs and points to the HM3 family. The HM3 branch preserves the same 33 V
stand-off, 53.3 V clamp, 124 A pulse-current class while moving the planning
baseline to an active AEC-Q101 branch. Schematic freeze still requires clamp
margin, overshoot, and DO-218AC assembly handling validation.

## 2026-07-10 — PB-100 total-current shunt candidate

Decision: PB-100 total input current measurement now uses a 0.5 mΩ
four-terminal AEC-Q200 shunt candidate, with Bourns CSS4J-4026R-L500F-class as
the preferred sourcing direction. INA228-Q1-class monitoring should use the
±40.96 mV shunt range candidate for the 0-60 A telemetry span.

Reason: A 0.5 mΩ shunt produces 30 mV at 60 A and about 1.8 W, while producing
20 mV and about 0.8 W at the 40 A board-budget target. This keeps measurement
loss and heating low while retaining enough signal for the dedicated input
current monitor. Schematic freeze still requires exact orderable suffix,
JLCPCB/PCBWay assembly class, Kelvin footprint, copper heating, and calibration
review.

## 2026-07-10 — PB-100 thermal NTC candidate

Decision: PB-100 thermal telemetry now uses a TDK `NTCGS103JF103FT8`-class
10 kΩ AEC-Q200 NTC as the preferred schematic-planning direction for
`TEMP_PCB`, `TEMP_PWR_A`, and `TEMP_PWR_B`. Vishay `NTCS0402E3` and Murata
`NCU18XH103D6SRB`-class automotive NTC families remain alternates.

Reason: The selected TDK class supports a 150 °C operating maximum and an
AEC-Q200 automotive grade while keeping all three thermal points on one common
10 kΩ curve. This closes the sensor-family gap without freezing divider values
or calibration constants. Schematic freeze still requires ADC scaling,
placement, self-heating review, JLCPCB/PCBWay assembly handling, and bench
calibration.

## 2026-07-10 — PB-100 CAN1 TX-disable capture contract

Decision: PB-100 CAN1 safety capture now explicitly treats `JP_CAN1` as the
DNP/open physical missing-link in `CAN1_TX_ROUTE` and `U_CAN1` as the optional
default-disabled gate or silent-control element with physical disabled-status
readback to LB-100.

Reason: The project rule is that BMW/vehicle CAN is read-only by default.
Documenting the capture contract and BOM ownership before final schematic
wiring keeps the default state auditable: no default-populated TX item,
configuration cannot enable TX, and any future transmit support still requires
a future ADR plus explicit hardware action.

## 2026-07-10 — PB-100/LB-100 JPB1 connector candidate pair

Decision: JPB1 board-to-board planning now uses a Hirose FX18 candidate pair:
`FX18-100P-0.8SV10` plus `FX18-100S-0.8SV20`. The pair is treated as a
schematic-planning candidate only and does not authorize footprint placement or
PCB layout.

Reason: The FX18 family matches the existing 100-position 0.8 mm mezzanine
direction and gives a concrete pair for sourcing and footprint review. The
candidate still needs stack-height confirmation, vendor drawing review,
vibration retention assessment, PCBA assembly handling review, and LB-100 MCU
resource binding before the board-to-board freeze gate can close.

## 2026-07-10 — PB-100 Q1 input reverse MOSFET pin evidence

Decision: `PB100_INPUT_NMOS_TOLL_PRELIM` is now captured as a project-local
preliminary KiCad symbol for the Infineon `IAUTN06S5N008` TOLL input reverse
MOSFET. The symbol uses gate pin 1, source pins 2-8, and drain tab evidence
from the official Infineon data sheet.

Reason: Q1 was the remaining pending schematic-symbol gate in the PB-100 input
reverse-protection path. Capturing the pin evidence removes the symbol blocker
without freezing the TOLL footprint, PCB copper strategy, package assembly
handling, gate clamp, or 40 A thermal path.

## 2026-07-10 — PB-100 board-current budget trace

Decision: PB-100 schematic planning now includes
`PB-100-board-current-budget-trace.csv` as the cross-artifact current-budget
review anchor. It ties ADR-0008, the 50 A main fuse target, 40 A board and
configuration limit, 0-60 A total-current telemetry range, 0.5 mΩ shunt
operating point, and output-limit oversubscription together.

Reason: The 40 A budget is a safety boundary spanning hardware, configuration,
telemetry, firmware, and garage-installed fuse/connectors. A dedicated trace
file makes drift machine-checkable without changing the accepted PB-100 current
budget or starting PCB copper/layout work.

## 2026-07-10 — PB-100 TVS/load-dump downstream margin trace

Decision: PB-100 schematic planning now includes
`PB-100-tvs-load-dump-margin-trace.csv` as the downstream voltage-class margin
trace for the active Vishay `SM8S33AHM3/I` branch. The trace preserves the
53.3 V clamp point against 40 V, 60 V, 80 V, and 100 V downstream classes.

Reason: The active TVS candidate is acceptable for 100 V devices and useful for
60 V MOSFET planning only if overshoot is controlled. A dedicated margin trace
keeps the 40 V smart-switch path deferred by ADR-0011, keeps 60 V devices
conditional, and avoids silently treating the TVS clamp as a PCB-layout-ready
decision.

## 2026-07-10 — PB-100 low-current output baseline trace

Decision: PB-100 schematic planning now includes
`PB-100-low-current-output-baseline-trace.csv` for OUT5, OUT8, and OUT9. The
trace locks the schematic-planning baseline to TPS48110-class external
controller plus external 60 V N-MOSFET stages while preserving configuration
role assignment.

Reason: ADR-0011 rejected direct 40 V smart-switch rails behind the active
SM8S33AHM3-class TVS for Rev.1. A dedicated trace makes that decision
machine-checkable across output matrix, output contracts, hardware capability
manifest, and config defaults without finalizing resistor values or PCB layout.

## 2026-07-10 — PB-100 assembly ownership trace

Decision: PB-100 schematic planning now includes
`PB-100-assembly-readiness-trace.csv` as the factory-vs-garage ownership trace
for critical symbol keys. Factory rows remain tied to JLCPCB/PCBWay assembly
class recheck, while garage rows remain limited to connectors, fuse holders,
main fuse, wiring, enclosure, and service-access items.

Reason: Assembly readiness spans symbol readiness, BOM ownership, sourcing
evidence, and garage-install boundaries. A single trace makes owner drift
machine-checkable without locking MPNs, footprints, pick-place data, or PCB
layout.

## 2026-07-10 — PB-100 high/medium output baseline trace

Decision: PB-100 schematic planning now includes
`PB-100-high-medium-output-baseline-trace.csv` for OUT2 and the medium-current
output groups. The trace keeps the Rev.1 baseline on TPS48110-class controllers
plus external 60 V N-MOSFETs, with OUT2 retaining its escape path until SOA is
closed.

Reason: High/medium output validation spans fuse class, configured current
limit, telemetry net, gate-drive values, sense path, OUT2 SOA, and inductive
clamp decisions. A dedicated trace makes those dependencies machine-checkable
without assigning accessory roles or starting PCB layout.

## 2026-07-10 — PB-100 current telemetry trace

Decision: PB-100 schematic planning now includes
`PB-100-current-telemetry-trace.csv` for per-output IMON ranges and total input
current telemetry. The trace keeps `IIN_SENSE` tied to the dedicated 0.5 mΩ
input shunt monitor and to board-level 40 A budget enforcement.

Reason: Current telemetry is a firmware safety input, not only a measurement
feature. The trace makes range targets, ADC/I2C ownership, calibration, RC
filtering, stale-telemetry safe-off behavior, and shunt Kelvin review
machine-checkable before schematic freeze.

## 2026-07-10 — PB-100 thermal telemetry trace

Decision: PB-100 schematic planning now includes
`PB-100-thermal-telemetry-trace.csv` for `TEMP_PCB`, `TEMP_PWR_A`, and
`TEMP_PWR_B`. The trace keeps the TDK `NTCGS103JF103FT8`-class NTC candidate,
LB ADC path, 85 °C warn, 105 °C cutoff, and 75 °C recovery defaults tied to
configuration-owned calibration.

Reason: Thermal telemetry is a safety input that must remain separate from
accessory role mapping and firmware constants. A dedicated trace makes divider
values, ADC scaling, placement, self-heating, calibration, and stale/cutoff
firmware behavior machine-checkable before schematic freeze.

## 2026-07-10 — PB-100 logic power rail trace

Decision: PB-100 schematic planning now includes
`PB-100-logic-power-rail-trace.csv` for the protected 5 V logic rail. The trace
keeps LM5164-Q1-class 100 V 1 A as the preferred baseline, LM5013-Q1-class
100 V as the higher-current fallback, and `PB_PWR_GOOD` as the LB-100-visible
validity signal.

Reason: Logic power is a safety dependency for output default-off behavior and
LB-100 startup. A dedicated trace makes the protected input rail, 5 V budget,
power-good timing, rail-invalid output behavior, and lower-voltage fallback
risk machine-checkable before schematic freeze.

## 2026-07-10 — PB-100 KiCad sheet note trace synchronization

Decision: PB-100 KiCad placeholder sheets now reference the same dedicated trace
artifacts as their capture work queue rows. Validation fails if a sheet note
drops the required trace source for input protection, logic power, outputs,
telemetry, B2B, or CAN1.

Reason: The sheets are still placeholders, but their capture notes are the
entry point for schematic work. Keeping sheet notes aligned with trace evidence
reduces the risk of capturing from stale assumptions without starting PCB
layout.

## 2026-07-10 — PB-100 capture work queue trace evidence synchronization

Decision: PB-100 schematic capture work queue now lists the dedicated trace
artifacts as primary source inputs for input protection, logic power, output
template/instances, telemetry, B2B, and CAN1 sheets. Validation fails if those
sheet work items lose their trace source artifacts.

Reason: Schematic capture should consume the same trace evidence that gates
freeze review. This reduces the risk of capturing a sheet from stale source
documents while the machine-checked traces have moved ahead.

## 2026-07-10 — PB-100 symbol readiness created-status synchronization

Decision: PB-100 symbol readiness now marks preliminary symbols as created when
the symbol capture worklist already records created pin evidence. Validation
fails if a worklist-created symbol regresses to a vague required/pending status
in `PB-100-symbol-mpn-readiness.csv`.

Reason: Schematic capture needs a clear distinction between missing symbols and
created preliminary symbols that still need datasheet or package review. This
keeps symbol readiness accurate without locking footprints or starting layout.

## 2026-07-10 — PB-100 validation traceability trace synchronization

Decision: PB-100 validation traceability now uses each conditional freeze
gate's dedicated trace artifact as a primary validation artifact. Validation
fails if CAN1 safety, current budget, B2B, output stages, input reverse
protection, TVS/load-dump, logic power, telemetry, or assembly readiness lose
their trace link.

Reason: Freeze validation must point at the same trace evidence used by the
manifest, checklist, and dashboard. This keeps review tests aligned with the
machine-checked close evidence.

## 2026-07-10 — PB-100 readiness dashboard trace evidence synchronization

Decision: PB-100 schematic-readiness dashboard now references the dedicated
trace artifacts on the rows where they are the machine-checked evidence source.
Validation fails if the dashboard drops trace evidence for output baselines,
input reverse protection, TVS/load-dump, logic power, telemetry, CAN1 safety, or
assembly readiness.

Reason: The dashboard is the cross-artifact review view. Keeping it aligned with
the release manifest and freeze checklist prevents stale readiness summaries
from hiding a missing trace before schematic freeze.

## 2026-07-10 — PB-100 freeze checklist trace evidence synchronization

Decision: PB-100 schematic-freeze checklist evidence now includes the dedicated
trace artifacts for every remaining conditional freeze gate. Validation fails if
the checklist omits the trace files that back CAN1 safety, current budget, B2B,
outputs, input reverse protection, TVS/load-dump, logic power, telemetry, or
assembly readiness.

Reason: The checklist is the human freeze gate while the trace files are the
machine-checked evidence. Keeping both synchronized prevents review drift before
schematic freeze.

## 2026-07-10 — PB-100 CAN1 TX-disable trace

Decision: PB-100 schematic planning now includes
`PB-100-can1-tx-disable-trace.csv` for the vehicle-CAN read-only boundary. The
trace ties `JP_CAN1`, `U_CAN1`, `CAN1_TX_ROUTE`,
`CAN1_TX_DISABLED_STATUS`, firmware listen-only behavior, DNP BOM ownership, and
the future-ADR plus explicit-hardware-action process together.

Reason: CAN1 TX safety is a physical safety boundary, not a configuration
setting. A dedicated trace keeps the DNP/open missing-link, disabled-status
readback, firmware denial, and production ownership synchronized before
schematic freeze.

## 2026-07-10 — PB-100 Q1 input reverse package trace

Decision: PB-100 schematic planning now includes
`PB-100-input-reverse-package-trace.csv` for the Q1 input reverse-protection
MOSFET package path. The trace keeps `IAUTN06S5N008ATMA1` as the preferred
TOLL path, `BUK7S1R2-80M` as the 80 V LFPAK88 alternate, and dual
`SIDR626LDP` PowerPAK devices as the factory-assembly fallback.

Reason: The input reverse MOSFET is part of the 40 A board-current safety path.
Tracing package, copper, TVS overshoot, shunt measurement, and factory assembly
blockers together prevents a footprint or MPN from being locked before
schematic freeze and thermal review.

## 2026-07-10 — PB-100 JPB1 B2B interface trace

Decision: PB-100 schematic planning now includes
`PB-100-b2b-interface-trace.csv` for the 100-pin `JPB1` interface. The trace
ties the Hirose FX18 candidate pair, power/status pins,
output controls/faults/current telemetry, board telemetry, CAN1 safety
crossing, and expansion reserves to the LB-100 resource-binding review.

Reason: The B2B connector is a lifecycle boundary between PB-100 and LB-100. A
dedicated trace makes pin-map drift, CAN1 safety crossing, power-good behavior,
and LB-100 resource assumptions machine-checkable without starting connector
placement or PCB layout.

## 2026-07-10 — PB-100 capture plan trace input synchronization

Decision: PB-100 schematic capture plan now lists the same dedicated trace
inputs as the capture work queue for input protection, logic power, outputs,
telemetry, B2B, and CAN1 safety. The PB-100 validator now fails if the capture
plan drops any required trace artifact for these capture rows.

Reason: The capture plan is the human execution entry point while the capture
work queue and KiCad sheet notes are machine-checked. Keeping all three aligned
prevents schematic capture from using stale source documents after trace files
have become the freeze-gate evidence.

## 2026-07-10 — PB-100 KiCad sheet manifest trace input synchronization

Decision: PB-100 KiCad sheet manifest now lists the same dedicated trace inputs
as the capture plan and work queue for each child schematic sheet. The PB-100
validator now fails if a manifest row drops a required trace artifact for its
sheet.

Reason: The manifest is the KiCad-facing source index. If it lags the
trace-driven capture plan, schematic work can start from obsolete planning
inputs even while the release packet appears complete.

## 2026-07-10 — PB-100 readiness review release-packet synchronization

Decision: PB-100 schematic readiness review now lists every required release
manifest artifact, including the dedicated trace files and KiCad schematic
source files. The PB-100 validator now fails if the readiness review packet
drops a release-manifest artifact or required capture trace.

Reason: The readiness review is the top-level human handoff for schematic
freeze work. It must match the machine-checked release manifest so reviewers do
not miss trace evidence while approving schematic capture inputs.

## 2026-07-10 — PB-100 schematic package release-packet synchronization

Decision: PB-100 schematic package now lists the concrete KiCad top schematic
and local PB100 symbol library from the release manifest. The PB-100 validator
now fails if the schematic package drops any release-manifest artifact except
the package document itself.

Reason: The schematic package is the governing input bundle for capture work.
It must point reviewers to the actual KiCad source files, not only the planning
documents, while still explicitly excluding PCB layout scope.

## 2026-07-10 — PB-100 bench test traceability synchronization

Decision: PB-100 bench test plan now traces logic rail, output class, CAN1,
input reverse, TVS/load-dump, current telemetry, board-current, thermal, B2B,
and assembly/vibration tests to the dedicated PB-100 trace artifacts. The
PB-100 validator now fails if the test plan drops these trace links or bench
test IDs.

Reason: Bench validation is freeze evidence. The test plan must point to the
same trace artifacts used by the schematic freeze gates so bench execution does
not validate against stale source documents.

## 2026-07-10 — PB-100 internal symbol trace provenance

Decision: PB-100 internal class symbols for the buck inductor, board-ID
resistor, and CAN1 TX-disable element now use dedicated trace artifacts as
their readiness and worklist provenance. Datasheet-backed concrete symbols keep
their manufacturer datasheets as symbol sources. The PB-100 validator now fails
if these internal symbols drift away from their trace sources.

Reason: Internal class symbols are schematic-planning constructs rather than
manufacturer-defined parts. Their freeze evidence comes from the trace files,
so readiness/worklist provenance must follow the same trace-first contract
without weakening datasheet provenance for real components.

## 2026-07-10 — PB-100 top-level KiCad sheet linking

Decision: PB-100 top-level KiCad schematic now links every child sheet listed
in `PB-100-kicad-sheet-manifest.csv`, and the capture work queue marks CAP-TOP
as `Linked scaffold`. The PB-100 validator now fails if a child sheet exists in
the manifest but is not linked from `PB-100.kicad_sch` or if CAP-TOP loses its
child-link plus ERC/netlist evidence.

Reason: Schematic capture needs a connected sheet hierarchy before component
placement. Linking placeholder sheets is a schematic-scaffold step only: it
does not place components, lock footprints, create a PCB layout, or generate
manufacturing outputs.

## 2026-07-10 — PB-100 B2B LB-100 resource-class binding

Decision: PB-100 schematic planning now includes
`PB-100-b2b-lb100-resource-binding.csv` as the resource-class binding between
`JPB1` pins and LB-100 planning resources. The artifact covers power, ground,
GPIO/PWM, GPIO input/interrupt, ADC, I2C, SPI, FDCAN, UART, external expansion,
and spare-reserve classes while explicitly avoiding exact STM32H5 package pin
assignments before LB-100 schematic review.

Reason: The B2B freeze gap needed more than a pin map but should not invent
LB-100 MCU pins before LB-100 schematic capture. A resource-class binding
narrows the gap and is now checked by the PB-100 validator without authorizing
connector placement or PCB layout.

## 2026-07-10 — PB-100 garage connector/fuse scope validation

Decision: PB-100 release manifest now includes the garage connector/fuse plan
and interface matrix. The PB-100 validator checks DTP/DT/DTM connector class
use, MINI/ATO per-output fuse scope, conditional battery-input derating, garage
BOM coverage, and crimp/tooling/service-access boundaries.

Reason: Garage-installed items must stay limited to user-serviceable
connectors, fuses, enclosure, wiring, and harness hardware. Machine-checking
the existing plan prevents factory/garage ownership drift without changing
component requirements or starting PCB layout.

## 2026-07-10 — PB-100 CAN1 production DNP review

Decision: PB-100 schematic planning now includes
`PB-100-can1-production-dnp-review.csv`, tying `JP_CAN1` DNP/open production
state, `U_CAN1` default-disabled behavior, physical disabled-status readback,
listen-only RX independence, firmware CAN1 deny/CAN2 expansion separation, and
the future-ADR plus hardware-action boundary into one review artifact. The
PB-100 validator now fails if the release packet, freeze checklist, capture
queue, test plan, KiCad CAN1 sheet note, or BOM-facing CAN1 evidence drops this
production-DNP boundary.

Reason: CAN1 read-only behavior is a constitutional hardware safety rule. The
schematic freeze gate needs explicit production ownership of the DNP/open TX
path so configuration or firmware cannot silently create a vehicle-CAN TX path
without a future ADR and deliberate hardware action.

## 2026-07-10 — PB-100 40 A board-current freeze review

Decision: PB-100 schematic planning now includes
`PB-100-board-current-budget-freeze-review.csv`, tying the 50 A main fuse
target, 40 A board/configuration limit, input connector derating, Q1 reverse
path thermal review, 0.5 mΩ four-terminal shunt Kelvin path, protected copper
distribution, 0-60 A total-current telemetry, 82 A output-limit
oversubscription boundary, and no-layout authorization boundary into one
review artifact. The PB-100 validator now checks this artifact against the
hardware capability manifest, config example, input power values, current
budget trace, and KiCad no-layout constraints.

Reason: The 40 A board budget must be reviewable before PCB layout starts, but
it must not imply copper geometry, footprint placement, or manufacturing
authorization. A dedicated freeze-review artifact keeps schematic constraints,
firmware enforcement, and remaining layout-blocked work explicit.

## 2026-07-10 — PB-100 current telemetry freeze review

Decision: PB-100 schematic planning now includes
`PB-100-current-telemetry-freeze-review.csv`, tying the 0.5 mΩ total-current
shunt range, INA228-Q1-class ±40.96 mV monitor candidate, INA229/INA226
alternates, Kelvin sense nets, ADC/I2C ownership, per-output IMON class ranges,
configuration-owned calibration, stale-telemetry fail-safe behavior, and bench
validation IDs into one review artifact. The PB-100 validator now checks this
artifact against the current telemetry strategy, net-domain plan, B2B resource
binding, firmware tests, freeze checklist, validation traceability, and review
packet.

Reason: Current telemetry is both measurement hardware and firmware safety
input. Schematic freeze must preserve range, calibration, interface ownership,
and stale-data behavior without authorizing high-current copper layout or
hard-coded firmware calibration constants.

## 2026-07-10 — PB-100 thermal telemetry freeze review

Decision: PB-100 schematic planning now includes
`PB-100-thermal-telemetry-freeze-review.csv`, tying the three required thermal
zones, TDK NTCGS103JF103FT8-class 10 kΩ 150 °C AEC-Q200 NTC direction,
Vishay/Murata alternates, divider/ADC scaling, placement intent, 85/105/75 °C
configuration thresholds, stale-thermal-telemetry cutoff behavior, calibration
boundary, assembly recheck, and bench validation into one review artifact. The
PB-100 validator now checks this artifact against the thermal strategy, map,
configuration defaults, firmware thermal tests, freeze checklist, validation
traceability, and schematic review packet.

Reason: Thermal telemetry is a layout-sensitive safety input. Schematic freeze
must keep sensor count, threshold ownership, fail-safe behavior, and calibration
evidence explicit without allowing premature sensor placement or thermal-copper
layout.

## 2026-07-10 — PB-100 output-stage freeze reviews

Decision: PB-100 schematic planning now includes
`PB-100-high-medium-output-freeze-review.csv` and
`PB-100-low-current-output-freeze-review.csv`. The high/medium review ties the
TPS48110 external-MOSFET baseline, OUT2 SOA envelope, medium-current fuse
paths, gate-drive default-off behavior, sense/telemetry, fault thresholds,
inductive clamp strategy, thermal review, and no-layout boundary together. The
low-current review ties OUT5/OUT8/OUT9 5 A fuse and 4 A current-limit classes,
ADR-0011 external-controller architecture, no-direct-40 V-smart-switch
boundary, gate-drive defaults, telemetry, threshold/timer values, clamp
strategy, sourcing, and configuration separation together. The PB-100 validator
now checks both artifacts against output traces, design values, firmware tests,
freeze checklist, validation traceability, capture sheet notes, and review
packet membership.

Reason: Output stages are the remaining high-risk path between schematic
planning and board layout. The reviews preserve electrical and firmware safety
constraints without hard-coding roles, locking values prematurely, or
authorizing MOSFET/fuse/connector placement.

## 2026-07-10 — PB-100 input reverse freeze review

Decision: PB-100 schematic planning now includes
`PB-100-input-reverse-freeze-review.csv`, tying LM74700 gate/default-off
behavior, IAUTN06S5N008 TOLL, BUK7S1R2 LFPAK88, dual SIDR626LDP fallback,
protected input-current measurement sequence, HM3 TVS overshoot dependency,
factory sourcing gate, critical alternates, and no-layout boundary into one
review artifact. The PB-100 validator now checks this artifact against the
input reverse package trace, pin contract, TVS/load-dump margin trace, sourcing
recheck, freeze checklist, validation traceability, KiCad sheet notes, and
release manifest.

Reason: The Q1 reverse-protection path is part of the 40 A board-current safety
path. Schematic freeze needs explicit controller, MOSFET package, voltage
margin, telemetry ordering, and sourcing evidence before any TOLL/LFPAK/PowerPAK
footprint, copper, placement, or manufacturing output is authorized.

## 2026-07-10 — PB-100 TVS/load-dump freeze review

Decision: PB-100 schematic planning now includes
`PB-100-tvs-load-dump-freeze-review.csv`, tying the active Vishay
SM8S33AHM3/I HM3 DO-218AC branch, 53.3 V clamp at 124 A, 100 V controller and
buck pass-with-margin paths, 60 V MOSFET overshoot dependencies, BUK7S1R2-80M
80 V input alternate, TPS54360B-Q1 60 V buck alternate boundary, TPS2HB35
ADR-0011 40 V smart-switch boundary, OV/input-filter dependencies, sourcing
gate, and no-layout boundary into one review artifact. The PB-100 validator now
checks this artifact against TVS margin trace, protection validation, input
power values, output-stage values, logic-power values, sourcing recheck,
freeze checklist, validation traceability, KiCad sheet notes, and release
manifest.

Reason: The selected load-dump clamp determines whether 60 V MOSFET and buck
alternates are acceptable. Schematic freeze must preserve voltage-class
boundaries and obsolete/NFD source exclusions without authorizing D1 footprint,
pulse-current return copper, placement, or manufacturing output.

## 2026-07-10 — PB-100 logic power freeze review

Decision: PB-100 schematic planning now includes
`PB-100-logic-power-freeze-review.csv`, tying the LM5164-Q1-class 100 V 1 A
preferred regulator, LM5013-Q1-class 100 V fallback, TPS54360B-Q1-class 60 V
conditional path, protected `VBAT_PROT` sequencing, 1000 mA `PB_5V_OUT` budget,
UVLO safe-off behavior, `PB_PWR_GOOD`, switch-node EMI boundary, inductor and
capacitor class review, factory sourcing gate, and no-layout boundary into one
review artifact. The PB-100 validator now checks this artifact against the
logic rail trace, logic budget, design values, buck pin template, sourcing
recheck, freeze checklist, validation traceability, KiCad sheet notes, and
release manifest.

Reason: Logic power is a safety dependency for controller default-off behavior
and LB-100 status. Schematic freeze needs explicit regulator-family, load
budget, UVLO, PGOOD, magnetics, and sourcing boundaries before any U3/L1 value,
footprint, switch-node copper, placement, or manufacturing output is
authorized.

## 2026-07-16 — System sleep, wake, and parking-current limits

Decision: ADR-0012 defines off-ignition sleep and deep-sleep current budgets,
wake sources, transition timing, and long-parking drain limits. Sleep targets
≤1.0 mA with a 2.0 mA hard maximum. Deep sleep targets ≤250 µA with a 500 µA
hard maximum. The system must enter sleep within 60 seconds after
ignition/accessory-off and deep sleep within 24 hours of continuous parking.
Parking drain is limited to 0.35 Ah over the first parked week and 0.45 Ah over
one parked month after deep-sleep transition.

Reason: SVC is permanently connected to the motorcycle battery. LB-100 power
selection and firmware state-machine work need explicit parasitic-current and
wake-source limits before logic-power choices or vehicle installation can be
treated as safe.

## 2026-07-16 — Firmware safety loop closes delayed cutoff, shedding, and derate gaps

Decision: Firmware host logic now applies `battery.shutdown_delay_s` before
low-voltage cutoff, revalidates budget and telemetry before PWM increases,
sheds lower-priority loads during new load requests and runtime total-current
enforcement, and applies thermal derate through the Output Manager by reducing
PWM-capable outputs and disabling non-PWM low-priority loads.

Reason: These behaviors are safety requirements, not diagnostics only. The
working control loop must actively protect battery health, PB-100 current
budget, and thermal margin instead of only computing advisory states.

## 2026-07-16 — PB-100 KiCad CI is fail-closed

Decision: PB-100 validation now requires `kicad-cli` 10.0.4, rejects
`sheet-placeholder`/`Placeholder sheet` markers, requires ERC and KiCad
S-expression netlist export, and rejects exported netlists with fewer than 20
components or 20 electrical nets. GitHub Actions installs the fixed KiCad CLI
before running `make check`.

Reason: Empty or placeholder schematics must not pass CI. The repository should
fail loudly until PB-100 child sheets contain captured schematic content with
real components and electrical nets.

## 2026-07-16 — PB-100 preliminary KiCad child-sheet capture

Decision: PB-100 child sheets now contain preliminary schematic capture content
for input protection, logic power, generic output channels, telemetry, B2B
interface, and CAN1 safety. The capture uses role-agnostic `OUT1`..`OUT10`
nets, keeps CAN1 TX DNP/open with no default-populated TX path, exports a KiCad
S-expression netlist above the component/net thresholds, and passes ERC with
passive preliminary class-symbol pins.

Reason: The repository needed to move past placeholder sheets into a real
machine-checked schematic baseline without pretending the schematic is frozen.
Passive abstract pins keep ERC useful for hierarchy and net continuity while
final pin electrical types, values, footprints, SOA, sourcing evidence, and
independent power-electronics review remain schematic-freeze blockers.

## 2026-07-16 — PB-100 board-release blockers are explicit

Decision: PB-100 now has
`hardware/power-board/PB-100/PB-100-board-release-blocker-register.csv`, with
one active release blocker for every conditional schematic-freeze gate. The
validator checks that those rows stay synchronized with the freeze checklist and
that each row explicitly blocks PCB layout.

Reason: After preliminary schematic capture, the next risk is treating
documentation volume as board readiness. PCB layout must remain blocked until
values, footprints, sourcing, SOA, thermal, connector, and production evidence
are actually closed for every conditional gate.

## 2026-07-16 — PB-100 logic-power candidate values

Decision: PB-100 logic-power planning now has a value-bearing but not-final
LM5164-Q1 candidate network in
`hardware/power-board/PB-100/PB-100-logic-power-design-calculation.md` and
`hardware/power-board/PB-100/PB-100-logic-power-design-values.csv`. The current
candidate uses a 5 V / 1 A `PB_5V_OUT` target, about 300 kHz switching, 41.2 kΩ
RON programming, 158 kΩ / 49.9 kΩ feedback, 332 kΩ / 100 kΩ UVLO, 2.2 nF
bootstrap, 47 µH inductor class, 2 × 22 µF output capacitance class, and 47 kΩ
PGOOD pull-up.

Reason: The board-release path needs concrete schematic-review values instead
of open TBD fields. These values are still not final: LM5164 orderability,
actual LB-100 load budget, inductor saturation/DCR, capacitor derating, EMI,
PGOOD timing, and switch-node ringing remain schematic-freeze blockers.

## 2026-07-16 — PB-100 thermal telemetry candidate divider

Decision: PB-100 thermal telemetry planning now has a value-bearing but
not-final NTC divider candidate in
`hardware/power-board/PB-100/PB-100-thermal-telemetry-design-calculation.md`.
The current candidate uses the TDK 10 kΩ 3435 K NTC class with a 4.7 kΩ pull-up
to `LB_3V3_IO`, 1 kΩ ADC series resistor, and 10 nF ADC filter for all three
thermal signals.

Reason: The default 85 °C warn, 105 °C cutoff, and 75 °C recovery thresholds
need concrete ADC voltage coverage before schematic review. The values remain
not final until LB-100 ADC settling, NTC self-heating, sensor placement,
calibration, and assembly sourcing are reviewed.

## 2026-07-16 — PB-100 current telemetry candidate values

Decision: PB-100 total-current telemetry planning now has a value-bearing but
not-final monitor and shunt candidate in
`hardware/power-board/PB-100/PB-100-current-telemetry-design-calculation.md`.
The current candidate keeps the 0.5 mΩ four-terminal shunt, uses the
INA228-Q1-class ±40.96 mV range, records 20 mV at 40 A and 30 mV at 60 A,
uses `A1 = GND` and `A0 = GND` as a candidate `0x40` I2C address, keeps
`PB_I2C` pull-ups LB-owned by default, and adds candidate shunt-input and
VBUS filter values for schematic review.

Reason: The current telemetry blocker needed concrete schematic-review values
instead of open address, pull-up, filter, and calibration placeholders. These
values remain not final until the LB-100 I2C plan, shunt footprint, Kelvin
routing, copper heating, VBUS surge stress, exact monitor suffix, and bench
calibration process are reviewed.

## 2026-07-16 — PB-100 CAN1 TX-disable candidate values

Decision: PB-100 CAN1 safety planning now has a value-bearing but not-final
default-disabled hardware candidate in
`hardware/power-board/PB-100/PB-100-can1-tx-disable-design-calculation.md`.
The current candidate keeps `JP_CAN1` DNP/open as a 0 Ω 0603 link or
normally-open solder bridge, uses an `SN74LVC1G125-Q1`-class 3-state gate for
`U_CAN1`, pulls the physical `OE` disable node high with 47 kΩ, biases
downstream TXD recessive with 47 kΩ, and reads the physical disable node back
to `CAN1_TX_DISABLED_STATUS` through a 1 kΩ series path plus 100 kΩ pull-up.

Reason: CAN1 read-only behavior is a constitutional hardware safety rule. The
release blocker needed concrete schematic-review values for the default-open
link, default-disabled gate, and physical status readback without creating any
default-populated vehicle-CAN TX path. These values remain not final until
factory DNP handling, exact gate package, reset/unpowered bench behavior,
direct DNP-link detection need, and independent CAN safety review close.

## 2026-07-16 — PB-100/LB-100 pin-binding precheck

Decision: PB-100 board-to-board planning now has an LB-100 resource-budget
precheck in
`hardware/power-board/PB-100/PB-100-b2b-lb100-pin-binding-precheck.md`. The
precheck requires the STM32H563 LQFP-100 schematic review to account for 10
PWM-capable output controls, 10 output fault inputs, 10 per-output ADC current
inputs, 6 board analog/ID measurements plus reference strategy, `PB_I2C`, CAN1
read-only safety pins, and future expansion reserves before exact pin binding
can close.

Reason: The B2B blocker cannot be closed by the PB-100 pin map alone. Exact
STM32H5 package pins must be assigned in the LB-100 schematic with USB, SWD,
clock, storage, BLE, sensors, sleep/wake, ADC, timer, FDCAN, UART, and SPI
conflicts visible. This precheck is deliberately not an exact pinout and keeps
connector placement and layout blocked until the real LB-100 pinout audit
passes.

## 2026-07-17 — PB-100 board-print release gate

Decision: PB-100 now has `tools/pb100_release_status.py` plus
`make pb100-release-status` and `make pb100-release-gate`.

Reason: The project needs a direct machine-readable answer for whether PB-100
can be sent for board printing. The gate reports the schematic-freeze status,
active board-release blockers, KiCad PCB presence, and manufacturing output
presence instead of relying on a manual reading of the release packet.

## 2026-07-17 — PB-100 garage connector class narrowing

Decision: PB-100 garage assembly planning now narrows output connectors to DTP
for OUT1 and OUT2, DT for OUT3 through OUT10, DTM for CAN/service/signal wiring,
and a MAXI near-battery main fuse holder class. The battery input path remains
conditional and explicitly excludes DT or DTP as the 50 A input connector class.

Reason: Board release needs the user-installed connector and fuse scope to be
concrete enough for harness planning while still blocking PCB layout until exact
housings, contacts, seals, crimp tooling, fuse holder, enclosure service access,
and derating evidence close.

## 2026-07-17 — PB-100 MOSFET voltage-margin review path

Decision: PB-100 schematic review now treats 60 V MOSFET paths behind the active
`SM8S33AHM3/I` TVS branch as conditional until overshoot evidence closes, and
makes an 80 V MOSFET review escape path explicit for output and input-reverse
MOSFET selections.

Reason: The active TVS clamp point leaves limited headroom below 60 V absolute
maximum MOSFET ratings. The release path must either prove the 60 V overshoot
margin or move affected MOSFET paths to an 80 V or higher class before
schematic freeze and PCB layout.

## 2026-07-17 — LB-100 power-budget precheck for PB-100 logic rail

Decision: LB-100 schematic review now has
`hardware/logic-board/LB-100/LB-100-power-budget-precheck.md`, tying the initial
500 mA sustained LB-100 allocation to the PB-100 `PB_5V_OUT` 1 A budget.

Reason: PB-100 cannot freeze the LM5164-Q1-class logic buck until LB-100 proves
its load budget. If LB-100 exceeds the 500 mA allocation, PB-100 must retain the
LM5013-Q1-class higher-current fallback before schematic freeze.

## 2026-07-17 — PB-100 total-current calibration config contract

Decision: PB-100 total-current telemetry planning now has a firmware
configuration contract for the schematic-review candidate. `telemetry.total_current`
in `firmware/configs/config-example.json` and `svc_telemetry_config_t` in
`firmware/core/svc_config.h` carry the 500 µΩ shunt value, 40960 µV monitor
range, zero offset, 1000000 ppm gain, 1000 ms stale timeout, and 60000 mA
plausible maximum. The C validator, JSON validator, and config-store checksum
now cover those fields.

Reason: PBREL-009 required evidence that current telemetry calibration is not
buried in firmware constants. This closes the total-current configuration
contract while keeping bench calibration, per-output IMON calibration, shunt
Kelvin footprint, copper heating, and ADC/I2C ownership open before schematic
freeze.

## 2026-07-17 — PB-100 per-output IMON calibration config contract

Decision: PB-100 current telemetry configuration now includes role-free
`telemetry.output_current` records for `OUT1` through `OUT10`. Each record
carries the IMON range, zero offset, gain, stale timeout, and plausible-current
limit. The defaults match the PB-100 telemetry map: OUT1 20 A, OUT2 30 A,
OUT3/OUT4/OUT6/OUT7/OUT10 15 A, and OUT5/OUT8/OUT9 8 A.

Reason: PBREL-009 covers both total input current and per-output telemetry.
Adding per-output calibration records keeps IMON scaling out of driver constants
and lets schema/C validation prove each configured output limit is covered
without closing ADC scaling, bench calibration, Kelvin routing, copper heating,
or LB-100 bus ownership before schematic freeze.

## 2026-07-17 — PB-100 thermal telemetry calibration config contract

Decision: PB-100 thermal telemetry configuration now includes
`telemetry.thermal` records for `TEMP_PCB`, `TEMP_PWR_A`, and `TEMP_PWR_B`.
Each record carries the NTC nominal value, beta value, pull-up value, ADC series
resistor, filter capacitor, stale timeout, and plausible-temperature range. The
defaults mirror the schematic-review candidate: 10 kΩ NTC, 3435 K beta,
4.7 kΩ pull-up, 1 kΩ ADC series resistor, 10 nF filter, 1000 ms stale timeout,
and -40 °C to 150 °C plausible range.

Reason: PBREL-010 needed calibration ownership to be explicit before schematic
freeze. The config contract keeps thermal divider constants out of driver code
and lets validation prove each plausible range covers the configured recovery
and cutoff thresholds. ADC settling, sensor placement, self-heating, sourcing,
and bench calibration remain open before PCB layout.

## 2026-07-17 — PB-100 CAN1 reset and DNP bench checklist

Decision: PB-100 CAN1 safety review now has
`hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv`. The
checklist covers LB-100 reset, LB-100 unpowered, production DNP/open inspection,
physical disabled-status readback, RX listen-only independence, and the future
ADR plus explicit hardware-action boundary.

Reason: PBREL-001 cannot close from schematic notes alone. The release packet
needs a concrete bench and production-inspection checklist proving that
`CAN1_TX_ROUTE` remains DNP/open, `CAN1_TX_DISABLED_STATUS` is physical
readback rather than firmware-only state, and no vehicle-CAN transmit frame is
observed in Rev.1 default assembly.

## 2026-07-17 — PB-100 board-current path design calculation

Decision: PB-100 board-current review now has
`hardware/power-board/PB-100/PB-100-board-current-budget-design-calculation.md`.
The calculation records the 50 A main-fuse review point, 40 A continuous board
budget, 0-60 A total-current telemetry range, 0.5 mΩ four-terminal shunt
dissipation, Q1 reverse-protection candidate dissipation, and pre-layout copper
loss boundary.

Reason: PBREL-002 needs numeric evidence before layout, but it must not create
layout geometry. The calculation keeps the accepted current-budget architecture
explicit while preserving the no-`PB-100.kicad_pcb` boundary until connector
derating, shunt package heating, Q1 thermal path, protected distribution, and
bench telemetry calibration close.

## 2026-07-17 — PB-100 B2B LB-100 pin audit checklist

Decision: PB-100 board-to-board review now has
`hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`. The
checklist covers the exact STM32H563 LQFP-100 pinout audit, ADC capacity,
output PWM default-low behavior, fault/wake routing, CAN1 read-only crossing,
PB-side bus and expansion conflicts, FX18 footprint drawing, stack height,
vibration retention, assembly handling, and no-layout boundary.

Reason: PBREL-003 cannot close from a resource-class precheck alone. The release
packet needs a machine-checked audit list that preserves the current JPB1 map
while making the remaining LB-100 pinout and FX18 mechanical evidence explicit
before any connector placement or `PB-100.kicad_pcb` work.

## 2026-07-17 — PB-100 B2B interface freeze checklist

Decision: PB-100 board-to-board release review now has
`hardware/power-board/PB-100/PB-100-b2b-interface-freeze-checklist.csv`. The
checklist ties the FX18 connector pair, power/status pins, role-free output
signals, board telemetry, `PB_I2C`, CAN1 read-only crossing, STM32H563
LQFP-100 audit, cross-artifact synchronization, and no-layout boundary to
PBREL-003.

Reason: The pin audit checklist defines execution evidence, but the schematic
freeze packet also needs a reviewer-facing gate that links B2B electrical,
mechanical, LB-100 resource, CAN1 safety, and no-layout conditions before any
mezzanine placement or manufacturing-output work.

## 2026-07-17 — PB-100 B2B interface closeout precheck

Decision: PB-100 board-to-board release review now has
`hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv`. The
precheck bridges the JPB1 100-position pin map, FX18 footprint drawing,
20 mm stack-height evidence, vibration and assembly handling, exact STM32H563
LQFP-100 pinout audit, ADC/PWM/resource limits, CAN1 DNP/open crossing, and
no-layout manufacturing boundary to PBREL-003.

Reason: The B2B freeze checklist names the gate, but print-readiness review
also needs a machine-checked closeout bridge that prevents connector placement,
stack-height lock, `PB-100.kicad_pcb`, Gerbers, drills, pick-place, or
manufacturing ZIP work until LB-100 pinout and FX18 mechanical evidence close.

## 2026-07-17 — PB-100 output-stage value freeze checklist

Decision: PB-100 output-stage review now has
`hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`.
The checklist covers TPS48110 baseline, OUT2 SOA and fuse energy, medium output
fuse paths, low-current ADR-0011 boundary, threshold and timer networks, gate
default-off behavior, sense telemetry and ADC scaling, inductive clamp and
MOSFET voltage margin, and no-layout boundary.

Reason: PBREL-004 and PBREL-005 need a shared close-work list before final
component values can be locked. The checklist keeps output channels generic,
keeps role mapping in configuration, and blocks MOSFET/fuse/connector placement
or `PB-100.kicad_pcb` work until schematic freeze evidence closes.

## 2026-07-17 — PB-100 output-stage value derivation precheck

Decision: PB-100 output-stage review now has
`hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`.
The precheck ties TI TPS4811-Q1 datasheet equations and TPS48110Q1EVM reference
positions to `OUTn_IWRN_SET`, `OUTn_ISCP_SET`, `OUTn_TMR`, `OUTn_BST`,
gate-drive, current-sense, and `OUTn_IMON` derivation for high, medium, and
low-current output classes.

Reason: PBREL-004/PBREL-005 cannot close from placeholder rows alone. The
schematic freeze packet needs a formula-backed bridge between controller
datasheet equations, OUT2 SOA/current limits, the low-current ADR-0011
boundary, telemetry ranges, and still-open final value-bearing schematic
instances.

## 2026-07-17 — PB-100 output-stage closeout precheck

Decision: PB-100 output-stage review now has
`hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`. The
precheck bridges TI TPS4811-Q1/TPS48110Q1EVM formulas, high/medium/low output
class maps, design-item completeness, threshold and timer derivations,
bootstrap/default-off behavior, current telemetry scaling, SOA/fuse/clamp
evidence, low-current ADR-0011 boundary, template/instance synchronization, and
no-layout manufacturing boundary to PBREL-004/PBREL-005.

Reason: The value checklist and derivation precheck define what must close, but
the print-readiness packet also needs a machine-checked bridge that prevents
MOSFET placement, fuse placement, connector placement, high-current copper,
`PB-100.kicad_pcb`, Gerbers, drills, pick-place, or manufacturing ZIP work
until final output values and low-current ADR boundaries close.

## 2026-07-17 — PB-100 input reverse Q1 freeze checklist

Decision: PB-100 input reverse-protection review now has
`hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`.
The checklist covers LM74700/LM74502 gate-default behavior, `INPUT_FET_GATE`
clamp/discharge timing, `IAUTN06S5N008ATMA1` TOLL preferred path,
`BUK7S1R2-80M` 80 V LFPAK88 alternate, dual `SIDR626LDP` fallback, protected
measurement sequence, 40 A thermal/copper/SOA audit, assembly sourcing, and
the no-layout boundary.

Reason: PBREL-006 needs an explicit close-work list before Q1 package and gate
network values can be locked. The checklist keeps the 60 V preferred path
conditional on overshoot and sourcing evidence, retains 80 V and dual-device
alternates, and blocks Q1 placement, copper geometry, and `PB-100.kicad_pcb`
until schematic freeze closes.

## 2026-07-17 — PB-100 input reverse Q1 derivation precheck

Decision: PB-100 input reverse-protection review now has
`hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv`.
The precheck ties TI LM74700-Q1 VCAP/gate-driver behavior, ideal-diode
thresholds, MOSFET RDS(on) operating window, TVS stress, protected measurement
sequence, assembly alternates, and the no-layout boundary to PBREL-006.

Reason: PBREL-006 cannot close from Q1 package rows alone. The release packet
needs a formula-backed bridge between the LM74700 controller datasheet,
`INPUT_FET_GATE` behavior, 40 A Q1 MOSFET candidates, TVS/load-dump dependency,
and the still-open final gate network, footprint, and copper decisions.

## 2026-07-17 — PB-100 input reverse Q1 closeout precheck

Decision: PB-100 input reverse-protection review now has
`hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv`.
The precheck bridges the LM74700-Q1 source boundary, VCAP/gate default-off
behavior, ideal-diode reverse-current behavior, RDS(on) thermal window,
TOLL/LFPAK88/PowerPAK package alternatives, TVS overshoot dependency, protected
measurement sequence, assembly sourcing, input capture synchronization, and
no-layout manufacturing boundary to PBREL-006.

Reason: The Q1 freeze checklist and derivation precheck define the evidence,
but print-readiness review also needs a machine-checked closeout bridge that
prevents Q1 placement, high-current copper, thermal relief, `PB-100.kicad_pcb`,
Gerbers, drills, pick-place, or manufacturing ZIP work until input reverse
package, gate, thermal, TVS, and assembly evidence close.

## 2026-07-17 — PB-100 TVS overshoot escape checklist

Decision: PB-100 TVS/load-dump review now has
`hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv`.
The checklist ties the active `SM8S33AHM3/I` HM3 source snapshot, 53.3 V clamp
at 124 A, 60 V MOSFET overshoot acceptance, `BUK7S1R2-80M` 80 V LFPAK88
escape path, 100 V downstream default, ADR-0011 40 V boundary, schematic-value
dependencies, sourcing review, and no-layout boundary into one machine-checked
artifact.

Reason: PBREL-007 cannot close from clamp math alone. The 60 V MOSFET paths
need measured or simulated overshoot evidence, otherwise affected paths must
migrate to an 80 V or higher class before schematic values, footprints, copper,
or `PB-100.kicad_pcb` work can be locked.

## 2026-07-17 — PB-100 TVS overshoot validation precheck

Decision: PB-100 TVS/load-dump review now has
`hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv`.
The precheck ties the active `SM8S33AHM3/I` HM3 clamp source,
`Vstress = Vclamp + Lloop * di/dt`, bench measurement and simulation setup,
60 V acceptance versus 80 V escape, 100 V downstream check, assembly
alternatives, and no-layout boundary to PBREL-007.

Reason: PBREL-007 needs a measurable or simulatable acceptance method before
60 V paths or 80 V migration can close. This prevents relying on datasheet
clamp math alone.

## 2026-07-17 — PB-100 TVS overshoot closeout precheck

Decision: PB-100 TVS/load-dump review now has
`hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv`. The
precheck bridges the active HM3 TVS source, overshoot method, 60 V MOSFET
acceptance, 80 V escape path, 100 V downstream defaults, 40 V ADR boundary,
schematic-value dependencies, D1 sourcing, validation synchronization, and
no-layout manufacturing boundary to PBREL-007.

Reason: The overshoot checklist and validation precheck define the review, but
print-readiness also needs a machine-checked closeout bridge that prevents D1
placement, pulse-current return copper, via strategy, thermal relief,
`PB-100.kicad_pcb`, Gerbers, drills, pick-place, or manufacturing ZIP work
until measured or simulated 60 V overshoot evidence or the 80 V escape decision
closes.

## 2026-07-17 — PB-100 logic-power value freeze checklist

Decision: PB-100 logic-power review now has
`hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`.
The checklist ties LM5164-Q1/LM5013-Q1/TPS54360B-Q1 family selection,
`PB_5V_OUT` 1000 mA budget and LB-100 500 mA allocation, `VBAT_PROT` input
filtering, UVLO, RON, feedback, bootstrap, L1/COUT, `PB_PWR_GOOD`, switch-node
EMI, factory sourcing, and the no-layout boundary into one machine-checked
artifact.

Reason: PBREL-008 cannot close from candidate equations alone. The buck family,
load budget, external values, magnetics, capacitors, PGOOD behavior, EMI
evidence, and sourcing must close before U3/L1/CIN/COUT values, footprints,
switch-node geometry, or `PB-100.kicad_pcb` work can be locked.

## 2026-07-17 — PB-100 logic-power value derivation precheck

Decision: PB-100 logic-power review now has
`hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`.
The precheck ties official TI LM5164-Q1/LM5013-Q1/TPS54360B-Q1 source
boundaries, `PB_5V_OUT` budget, UVLO/RON/feedback formulas, bootstrap and
PGOOD interface, L1/COUT review, switch-node EMI, factory sourcing, and
no-layout boundary to PBREL-008.

Reason: PBREL-008 needs a formula-backed bridge between the value checklist,
LM5164 candidate calculation, LB-100 load-budget contract, TVS/load-dump stress,
and factory sourcing before logic-power values or footprints can close.

## 2026-07-17 — PB-100 logic-power closeout precheck

Decision: PB-100 logic-power review now has
`hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv`. The
precheck bridges the regulator family source boundary, `PB_5V_OUT` budget,
protected input/transient stress, UVLO/default-off behavior, RON/feedback/
bootstrap values, inductor/COUT stability, PGOOD interface, switch-node EMI,
factory sourcing, and no-layout manufacturing boundary to PBREL-008.

Reason: The logic-power value checklist and derivation precheck define the
candidate calculations, but print-readiness also needs a machine-checked
closeout bridge that prevents U3/L1/CIN/COUT placement, switch-node copper,
thermal-pad vias, `PB-100.kicad_pcb`, Gerbers, drills, pick-place, or
manufacturing ZIP work until load-budget, TVS stress, EMI/stability, PGOOD, and
sourcing evidence close.

## 2026-07-17 — PB-100 current telemetry value freeze checklist

Decision: PB-100 current-telemetry review now has
`hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv`.
The checklist ties the 0.5 mΩ total-current shunt, INA228/INA229/INA226 monitor
family, Kelvin sense and input filter, I2C address and pull-up ownership,
diagnostic alert behavior, protected `VBAT_PROT` VBUS sense, per-output IMON
scaling, configuration-owned calibration, stale-telemetry bench tests, sourcing,
and no-layout boundary into one machine-checked artifact.

Reason: PBREL-009 cannot close from the candidate calculation alone. Shunt
package heating, Kelvin footprint, monitor orderability, address and pull-up
ownership, alert behavior, ADC/I2C mapping, bench calibration, and stale-data
safety must close before telemetry routing, shunt copper, footprints, or
`PB-100.kicad_pcb` work can be locked.

## 2026-07-17 — PB-100 current telemetry value derivation precheck

Decision: PB-100 current-telemetry review now has
`hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv`.
The precheck ties `Vshunt = I * Rshunt`, `Pshunt = I^2 * Rshunt`,
INA228/INA229 monitor range, Kelvin/filter network, I2C ownership, alert
boundary, VBUS protected-rail stress, per-output IMON scaling,
configuration-owned calibration, bench safe-fault path, sourcing, and
no-layout boundary to PBREL-009.

Reason: PBREL-009 needs a formula-backed bridge between the value checklist,
current telemetry calculation, board-current budget, firmware configuration
contract, and factory sourcing before shunt, monitor, routing, or calibration
values can close.

## 2026-07-17 — PB-100 current telemetry closeout precheck

Decision: PB-100 current-telemetry review now has
`hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv`.
The precheck bridges the shunt formulas, INA228/INA229/INA226 monitor family,
Kelvin and input-filter network, I2C address/pull-up/interrupt ownership,
protected VBUS stress, per-output IMON ADC scaling, configuration-owned
calibration, bench safe-fault evidence, sourcing/symbol synchronization, and
no-layout manufacturing boundary to PBREL-009.

Reason: The current telemetry value checklist and derivation precheck define the
candidate values, but print-readiness also needs a machine-checked closeout
bridge that prevents shunt placement, Kelvin routing, monitor footprints,
`PB-100.kicad_pcb`, Gerbers, drills, pick-place, or manufacturing ZIP work until
shunt package heating, monitor sourcing, LB-100 ADC/I2C ownership, calibration,
and bench evidence close.

## 2026-07-17 — PB-100 thermal telemetry value freeze checklist

Decision: PB-100 thermal-telemetry review now has
`hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`.
The checklist ties the TDK `NTCGS103JF103FT8` 10 kΩ NTC class, `TEMP_PCB`,
`TEMP_PWR_A`, and `TEMP_PWR_B` placement zones, 4.7 kΩ/1 kΩ/10 nF divider
candidate, self-heating estimate, LB ADC settling, 85/105/75 °C configuration
thresholds, stale thermal fail-safe behavior, bench validation, sourcing
alternates, and no-layout boundary into one machine-checked artifact.

Reason: PBREL-010 cannot close from the candidate divider calculation alone.
ADC settling, physical placement, self-heating, bench calibration, firmware
threshold ownership, NTC sourcing, and stale-telemetry fail-safe evidence must
close before sensor placement, thermal copper, footprints, or
`PB-100.kicad_pcb` work can be locked.

## 2026-07-17 — PB-100 thermal telemetry value derivation precheck

Decision: PB-100 thermal-telemetry review now has
`hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`.
The precheck ties NTC source boundaries, the beta equation, divider ADC
equation, self-heating estimate, ADC settling, placement zones,
configuration-owned calibration, firmware fail-safe behavior, sourcing, and
no-layout boundary to PBREL-010.

Reason: PBREL-010 needs a formula-backed bridge between the value checklist,
thermal telemetry calculation, configuration contract, bench validation, and
factory sourcing before thermal values, sensor placement, or footprints can
close.

## 2026-07-17 — PB-100 thermal telemetry closeout precheck

Decision: PB-100 thermal-telemetry review now has
`hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`.
The precheck bridges the NTC source class, divider equations and values,
placement zones, self-heating, ADC settling, configuration-owned calibration,
firmware fail-safe behavior, bench validation, sourcing/symbol synchronization,
and no-layout manufacturing boundary to PBREL-010.

Reason: The thermal telemetry value checklist and derivation precheck define the
candidate values, but print-readiness also needs a machine-checked closeout
bridge that prevents sensor placement, thermal copper, board-zone keepouts,
`PB-100.kicad_pcb`, Gerbers, drills, pick-place, or manufacturing ZIP work until
sensor package, ADC settling, placement, self-heating, calibration, sourcing,
and bench evidence close.

## 2026-07-17 — PB-100 factory assembly freeze checklist

Decision: PB-100 factory assembly review now has
`hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`.
The checklist ties factory-owned critical symbol keys, critical alternates,
JLCPCB/PCBWay assembly class, reel/tray/cut-tape handling, date-stamped sourcing
evidence, power-package handling, TVS source hygiene, logic/current/thermal
sourcing, B2B connector production handling, CAN1 DNP/open handling, BOM
evidence synchronization, and the no-layout boundary into one machine-checked
artifact.

Reason: PBREL-011 cannot close from preliminary MPN candidates alone. Current
factory assembly class, exact orderable suffixes, authorized distributor
continuity, alternates, DNP/open production notes, and BOM evidence must close
before MPN lock, footprint lock, pick-place output, PCBA order package, or
`PB-100.kicad_pcb` work can be released.

## 2026-07-17 — PB-100 factory assembly sourcing precheck

Decision: PB-100 factory-assembly review now has
`hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`.
The precheck ties factory-owned critical keys, BOM/evidence register alignment,
JLCPCB/PCBWay assembly-platform recheck, critical alternates, package handling,
TVS source hygiene, logic/current/thermal sourcing, B2B/CAN1 production
handling, date-stamped sourcing evidence, and no-layout boundary to PBREL-011.

Reason: PBREL-011 needs a closeable sourcing bridge between the factory freeze
checklist, symbol readiness, BOM map, sourcing recheck register, evidence
snapshot, and board-print no-go boundary. It prevents stale assembly-platform
or distributor evidence from being treated as sufficient for MPN, footprint,
pick-place, PCBA order, or layout release.

## 2026-07-17 — PB-100 factory assembly closeout precheck

Decision: PB-100 factory-assembly review now has
`hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`.
The closeout precheck ties factory-owned critical key ownership, critical
alternates, JLCPCB/PCBWay assembly-platform handling, power-path package
handling, TVS source hygiene, logic/current/thermal sourcing, B2B/CAN1
production handling, BOM evidence synchronization, inspection/rework evidence,
and no-layout manufacturing boundary to PBREL-011.

Reason: PBREL-011 cannot close from the factory freeze checklist and sourcing
precheck alone. Board-print readiness needs a final evidence bridge that keeps
current assembly-platform support, authorized distributor continuity, exact
orderable suffixes, DNP/open inspection, rework risk, and BOM synchronization
explicit before any MPN lock, footprint lock, pick-place, PCBA order package,
fabrication package, or `PB-100.kicad_pcb` work is released.

## 2026-07-17 — PB-100 garage install freeze checklist

Decision: PB-100 garage assembly review now has
`hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv`.
The checklist ties user-installed connector/fuse ownership, the 50 A
battery/MAXI path, DTP/DT/DTM connector classes, MINI/ATO per-channel fuse
access, purchase-ready connector kit evidence, wire gauges, enclosure service
access, BOM evidence synchronization, and the no-layout boundary into one
machine-checked artifact.

Reason: PBREL-012 cannot close from connector family classes alone. Exact
housings, contacts, seals, wedgelocks, boots, backshells, crimp tooling,
wire-gauge derating, enclosure entry, service access, and spare handling must
close before garage purchase lock, installation signoff, connector footprints,
fuse-holder footprints, enclosure release, manufacturing output, or
`PB-100.kicad_pcb` work can be released.

## 2026-07-17 — PB-100 garage install sourcing precheck

Decision: PB-100 garage assembly review now has
`hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv`.
The precheck ties garage-owned symbol keys, the 50 A battery/MAXI path,
DTP/DT/DTM connector boundaries, user-serviceable fuses, purchase-ready kit
evidence, wire/harness derating, enclosure service review, BOM/source
synchronization, and no-layout boundary to PBREL-012.

Reason: PBREL-012 needs a closeable sourcing and install bridge between the
garage freeze checklist, connector/fuse plan, garage BOM, sourcing recheck,
evidence snapshot, and board-print no-go boundary. It prevents connector/fuse
family classes from being treated as purchase-ready kits or PCB-footprint
authorization.

## 2026-07-17 — PB-100 garage install closeout precheck

Decision: PB-100 garage assembly review now has
`hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`.
The closeout precheck ties user-installed critical key ownership, the 50 A
battery/MAXI path, DTP/DT/DTM connector classes, user-serviceable fuses,
purchase-ready kits, wire/harness derating, enclosure service and vibration
evidence, BOM/source synchronization, and no-layout manufacturing boundary to
PBREL-012.

Reason: PBREL-012 cannot close from garage connector family choices alone.
Board-print readiness needs a final evidence bridge that keeps exact housings,
contacts, seals, wedgelocks, boots, backshells, crimp tooling, spare contacts,
wire gauge, enclosure service access, vibration inspection, and garage/PB-100
scope separation explicit before purchase lock, installation signoff,
connector footprints, fuse-holder footprints, enclosure CAD release,
fabrication package, manufacturing output, or `PB-100.kicad_pcb` work is
released.

## 2026-07-17 — PB-100 CAN1 default-disable freeze checklist

Decision: PB-100 CAN1 safety review now has
`hardware/power-board/PB-100/PB-100-can1-default-disable-freeze-checklist.csv`.
The checklist ties ADR-0002 policy, `JP_CAN1` DNP/open missing link,
`U_CAN1` default-disabled gate behavior, 47 kΩ pulls, TXD recessive bias,
1 kΩ/100 kΩ physical disabled-status readback, optional DNP filtering,
DNP-link detect boundary, RX listen-only independence, firmware/capability
boundary, PB-BENCH-012, and the no-layout boundary into one machine-checked
artifact.

Reason: PBREL-001 cannot close from policy text or candidate values alone. The
physical missing link, reset/unpowered default-disable behavior, production DNP
handling, physical status readback, firmware listen-only behavior, and bench
evidence must close before CAN1 footprints, routing, manufacturing output, or
`PB-100.kicad_pcb` work can be released.

## 2026-07-17 — PB-100 CAN1 default-disable derivation precheck

Decision: PB-100 CAN1 safety review now has
`hardware/power-board/PB-100/PB-100-can1-default-disable-derivation-precheck.csv`.
The precheck ties ADR-0002 policy/configuration boundaries, `JP_CAN1` DNP/open
missing-link evidence, `U_CAN1` default-disabled gate polarity, TXD recessive
bias, physical disabled-status readback, optional DNP link detect, RX
listen-only independence, firmware/capability/bench evidence, factory DNP
sourcing, and no-layout boundary to PBREL-001.

Reason: PBREL-001 needs a closeable bridge between policy, value calculation,
freeze checklist, production DNP review, reset bench evidence, sourcing/BOM
ownership, and board-print no-go boundary. It prevents configuration,
firmware-only status, or BOM-only claims from being treated as CAN1 TX safety
closure.

## 2026-07-17 — PB-100 CAN1 default-disable closeout precheck

Decision: PB-100 CAN1 safety review now has
`hardware/power-board/PB-100/PB-100-can1-default-disable-closeout-precheck.csv`.
The precheck bridges ADR-0002 policy, `JP_CAN1` DNP/open missing-link evidence,
`U_CAN1` default-disabled gate behavior, TXD recessive bias, physical
disabled-status readback, DNP link-detect boundary, RX listen-only independence,
firmware/capability/bench evidence, factory DNP sourcing, and no-layout
manufacturing boundary to PBREL-001.

Reason: The freeze checklist and derivation precheck define the CAN1 safety
inputs, but print-readiness also needs a machine-checked closeout bridge that
prevents CAN1 TX route layout, jumper footprint lock, `PB-100.kicad_pcb`,
Gerbers, drills, pick-place, or manufacturing ZIP work until the physical
missing link, gate polarity, disabled-status readback, DNP handling, bench
evidence, and sourcing close.

## 2026-07-17 — PB-100 board-current budget value freeze checklist

Decision: PB-100 board-current review now has
`hardware/power-board/PB-100/PB-100-board-current-budget-value-freeze-checklist.csv`.
The checklist ties ADR-0008 current-budget targets, the 50 A main fuse and 40 A
board/configuration budget, high-current path sequence, connector/wire derating,
Q1 thermal-path candidates, 0.5 mΩ four-terminal shunt operating points, copper
pre-layout loss boundary, firmware enforcement, total-current telemetry
enforcement, bench validation, and the no-layout boundary into one
machine-checked artifact.

Reason: PBREL-002 cannot close from a numeric design calculation alone. The
connector derating, Q1 package thermal path, shunt package/Kelvin evidence,
protected distribution, firmware-visible budget enforcement, bench calibration,
and no-layout boundary must close before high-current copper, shunt copper,
connector footprint lock, manufacturing output, or `PB-100.kicad_pcb` work can
be released.

## 2026-07-17 — PB-100 board-current budget value derivation precheck

Decision: PB-100 board-current review now has
`hardware/power-board/PB-100/PB-100-board-current-budget-value-derivation-precheck.csv`.
The precheck ties ADR-0008 targets, protected high-current path sequence,
0.5 mΩ shunt formulas, Q1 thermal operating points, copper pre-layout loss,
garage fuse/connector/wire derating, firmware budget enforcement, telemetry
enforcement, sourcing/BOM ownership, and no-layout boundary to PBREL-002.

Reason: PBREL-002 needs a formula-backed bridge between the trace, design
calculation, value checklist, input reverse review, current telemetry review,
garage sourcing, firmware tests, and board-print no-go boundary before any
high-current copper, shunt copper, connector footprint, or manufacturing output
can be released.

## 2026-07-17 — PB-100 board-current budget closeout precheck

Decision: PB-100 board-current review now has
`hardware/power-board/PB-100/PB-100-board-current-budget-closeout-precheck.csv`.
The precheck bridges ADR-0008 targets, the protected high-current path, main
fuse/wire derating, Q1 thermal candidates, total-current shunt/Kelvin telemetry,
copper pre-layout constraints, firmware budget enforcement, bench telemetry
evidence, factory/garage BOM owner split, and no-layout manufacturing boundary
to PBREL-002.

Reason: The value checklist and derivation precheck define the budget math, but
print-readiness also needs a machine-checked closeout bridge that prevents
high-current copper, shunt copper, Q1 copper, connector placement,
`PB-100.kicad_pcb`, Gerbers, drills, pick-place, or manufacturing ZIP work until
connector derating, shunt package/Kelvin evidence, Q1 thermal path, protected
distribution, telemetry calibration, sourcing, and bench evidence close.

## 2026-07-17 — PB-100 board-print closure matrix

Decision: PB-100 board-print readiness now has
`hardware/power-board/PB-100/PB-100-board-print-closure-matrix.csv`.
The matrix maps every active `PBREL-001` through `PBREL-012` release blocker to
its closeout artifact, current proof state, remaining dated evidence, required
current-state evidence, and board-print blocked action.

Reason: Closeout artifacts are now present for every active release blocker, but
PCB print readiness still depends on dated bench, sourcing, thermal, SOA,
pin-audit, calibration, inspection, and serviceability evidence. The matrix
keeps those gaps explicit and machine-checked so `PB-100.kicad_pcb`, Gerbers,
drills, pick-place, fabrication package, manufacturing ZIP, or PCBA order
package work cannot be treated as authorized while any closure row remains
Conditional.

## 2026-07-20 — Firmware rule action grammar canonicalization

Decision: Firmware rule actions now use a canonical PWM literal grammar shared
by `firmware/services/rule_text.c`, `firmware/configs/svc-config.schema.json`,
and `tools/validate_config.py`. Supported rule actions are role names accepted
by the firmware rule-text parser with `.pwm = 0` or `.pwm = 1..100`; signed
values and leading-zero PWM values are rejected.

Reason: The configuration schema, repository validator, and host-tested firmware
parser must reject the same rule-action language before persisted user
configuration can safely drive role-mapped output actions. Keeping the validator
derived from parser role/condition tables reduces drift while preserving the
configuration/firmware separation and Output Manager enforcement path.

## 2026-07-20 — Runtime current-telemetry fail-safe shutdown

Decision: System Safety now treats stale or invalid total-current telemetry in
the runtime power-budget path as a safe fault. Active outputs are disabled
through the Output Manager, and a power-budget shed event is published when the
coordinator disables loads.

Reason: PB-100 board-current enforcement depends on independent total-current
telemetry. Missing, stale, saturated, or implausible total-current data must not
leave already-active loads running under an unenforceable board budget. The
change keeps startup refusal, load shedding, and stale-telemetry shutdown in the
same host-tested safety path without changing PB-100 hardware requirements.

## 2026-07-20 — CAN decode dropped-edge retry

Decision: CAN Event Decode now updates per-rule decoded state only after a
state-change event is successfully published to the Event Bus. If the Event Bus
is full and publication is dropped, the rule state remains unchanged so the next
matching received frame retries publication.

Reason: CAN-derived edges such as high-beam or indicator transitions must not be
permanently hidden by transient Event Bus pressure. The decoder remains
receive-only and still does not control outputs directly; it preserves the
event-to-rule-to-Output-Manager safety path while making dropped internal events
recoverable.

## 2026-07-20 — Overflow-safe current-budget projection

Decision: Power Budget and Output Manager projected-current calculations now
saturate unsigned additions at `UINT32_MAX`. Overflowed projections are treated
as over-budget and deny output starts or PWM duty-cycle increases.

Reason: Board-current enforcement must not allow a load because arithmetic
wrapped a very large measured-current value into a small projected current. The
change preserves the existing configuration-owned 40 A budget and shed ordering
while making current projection fail closed.

## 2026-07-20 — Event Log drop counter saturation

Decision: Event Log overwrite accounting now saturates the diagnostic dropped
entry counter at `UINT32_MAX` instead of allowing unsigned wraparound.

Reason: The diagnostic log is intentionally bounded, but long-running overflow
conditions must not make drop accounting appear fresh or low after counter wrap.
Saturating preserves the latest event entries and keeps diagnostic evidence
conservative without changing the fixed-size storage model.

## 2026-07-20 — CAN RX Log diagnostic counter saturation

Decision: CAN RX Log dropped-frame and per-port receive counters now saturate at
`UINT32_MAX` instead of wrapping.

Reason: CAN capture is receive-only diagnostic evidence for vehicle and
expansion traffic. Long-running capture sessions must not make frame activity or
drop pressure appear low because an unsigned counter wrapped; saturating keeps
the diagnostic state conservative while preserving the fixed-size ring buffer
and CAN1 no-transmit boundary.

## 2026-07-20 — Configuration Store sequence wrap selection

Decision: Configuration Store two-slot selection now compares record sequence
numbers with wrap-aware unsigned serial arithmetic, so sequence `0` is treated
as newer than `UINT32_MAX` after counter rollover.

Reason: Persisted user configuration must remain preferred across firmware
updates and long service life. A raw numeric `>=` comparison can resurrect an
older pre-wrap record after the sequence rolls over, while wrap-aware selection
keeps the newest valid record active without changing the storage format.

## 2026-07-20 — Overflow-safe battery elapsed-time conversion

Decision: System Safety now converts telemetry update elapsed milliseconds to
seconds using division and remainder arithmetic instead of adding 999 ms before
division. Very large intervals saturate the battery undervoltage duration at
`UINT16_MAX`.

Reason: The battery cutoff delay is a safety boundary. Overflow in
`elapsed_ms + 999` could turn a long interval into a one-second increment and
delay low-voltage cutoff. The new conversion preserves ceiling behavior for
normal intervals and fails toward cutoff for long-running or delayed updates.

## 2026-07-20 — Power-budget shed event retry

Decision: System Safety now retains a pending runtime power-budget shed event
when the Event Bus is full and retries publication on later power-budget safety
updates until the event is accepted.

Reason: Runtime budget enforcement can disable outputs because measured current
is over limit or total-current telemetry is stale/invalid. That shutdown remains
the priority, but diagnostic evidence must not be lost permanently because the
Event Bus was full at the shutdown instant. Retrying keeps the safety action
unchanged while preserving the event path once queue capacity is available.

## 2026-07-20 — Atomic rule text compile buffers

Decision: Rule text compile helpers now validate condition and action strings
before writing caller-provided condition buffers or compiled rule entries.

Reason: Rule compilation uses caller-owned static storage to avoid dynamic
allocation. A rejected rule must not leave partially updated condition storage
that could be reused accidentally by a later rule evaluation. Validating first
keeps failed compilation side-effect free for the caller-owned buffers.

## 2026-07-20 — PBREL local evidence separated from external closeout

Decision: PB-100 board-release evidence now has a dedicated local closeout
ledger for `make check`-verified ERC, netlist, firmware host-test, capability,
and configuration evidence. PBREL statuses remain `Conditional` until dated
external bench, sourcing, schematic-value, and review records close.

Reason: Local validation was complete for several firmware and schematic
scaffold paths, but the board-release blockers also require physical bench
records, current sourcing checks, and final value/footprint reviews. Separating
local evidence prevents stale blocker wording without falsely authorizing PCB
layout, Gerbers, drills, pick-place, manufacturing ZIPs, fabrication packages,
or PCBA order packages.

## 2026-07-20 — PB-100 sourcing snapshot refreshed without BOM lock

Decision: PB-100 factory and garage sourcing records were refreshed against
selected manufacturer, distributor, and JLCPCB componentSearch pages for the
current PBREL pass, and the refresh was synchronized between the sourcing
evidence snapshot and assembly recheck register. The refresh does not lock the
BOM or authorize layout.

Reason: Distributor/manufacturer evidence can reduce stale sourcing risk, but
PBREL-011 and PBREL-012 still require PCBWay assembly-class evidence, resolution
of zero or low JLCPCB stock risks, exact orderable suffixes, inspection/rework
handling, garage housings, contacts, seals, crimp tooling, fuse holders,
enclosure access, and purchase-ready kit evidence before schematic freeze or
board release.

## 2026-07-20 — PB-100 garage kit candidates narrowed without purchase lock

Decision: PB-100 garage install evidence now has
`hardware/power-board/PB-100/PB-100-garage-purchase-kit-candidates.csv`. The
candidate kit narrows DTP06/DTP04, DT06/DT04, DTM06/DTM04, size 12/16/20
contacts, wedgelocks, Littelfuse MAXI and MINI/ATO fuse-holder classes, and
HDT-48-00-class crimp tooling against current TE and Littelfuse source pages.
PBREL-012 remains `Conditional` and the plan still does not freeze exact
connector MPNs.

Reason: The previous garage evidence proved connector and fuse families but did
not bind candidate housings, contacts, wedgelocks, fuse-holder classes, and
tooling into one auditable purchase-kit artifact. This closes part of the
external sourcing gap without authorizing PCB layout, connector footprints,
fuse-holder footprints, enclosure CAD release, manufacturing ZIPs, fabrication
packages, or PCBA order packages. Final lock still needs supplier stock, exact
quantities, boots/backshells, insertion/removal tools, wire-gauge fit, enclosure
entry, heat/service access, vibration inspection, and garage signoff.

## 2026-07-20 — PB-100 PCBWay process evidence separated from MPN lock

Decision: PB-100 factory assembly readiness now has
`hardware/power-board/PB-100/PB-100-factory-assembly-platform-evidence.csv`.
The evidence records PCBWay generic SMT assembly limits, package-input modes,
component sourcing modes, and the distinction between generic process capability
and PB-100 MPN/package-specific approval. PBREL-011 remains `Conditional`.

Reason: PCBWay generic process evidence can close part of the assembly-platform
source gap, but it does not prove exact PB-100 orderable suffix availability,
PowerPAK/TOLL/LFPAK88/DO-218AC/CSS4J/FX18 handling, DNP/open inspection, or
first-article rework limits. Keeping that evidence separate prevents a generic
assembly capability page from being treated as BOM lock, pick-place release,
manufacturing ZIP, fabrication package, or PCBA order approval.

## 2026-07-20 — PB-100 bench validation moved after prototype assembly

Decision: PB-100 pre-layout closure now follows ADR-0013 and separates
schematic/source/package evidence from physical bench execution. The new
`hardware/power-board/PB-100/PB-100-post-prototype-validation-gate.csv` tracks
PB-BENCH-001 through PB-BENCH-015 as deferred post-prototype gates that block
first motorcycle power, field use, and production release, but not the first
prototype PCB fabrication package after schematic freeze.

Reason: Several checks require an assembled PB-100 board or PB-100/LB-100
stack. Requiring those measurements before the first board exists creates a
process deadlock. Pre-layout release blockers may still require calculations,
simulations, source evidence, package/footprint review inputs, test hooks, and
bench procedures; physical records close only after prototype assembly.

## 2026-07-20 — Three-board order gate added before JLCPCB package work

Decision: LB-100 and FB-100 baseline requirements are frozen for schematic
planning by ADR-0014, and both boards now have schematic-freeze checklists,
board-release blocker registers, and review manifests. The project-level order
readiness register
`production/board-order/three_board_jlcpcb_order_readiness.csv` tracks PB-100,
LB-100, and FB-100 together, with `make board-order-status` reporting the
overall NO-GO/READY state.

Reason: The product cannot be treated as ready to order while only PB-100 has
release gates. A three-board gate makes the missing LB-100 and FB-100 KiCad
scaffolds, schematic freezes, layout files, fabrication outputs, and assembly
outputs explicit without starting PCB layout before the required schematic
freeze evidence exists.

## 2026-07-20 — LB-100 and FB-100 KiCad scaffolds started without layout

Decision: LB-100 and FB-100 now each have a project-local KiCad schematic
scaffold under `hardware/logic-board/LB-100/kicad/` and
`hardware/front-board/FB-100/kicad/`. The scaffolds are top-level note sheets
with local symbol and footprint library tables, and intentionally do not include
`.kicad_pcb`, Gerber, drill, pick-place, BOM/CPL, or manufacturing packages.

Reason: ADR-0014 freezes LB-100 and FB-100 baseline requirements enough to open
schematic planning workbenches. Creating note-sheet scaffolds removes the
"missing KiCad project" blocker while preserving the no-layout boundary until
each board's schematic freeze checklist and blocker register close.

## 2026-07-20 — LB-100 and FB-100 pre-layout contracts started

Decision: LB-100 now has `LB-100-jpb1-resource-budget.csv` and
`LB-100-rail-tree-precheck.csv` to start exact MCU resource and power-tree
closeout. FB-100 now has `FB-100-interface-signal-plan.csv` and
`FB-100-ui-mechanical-precheck.csv` to start the front-panel signal, USB,
indicator, button, OLED, and enclosure closeout.

Reason: These contracts reduce the unknowns blocking LB-100 and FB-100
schematic freeze without creating layout, board outlines, component placement,
Gerbers, drills, pick-place files, BOM/CPL packages, or JLCPCB/PCBWay order
artifacts.

## 2026-07-20 — LB-100 MCU and FB-100 service/UI sourcing started

Decision: LB-100 MCU sourcing evidence now has
`hardware/logic-board/LB-100/LB-100-mcu-sourcing-precheck.csv` covering the
STM32H563VIT6 preferred path, STM32H573VIT6 security alternate, and a downsized
STM32H563RGT6 fallback that would require a resource reduction before use.
FB-100 component sourcing evidence now has
`hardware/front-board/FB-100/FB-100-component-sourcing-precheck.csv` covering
USB-C service connector candidates, USB ESD protection candidates, RGB status
LED class, and channel indicator LED class.

Reason: Current JLCPCB/LCSC/DigiKey/ST/TI source evidence closes part of the
factory-sourcing gap for LB-100 and FB-100 while leaving exact pin audit,
footprint orientation, USB no-back-power, LED drive values, final quantities,
BOM/CPL, PCB layout, and manufacturing outputs blocked.

## 2026-07-20 — LB-100 and FB-100 pre-layout release blockers closed

Decision: LB-100 release blockers LBREL-001 through LBREL-007 and FB-100
release blockers FBREL-001 through FBREL-006 are now closed with machine-checked
pre-layout evidence. LB-100 has exact STM32H563VITx LQFP100/JPB1 pin binding,
rail budget, communication-safety, service/storage/sensor, and sourcing
closeout records. FB-100 has JFB1 pinout, USB service/no-back-power, UI/control,
mechanical-envelope, and sourcing closeout records.

Reason: These records remove the LB-100 and FB-100 release-blocker deadlock
without creating PCB layouts, Gerbers, drills, pick-place files, BOM/CPL order
packages, manufacturing ZIPs, or JLCPCB/PCBWay order artifacts. Both boards
remain NO-GO for ordering until their schematic-freeze checklists close with
reviewed value-bearing schematic sheets; PB-100 remains blocked by its active
PBREL register.

## 2026-07-20 — Engineering execution authority formalized

Decision: Repository agent rules now include a `Decision Authority` boundary and
`docs/ENGINEERING_PRINCIPLES.md` as a required engineering-execution reference.
Codex acts as Lead Hardware/Firmware Engineer for implementation, while
architecture decisions remain under ChatGPT plus Product Owner authority and
final approval remains with the Product Owner.

Reason: The project has moved from architecture definition into higher-risk
engineering execution. Persistent rules are required so PB-100 blocker closeout,
component selection, firmware changes, manufacturing planning, and commits stay
evidence-driven, architecture-preserving, capability-compatible, and blocked
from PCB layout or manufacturing output until the proper gates close.

## 2026-07-20 — PB-100 PBREL engineering blockers closed

Decision: PB-100 release blockers PBREL-001 through PBREL-012 are closed for
pre-layout engineering evidence in
`hardware/power-board/PB-100/PB-100-engineering-blocker-closeout.md`. The blocker
register and board-print closure matrix now treat those rows as closed history,
while the PB-100 schematic-freeze checklist remains `Open` with conditional
freeze gates.

Reason: The evidence package now documents why each blocker existed, candidate
comparisons, selected engineering direction, risks, alternatives, cost impact,
thermal impact, production impact, field reliability, datasheet/source evidence,
and post-prototype validation boundaries. This removes the PBREL evidence
deadlock without creating PCB layout, Gerbers, drills, pick-place files,
BOM/CPL order packages, manufacturing ZIPs, or JLCPCB/PCBWay order artifacts.

## 2026-07-20 — LB-100 and FB-100 schematic freeze closed

Decision: LB-100 and FB-100 schematic-freeze checklists are closed for PCB-layout
start. Each board now has a reviewed value-bearing KiCad schematic sheet and a
schematic-review closeout document:
`hardware/logic-board/LB-100/LB-100-schematic-review-closeout.md` and
`hardware/front-board/FB-100/FB-100-schematic-review-closeout.md`.

Reason: LB-100 and FB-100 release blockers were already closed with exact
interface, power, safety, mechanical, and sourcing evidence. The added schematic
review closeouts and KiCad sheet evidence close the remaining note-only
schematic gap without creating PCB layout, Gerbers, drills, pick-place files,
BOM/CPL order packages, manufacturing ZIPs, fabrication packages, or PCBA order
artifacts.

## 2026-07-20 — PB-100 schematic freeze closed

Decision: PB-100 schematic freeze is closed for controlled PCB-layout start in
`hardware/power-board/PB-100/PB-100-schematic-review-closeout.md`. The PBREL
blocker register remains closed, the freeze gap register is retained as closed
history, and the readiness dashboard now marks layout authorization as ready.

Reason: PB-100 now has closed pre-layout engineering evidence for CAN1 safety,
board current budget, board-to-board interface, output stages, input reverse
protection, TVS/load-dump strategy, logic power, current telemetry, thermal
telemetry, factory assembly, and garage assembly. This does not create
`PB-100.kicad_pcb`, Gerbers, drills, pick-place files, BOM/CPL order packages,
manufacturing ZIPs, fabrication packages, or PCBA order artifacts; JLCPCB/PCBWay
ordering remains NO-GO until reviewed PCB layout and manufacturing outputs
exist.

## 2026-07-20 — Three-board layout-start gate created

Decision: PB-100, LB-100, and FB-100 now have a controlled layout-start gate
that separates layout planning from KiCad board import and manufacturing-output
generation. The consolidated readiness artifact is
`production/board-order/three_board_layout_start_readiness.csv`; board-specific
checklists are `PB-100-pcb-layout-start-checklist.csv`,
`LB-100-pcb-layout-start-checklist.csv`, and
`FB-100-pcb-layout-start-checklist.csv`.

Reason: Schematic freeze is closed on all three boards, but every KiCad
schematic still has empty footprint properties and the mechanical envelopes are
not reviewed enough for responsible board import. The new gate records
layout-planning `READY`, KiCad board import `BLOCKED`, and JLCPCB/PCBWay order
`NO-GO`. It also locks a conservative JLCPCB/PCBWay DRC/DFM baseline in
`production/board-order/three_board_layout_rules.md` while continuing to block
Gerbers, drills, pick-place files, BOM/CPL order packages, manufacturing ZIPs,
fabrication packages, and PCBA orders.

## 2026-07-20 — Footprint binding inventory blocks board import

Decision: The next board-import blocker is decomposed into explicit footprint
binding inventories for PB-100, LB-100, and FB-100. The consolidated status file
is `production/board-order/three_board_footprint_binding_status.csv`; per-board
inventories are `PB-100-footprint-binding-inventory.csv`,
`LB-100-footprint-binding-inventory.csv`, and
`FB-100-footprint-binding-inventory.csv`.

Reason: All three schematics are frozen, but the KiCad symbols still have empty
`Footprint` properties or value-bearing text scaffolds without footprint-bound
symbols. Creating `.kicad_pcb` files before package drawing review and footprint
binding would produce false layout evidence. Board import therefore remains
`BLOCKED` until package drawings, pad geometry, pin-1/orientation, DNP/open
handling, assembly ownership, and mechanical keepout evidence close for every
open footprint item.

## 2026-07-20 — Mechanical envelope inventory blocks board import

Decision: The second board-import blocker is decomposed into explicit
mechanical-envelope inventories for PB-100, LB-100, and FB-100. The consolidated
status file is
`production/board-order/three_board_mechanical_envelope_status.csv`; per-board
inventories are `PB-100-mechanical-envelope-inventory.csv`,
`LB-100-mechanical-envelope-inventory.csv`, and
`FB-100-mechanical-envelope-inventory.csv`.

Reason: Layout planning is allowed, but KiCad board import still needs reviewed
board outline, mounting, connector placement, service access, cable exits,
mezzanine stack, antenna/optical/sensor keepouts, high-current zones, and
panel/edge constraints. These are layout inputs, not architecture changes.
Keeping board import `BLOCKED` prevents false `.kicad_pcb` evidence and keeps
Gerbers, drills, pick-place files, BOM/CPL order packages, manufacturing ZIPs,
fabrication packages, and PCBA orders blocked until layout review.

## 2026-07-20 — Off-board items removed from footprint blockers

Decision: Garage-installed items that do not require a PCB footprint are now
marked `Not required` in the footprint-binding inventories instead of being
counted as KiCad footprint blockers. This closes PB-100 output fuse holder and
high-current connector footprint blockers, LB-100 service USB connector
footprint blocker, and FB-100 garage FFC cable footprint blocker.

Reason: These items still need mechanical-envelope, harness, service-access,
garage-kit, and sourcing review, but they should not block KiCad footprint
binding as if they were on-board SMT/THT land patterns. This reduces false
board-import blockers while preserving the manufacturing boundary and without
removing any DNP footprint or board capability.

## 2026-07-20 — Footprint package sources identified

Decision: The footprint-binding inventories now distinguish package-source
identification from completed footprint binding. PB-100 has 14 of 15 open
on-board footprint items with package sources identified, LB-100 has 9 of 13,
and FB-100 has 8 of 12.

Reason: Official package/source evidence is required before creating project
local footprints, but identifying a package source does not prove pad geometry,
pin-1/orientation, courtyard, stencil, solder-mask, or assembly handling. Board
import therefore remains `BLOCKED` until each source-identified item is
converted into reviewed KiCad footprint evidence and every remaining open source
gap is resolved.

## 2026-07-20 — Remaining PB/LB footprint package sources identified

Decision: PB-100 and LB-100 now have package sources identified for every open
on-board footprint item. PB-100 is 15 of 15 and LB-100 is 13 of 13. FB-100 is
10 of 12; its remaining package-source gaps are exact status RGB LED and channel
LED MPN/package selection.

Reason: CAN1 TX disable package evidence, BLE module footprint source, BMI270
LGA package evidence, VEML7700 optical package evidence, TF-015 microSD source,
and optional OLED module sources have been traced without creating KiCad
footprints or a PCB. The open FB LED items remain intentionally open because
generic LED categories are not enough evidence for package binding; exact MPN,
polarity, optical/mechanical fit, current-limit values, and JLCPCB/PCBWay
assembly evidence must close first.

## 2026-07-20 — FB-100 LED package sources identified

Decision: FB-100 now has package sources identified for every open on-board
footprint item. Status RGB uses Everlight 19-237/R6GHBHC-A01/2T class with
LCSC C60105 and JLCPCB RGB LED evidence. Channel indicators use KT-0805Y
preferred or KT-0603R alternate class with JLCPCB LED indication evidence.
FB-100 package-source coverage is now 12 of 12.

Reason: Generic LED categories were insufficient for footprint-source evidence.
Exact LED package source paths remove the last FB-100 package-source gap while
leaving drive polarity, current-limit values, brightness, light-pipe alignment,
optical orientation, and actual footprint binding blocked until reviewed layout
inputs close.

## 2026-07-20 — FB-100 mechanical layout inputs closed

Decision: FB-100 mechanical envelope is closed as a board-import input with an
80.0 mm x 35.0 mm prototype outline, four M2.5 NPTH mounting holes, USB-C
service edge datum, rear/internal JFB1 FFC cable exit, role-free STATUS and
CH1..CH10 optical grid, separated SERVICE/RESET actuator targets, optional
OLED DNP keepout, and tab-route-first panelization assumptions. Evidence is in
`hardware/front-board/FB-100/FB-100-mechanical-layout-inputs.csv` and
`hardware/front-board/FB-100/FB-100-mechanical-layout-input-closeout.md`.

Reason: FB-100 schematic freeze had enough mechanical policy for planning but
not enough exact layout-input dimensions for responsible board import. Closing
the FB-100 mechanical rows removes 7 mechanical blockers without creating
`FB-100.kicad_pcb`, Gerbers, drill files, pick-place files, BOM/CPL order
packages, manufacturing ZIPs, fabrication packages, panel CAD, enclosure CAD,
or PCBA orders. FB-100 board import remains blocked by footprint binding and
USB/no-back-power layout-model review.

## 2026-07-20 — FB-100 USB no-back-power layout model closed

Decision: FB-100 USB/no-back-power layout model is closed as a board-import
input. USB ESD must sit between the USB-C receptacle and JFB1, `USB_D_P` and
`USB_D_N` must route as a short coupled pair, `USB_VBUS_SENSE` remains
sense-only with no connection to `FB_3V3_OR_IO`, `PB_5V_OUT`, `LB_3V3_IO`,
PB-100, or any output rail, CC pins remain device-role only, shield/ESD return
cannot be a high-current return, and JFB1 USB pins remain fixed. Evidence is in
`hardware/front-board/FB-100/FB-100-usb-no-back-power-layout-rules.csv` and
`hardware/front-board/FB-100/FB-100-usb-no-back-power-layout-closeout.md`.

Reason: FB-100 schematic freeze closed USB policy but not USB layout-specific
placement/routing constraints. This closes the USB/no-back-power layout-model
gate without creating `FB-100.kicad_pcb`, Gerbers, drill files, pick-place
files, BOM/CPL order packages, manufacturing ZIPs, fabrication packages, or
PCBA orders. FB-100 board import remains blocked by footprint binding.

## 2026-07-20 — FB-100 local footprint binding closed

Decision: FB-100 now has project-local KiCad footprint bindings for every
on-board footprint item in `hardware/front-board/FB-100/kicad/lib/FB100.pretty`.
The bindings cover USB-C preferred and alternate connectors, USB ESD preferred
and alternate packages, RGB/status LED, channel LED preferred and alternate
packages, JFB1 FPC connector, SERVICE/RESET switch options, optional OLED DNP
preferred and alternate footprints, and local 0603/0805 passive footprints.
Evidence is in `hardware/front-board/FB-100/FB-100-footprint-binding-closeout.csv`
and `hardware/front-board/FB-100/FB-100-footprint-binding-closeout.md`.

Reason: FB-100 package sources were identified, but board-import preparation
still lacked local KiCad footprint evidence. JLCPCB/LCSC/EasyEDA footprint
sources were converted and normalized to KiCad 10 format, with temporary 3D
model paths removed. This closes FB-100 footprint binding without creating
`FB-100.kicad_pcb`, Gerbers, drill files, pick-place files, BOM/CPL order
packages, manufacturing ZIPs, fabrication packages, or PCBA orders. FB-100 board
import remains blocked by schematic symbol promotion because the KiCad
schematic is still a value-bearing scaffold rather than footprint-bound symbol
instances.

## 2026-07-20 — PB/LB footprint binding progress imported

Decision: Import and normalize project-local KiCad footprints for the PB-100 and
LB-100 package classes that already have successful JLCPCB/LCSC/EasyEDA footprint
evidence. This is a footprint-binding progress increment, not a layout start.

Rationale: PB-100 and LB-100 were both blocked by open footprint inventories even
after package-source evidence existed. EasyEDA conversion succeeded for the
TPS48110 VSSOP, SIDR626 PowerPAK, LM74700 SOT-23-6, LM5164 SO PowerPAD,
INA228 VSSOP, NTC 0402, STM32H563 LQFP100, LB regulators/transceivers,
BLE module, IMU, lux sensor, and microSD socket. These are now committed as
project-local `.kicad_mod` evidence under `PB100.pretty` and `LB100.pretty`.

Impact: PB-100 footprint inventory drops from 15 open items to 9 open items.
LB-100 footprint inventory drops from 13 open items to 1 open item. KiCad board
import remains blocked because PB still needs TOLL/LFPAK/DO-218AC/CSS4J/FX18
and related optional/safety footprint decisions, while LB still needs the FX18
JPB1 footprint and mechanical layout gates. No `*.kicad_pcb`, Gerbers, drills,
pick-place, BOM/CPL, manufacturing ZIP, fabrication package, panel output, or
PCBA order artifact is authorized or created by this increment.

## 2026-07-20 — PB/LB FX18 local footprint binding

Decision: PB-100 and LB-100 now include project-local source-derived Hirose
FX18 footprints for the JPB1 mezzanine pair: `PB100:FX18-100P-0.8SV10_Hirose`
and `LB100:FX18-100S-0.8SV20_Hirose`. The derivation uses the official Hirose
FX18 catalog recommended land pattern plus official 2026 2D drawings for
`CL0579-0034-1-00` and `CL0579-0038-2-00`; the footprint files intentionally
keep MF/TH mechanical details as mechanical-envelope follow-up evidence rather
than authorizing board import.

Reason: JLCPCB/EasyEDA API did not expose the FX18 models, Hirose Allegro
footprints require member access, and the project must keep footprint binding
moving without starting layout or fabricating artifacts. Signal pad pitch, pad
size, body outline, pin numbering, and source links are captured locally; paired
stack datum, 20 mm spacing, pin-1 cross-board orientation, vibration retention,
and assembly handling remain blocked in mechanical layout gates.

## 2026-07-20 — PB-100 CAN1 and LM5013 footprint binding

Decision: Close two additional PB-100 footprint-binding rows without changing
architecture or starting layout. `LM5013-Q1` is bound only as a package-compatible
DDA SO PowerPAD-8 alternate using the existing local
`PB100:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL-EP2.9` footprint. CAN1 TX-disable
hardware now has local footprint evidence for default-open `JP_CAN1`
(`PB100:R0603_DNP_LINK_1608Metric`) and the `SN74LVC1G125-Q1`-class
default-disabled DBV gate candidate (`PB100:SOT-23-5_DBV_TI`).

Reason: TI package evidence confirms the `LM5013-Q1` alternate uses the same
SO PowerPAD-8 class as the reviewed `LM5164QDDATQ1` footprint, and TI
`SN74LVC1G125-Q1` DBV0005A evidence gives a source-derived SOT-23-5 land
pattern for `U_CAN1`. The default vehicle-CAN TX route remains DNP/open per
ADR-0002 and still requires a future ADR plus explicit hardware action before
any TX population. This is footprint evidence only; no `PB-100.kicad_pcb`,
Gerbers, drills, pick-place files, BOM/CPL order packages, manufacturing ZIPs,
fabrication packages, panel outputs, or PCBA orders are created or authorized.

## 2026-07-20 — PB-100 TVS shunt and optional temp footprints

Decision: Add local source-derived PB-100 footprints for the Vishay SM8S
DO-218AC input TVS, Bourns CSS4J-4026 four-terminal total-current shunt, and
TMP112-Q1 optional DNP digital temperature sensor. The footprint inventory now
records these rows as bound and reviewed while leaving TOLL/LFPAK MOSFET package
selection open.

Reason: Vishay document 98647 includes a DO-218AC mounting pad layout, Bourns
CSS4J-4026 documentation includes a recommended Kelvin pad layout and AEC-Q200
evidence, and TI TMP112-Q1 documentation provides the DRL SOT-563 package path
for an optional DNP digital sensor. This is footprint-binding evidence only:
TVS surge thermal behavior, shunt copper heating, Kelvin polarity, solder
voiding, optional I2C ownership, and production inspection remain layout/BOM
gates. No `PB-100.kicad_pcb`, Gerbers, drills, pick-place files, BOM/CPL order
packages, manufacturing ZIPs, fabrication packages, panel outputs, or PCBA
orders are created or authorized.

## 2026-07-20 — PB-100 MOSFET footprint inventory closed

Decision: Add local PB-100 source-derived MOSFET package footprints for
Infineon PG-HSOF-8-1 TOLL (`PB100:PG-HSOF-8-1_TOLL_Infineon`) and Nexperia
LFPAK88 SOT1235 (`PB100:LFPAK88_SOT1235_Nexperia`). The PB-100 footprint
inventory now has zero Open rows.

Reason: Infineon package evidence gives the TOLL footprint and IAUTN06S5N008
pinout with pin 1 gate, pins 2-8 source, and tab drain. Nexperia package
evidence gives LFPAK88 SOT1235 footprint and BUK7S1R2-80M pinout with pin 1
gate, pins 2-4 source, and mounting base drain. This closes footprint-binding
evidence only; OUT2 escape package selection, input reverse FET thermal path,
paste aperture segmentation, via field, solder voiding, sourcing stock, and
controlled schematic symbol promotion remain before board import. No
`PB-100.kicad_pcb`, Gerbers, drills, pick-place files, BOM/CPL order packages,
manufacturing ZIPs, fabrication packages, panel outputs, or PCBA orders are
created or authorized.

## 2026-07-20 — PB-100 and LB-100 mechanical layout inputs closed

Decision: Close the PB-100 and LB-100 mechanical-envelope inventories as
pre-layout board-import inputs only. PB-100 now has a reviewed `150.0 mm x
90.0 mm` prototype outline, four M3 NPTH mounting holes, off-board battery
entry, generic OUT1..OUT10 harness/service zones, centered JPB1 FX18 datum,
high-current placement zones, and a separated CAN1 service exit. LB-100 now has
a reviewed `100.0 mm x 70.0 mm` prototype outline, four M2.5 NPTH mounting
holes, centered JPB1 FX18 datum, STM32H563VITx service zone, power-rail
keepouts, microSD access, BLE antenna keepout, sensor orientation, and generic
DNP/service connector zones with CAN1_TX_ROUTE DNP/open by default.

Reason: footprint evidence is closed for all three boards, but board import was
still blocked by missing PB/LB mechanical datums. The new closeouts define only
prototype layout inputs and preserve the manufacturing boundary: no
`PB-100.kicad_pcb`, `LB-100.kicad_pcb`, Gerbers, drills, pick-place files,
BOM/CPL order packages, manufacturing ZIPs, fabrication packages, panel outputs,
or PCBA orders are created or authorized. PB-100 board import remains blocked
by thermal/current layout evidence and controlled schematic symbol promotion.
LB-100 board import remains blocked by signal-integrity layout evidence and
controlled schematic symbol promotion.

## 2026-07-20 — PB-100 footprint binding review remediation

Decision: tighten PB-100 footprint-binding evidence after review. The TOLL
input MOSFET footprint drain pad now uses `Tab` to match
`PB100_INPUT_NMOS_TOLL_PRELIM`; the LFPAK88 drain mounting-base pad now uses
`mb` to match `PB100_POWER_NMOS_ESCAPE_PRELIM`. `JP_CAN1` and `U_CAN1` no
longer share the generic five-pin CAN1 safety symbol in the CAN1 sheet:
`JP_CAN1` uses a concrete two-pin DNP/open link symbol and `U_CAN1` uses a
concrete SN74LVC1G125-Q1 DBV five-pin gate symbol. `PB-100-symbol-footprint-pad-map.csv`
and `tools/validate_pb100.py` now check these symbol-pin to footprint-pad
contracts automatically.

Reason: a local `.kicad_mod` alone is not enough evidence for safe board import.
Symbol pins and footprint pads must match before controlled symbol promotion,
and large MOSFET drain pads must not carry a solid stencil aperture. The TOLL
and LFPAK88 drain copper pads now exclude `F.Paste` and use segmented
paste-only apertures checked by the validator. Solder-voiding, thermal-via
fields, final MOSFET package selection, overshoot/SOA margin, and schematic
Footprint property promotion remain blocked before board import. No
`PB-100.kicad_pcb`, Gerbers, drills, pick-place files, BOM/CPL order packages,
manufacturing ZIPs, fabrication packages, panel outputs, or PCBA orders are
created or authorized.

## 2026-07-20 — Electrical/topology audit remediation and freeze retraction

Decision: retract the premature PB-100, LB-100, and FB-100 schematic-freeze
closeouts without changing the frozen three-board architecture. PB-100 CAN1 now
uses the explicit sequence `CAN1_TX_ROUTE` -> `U_CAN1` ->
`CAN1_TX_GATE_OUT` -> DNP `JP_CAN1` -> `CAN1_TXD_SAFE`, with physical 47 kΩ
OE pull-up, 47 kΩ downstream TXD bias, 1 kΩ status series resistor, and
100 kΩ status pull-up. `tools/validate_pb100.py` exports the KiCad XML
netlist and checks exact component-pin-net membership, values, footprints, and
the DNP property instead of accepting text markers.

Decision: reopen PB/LB FX18 footprint, electrical-interface, and mechanical
gates. Official Hirose drawings `0000951879` and `0000951892` specify 0.8 mm
signal pitch, 4.9 mm signal-row center spacing, and 0.5 mm by 2.1 mm signal
lands. A high-resolution drawing review confirmed that the existing 4.9 mm
signal-row spacing was correct; the 8.4 mm callout is not the signal-row
spacing and must not be substituted for it. The socket pin-1 marker was
mirrored to its actual signal end, and misleading F.Fab circles that did not
represent physical holes were removed.

The same Hirose drawings, product data, and official Allegro footprint packages
`0001474376`/`0001474378` identify four additional MF electrical positions per
connector. MF Contact A has two soldering poles that must be connected to the
same circuit, while MF Contact B has one; the paired ends therefore require six
physical plated TH lands representing four circuits. The 100-position JPB1
signal map does not assign those four MF circuits. They remain unassigned in
`PB-100-fx18-mf-contact-ownership-precheck.csv`, and no speculative TH pads or
net assignments were added.

`tools/validate_board_order.py` now validates every signal-pad coordinate,
size, layer set, pitch, row spacing, and plug/socket mirroring. It cannot treat
an FX18 footprint as complete until it also has exactly six plated TH lands,
four non-signal circuit identifiers, and the two duplicated identifiers needed
to join both split-pole MF A pairs. The earlier FX18/mechanical closeout entries
are superseded by this audit result; PCB import remains blocked pending Product
Owner approval of MF net ownership and independent paired-footprint review.

Decision: keep the PB-100 60/80 V choice Conditional. A 53.3 V datasheet clamp
point alone does not accept a 60 V MOSFET. Closure requires reproducible
`Vstress = Vclamp + Lloop * di/dt` simulation or measurement with waveform,
parasitics, temperature, source impedance, fixture/probe uncertainty and SOA;
otherwise an 80 V migration requires Product Owner approval plus thermal,
sourcing, footprint, and assembly review. LB-100 and FB-100 remain Open because
their KiCad schematics contain no component instances. No `.kicad_pcb`, Gerber,
drill, pick-place, BOM/CPL order, manufacturing ZIP, fabrication, or PCBA order
artifact is authorized or created.

## 2026-07-20 — CAN1 physical-layer ownership contradiction exposed

Decision: do not create an LB-100 CAN1 transceiver schematic from the current
documents. The post-jumper `CAN1_TXD_SAFE` net exists only on PB-100, while the
current LB sourcing and footprint inventories assign the transceiver to LB-100.
JPB1 has no post-jumper return signal, so the earlier instruction to connect an
LB transceiver TXD directly to `CAN1_TXD_SAFE` cannot be implemented
electrically. PBREL-001, LBREL-004, and the related CAN freeze rows are
Conditional rather than Closed.

Proposed ADR-0015 compares three topologies. Candidate A is recommended: LB-100
keeps STM32 FDCAN, protocol, and firmware ownership, while PB-100 owns the CAN1
transceiver, protection, termination options, and vehicle-harness physical
layer. This keeps `CAN1_TXD_SAFE` local, preserves all four existing JPB1 logic
signals, and avoids carrying CANH/CANL or a post-jumper return through the
mezzanine connector. Candidate B colocates the entire CAN1 chain on LB-100;
candidate C adds a return path across JPB1 and is not recommended.

ADR-0015 remains `Proposed`. No transceiver was moved or instantiated, no
accepted architecture was changed, and no DNP capability was removed. Product
Owner approval is required before BOM ownership, rail budgets, protection,
termination, footprint binding, or value-bearing CAN1 capture is changed.

## 2026-07-20 — ADR-0015 accepted and FX18 MF circuits assigned

Decision: Product Owner accepted ADR-0015 candidate A. PB-100 owns the CAN1
transceiver, ESD/TVS protection, optional common-mode choke and termination,
CANH/CANL, and vehicle-harness physical boundary. LB-100 retains STM32 FDCAN,
protocol, and read-only firmware policy. The PB schematic now implements
`CAN1_TX_ROUTE -> U_CAN1 -> CAN1_TX_GATE_OUT -> JP_CAN1 (DNP/open) ->
CAN1_TXD_SAFE -> U_CAN1_PHY TXD`; `U_CAN1_PHY RXD` connects only to
`CAN1_RX_ROUTE`. A 47 kOhm silent-mode pull-up plus DNP `JP_CAN1_NORMAL` adds a
second hardware transmit lock. The XML-netlist validator checks the transceiver,
supplies, ESD, DNP termination, silent-mode lock, TX chain and RX route by
component pin rather than text markers.

Decision: Product Owner assigned all four FX18 MF circuits to `GND` on PB-100
and LB-100. Each footprint now contains exactly six official 1.4 mm by 2.4 mm
plated oval lands with 1.0 mm by 2.0 mm slots. Each MF A pair shares one logical
pad identifier; both MF B contacts use separate identifiers. The four IDs are
unique, plug/socket X geometry is mirrored, pin-1 ends are preserved, and no MF
contact may connect to AGND, PB_5V_OUT, LB_3V3_IO or VBAT. JPB1 on PB-100 now
binds the reviewed FX18 footprint and its four MF logical pins export on GND.

These decisions close only the ownership and captured-topology contradictions.
PCB layout remains blocked by the remaining connector/harness, mechanical,
thermal, SOA, assembly-source and full schematic-freeze gates.

## 2026-07-20 — Product Owner selected the 80 V MOSFET baseline

Decision: select Nexperia `BUK7S1R2-80M` 80 V LFPAK88 for PB-100 Q1 and
Q101-Q110. The selected KiCad symbols, footprints, schematic instances,
factory BOM, sourcing trace, power budget and thermal planning now name the
same part. `IAUTN08S5N012L` 80 V TOLL and `BUK7J2R4-80M` 80 V LFPAK56E are
retained as controlled non-drop-in alternatives. `IAUTN06S5N008` and
`SIDR626LDP` 60 V paths remain historical evidence and are not approved Rev.1
assembly substitutions.

This closes the contradictory 60/80 V selection only. It does not close the
selected part's actual clamp-loop overshoot, SOA, fuse-energy, copper thermal,
enclosure thermal, live sourcing or factory-assembly evidence. PBREL-004,
PBREL-006, PBREL-007 and PBREL-011 therefore remain `Conditional`, and their
engineering-closeout section statuses are synchronized to the release-blocker
register. No PCB layout or manufacturing artifact is authorized.

## 2026-07-20 — PB-100 validator decomposed by engineering ownership

Decision: keep `tools/validate_pb100.py` as the stable command-line entrypoint
and move its implementation into `tools/pb100_validation/`. Checks are grouped
by KiCad, symbol/footprint evidence, release gates, pin contracts, outputs,
input power, logic power, CAN1, current budget, current telemetry, thermal
telemetry, factory sourcing, garage installation, TVS/load-dump protection,
JPB1/LB interface, and review-packet ownership.

The ordered set of 109 top-level checks and all 142 previous validator/helper
functions are preserved. The release-manifest hook registry now discovers
`validate_*` callables across the package instead of depending on one module's
`globals()`. `make check` remains the compatibility contract. This is an
implementation-maintainability change only; it does not change hardware
architecture, freeze status, PCB authorization, or manufacturing readiness.

## 2026-07-21 — Cross-document readiness consistency gate

Decision: synchronize active readiness documents with ADR-0015 Accepted, the
captured six-land FX18 footprints, the selected BUK7S1R2-80M 80 V baseline, and
the three board-release blocker registers. The current active blocker set is
PBREL-001/003/004/006/007/011, LBREL-003/007, and FBREL-006. Footprint capture
is distinct from the still-open physical FX18 paired-stack, vibration, mating,
and assembly-fixture evidence.

Decision: add `tools/readiness_validation/consistency.py` as a separate
single-responsibility validator. It derives blocker counts and exact IDs from
the board registers, compares both three-board readiness CSV files and
`docs/product/final-readiness.md`, requires the accepted CAN1/FX18/80 V facts,
and rejects the known stale claims. `make check` now executes this gate.

Reason: green electrical, footprint, or artifact checks did not prove that
human-facing status documents agreed with their sources of truth. The separate
gate prevents stale status text without coupling document policy back into the
large electrical validators. It changes no architecture and authorizes no PCB
layout or manufacturing output.

## 2026-07-21 — LB-100/FB-100 value-bearing schematic closeout

Decision: replace the LB-100 and FB-100 text-only scaffolds with deterministic,
footprint-bound KiCad schematics generated by
`tools/generate_lb_fb_schematics.py`. LB-100 now exports 63 components and 186
electrical nets; FB-100 exports 44 components and 46 electrical nets. The
accepted architecture is preserved: PB-100 owns the CAN1 physical layer, LB-100
owns STM32 FDCAN/protocol/read-only policy, and FB-100 remains a role-free
service/UI board with sense-only USB VBUS.

Decision: select TCA9539-Q1 for LB role-free UI expansion, TPS22918-Q1-class
load switches for BLE/microSD service domains, and LTC3212 for the FB one-wire
RGB implementation. The LTC3212 source is currently out of stock and is a
production sourcing risk, not a reason to hide or bypass the approved one-wire
interface. Component margins, alternatives, lifetime, junction-temperature,
qualification, sourcing, and assembly risks are recorded in the LB/FB component
decision records.

Decision: add `tools/board_schematic_validation/` as a focused validator for
deterministic-generation freshness, exported-netlist topology, exact connector
contracts, symbol-to-footprint pad sets, DNP state, and ERC. LB ERC is accepted
only with the two explicit cross-board `USB_CC1`/`USB_CC2` isolated-label
warnings; FB ERC must remain finding-free. This closes LBREL-007 and FBREL-006.

## 2026-07-21 — FX18 pair correction and mechanical pre-layout closeout

Decision: supersede the earlier FX18-100P-0.8SV10 plus
FX18-100S-0.8SV20 assumption. The official Hirose stack table makes that pair a
30 mm stack, so it cannot satisfy the frozen 20 mm envelope. Retain the PB
FX18-100P-0.8SV10 and change the LB receptacle to FX18-100S-0.8SV10
(CL0579-0058-0-00, drawing 0000954081, JLC/LCSC C6048965). This is the minimum
component correction that preserves the approved interface and produces the
official nominal 20 mm stack.

Decision: use four shared M2.5 stack holes and four 20.3 +/-0.127 mm spacers.
Each footprint keeps exactly six plated TH lands, four distinct logical MF
identifiers, and all MF circuits on GND with mirrored plug/socket X geometry and
reviewed pin 1. The fixture and inspection plan close PBREL-003 and LBREL-003
for pre-layout work under ADR-0013. PB-BENCH-014 continuity and PB-BENCH-015
vibration execution remain mandatory before motorcycle power, field use, or
production release.

Decision: include a 35 mA FB-100 worst-case UI allowance in the shared 5 V
budget. The reviewed totals are 229.2 mA sustained and 381.2 mA service peak,
both below the 500 mA PB_5V_OUT allocation.

Result: LB-100 and FB-100 have zero active board-release blockers. LB board
import still waits for its signal-integrity/safety layout model; FB controlled
board import is ready. PB-100 retains five active blockers:
PBREL-001/004/006/007/011. No `.kicad_pcb`, Gerber, drill, placement,
manufacturing ZIP, or PCBA order artifact is created by this decision.

## 2026-07-21 — PB-100 five pre-layout blocker closeout

Decision: supersede the preliminary 2026-07-20 LFPAK88 selection with exact
Infineon `IAUT300N08S5N012ATMA2`, an active/preferred automotive 80 V
PG-HSOF-8-1 TOLL MOSFET, for Q1 and Q101-Q110. The same-footprint controlled
alternative is `IAUT300N08S5N014ATMA1`; `BUK7J2R4-80MX` LFPAK56E remains a
deliberately non-drop-in alternative. Generated Q1 evidence records the
2.52 mOhm hot bound, 4.032 W loss at 40 A, 126.61 degC junction estimate at the
125 degC case limit, and 48.39 degC absolute-junction margin.

Decision: close PBREL-004 with generated per-class TPS48110-Q1 values and SOA
envelopes. OUT2 is bounded at 30 A for 100 ms, 80 A for 4 ms, and 95.91 A for
5 us; every output retains role-free configuration, local clamp, sense,
timer, threshold, and fuse evidence. Physical pulse and thermal execution stay
in the layout/prototype gates.

Decision: close PBREL-007 with a reproducible transient model. The
SM8S33AHM3/I 53.3 V raw 124 A clamp point is temperature-adjusted and combined
with a 20 nH loop, 15 A/us edge, and 1 V uncertainty to produce a 59.45 V
bounded stress. This leaves 20.55 V to the selected 80 V MOSFETs. Reopen the
design if extracted clamp-loop inductance exceeds 20 nH or PB-BENCH-004
measures 60 V or more.

Decision: close PBREL-001 from the captured and exported CAN1 topology,
including the DNP/open JP_CAN1 missing link, OE/TXD pulls, physical disabled
readback, PB-owned transceiver/protection, RX-only return, and exact DTM04-4P /
DTM06-4S harness boundary. Close PBREL-011 from the exact TOLL/TVS/output/CAN1
and FX18 source/process routes, alternates, paste, DNP, inspection, and honest
consignment evidence. Order-date stock, quote, DFM, FAI, DNP inspection, and
bench execution remain later gates.

Decision: generate release calculations from `tools/pb100_evidence/`, validate
their freshness and cross-artifact bindings in
`tools/pb100_validation/release_evidence.py`, and require the local PBREL
closeout ledger and release manifest to match the blocker register. All twelve
PBREL rows are now `Closed` for pre-layout evidence. PB-100 schematic freeze
remains `Open` for controlled value-bearing sheet promotion, final review, and
Product Owner approval; no PCB layout or manufacturing artifact is authorized.

## 2026-07-21 — Corrective PB load-dump and LB/FB electrical review

Decision: accept ADR-0016 and reopen PBREL-007. The former 100 V 10/1000 us
59.45 V peak-stress calculation is rejected as load-dump closeout evidence.
The project requirement is now the ISO 16750-2 Test A 12 V envelope of
79-101 V, 0.5-4 ohm, and 40-400 ms with current, energy, transient thermal
impedance, tolerance, self-heating, and repeated-pulse evidence. Generated
screening shows that the current SM8S33AHM3/I branch fails multiple corners and
does not preserve the required 5 V margin to the LM74700-Q1 60 V recommended
ceiling.

Decision: mark PBREL-006 Conditional until layout copper/thermal extraction and
PB-BENCH-010 prove the assumed 125 degC Q1 case boundary. The selected
IAUT300N08S5N012ATMA2 80 V TOLL voltage class remains accepted; its existing
junction estimate is a screening condition rather than measured thermal proof.

Decision: correct LB-100/FB-100 electrical capture without changing the frozen
board architecture. IC electrical pin types now drive ERC; ADC_REF is sourced
from the analog rail with local 1 uF/100 nF decoupling and AGND has one
documented 0 ohm return to GND; USB VBUS presence is converted by a 5 V-tolerant
digital buffer instead of an invalid PD10 ADC divider; STM32 PD7 directly drives
the timing-critical LTC3212 LEDEN path; BMI270 VDDIO/CSB and the other I2C
sensor interface supply remain on always-on LB_3V3_IO while BMI270 VDD alone is
switched, preventing pull-up back-power.

Result: corrective schematic validation remains green. PB-100 has two active
release blockers and no `.kicad_pcb`, Gerber, drill, placement, manufacturing
ZIP, or PCBA order artifact is created.

## 2026-07-21 — E73 powered-off isolation and defined USB VBUS removal

Decision: temporarily treat `LBREL-005`, `LBREL-007`, `FBREL-002`, and
`FBREL-006` as Conditional after review found that E73 UART/reset were driven
from the always-on STM32 domain while `RADIO_SENSOR_3V3` was off and that
`USB_VBUS_DETECT_RAW` had no DC pulldown. Re-close those four schematic gates
only with the corrective topology and machine-checked evidence below.

Decision: retain the switched E73 rail and add U15-U17
`SN74LVC1G125-Q1` gates powered from `RADIO_SENSOR_3V3`. Both UART directions
and reset now cross the domain through `Ioff` buffers. R18/R19 22 kOhm idle
pulls terminate on the quick-output-discharged switched rail and bound
module-side powered-off UART voltage to 0.222 V maximum, while R9 moves to the
switched rail so RESET is bounded to 0.101 V maximum. R20/R22 hold both
always-on UART sides idle-high and R21 keeps reset asserted until firmware
releases it after rail settling. All module-side bounds are below the
nRF52840 `VDD + 0.3 V` absolute limit at VDD = 0 V. The always-on alternative
was rejected because it would make parking-current and fault containment rely
only on nRF52840 System OFF firmware behavior.

Decision: change FB R13 to 3.9 kOhm, add R14 15 kOhm from
`USB_VBUS_DETECT_RAW` to GND, and retain C1 100 nF. With VBUS 4.75-5.50 V,
1% resistors, U14 input leakage, and a conservative 70-130 nF effective
capacitance range, the raw input is 3.723 V minimum when present and 0.152 V
maximum when absent. It crosses even the 3.43 V maximum positive threshold in
the complete TI table within 1.04 ms and falls below the minimum 0.77 V
Schmitt threshold within 3.81 ms.

Decision: extend `tools/board_schematic_validation/rules.py` to require the
exact switched-buffer nets, module-side clamps, switched reset pull-up, and
USB R13/R14/C1 topology. The generated LB netlist is now 81 components and
191 nets; FB is 44 components and 46 nets. ERC and exported-netlist validation
pass. `PBREL-006` remains Conditional, `PBREL-007` remains Open, and no
`.kicad_pcb` or manufacturing output is authorized.

## 2026-07-21 — Remove the PB-100 layout/qualification gate deadlock

Decision: accept ADR-0017 and replace the binary PB board-print gate with four
ordered authorization states: `BLOCKED`, `LAYOUT-ONLY`, `PROTO-ONLY`, and
`PRODUCTION-READY`. Pre-layout component selection and calculations permit only
controlled layout; reviewed copper/current/thermal and clamp-loop extraction
permits only a marked engineering prototype; prototype qualification permits
the blocker-specific production-ready transition. All other applicable PB bench
and production gates still apply before field or production release.

Decision: keep PBREL-006 Conditional and PBREL-007 Open as overall blockers but
track their stage evidence in `PB-100-staged-release-readiness.csv`. PBREL-006
is individually `LAYOUT-ONLY`; PBREL-007 is `BLOCKED` because the current TVS
branch fails its ADR-0016 pre-layout model. Aggregate PB-100 authorization is
therefore still `BLOCKED`, with production and field use `NO-GO`. No second
developer is required.

Decision: make the earlier LB/FB powered-off calculations executable evidence.
`tools/generate_lb_fb_release_evidence.py` now recalculates the 0.2222 V E73
UART powered-off clamp, 3.7231 V minimum USB-present level, 0.1515 V maximum
USB-absent level, and 3.4389 ms removal time against the retained 3.81 ms bound;
schematic validation rejects stale or failing generated evidence.

## 2026-07-21 — Select passive Q1 cooling and LM74930-Q1 load-dump cutoff

Decision: accept ADR-0018. Fix Q1 as `IAUT300N08S5N012ATMA2`, 80 V TOLL,
with passive PCB-copper and metal-enclosure cooling only. At 40 A the generated
hot-loss bound is 4.032 W; the 125 degC ambient / 150 degC target requires a
complete thermal path of no more than 6.20 K/W. PBREL-006 closes as a
design-selection gate while extraction and PB-BENCH-010 remain later stages.

Decision: replace the failed single-SM8S33AHM3/I load-dump branch with
`LM74930QRGERQ1` hard cutoff, 42.2 kOhm + 42.2 kOhm / 1.00 kOhm OV divider, protected 80 V
Q1 on DGATE, and raw-side `IAUTN15S6N025ATMA1` 150 V Q2 on HGATE. Generated
evidence gives 48.99-54.89 V cutoff and explicit load disconnection.

Correction: the initial 0.0327 J to 0.490 J avalanche comparison did not prove
linear-mode SOA. Replace it with 16 cold/hot ISO corner rows, a conservative
101 V / 40 A / 10 us SOA screen derated to 66.67 A at 125 degC, and generated
Q2 conduction evidence: 4.000 W at the 25 degC maximum, 7.200 W hot, and a
3.47 K/W post-layout full-path limit. PBREL-007 remains Conditional overall;
its closed pre-layout stage preserves `LAYOUT-ONLY`. Extracted overshoot/SOA
and PB-BENCH-004 remain post-layout/prototype gates. Production and field use
remain NO-GO.

## 2026-07-21 — Correct PBREL-007 hot-start SOA evidence

Correction: link Q2 load-dump initial junction temperature to continuous
heating. The 7.200 W hot loss through the 3.47 K/W target path raises Q2 from
125 degC ambient to 150 degC before the pulse. Generated evidence now covers
24 source/thermal combinations including that hot steady-40 A state.

Correction: do not add the LM74930-Q1 7 us OV deglitch interval to linear-mode
time. Q2 remains fully enhanced during deglitch. The separate provisional
transition uses 40 nC maximum Qgd divided by 128 mA minimum HGATE sink, giving
0.31 us. The conservative graph-derived 101 V / 1 us screen derates to
83.33 A at 150 degC, or 2.08x at 40 A.

Decision: the numerical screen is not final pre-layout proof because Qgd is
design-specified at 75 V / 123 A and the SOA current is digitized from a graph.
PBREL-007 pre-layout returns to `Conditional`; aggregate PB-100 authorization
is `BLOCKED` until a qualified maximum-bound 101 V / 40 A trajectory exists.
No `.kicad_pcb` or manufacturing output is authorized.

## 2026-07-21 — Add complete Q2 charge envelope and protected-node peak budget

Correction: the 0.31 us Qgd interval covers only Miller VDS rise. Add a
separate post-Miller current-fall phase conservatively bounded by the complete
52 nC maximum Qgs. At the 128 mA minimum HGATE sink the phases are 0.31 us and
0.41 us, for a 0.72 us provisional linear-transition envelope. The existing
101 V / 1 us graph-derived SOA screen remains 2.08x at 150 degC initial Tj.

Correction: 54.89 V is the maximum OV threshold, not the maximum protected-node
voltage. Expand the generated matrix to 48 rows with the TI 5-10 ms rise-time
range. At 101 V / 5 ms the conservative input rise during the 7 us delay is
0.1225 V. Adding a 4.50 V pre-layout commutation allocation produces a
59.52 V protected-node peak budget and 20.48 V margin to the selected 80 V Q1.

Decision: these calculations do not close PBREL-007 because Infineon specifies
Qgd/Qgs at 75 V / 123 A as design values not subject to production testing.
PBREL-007 remains `Conditional`, aggregate PB-100 remains `BLOCKED`, and no
layout or manufacturing output is authorized until a qualified maximum-bound
101 V / 40 A / 150 degC VDS-rise and ID-fall trajectory exists.

## 2026-07-21 — Define the Q2 manufacturer-qualification contract

Decision: do not mislabel the public Q2 datasheet values or a typical SPICE
model as the required production maximum. The public 40 nC Qgd and 52 nC Qgs
limits are specified at 75 V / 123 A, while the release corner is 101 V / 40 A
from an initial Q2 junction temperature of 150 degC. Infineon's official MOSFET
simulation guidance also states that its models describe typical devices and
do not replace hardware evaluation.

Decision: request a traceable Infineon application-engineering artifact for
the exact `IAUTN15S6N025ATMA1`. The acceptance contract fixes the LM74930-Q1
10.0-14.5 V initial HGATE drive range, 128 mA minimum sink, separate 7 us
fully-enhanced deglitch, and ten events at 60 s spacing. Acceptance requires a
process/temperature/lot-covered paired `VDS(t)` / `ID(t)` envelope, maximum
Miller VDS-rise and post-Miller ID-fall times, residual-current criterion,
guardband, and hot linear-mode SOA confirmation.

Result: `PB-100-q2-maximum-bound-qualification.csv` machine-records the known
inputs and missing vendor outputs; `PB-100-q2-vendor-support-request.md`
contains the reviewed support request. Until a traceable response is received
and reviewed, PBREL-007 stays Conditional, aggregate PB-100 stays `BLOCKED`,
and PCB layout, prototype manufacturing, production, and field use remain
unauthorized. No second developer is required.
