# ADR-0023: Mobile BrandPacks and startup presentation

Status: Accepted
Date: 2026-07-23

## Decision

SVC Mobile uses a platform-neutral BrandPack contract for phone-only startup
presentation. The personal reference pack is `bmw-r1200gs-k25-personal` with
the `svc-boxer-blue` theme. Missing owner-provided BMW SVG resources select the
generic SVC fallback; resources are never downloaded or committed.

The normal timeline is 2100 ms and contains only screen-on glow, identity,
vehicle, tagline, and a continuous dashboard reveal. Diagnostics run in
parallel and appear after startup. Critical state may reduce startup to 500 ms.
Animation disable and reduced-motion paths never block application readiness.

The last available primary screen is stored locally. Unknown or unavailable
destinations resolve to Dashboard. CarPlay and Android Auto do not play the
phone startup animation.

## Consequences

Brand identity remains configuration rather than vehicle-specific BLE, OTA,
CAN, or safety code. BMW trademarks and other licensed assets remain local to
the owner's build. The common timing and semantic fields can support Honda,
Yamaha, KTM, Ducati, Volkswagen, Toyota, and generic profiles without changing
device protocols.
