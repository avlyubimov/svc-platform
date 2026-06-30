# ADR-0006: PB-100 baseline requirements

## Status
Accepted

## Context
PB-100 is the long-lifecycle board. It carries the highest electrical,
thermal, wiring, and manufacturing risk in the SVC platform.

## Decision
PB-100 will provide at least 10 generic protected outputs with per-channel fuse,
switching, current measurement, overcurrent protection, thermal derating, fault
lockout, and configuration-based role assignment.

PB-100 requirements are tracked in
`docs/requirements/pb-100-requirements.md`. Future changes to PB-100 output
count, protection model, role-mapping model, or vehicle-CAN safety behavior
require a new ADR.

## Consequences
Architecture and firmware can evolve around a stable power-stage contract.
Schematic planning may begin only after these requirements are accepted, but PCB
layout remains blocked until architecture freeze.
