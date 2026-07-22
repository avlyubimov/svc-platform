# PB-100 Dual Fog Switch Interface

Status: `EVT-LAYOUT-AUTHORIZED`; the dual input is captured in KiCad and the
external harness remains blocked until the physical switch is measured.
`EVT-FAB-AUTHORIZED` additionally requires routed-board DRC, connector review,
protection pulse review and the selected assembly variant recorded in the BOM.

## Interface contract

The owner-supplied double three-wire handlebar switch is treated as one common
wire plus two independent contacts. Wire colors and contact type are unknown
until offline measurement and shall not be assigned by documentation or loom.
The switch carries signal current only; lamp current never passes through it.

Use a sealed TE Connectivity DEUTSCH DTM three-position pair
`DTM04-3P`/`DTM06-3S` with size-20 contacts as a garage-owned harness item:

| Contact | Signal | Function |
|---:|---|---|
| 1 | `SW_GND` | Assumed common dry-contact return |
| 2 | `FOG_A_SW_IN` | User request for configured pair A, reference OUT3/OUT4 |
| 3 | `FOG_B_SW_IN` | User request for configured pair B, reference OUT6/OUT7 |

PB-100 carries `FOG_A_SW_IN` on JPB1 pin 82 and `FOG_B_SW_IN` on pin 83.
LB-100 binds the protected logic outputs to STM32H563 PA8 and PA9 respectively.
Neither external wire reaches an MCU pin directly.

## Selected protection circuit

The two channels are electrically independent after the shared dual raw-line
ESD/EMI protector:

- `D18`: TI `ESD2CANFD24DBZRQ1`, AEC-Q101, SOT-23, ±24 V working voltage,
  ISO 10605 automotive ESD protection and 3.5 A 8/20 us surge capability.
- `R23`/`R27`: individual 4.7 kOhm 1% dry-contact series resistors.
- `R26`/`R30`: individual 47 kOhm 1% pull-ups to `LB_3V3_IO`.
- `C35`/`C36`: individual 47 nF X7R filters.
- `D19`/`D20`: Nexperia `BZT52H-B4V3-Q`, AEC-Q101, 4.3 V ±2%, SOD123F,
  150 C maximum junction temperature, 375 mW on the standard test board and
  up to 830 mW with the documented enlarged cathode pad.
- `U18`/`U19`: TI `SN74LVC1G17QDBVRQ1`, AEC-Q100 Grade 1 Schmitt buffers,
  powered from 3.3 V. Their outputs `FOG_A_SW_IN_MCU` and
  `FOG_B_SW_IN_MCU` provide the MCU voltage boundary.
- `C37`/`C38`: individual 100 nF buffer decoupling capacitors.

With a closed dry contact, the worst nominal divider level is
`3.3 V * 4.7 kOhm / (47 kOhm + 4.7 kOhm) = 0.30 V`. The input time constants
are approximately 0.22 ms when pulled low and 2.21 ms when released; the 50 ms
firmware debounce is intentionally dominant. At the 37 V representative D18
clamp point, the 4.7 kOhm resistor limits the 4.3 V clamp current to about
6.9 mA and the zener dissipation to about 30 mW. These calculations do not
replace routed-board ISO pulse and ground-return review at `EVT-FAB-REVIEW`.

Primary sources:

- https://www.ti.com/lit/ds/symlink/esd2can24-q1.pdf
- https://www.ti.com/lit/ds/symlink/sn74lvc1g17-q1.pdf
- https://assets.nexperia.com/documents/data-sheet/BZT52H-Q_SER.pdf
- https://www.diodes.com/datasheet/download/BC846AQ-BC848CQ.pdf
- https://www.te.com/content/dam/te-com/documents/industrial-and-commercial-transportation/global/ict-connector-selector-en.pdf

## Assembly variants

The default Rev.1 option is an active-low dry contact. If offline measurement
shows that the button contains electronics or emits 12 V, the alternate
protected transistor path may be populated without changing the PCB.

| Variant | Fit | DNP | Electrical result |
|---|---|---|---|
| `FOG_DRY_CONTACT` default | R23, R27 | R24, R25, R28, R29, Q18, Q19 | Each contact closes its raw input to `SW_GND`; open wire is OFF |
| `FOG_12V_ACTIVE_HIGH` alternate | R24, R25, R28, R29, Q18, Q19 | R23, R27 | 12 V drives a `BC847BQ-7-F`; its collector creates the same active-low filtered logic |

The 12 V option uses 47 kOhm base resistors and 100 kOhm base-emitter
pull-downs. At 12 V, base current is approximately 0.24 mA while collector
current is approximately 0.07 mA. `BC847BQ-7-F` is AEC-Q101, rated to 45 V and
150 C. The 24 V raw protector limits the reviewed surge node below that
collector rating for its specified 8/20 us condition. A 12 V switch must use a
fused, reviewed vehicle source; this option is not authorization to connect an
unknown illuminated switch.

Do not fit `R23` with `R24/R25/Q18`, or `R27` with `R28/R29/Q19`. The selected
variant must be recorded in the assembly BOM and inspected before power. The
two channels may not use undocumented mixed variants.

Alternatives remain Nexperia `PESD2IVN24-T` for raw protection,
Nexperia `74LVC1G17-Q100` for the Schmitt buffer, and an AEC-Q101 45 V NPN in
the same reviewed pinout after substitution review. Exact LCSC/JLCPCB stock is
rechecked at EVT package review; the DTM switch connector is garage-installed.

## Firmware behavior

`FOG_A_SW_IN` and `FOG_B_SW_IN` create independent user requests. Each input
supports configuration behavior `momentary_toggle` or `maintained`; the
unverified default is `momentary_toggle`. A valid request enables its two
configured roles sequentially with `channel_delay_ms`. A valid off command
removes both channel requests in the same update. Both pairs may be requested
at once.

Boot, reset, invalid configuration, undervoltage, overcurrent, thermal denial,
telemetry fault or a stuck momentary input clears the affected request. A held
input at boot must first return to OFF before it can arm. Failure or sticking
of A does not block B. Output Manager remains authoritative and load shedding
removes pair B before pair A. The stock headlamp remains on factory wiring.

## Offline switch measurement

Perform these checks with the switch disconnected from the motorcycle and all
power sources:

1. Find the common wire with the multimeter continuity function.
2. Check common-to-each-other-wire continuity independently for button A and B.
3. Record resistance in every pressed and released state.
4. Use diode mode in both polarities to detect LEDs or electronic circuitry.
5. Record wire colors, a complete state table and every measured value.
6. Do not finalize or energize the external harness until the record is reviewed.

`SERVICE` and `RESET` are not fog controls. FB-100 remains
`EVT-LAYOUT-AUTHORIZED`; its optional single-button fit idea is not a substitute
for these two independent handlebar contacts.
