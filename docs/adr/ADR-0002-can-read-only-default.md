# ADR-0002: Vehicle CAN is read-only by default

## Status
Accepted

## Context
BMW K25 CAN is shared by critical modules such as ZFE, ABS, DME, KOMBI.

## Decision
SVC will only listen to vehicle CAN by default. CAN TX to vehicle network is physically disabled by solder jumper/hardware gate.

## Consequences
Low risk to motorcycle electronics. Future CAN TX requires explicit ADR and hardware enable.
