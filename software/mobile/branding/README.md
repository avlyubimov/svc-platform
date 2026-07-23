# Mobile branding

Startup animation behavior is platform-neutral. A `BrandPack` supplies
`BrandLogo`, `ManufacturerWordmark`, `VehicleModel`, `VehicleGeneration`,
`BrandTagline`, and `AccentColor`; BLE, OTA, CAN, diagnostics, and safety logic
must not inspect a brand identifier.

The personal profile defaults to `bmw-r1200gs-k25-personal` and theme
`svc-boxer-blue`. Place owner-provided files at:

```text
software/mobile/branding/local/bmw-roundel.svg
software/mobile/branding/local/bmw-motorrad-wordmark.svg
```

`branding/local` is ignored by Git. Builds never download brand assets. Both
apps require both local files before selecting the BMW presentation; otherwise
they use the original SVC fallback copy and mark.

The full animation runs only in the phone application. CarPlay and Android Auto
keep their host-controlled launch behavior and information-only templates.
