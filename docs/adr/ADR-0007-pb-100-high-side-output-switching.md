# ADR-0007: PB-100 uses high-side output switching

## Status
Accepted

## Context
Vehicle accessories normally share chassis or battery negative return paths.
Switching the low side can leave loads permanently connected to battery positive
and can create confusing fault behavior through shared grounds, harnesses, or
mounting points.

PB-100 outputs must behave like automotive body-controller outputs: protected,
diagnosable, generic, and safe by default.

## Decision
PB-100 generic outputs will use high-side switching.

Preferred implementations:
- Smart high-side switches for lower-current channels where thermal limits fit.
- External N-channel MOSFET high-side controllers for higher-current channels.

Each output still requires a user-serviceable fuse, current measurement or
current-sense output, overcurrent protection, thermal derating or shutdown
strategy, fault reporting, and safe default-off behavior.

## Consequences
Loads can keep normal ground wiring, diagnostics are easier to reason about, and
fault handling matches common automotive practice.

High-current channels require careful thermal design, MOSFET SOA review, and
component-family verification before schematic freeze.
