# Mobile branding

Startup animation behavior is platform-neutral. The runtime-loaded
`brand-pack-index-v1.json` selects a `BrandPack`, which supplies
`BrandLogo`, `ManufacturerWordmark`, `VehicleModel`, `VehicleGeneration`,
`BrandTagline`, and `AccentColor`; BLE, OTA, CAN, diagnostics, and safety logic
must not inspect a brand identifier.

The personal profile defaults to `bmw-r1200gs-k25-personal` and theme
`svc-boxer-blue`. Place owner-provided files at:

```text
software/mobile/branding/local/bmw-r1200gs-k25-personal/logo.svg
software/mobile/branding/local/bmw-r1200gs-k25-personal/wordmark.svg
```

`branding/local` is ignored by Git. Builds never download brand assets. The
BMW `logo.svg` is required for BMW presentation. `wordmark.svg` is optional;
when it is absent, the shared BrandPack text renders `BMW MOTORRAD`. If the
logo is absent, both apps use the committed SVC fallback assets under
`branding/svc`.

`branding/svc/app-icon.svg` is the source identity for the phone, CarPlay, and
Android Auto application icon. Manufacturer marks are profile content only and
must never replace the SVC application identity or the neutral black system
launch surface.

Adding a manufacturer does not require Swift or Kotlin edits: add a schema-valid
BrandPack JSON, list it in `brand-pack-index-v1.json`, and provide its asset
files through the appropriate licensed/local build input.

The full animation runs only in the phone application. CarPlay and Android Auto
keep their host-controlled launch behavior and information-only templates.
