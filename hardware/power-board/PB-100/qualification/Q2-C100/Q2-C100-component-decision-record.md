# Q2-C100 Component Decision Record

The coupon is a test instrument for one frozen PB-100 decision, not a new
product architecture. Exact QDUT and UCTRL substitution is therefore forbidden
in accepted correlation/qualification data.

For every selection below, the record states why the part is used, why the
reviewed alternatives are not equivalent, and which evidence remains open.

## QDUT and UCTRL

`IAUTN15S6N025ATMA1` is retained because it is the ADR-0018 selected 150 V,
2.5 mOhm maximum automotive TOLL device and the open evidence gap belongs to
this exact orderable part. `IAUTN15S6N038ATMA1`, Vishay SQJQ570E/SQJ590EP and
industrial linear-FET candidates do not provide the missing public paired hot
trajectory and are not drop-in evidence replacements. Testing them would not
qualify PB-100 Q2.

`LM74930QRGERQ1` is exact because its guaranteed discharge behavior and
deglitch are part of the qualification corner. A stronger external driver is
not an alternative. The Forced-B driver is accepted only after its complete
waveform is shown no stronger than the reviewed controller corner.

Both are automotive-qualified. QDUT operates from an initial 150 degC but must
remain below its 175 degC maximum; UCTRL must remain within its 150 degC
operating-junction limit and is thermally separated from the heater. Lot/date
traceability and authorized distribution are mandatory. No claimed lifetime is
derived from ten events; post-stress parametrics and later PB thermal evidence
remain required.

## QREV

`IAUT300N08S5N012ATMA2` preserves the accepted PB common-source topology,
package and protected-side 80 V class. The same-footprint
`IAUT300N08S5N014ATMA1` and non-drop-in `BUK7J2R4-80MX` remain sourcing escape
paths for PB, but using either here would weaken correlation. QREV is omitted in
Forced-B so its gate/control behavior cannot alter the QDUT component test.

## Terminals

Würth `786202073` was selected because its official specification provides a
9-pin 2.54 mm press-fit pattern, 1.60 mm drill, 1.475 mm finished-hole target,
130 A component rating, -55..150 degC range, automotive release and an active
greater-than-10-year lifecycle statement. A 16-pin `786202094` has more current
margin but increases loop area and changes geometry. Generic screw terminals
are rejected because their contact and PCB-current evidence is weaker.

The 130 A terminal value is not credited as a board rating. Copper/via thermal
extraction and measured connector temperature at 40 A remain fabrication and
bench gates. Press-fit requires post-reflow insertion, board support and an
insertion-force record, so JLCPCB/PCBWay compatibility requires a separate
mechanical/assembly quote.

## VS clamp and storage

Nexperia `BZT52H-B56-Q` supplies an AEC-Q101, 56 V SOD123F clamp with a public
power rating. A generic Zener is rejected because tolerance, temperature and
qualification are part of the 65 V controller-pin boundary.

Two TDK `CGA6N3X7R2A225M230AE` capacitors provide 4.4 uF nominal, 100 V X7R,
AEC-Q200 soft-termination storage. One nominal 1 uF part is rejected because TI
requires at least 1 uF in the resistor/Zener load-dump topology and MLCC DC bias
can remove the nominal margin. The chosen parts still require measured
effective capacitance of at least 1.0 uF at 56 V over temperature.

## OV divider package boundary

ROV1 and ROV2 use 1206 lands. Their equal 42.2 kOhm values split the raw-side
working voltage, while the larger package preserves routing room for the
reviewed 2.0 mm RAW_101V clearance outside the component body and provides a
better working-voltage/pulse starting point than 0603. A 0603 upper leg is
rejected because its land geometry and voltage margin are poor for this
101 V qualification fixture. A larger 1210/2512 network would add loop area
without closing the still-required resistor-series pulse and working-voltage
evidence. ROV3 remains 0603 because it is the low-side 1.00 kOhm leg and does
not see RAW_101V. Exact AEC-Q200 MPNs, tolerance/temperature coefficients,
maximum continuous working voltage, pulse load and a second source remain open
before `FAB-REVIEW`.

## Reliability, production and cost boundary

The expected component lifecycle is sufficient for a multi-lot laboratory
program, but the coupon itself has no 10-15 year field-life claim. Fine-pitch
UCTRL, TOLL devices and SMD passives require factory reflow; REDCUBE and probe
hardware are post-reflow operations. Exact quotes, LCSC availability and
JLCPCB/PCBWay handling are open before FAB-REVIEW. The selected terminals and
automotive parts cost more than generic lab hardware, but remain comfortably
inside the project's 500 USD prototype target; no cost value is frozen before
supplier quotes. Safety, measurement integrity and correlation dominate cost.
