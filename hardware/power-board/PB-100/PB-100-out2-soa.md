# PB-100 OUT2 SOA and Inrush Envelope

Status: Preliminary schematic-planning input

This document closes the PB-FRZ-002 planning blocker by defining the OUT2
startup and inrush envelope that the schematic must support or explicitly reject.
It does not freeze the final OUT2 MOSFET.

OUT2 remains a generic output. The compressor case is only the BMW K25 reference
worst-case sizing load.

## Source assumptions

- OUT2 target fuse: 20 A.
- OUT2 default current limit: 18 A.
- BUK7S1R2-80M 80 V LFPAK88 is the selected output MOSFET.
- The conservative hot thermal estimate uses 2.4 mOhm and gives about 0.78 W
  at the 18 A continuous OUT2 limit before switching and copper losses.
- The Nexperia data sheet provides the selected package, thermal and SOA
  evidence; application-specific motor inrush and fault timing still require
  reproducible analysis or bench evidence.

## Schematic decision

Use the selected BUK7S1R2-80M for OUT2 only after the detailed SOA review
confirms the startup envelope and short-circuit fault timing.

The schematic must preserve an escape path for OUT2:

- IAUTN08S5N012L 80 V TOLL or BUK7J2R4-80M 80 V LFPAK56E through a controlled
  non-drop-in substitution review; or
- lower OUT2 current/inrush limit through a future ADR if hardware margin is not
  proven.

OUT2 must not rely on indefinite linear current limiting during compressor
startup or short-circuit events. The high-side controller must either drive the
MOSFET fully enhanced for allowed startup pulses or fault/latch off inside the
validated FET SOA.

## Preliminary envelope

Detailed envelope CSV:
`hardware/power-board/PB-100/PB-100-out2-soa-envelope.csv`.

| Case | Current | Duration | Preliminary interpretation |
|---|---:|---:|---|
| Continuous configured limit | 18 A | continuous | Board thermal validation required |
| Compressor startup pulse | 40 A | 1 s | Allowed only if FET is fully enhanced and SOA is confirmed |
| Fast inrush transient | 80 A | 100 ms | Allowed only if fuse, controller, and FET pulse SOA are confirmed |
| Hard short current limit | 18 A current-limit target | 10 ms maximum before fault | Linear-mode stress must be bounded by controller fault timing |

These are schematic-review targets, not user-configurable output limits.

## Schematic requirements

- Provide OUT2 current-limit/fault behavior that can be verified on the bench.
- Keep OUT2 gate drive strong enough for fully enhanced operation during allowed
  startup pulses.
- Place high-current copper and thermal sensing so OUT2 can be derated before
  sustained overheating.
- Validate OUT2 inductive and compressor-motor transient behavior with the
  selected clamp/flyback strategy.
- Do not release PCB layout until OUT2 SOA is checked against the selected FET
  data sheet and controller fault timing.

## Evidence links

- Nexperia BUK7S1R2-80M data sheet:
  https://assets.nexperia.com/documents/data-sheet/BUK7S1R2-80M.pdf
- Historical SIDR626LDP evidence is retained only to explain rejection of the
  former 60 V path: https://www.vishay.com/docs/77277/sidr626ldp.pdf
