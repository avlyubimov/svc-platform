# SVC Brand Pack

Original identity for **SVC — Smart Vehicle Controller**.

The emblem combines three ideas:

- two protective controller rails;
- an electrical heartbeat/control signal;
- two road lanes converging toward the controller.

It is intentionally independent from BMW and other vehicle-manufacturer marks.
Use SVC for the application icon, store listing, website, documentation and
generic startup fallback. Vehicle logos belong only to optional vehicle-profile
startup presentations.

## Master files

- `svg/svc-emblem-color.svg` — primary transparent emblem.
- `svg/svc-emblem-white.svg` — dark-background and laser-marking version.
- `svg/svc-emblem-black.svg` — single-color print and PCB silkscreen version.
- `svg/svc-wordmark-horizontal-dark.svg` — light-background wordmark.
- `svg/svc-wordmark-horizontal-light.svg` — dark-background wordmark.
- `svg/svc-app-icon.svg` — application/store icon master.
- `svg/svc-startup-lockup.svg` — generic startup fallback.

## Rules

- Keep the emblem proportions unchanged.
- Keep clear space of at least 12.5% of the emblem width.
- Do not rotate, skew, outline or recolor individual pieces.
- Use the black or white single-color version below 32 px or on PCB silk.
- The application icon is always SVC, even when a BMW or other vehicle profile
  supplies the phone-only startup animation.

## Repository placement

Recommended target:

```text
software/mobile/branding/svc/
```

The generated PNG directory contains common iOS, Android, web and documentation
sizes. The SVG masters remain the source of truth.

## Origin

The initial visual direction was produced with the built-in OpenAI image
generation tool and then redrawn as deterministic project-owned SVG geometry.
No third-party vehicle logo or trademark was used in the SVC artwork.
