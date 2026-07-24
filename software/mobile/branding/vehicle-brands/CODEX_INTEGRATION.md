# Codex integration brief

1. Copy this directory to `software/mobile/branding/vehicle-brands/`.
2. Keep the SVC artwork as the application, store, CarPlay and Android Auto
   icon. Manufacturer marks are phone-only startup/profile decoration.
3. Load brands from `vehicle-brands-v1.json` by stable `id`.
4. Keep `brandId`, `model`, `generation` and `year` as separate profile fields.
5. Render `logo-on-dark.svg` on the standard dark startup background.
6. For the owner's 2007 BMW K25 profile, prefer
   `brands/bmw/bmw-roundel-1997-2020.svg`.
7. Treat any wordmark/combination asset as optional. Fall back to the catalog
   display name as text.
8. Do not display a manufacturer mark in the SVC launcher icon, store listing,
   CarPlay launcher or Android Auto launcher.
9. Preserve `THIRD_PARTY_NOTICES.md`, the upstream license/disclaimer files and
   the source URL stored in every `brand.json`.
10. Add automated checks that every catalog entry has `brand.json`,
    `logo-source.svg`, `logo-on-dark.svg`, `logo-on-light.svg` and
    `logo-accent.svg`, and that every SVG parses as XML.
