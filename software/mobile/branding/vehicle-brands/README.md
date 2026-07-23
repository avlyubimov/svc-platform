# SVC Vehicle Brand Icons

Optional manufacturer marks for the phone-only vehicle-profile startup
presentation. These files never replace the SVC application icon, store
artwork, CarPlay icon or Android Auto icon.

## Catalog

- 13 motorcycle brands;
- 17 car brands;
- BMW is shared by both categories;
- every brand has a stable ID, display name, category and accent color.

`vehicle-brands-v1.json` is the machine-readable catalog. A vehicle profile
references a brand ID and separately supplies model, generation and year.

For Simple Icons entries:

- `logo-source.svg` is the upstream single-color source;
- `logo-on-dark.svg` is a white startup-safe variant;
- `logo-on-light.svg` is a black light-background variant;
- `logo-accent.svg` uses the catalog accent color.

Selected Wikimedia Commons entries retain their original SVG as
`logo-source.svg`; derived display variants are generated only when the source
can be safely normalized.

Use `logo-on-dark.svg` for the standard dark startup animation. If a profile
needs the manufacturer's original colors, use `logo-source.svg` or a named
additional asset instead.

## BMW K25 personal profile

`brands/bmw/bmw-roundel-1997-2020.svg` is the color roundel corresponding to
the 1997–2020 identity period and is appropriate for the 2007 K25 personal
profile. The public SVC application icon remains unchanged.

The BMW Motorrad combination mark is included as an optional additional asset.
If it is absent in a downstream build, render the manufacturer name as ordinary
text rather than failing the animation.

## Legal boundary

SVC does not claim ownership of manufacturer names or marks. The Simple Icons
package is distributed under CC0-1.0, but its disclaimer explicitly notes that
individual brand marks may have separate copyright, licensing and trademark
restrictions. Wikimedia Commons file pages likewise identify trademark
restrictions.

Keep `THIRD_PARTY_NOTICES.md`, source URLs and the pinned Simple Icons version
with redistributed assets. For a public store release, confirm permission for
every bundled brand or move the catalog to user-installed local brand packs.
