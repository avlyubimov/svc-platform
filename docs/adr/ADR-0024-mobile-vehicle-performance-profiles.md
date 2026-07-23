# ADR-0024: Mobile vehicle performance profiles

Status: Accepted
Date: 2026-07-23

## Decision

SVC Mobile stores vehicle performance configuration under
`software/mobile/vehicle-profiles/`, independently from manufacturer branding.
Both phone clients consume the same versioned JSON index and profile schema.

The profile owns dashboard scale and reference values such as RPM zones, idle
band, fuel capacity, gearbox count, and ice-warning threshold. BrandPack owns
logos, copy, and startup presentation. Telemetry quality, BLE state, CAN
decoding, device safety, and channel roles belong to neither profile.

Unknown technical values are explicit nulls. The Generic Motorcycle fallback
contains no assumed red zone, engine limits, gearbox count, or fuel values. The
BMW R1200GS K25 2007 profile has no rev-limiter value, so the dashboard must not
draw a limiter or cut-off marker.

## Consequences

Dashboard behavior can vary by confirmed vehicle capability without coupling
performance limits to trademarks or duplicating constants in Swift and Kotlin.
Changing a visual theme cannot change safety or performance thresholds.

The profile does not confirm CAN availability. BMW CAN remains listen-only and
signals stay unavailable until separately verified from recorded data. No
hardware, firmware, wire protocol, or Power Board architecture changes result
from this decision.
