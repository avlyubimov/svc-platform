# PB-100 Input Reverse-Protection MOSFET Strategy

Status: Schematic-planning input

This document resolves the PB-FRZ-003 planning blocker by selecting a thermal
strategy for the LM74700-class input ideal-diode MOSFET. It does not freeze the
final MPN.

## Problem

The initial thermal table used the same 2.1 mOhm MOSFET class as the output
channels for the 40 A board input path. At 40 A with a conservative 2.0
temperature multiplier, that produces about 6.72 W in a single package:

```text
P = I^2 * Rds * multiplier
P = 40^2 * 0.0021 * 2.0 = 6.72 W
```

That is too high for the default input reverse-protection assumption.

## Decision

Use a dedicated low-Rds input MOSFET strategy for Rev.1 schematic planning:

| Strategy | Rds assumption | 40 A estimate | Status |
|---|---:|---:|---|
| IAUTN06S5N008ATMA1-class 60 V TOLL MOSFET | 0.76 mOhm | 2.43 W | Preferred pending assembly-source check |
| BUK7S1R2-80M-class 80 V LFPAK88 MOSFET | 1.2 mOhm | 3.84 W | Higher-voltage alternate |
| Dual SIDR626LDP-class PowerPAK MOSFETs in parallel | 2.1 mOhm each | 1.68 W per FET | Factory-assembly fallback if TOLL/LFPAK88 sourcing is weak |

The Rev.1 schematic must not use a single 2.1 mOhm PowerPAK-class MOSFET for the
40 A input reverse-protection path unless the board current target is lowered by
ADR or a later thermal model proves acceptable margin.

## Source snapshot

- Infineon IAUTN06S5N008: 60 V automotive MOSFET, TOLL package, 0.76 mOhm max
  Rds(on), active/preferred status.
- Nexperia BUK7S1R2-80M: 80 V automotive LFPAK88 MOSFET, 1.2 mOhm class,
  AEC-Q101-qualified data sheet.
- SIDR626LDP-T1-RE3 remains useful as an output MOSFET and as a parallel input
  fallback because it already has an LCSC candidate entry.

## Schematic requirements

- Use an input MOSFET footprint strategy that can support either the preferred
  low-Rds device or a documented alternate.
- Keep source/drain copper sized for at least the 40 A board-level current
  budget before thermal derating.
- Place input current measurement so it measures the board input current used by
  firmware current-budget enforcement.
- Validate transient voltage margin against the selected TVS clamp.
- Recheck JLCPCB/PCBWay assembly support for TOLL, LFPAK88, or fallback
  PowerPAK before schematic freeze.

## Evidence links

- Infineon IAUTN06S5N008 product page: https://www.infineon.com/part/IAUTN06S5N008
- Infineon IAUTN06S5N008 data sheet: https://www.infineon.com/dgdl/Infineon-IAUTN06S5N008_Datasheet-DataSheet-v02_00-EN.pdf?fileId=8ac78c8c85ecb3470186314156af0dfa
- Nexperia BUK7S1R2-80M data sheet: https://assets.nexperia.com/documents/data-sheet/BUK7S1R2-80M.pdf
- Nexperia power-switch application note: https://www.nexperia.com/applications/interactive-app-notes/IAN50020_Power_Switch_MOSFETs
