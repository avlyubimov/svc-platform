# ADR-0021: Fog-switch common and primary-protection ownership

## Status

Accepted — Product Owner corrective direction on 2026-07-22.

This ADR amends the fog-switch electrical boundary in ADR-0020. All other
ADR-0020 decisions remain in force.

## Context

The owner-provided double three-wire switch has one common conductor and two
independent contacts, but its contact polarity, electronics, illumination and
wire colors have not yet been measured. Naming contact 1 `SW_GND` prematurely
committed the harness to a dry-contact implementation. The handlebar cable also
enters the PB-100 enclosure before its two signals cross JPB1 to LB-100, so a
raw-line protector located only on LB-100 leaves the PB trace and board-to-board
connector exposed to the external transient.

## Decision

- Contact 1 is `SW_COMMON`; contact 2 is `FOG_A_SW_IN`; contact 3 is
  `FOG_B_SW_IN`. Wire colors remain unassigned until offline measurement.
- PB-100 owns the cable-entry connector termination and the primary dual-line
  automotive ESD/EMI suppressor. Its return is routed directly to the local PB
  ground near the cable entry and does not traverse JPB1.
- The default `FOG_DRY_CONTACT` assembly fits a zero-ohm link from
  `SW_COMMON` to `GND` and leaves the 12 V common source DNP.
- The alternate `FOG_12V_ACTIVE_HIGH` assembly removes the ground link and
  fits a mutually exclusive zero-ohm link from `SW_COMMON` to
  `SW_12V_FUSED`. The fused source remains DNP until offline measurement proves
  that the switch requires or emits a protected 12 V signal.
- LB-100 retains two independent series resistors, RC filters, 4.3 V clamps,
  Schmitt buffers and optional transistor conversion networks. No external
  conductor is connected directly to an STM32 pin.
- PA8 remains `FOG_A_SW_IN_MCU`; PA9 remains `FOG_B_SW_IN_MCU`. Output Manager
  remains authoritative, and neither input directly controls a power channel.
- `EVT-FAB-AUTHORIZED` remains blocked until the actual switch state table,
  mutually exclusive population, connector pinout, pulse capability and routed
  return path are reviewed. This does not revoke `EVT-LAYOUT-AUTHORIZED`.

## Selected parts for EVT routing

- Primary two-line suppressor: TI `ESD2CANFD24DBZRQ1`, with Nexperia
  `PESD2IVN24-T` as the reviewed alternative after pinout and pulse review.
- Optional common-source fuse: Littelfuse `nanoASMDC010F`, AEC-Q200, 0.10 A
  hold and 60 V maximum, with the automotive Bourns `MF-MSMF` 60 V family as
  the alternative after exact order-code review.
- External sealed connector: TE Connectivity DEUTSCH
  `DTM04-3P`/`DTM06-3S`; the board terminates its short enclosure pigtail at
  `JFOG1` adjacent to the primary protector.
- PCB designators are `D_FOG1` for the PB primary suppressor,
  `R_FOG_GND` for the default common-to-ground link, `R_FOG_12V` for the
  alternate common-source link and `F_FOG_12V` for its DNP protected supply.

Part selection authorizes footprints and routing only. Purchase-time stock,
exact alternative pinout, pulse margin and supplier assembly compatibility are
rechecked at `EVT-FAB-REVIEW`.

## Consequences

The same PCB supports either measured switch type without copper rework, but
the incompatible common links cannot be populated together. PB-100 absorbs
the first external transient at the cable boundary; LB-100 provides the local
MCU-safe boundary. The external loom and production release remain blocked
until measurement and EVT evidence exist.
