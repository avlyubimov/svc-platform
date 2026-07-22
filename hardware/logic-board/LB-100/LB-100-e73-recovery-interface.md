# LB-100 E73 programming and recovery interface

Status: Implemented in the Rev.1 EVT schematic and routed PCB

## Decision

LB-100 exposes five top-side, 1.2 mm pogo-test lands next to the service/RF
area. They are not assembly components and are excluded from BOM and position
outputs.

| Reference | Net | E73 endpoint | Purpose |
|---|---|---|---|
| `TP1` | `E73_SWDIO` | U7.37 `SWDIO` | nRF52840 SWD data |
| `TP2` | `E73_SWDCLK` | U7.39 `SWDCLK` | nRF52840 SWD clock |
| `TP3` | `BLE_RESET_N` | U7.26 `RESET` | target reset/recovery |
| `TP4` | `RADIO_SENSOR_3V3` | U7.19 `VCC` | target-voltage reference |
| `TP5` | `GND` | U7 GND domain | programmer return |

The Ebyte product page identifies E73-2G4M08S1C as an nRF52840 module delivered
without user firmware, and its pin table identifies pin 37 as SWDIO, pin 39 as
the serial-debug clock, pin 26 as reset, pin 19 as VCC, and pins 5/21/24 as
GND: <https://www.ebyte.com/product/444.html>.

UART remains an application/service transport only. It is not accepted as the
first-programming or recovery path.

## Power and fixture rules

- Program the LB STM32 through `JDBG1` first, then use a service mode that turns
  on `RADIO_SENSOR_3V3` before attaching the E73 SWD fixture.
- `TP4` is the programmer VTref/measurement point. Do not inject external power
  into it until U13 reverse-current behavior and the complete switched-domain
  back-power path have been bench-qualified.
- The fixture must share `TP5` GND, use 3.3 V-compatible SWD levels, assert reset
  only through `TP3`, and must not drive E73 pins while the target rail is off.
- Keep the fixture and routes outside the module antenna copper keepout. Verify
  rail settling, reset release, device identification, erase, program, verify,
  and recovery from an intentionally invalid image before EVT motorcycle tests.

## Validation

`tools/validate_board_schematics.py` checks the exact U7/test-pad endpoints and
the footprint pad contract. `tools/validate_lb100_layout.py` checks that all five
pads are present on the top side, routed without shorts/clearance errors, and
remain excluded from assembly outputs. This interface does not authorize
Gerber, drill, BOM/CPL, pick-and-place, or board ordering.
