# PB-100 C36 Bidirectional Branch

Status: Rev.1 EVT architecture accepted by ADR-0020

## Decision

`C36_BIDIRECTIONAL` is an independent harness capability connected directly to
the battery/`VBAT_RAW` domain through the manufacturer cable and a dedicated
fuse placed near the battery. It does not pass through TPS48110, OUT1 through
OUT10, the PB-100 input shunt or a one-way load switch. It therefore works with
PB-100, LB-100 and the MCU off and preserves both accessory-power and
battery-charge directions.

C36 current is excluded from the PB-100 40 A managed-output budget and from
`IIN_SENSE`, but it remains part of the motorcycle generator-energy budget.
Firmware may warn from `VBAT_SENSE` and available engine state; it cannot claim
to disconnect the branch. Rev.1 EVT measures both directions with an external
clamp or shunt. Integrated bidirectional monitoring is a Rev.2 option, not a
Rev.1 fabrication blocker. C36 is not a starter-current source.

## Alternatives

- **Selected:** manufacturer-defined direct bidirectional battery branch.
- **Rejected A:** normal TPS48110 output; the one-way path can block reverse
  charging and makes rescue charging depend on electronics state.
- **Rejected B:** MCU-controlled bidirectional switch; it adds quiescent load,
  boot dependency and a new safety-critical design before Rev.1 measurements.

## Engineering Record

- Expected service life: 10-15 years, subject to cable, fuse-holder and sealed
  connector inspection intervals.
- Operating margin: cable, fuse and connector ratings must exceed the measured
  continuous current in both directions under the installed temperature.
- Maximum junction temperature: not applicable to the passive Rev.1 branch;
  any future monitor or switch requires a separate junction-temperature record.
- Availability: the exact C36 cable and fuse requirements are rechecked before
  EVT purchase and installation.
- Automotive qualification: the external accessory is used per its vendor
  instructions; the motorcycle-side fuse, cable and sealing remain vehicle
  installation responsibilities.
- JLCPCB/PCBWay/LCSC: no factory-assembled PB component is added by Rev.1; any
  Rev.2 monitor requires sourcing and assembly compatibility review.
- Known risks: reverse polarity, unnoticed battery drain, unfused cable length,
  connector heating and misuse as a starter source. The near-battery fuse,
  vendor cable, mode guidance and bidirectional EVT measurements mitigate them.
