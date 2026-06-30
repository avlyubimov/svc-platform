# ADR-0010: PB-100 power-path candidate strategy

## Status
Accepted

## Context
PB-100 uses generic high-side outputs. The output set includes one 18 A channel,
six 8-12 A channels, and three 4 A channels.

Integrated smart high-side switches simplify diagnostics, but thermal margin can
be tight on 8-18 A channels in an enclosed motorcycle controller. External
N-channel MOSFET high-side controllers require more parts, but allow MOSFET SOA,
thermal, and package choices to be sized per output class.

## Decision
Use this schematic-planning strategy:

- High-current and medium-current channels use an external smart high-side
  controller with an external 60 V or higher N-channel MOSFET.
- Low-current channels may use integrated automotive smart high-side switches
  when thermal review confirms margin and the protected battery rail is clamped
  within their voltage limits.
- Input reverse-polarity protection uses an automotive ideal-diode controller
  with an external N-channel MOSFET.
- Input transient protection starts from SM8S33A-class load-dump TVS sizing.

Candidate MPNs are tracked in
`hardware/power-board/PB-100/PB-100-power-path-candidates.csv`.

This is not a final MPN lock. Final schematic selections still require
JLCPCB/PCBWay assembly-class confirmation, MOSFET SOA review, thermal review,
and TVS clamp-voltage validation.

If the input transient clamp cannot be kept within the voltage rating of
integrated smart switches, low-current outputs must fall back to the external
high-side controller plus MOSFET architecture.

## Consequences
The design keeps thermal and SOA margin for compressor, heated-seat, and lighting
loads at the cost of more schematic complexity and board area.

Low-current channels remain simpler where integrated smart switches are
appropriate.
