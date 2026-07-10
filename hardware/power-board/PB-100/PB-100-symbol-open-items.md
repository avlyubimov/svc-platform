# PB-100 Symbol Open Items

Status: No pending schematic-symbol items; no PCB layout

This file tracks symbol risks that are intentionally not marked as fully closed.

## Open items

| Symbol key | Concrete symbol | Status | Remaining close evidence |
|---|---|---|---|
| `INPUT_REVERSE_FET` | `PB100_INPUT_NMOS_TOLL_PRELIM` | Evidence captured | Footprint drawing, assembly support, and 40 A copper/thermal review remain open |

## Rules

- Do not lock the TOLL footprint or start PCB placement from this open item.
- Keep BUK7S1R2-80M LFPAK88 and dual SIDR626LDP fallback paths available until
  assembly support and 40 A thermal evidence close.
