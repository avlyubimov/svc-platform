# PB-100 Symbol Open Items

Status: No pending schematic-symbol items; no PCB layout

This file tracks symbol risks that are intentionally not marked as fully closed.

## Open items

| Symbol key | Concrete symbol | Status | Remaining close evidence |
|---|---|---|---|
| `INPUT_REVERSE_FET` | `PB100_POWER_NMOS_TOLL_80V` | Evidence captured; exact 80 V TOLL value and footprint selected; generated 40 A bound passes | Final plane/polygon/bus review remains a layout gate |

## Rules

- Do not start PCB placement until the separate schematic-freeze gate closes.
- During layout, prove the Q1 plane/polygon/bus thermal path and coupon rules before
  manufacturing release; that physical gate is not a reopened PBREL blocker.
- Keep both documented 80 V alternatives available. They are sourcing escape paths,
  not unreviewed drop-in substitutions for the selected schematic.
