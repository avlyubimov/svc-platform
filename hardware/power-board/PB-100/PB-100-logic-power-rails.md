# PB-100 Logic Power Rails

Status: Schematic-planning input

This document defines the PB-100 logic-power strategy for schematic planning. It
does not freeze the final regulator MPN.

## Decision

PB-100 generates a protected `PB_5V_OUT` rail from the protected battery input
and exports it to LB-100 through `JPB1`.

Rev.1 preferred regulator family:

- LM5164-Q1 class, 6-100 V input, 1 A synchronous buck, automotive qualified.

Higher-current alternate:

- LM5013-Q1 class, 6-100 V input, 3.5 A non-synchronous buck, automotive
  qualified.

Conditional alternate:

- TPS54360B-Q1 class, 60 V input, 3.5 A buck. This remains conditional because
  it has less margin against an SM8S33A-class TVS clamp than the 100 V families.

## Rail ownership

| Rail | Owner | Direction | Purpose |
|---|---|---|---|
| `PB_5V_OUT` | PB-100 | PB-100 to LB-100 | Protected logic supply for LB-100 and PB-side low-power circuitry |
| `LB_3V3_IO` | LB-100 | LB-100 to PB-100 | Logic-level reference for PB-side control and status signals |
| `PB_PWR_GOOD` | PB-100 | PB-100 to LB-100 | Logic-power validity status |

`PB_5V_OUT` is not an accessory output and must not power USB-C accessory loads.
Accessory power remains on generic protected outputs such as `OUT1`.

## Initial 5 V budget

Detailed budget CSV:
`hardware/power-board/PB-100/PB-100-logic-power-budget.csv`.

The initial 1 A plan reserves current for LB-100 logic, PB-side controllers and
sensors, telemetry pullups, and expansion margin. If schematic allocation exceeds
1 A, Rev.1 must move to the LM5013-Q1-class 100 V higher-current buck before
choosing a 60 V regulator family.

## Cold-crank and brownout behavior

- Normal input target remains 6-18 V.
- The 5 V rail is designed around regulator families that can operate from 6 V
  input.
- Below the regulator operating range, PB-100 and LB-100 must fail safe with all
  outputs off.
- Hold-up capacitance is a schematic-review item, not a PCB-layout decision.

## Schematic requirements

- Feed the buck after input reverse protection and transient protection.
- Connect regulator power-good to `PB_PWR_GOOD`.
- Keep `OUT1` through `OUT10` control defaults off when `PB_5V_OUT` or
  `LB_3V3_IO` is absent.
- Size input/output capacitors and EMI components for motorcycle wiring.
- Keep the regulator input voltage rating compatible with the selected TVS clamp.
- Recheck JLCPCB/PCBWay assembly support before schematic freeze.

## Evidence links

- TI LM5164-Q1 product page: https://www.ti.com/product/LM5164-Q1
- TI LM5164-Q1 data sheet: https://www.ti.com/lit/ds/symlink/lm5164-q1.pdf
- TI LM5013-Q1 product page: https://www.ti.com/product/LM5013-Q1
- TI TPS54360B-Q1 product page: https://www.ti.com/product/TPS54360B-Q1
