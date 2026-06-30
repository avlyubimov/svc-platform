# PB-100 Symbol Open Items

Status: Schematic-symbol risk register; no PCB layout

This file tracks symbol work that is intentionally not marked as created.

## Open items

| Symbol key | Concrete symbol | Status | Required evidence before marking created |
|---|---|---|---|
| `INPUT_REVERSE_FET` | `PB100_INPUT_NMOS_TOLL_PRELIM` | Pending | Infineon IAUTN06S5N008 package pin evidence reviewed against the official data sheet and package drawing |

## Rules

- Do not add `PB100_INPUT_NMOS_TOLL_PRELIM` to `PB100.kicad_sym` until the pin
  evidence is reviewed.
- Do not lock the TOLL footprint or start PCB placement from this open item.
- Keep BUK7S1R2-80M LFPAK88 and dual SIDR626LDP fallback paths available until
  assembly support and 40 A thermal evidence close.
