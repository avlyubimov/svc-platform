# ADR-0023: Mobile BrandPacks and startup presentation

Status: Accepted
Date: 2026-07-23

## Decision

SVC Mobile uses a platform-neutral BrandPack contract for phone-only startup
presentation. The personal reference pack is `bmw-r1200gs-k25-personal` with
the `svc-boxer-blue` theme. Both clients load the same runtime profile catalog,
vehicle-brand catalog, asset paths, and timeline. Profiles keep `brandId`,
`model`, `generation`, and `year` as separate fields and resolve manufacturers
through the stable IDs in `vehicle-brands-v1.json`. Adding a profile or brand
does not require duplicated Swift and Kotlin constants.

The standard dark startup uses `logo-on-dark.svg`. A catalog may nominate a
`preferredAsset`; the 2007 BMW K25 profile uses the 1997–2020 roundel. A
wordmark or combination mark is optional and falls back to the catalog display
name as text. A missing profile or required logo selects the committed generic
SVC fallback. Neither client downloads brand resources at runtime.

The application, phone launcher, CarPlay, and Android Auto identity is always
SVC. Manufacturer marks are limited to the selected post-launch phone
presentation and never replace the SVC app icon or the neutral system launch
surface.

The normal timeline is 2100 ms and contains only screen-on glow, identity,
vehicle, tagline, and a continuous dashboard reveal. Diagnostics run in
parallel and appear after startup. Critical state may reduce startup to 500 ms.
Animation disable and reduced-motion paths never block application readiness.

The last available primary screen is stored locally. Unknown or unavailable
destinations resolve to Dashboard. CarPlay and Android Auto do not play the
phone startup animation.

## Consequences

Brand identity remains configuration rather than vehicle-specific BLE, OTA,
CAN, or safety code. The committed SVC pack provides the deterministic
fallback, launcher/store artwork, and projected-display identity. The
manufacturer catalog provides optional phone presentation only.

Every catalog entry carries its source metadata and standard SVG variants.
Third-party notices, upstream license/disclaimer files, and per-brand source
URLs remain committed with the assets. Packaging a manufacturer mark does not
grant trademark rights, so public-store redistribution requires a separate
rights review. The common timing and semantic fields support additional
motorcycle and automotive profiles without changing mobile source code or
device protocols.
