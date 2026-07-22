# ADR-0016: PB-100 Load-Dump Design Requirement

Status: Accepted — release authorization superseded in part by ADR-0019

Date: 2026-07-21

## Context

PBREL-007 was closed using a 100 V, 10/1000 us pulse and a peak-voltage-only
screen. That waveform does not represent the 40-400 ms duration of the ISO
16750-2 12 V load-dump envelope and therefore does not prove TVS energy or
thermal survival. The former 59.45 V result also left only 0.55 V to the
LM74700-Q1 60 V recommended input ceiling before full tolerance, dynamic
resistance, self-heating, layout parasitics, and measurement uncertainty were
known.

The Product Owner directed a corrective review. This ADR changes the PB-100
protection requirement and evidence gate; it does not change the frozen
vehicle-agnostic power-board architecture.

## Decision

PB-100 load-dump design evidence shall cover the ISO 16750-2 Test A 12 V design
envelope at all corners of:

- open-circuit source voltage `Us = 79-101 V`;
- source resistance `Ri = 0.5-4 ohm`;
- pulse duration `td = 40-400 ms`;
- cold and hot initial junction conditions;
- ten pulses with 60 s spacing for the final qualification plan.

Pre-layout evidence shall calculate TVS current, clamp voltage, instantaneous
power, absorbed energy, transient thermal impedance, predicted junction
temperature, tolerance effects, temperature coefficient, dynamic resistance,
self-heating, and explicit parasitic/measurement uncertainty.

The protected LM74700-Q1 node shall retain at least `5 V` modeled margin to the
60 V recommended ceiling at every accepted corner. The 65 V absolute maximum
is a destructive boundary, not design margin. Passing the 80 V MOSFET voltage
class does not close controller or TVS thermal evidence.

ADR-0018 rejects the current SM8S33AHM3/I branch as the active energy sink and
selects LM74930-Q1 hard cutoff with a 150 V raw-side MOSFET. The PBREL-007
pre-layout stage is now closed by generated cutoff and transient-SOA evidence.
Extracted-loop review and PB-BENCH-004 remain separate post-layout and
prototype-qualification stages under ADR-0017. PBREL-006 retains accepted
pre-layout Q1 selection evidence; copper/thermal extraction and PB-BENCH-010
remain its separate post-layout and prototype-qualification stages.

## Consequences

- The former 10/1000 us result remains historical rejected evidence only.
- A TVS with adequate peak clamp but inadequate energy or transient thermal
  performance cannot close PBREL-007.
- TVS arrays, staged suppression, higher-power parts, or controller isolation
  may be compared without removing required capabilities; any architecture
  change still needs Product Owner approval and another ADR.
- ADR-0019 authorizes controlled Rev.1 EVT layout and a five-board EVT package
  after routed-board DRC and pre-fab review even while PBREL-007 remains
  Conditional. The load-dump evidence in this ADR blocks
  `PRODUCTION-RELEASE`, not `EVT-LAYOUT-AUTHORIZED` or a reviewed
  `EVT-FAB-AUTHORIZED` package. Production and general field release remain
  prohibited until bench, motorcycle, Rev.2 and normal production gates close.

## Evidence

- TI automotive load-dump application brief:
  https://www.ti.com/lit/ab/snoaaa1/snoaaa1.pdf
- Vishay SM8S33AHM3/I datasheet:
  https://www.vishay.com/docs/98647/sm8s85ahm3.pdf
- TI LM74700-Q1 datasheet:
  https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf
- `hardware/power-board/PB-100/PB-100-transient-margin-evidence.csv`
