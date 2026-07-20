# PB-100 Symbol Open Items

Status: No pending schematic-symbol items; no PCB layout

This file tracks symbol risks that are intentionally not marked as fully closed.

## Open items

| Symbol key | Concrete symbol | Status | Remaining close evidence |
|---|---|---|---|
| `INPUT_REVERSE_FET` | `PB100_POWER_NMOS_ESCAPE_PRELIM` | Evidence captured; 80 V value and LFPAK88 footprint selected | Factory production-status confirmation, SOA, and 40 A copper/thermal review remains open |

## Rules

- Do not start PCB placement from this open item until the 40 A thermal path closes.
- Keep the two documented 80 V alternatives available. The former 60 V TOLL and
  SIDR626LDP paths are review history, not assembly substitutions for the selected
  80 V schematic.
