# Vehicle performance profiles

Vehicle performance profiles are runtime configuration shared by the iOS and
Android phone applications. They are separate from `branding/`: a BrandPack
controls presentation, while a vehicle profile supplies confirmed technical
limits and dashboard scale metadata.

`vehicle-profile-index-v1.json` selects the default and safe fallback profiles.
Every listed JSON document validates against `vehicle-profile-v1.schema.json`.
Unknown values remain explicit `null`; clients must not replace them with
generic-looking numbers.

The BMW reference profile defines the SVC tachometer scale, warning zone, red
zone, idle band, fuel capacity, and ice-warning threshold approved for
Reference Vehicle #001. It intentionally leaves `revLimiterRpm` null because no
limiter value has been confirmed.

The Generic Motorcycle fallback has no warning/red zone and no assumed engine,
gearbox, fuel, or year data. A dashboard using it must render performance
features unavailable until a suitable profile is selected.

Performance profiles do not contain CAN identifiers, decoding formulas, BLE
state, theme colors, logos, or safety commands.
