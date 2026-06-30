# ADR-0011: PB-100 low-current outputs use external-controller baseline

## Status
Accepted

## Context
ADR-0010 allowed low-current outputs to use integrated smart high-side switches
when thermal review confirmed margin and the protected battery rail was clamped
within their voltage limits.

Preliminary protection validation found that an SM8S33A-class input TVS can
clamp above the voltage class of 40 V integrated smart switches. Adding a
separate lower-clamp rail or local clamp network for only three channels adds
another protection domain and still requires tight load-dump validation.

For Rev.1, protection robustness and schematic simplicity have higher priority
than reducing the low-current channel BOM.

## Decision
Use the external smart high-side controller plus external 60 V or higher
N-MOSFET architecture for all PB-100 Rev.1 output channels, including OUT5,
OUT8, and OUT9.

Low-current channel limits remain unchanged:

- OUT5: 5 A fuse target, 4 A current limit.
- OUT8: 5 A fuse target, 4 A current limit.
- OUT9: 5 A fuse target, 4 A current limit.

Integrated smart high-side switches remain deferred alternatives only. They may
be reconsidered after a future ADR accepts a lower-clamp rail, local protection
network, or a smart-switch family with suitable transient rating.

## Consequences
PB-100 Rev.1 avoids a direct 40 V smart-switch rail behind an SM8S33A-class TVS.
This closes the immediate low-current output protection conflict.

The schematic uses a more uniform output-stage architecture across all 10
channels, which simplifies protection assumptions, telemetry mapping, and spare
channel behavior.

The tradeoff is higher BOM cost, board area, and controller/MOSFET count for
low-current channels. Schematic freeze still requires MOSFET SOA, thermal,
current-sense, and assembly-source validation for every output class.
