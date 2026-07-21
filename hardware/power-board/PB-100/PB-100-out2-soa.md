# PB-100 OUT2 SOA and Inrush Envelope

Status: Closed pre-layout electrical evidence; schematic value promotion and physical validation remain gated

OUT2 remains a generic 20 A fused output. The compressor case is a reference
stress envelope, not a hard-coded channel role.

## Accepted envelope

| Case | Current | Duration | Result |
|---|---:|---:|---|
| Configured continuous limit | 18 A | continuous | 0.816 W at the 2.52 mOhm hot bound |
| Fuse-compatible startup | 30 A | 100 ms | 0.2268 J, fully enhanced |
| Fast transient | 80 A | 4 ms | 0.0645 J, below the selected fuse minimum-opening boundary |
| Hard short | 95.91 A threshold | <=5 us | 104.1 A below the conservative 10 us / 60 V SOA current bound |

The previous 40 A / 1 s and 80 A / 100 ms planning cases were incompatible
with an honest 20 A fuse-coordination claim and are superseded by
`PB-100-out2-soa-envelope.csv` and the generated
`PB-100-output-soa-evidence.csv`.

## Selected circuit values

- Controller: `TPS48110AQDGXRQ1`.
- MOSFET: `IAUT300N08S5N012ATMA2`, 80 V PG-HSOF-8-1 TOLL.
- Sense: 0.5 mOhm Kelvin element and 100 ohm RSET.
- Overcurrent: 67.3 kohm RIWRN, calculated 34.96 A threshold.
- Short circuit: 2.61 kohm RISCP, calculated 95.91 A threshold; 1 nF
  filter from ISCP to CS-.
- Timer: 680 nF, calculated 9.95 ms overcurrent interval.
- Bootstrap: 470 nF / 25 V X7R. The maximum 231 nC gate-charge case needs
  231 nF for a 1 V allowed dip before DC-bias derating.
- Gate path: 3.3 ohm PU and direct/0 ohm PD.
- Local flyback: `STPS40170CGY-TR`, both anodes to GND and common cathode to
  `OUT2_LOAD`; harness suppression is supplementary only.

The MOSFET is driven fully enhanced for accepted startup/transient cases.
Indefinite linear current limiting is not permitted. Persistent overcurrent
uses hardware shutdown/slow retry and firmware fault lockout.

## Hard constraints and later gates

- The Q102 case-temperature acceptance ceiling is 125 degC at continuous load.
- Power copper must be a reviewed plane, polygon, or bus path; a trace-only
  18 A claim is rejected.
- PB-BENCH-005 must verify the short-circuit response after prototype assembly.
- PB-BENCH-010 must verify thermal rise in the enclosure.
- Any measured startup beyond 30 A / 100 ms or fast pulse beyond 80 A / 4 ms
  reopens the SOA and fuse review.

These physical tests are post-prototype gates under ADR-0013. This evidence
closes PBREL-004 as a pre-layout engineering blocker, but it does not close
schematic freeze or authorize PCB layout/manufacturing output.

## Primary sources

- Infineon IAUT300N08S5N012 data sheet:
  <https://www.infineon.com/assets/row/public/documents/10/49/infineon-iaut300n08s5n012-datasheet-en.pdf>
- TI TPS4811-Q1 data sheet:
  <https://www.ti.com/lit/ds/symlink/tps4811-q1.pdf>
- ST STPS40170C-Y data sheet:
  <https://www.st.com/resource/en/datasheet/stps40170c-y.pdf>
- Littelfuse ATO/MINI fuse time-current source:
  <https://www.littelfuse.com/assetdocs/lf_aftermarketcatalog_2016_micro3>
