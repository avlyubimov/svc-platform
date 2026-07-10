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
