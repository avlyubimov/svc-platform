# PB-100 Logic Power Design Calculation

Status: Candidate values for schematic review; not final

This note derives the first value-bearing `LM5164-Q1` candidate network for
`PB_5V_OUT`. It does not authorize PCB layout, switch-node placement, copper, or
manufacturing output.

## Inputs

- Regulator family: `LM5164-Q1`, 6 V to 100 V input, 1 A synchronous buck.
- Output rail: `PB_5V_OUT`.
- Output target: 5.0 V, up to 1 A budget before LB-100 load review.
- Input rail: `VBAT_PROT` after reverse protection and TVS.
- Design priority: wide input survival, safe UVLO, low BOM risk, and no layout
  release before schematic freeze.

## Datasheet anchors

- `LM5164-Q1` is AEC-Q100-qualified and rated for 6 V to 100 V input.
- The feedback reference is 1.2 V typical.
- `PGOOD` is open-drain and uses a 10 kΩ to 100 kΩ pull-up.
- `BST` requires a 2.2 nF 50 V X7R capacitor from `BST` to `SW`.
- `EN/UVLO` starts switching above about 1.5 V and shuts down below about 1.1 V.

## Candidate values

| Item | Candidate | Rationale | Still open |
|---|---:|---|---|
| Switching frequency | ~300 kHz | Conservative EMI and switching-loss point for 5 V rail | EMI review |
| `RRON` | 41.2 kΩ 1% | Uses `fSW ≈ VOUT × 2500 / RRON(kΩ)` | Verify against final input range |
| `RFB_TOP` | 158 kΩ 0.1% | With 49.9 kΩ bottom gives about 5.0 V from 1.2 V reference | Tolerance review |
| `RFB_BOT` | 49.9 kΩ 0.1% | Common low-current divider value | No-load and leakage review |
| `RUV_TOP` | 332 kΩ 1% | With 100 kΩ bottom gives about 6.5 V rising UVLO | Cold-crank behavior |
| `RUV_BOT` | 100 kΩ 1% | Keeps divider current modest but not ultra-high impedance | Leakage/noise review |
| `CBST` | 2.2 nF 50 V X7R | Matches datasheet bootstrap requirement | Package and voltage derating |
| `L1` | 47 µH shielded AEC-Q200 | Keeps 1 A peak margin reasonable at high input voltage | Saturation and DCR |
| `COUT` | 2 × 22 µF 10 V X7R plus 0.1 µF | First stability/load-step candidate | DC-bias derating |
| `CIN` | 2.2 µF 100 V X7R plus local 0.1 µF | Matches datasheet-class local input bypass | Surge and damping |
| Input bulk | 10 µF 100 V automotive bulk candidate | Harness transient energy and damping candidate | EMI and load dump review |
| `PGOOD` pull-up | 47 kΩ to `LB_3V3_IO` | Inside datasheet pull-up range and LB-visible only when LB rail exists | Timing/filtering |
| PGOOD filter | Optional 10 nF DNP candidate | Debounce/noise option without default delay lock | Timing review |
| Switch snubber | DNP RC footprint candidate only | Do not lock damping before layout/parasitic evidence | Bench ringing review |

## Quick checks

- Feedback: `VOUT = 1.2 × (1 + 158k / 49.9k) ≈ 5.0 V`.
- UVLO rising: `VIN ≈ 1.5 × (332k + 100k) / 100k ≈ 6.48 V`.
- UVLO shutdown: `VIN ≈ 1.1 × (332k + 100k) / 100k ≈ 4.75 V`.
- At 1 A load and 47 µH, inductor saturation must exceed the peak current
  including high-input ripple and current-limit tolerance. Use `Isat ≥ 2.2 A`
  as a sourcing floor before schematic freeze.

## Freeze blockers

- Confirm actual LB-100 plus PB-side 5 V load budget.
- Verify LM5164QDDATQ1 orderability or choose LM5164QDDARQ1 / LM5013-Q1 path.
- Select an AEC-Q200 shielded inductor with saturation, RMS, DCR, and package
  evidence.
- Verify ceramic capacitor DC-bias derating and 100 V input capacitor class.
- Review EMI and switch-node ringing before deciding any snubber population.
- Keep PCB layout blocked until schematic freeze closes.
