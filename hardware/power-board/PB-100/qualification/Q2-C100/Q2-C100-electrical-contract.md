# Q2-C100 Electrical Contract

Status: `FROZEN FOR CONTROLLED ROUTING / TEST RESULTS PENDING`

## Power topology

The accepted nets are:

```text
JRAW RAW_101V -> QDUT drain
QDUT sources -> COMMON_SOURCE -> QREV sources
COMMON_SOURCE -> JCOMMON (forced-build load point)
QREV drain -> SYSTEM_OUT -> JOUT (correlation-build load point)
```

QDUT is exactly `IAUTN15S6N025ATMA1`; accepted data may not use a different
orderable MOSFET under the QDUT reference.

QDUT pin 1 is `Q2_HGATE`, pins 2 through 8 are `COMMON_SOURCE`, and `Tab` is
`RAW_101V`. QREV has the same package mapping, with `Tab` on `SYSTEM_OUT`.
This preserves the PB-100 common-source orientation.

UCTRL pin mapping follows the LM74930-Q1 RGE data sheet. In particular:

- HGATE pin 14 connects directly to QDUT pin 1;
- OUT pin 15 and A pin 2 use separate Kelvin branches to `COMMON_SOURCE`;
- DGATE pin 1 drives QREV pin 1;
- C pin 24 and CS+/CS-/ISCP pins 20/19/18 remain on `SYSTEM_OUT`;
- OVCLAMP pin 16, TMR pin 9 and ILIM pin 11 are grounded for hard cutoff and
  no controller-owned overcurrent function;
- RTN exposed pad 25 is electrically isolated and must not be tied to GND;
- SW and all N.C. pins are physically no-connect.

Only QDUT drain and the resistor-fed RAW sense branches see `RAW_101V`. UCTRL
A, OUT, VS, SW, CS+, CS- and ISCP may not exceed the TI 65 V recommended
operating limit. The correlation procedure must abort if any protected
controller pin plus measurement uncertainty reaches 65 V.

## Controller passives

- OV divider: two `CRCW120642K2FKEAHP` 42.2 kOhm 1% upper elements and
  `CRCW06031K00FKEAHP` 1.00 kOhm 1% lower element, from RAW_101V to GND.
- VS feed: `CRCW120610K0FKEAHP`, 10.0 kOhm 1% 1206, from RAW_101V.
- VS clamp: `BZT52H-B56-Q`, nominal 56 V, AEC-Q101.
- VS storage: two `CGA6N3X7R2A225M230AE`, 2.2 uF, 100 V, X7R,
  AEC-Q200. The assembled effective total at 56 V and the test temperature
  must be measured and remain at least 1.0 uF before energizing.
- CAP-to-VS: `CGA3E2X7R1H104K080AE`, 100 nF, 50 V, X7R, AEC-Q200,
  soft termination.

TI requires at least 1 uF on VS for the resistor/Zener unsuppressed-load-dump
topology. Nominal capacitance alone is not acceptance evidence because MLCC DC
bias, tolerance and temperature effects apply.

## Measurement boundary

TPD, TPG and TPS are the QDUT drain, gate and source Kelvin points. TPHG is the
controller-side HGATE point; TPOV, TPVS, TPFLT and TPGND expose trigger/control
observability. Drain current is measured outside the gate/source Kelvin loop by
the calibrated external current channel defined in the qualification plan.

No grounded oscilloscope input may be attached directly to RAW_101V or the
floating VDS measurement. VDS requires the rated differential probe. Probe
capacitance and loop area are recorded in the fixture loading budget.

## Variant invariant

There is no gate-path selector in the accepted design. `CORRELATION-A` obtains
the direct LM74930-Q1 waveform. `FORCED-B` removes UCTRL/QREV by population and
uses JCOMMON as the load point. An assembly with UCTRL populated while an
external driver is attached is prohibited unless a separate contention review
authorizes that one setup.
