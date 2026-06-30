# Roadmap

## Phase 0 — Architecture
Status: Complete

- Project constitution
- Architecture review
- ADRs
- Requirements
- BOM strategy

## Phase 1 — PB-100 Power Board
Status: In progress

- Schematic package
- Schematic freeze checklist
- KiCad schematic scaffold
- Layout/manufacturing artifact blocker
- Schematic capture
- PCB
- Gerber
- Factory BOM
- Garage BOM
- Bench test

## Phase 2 — LB-100 Logic Board
- MCU
- CAN
- BLE
- SD
- sensors
- RTC/FRAM
- bench test

## Phase 3 — FB-100 Front Board
- USB-C service
- status LEDs
- service button

## Phase 4 — Firmware MVP
Status: In progress

- output control
- event-derived rule conditions
- battery protection
- role-mapped rule actions
- CAN read-only logger
- config JSON schema

Current host-tested services:

- Configuration Validator
- Event Bus
- Event Dispatcher
- Power Budget
- Output Manager
- Battery Protection
- CAN Safety Guard
- System Safety Coordinator
- Role Resolver
- Rule Engine skeleton
- Rule condition evaluator
- In-memory rule runner
- Rule text parser
- Rule text-to-runner compile helper
- Output Manager PWM duty-cycle state
- Telemetry Snapshot

## Phase 5 — BMW K25 integration
- harness
- CAN capture
- fog light rules
- reference vehicle testing
