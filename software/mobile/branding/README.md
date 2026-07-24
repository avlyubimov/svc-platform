# Mobile branding

Startup animation behavior is platform-neutral. The runtime-loaded
`brand-pack-index-v1.json` selects a profile, while
`vehicle-brands/vehicle-brands-v1.json` resolves its manufacturer by stable
`brandId`. The profile keeps `brandId`, `model`, `generation`, and `year` as
separate fields. BLE, OTA, CAN, diagnostics, and safety logic must not inspect
a brand identifier.

The personal profile defaults to `bmw-r1200gs-k25-personal` and theme
`svc-boxer-blue`. On the standard dark startup surface, clients render the
catalog's `logo-on-dark.svg`. A catalog `preferredAsset` overrides that
default; the BMW K25 profile therefore uses
`vehicle-brands/brands/bmw/bmw-roundel-1997-2020.svg`. A combination mark or
wordmark is optional. When absent, clients render the catalog display name as
ordinary text.

Both clients fall back to `generic-automotive` and the committed SVC artwork if
a profile or its required logo cannot be resolved. Builds never download brand
assets. `branding/local` remains ignored for future owner-only custom packs,
but the committed BMW profile does not depend on it.

`svc/svg/svc-app-icon.svg` is the source identity for the phone launcher, store
listing, CarPlay, and Android Auto icon. Platform-ready exports live under
`svc/platform`. Manufacturer marks are phone startup/profile decoration only
and must never replace the SVC application identity or the neutral black system
launch surface.

Adding a manufacturer does not require Swift or Kotlin edits: add a complete
catalog directory, preserve its source metadata and notices, and reference the
stable ID from a schema-valid profile. Every committed catalog entry must have
`brand.json`, `logo-source.svg`, `logo-on-dark.svg`, `logo-on-light.svg`, and
`logo-accent.svg`; protocol validation parses every SVG as XML.

Preserve `vehicle-brands/THIRD_PARTY_NOTICES.md`,
`vehicle-brands/third-party/simple-icons/LICENSE.md`,
`vehicle-brands/third-party/simple-icons/DISCLAIMER.md`, and the source URL in
every `brand.json`. Before a public store release, confirm redistribution and
trademark permissions for every bundled manufacturer mark.

The full animation runs only in the phone application. CarPlay and Android Auto
keep their host-controlled launch behavior and information-only templates.
