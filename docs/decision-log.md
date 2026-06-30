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
