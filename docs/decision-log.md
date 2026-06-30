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
