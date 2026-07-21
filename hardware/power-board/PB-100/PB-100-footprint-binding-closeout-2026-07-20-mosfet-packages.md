# PB-100 MOSFET Package Footprint Binding Closeout 2026-07-20

Status: Footprint-binding evidence update

Selection update: Product Owner subsequently selected `IAUT300N08S5N012ATMA2`
80 V PG-HSOF-8-1 TOLL for Q1 and Q101-Q110. Former LFPAK88 and 60 V footprint
work below is retained as historical package evidence only and does not define
the Rev.1 assembly baseline.

This closeout binds the remaining PB-100 MOSFET package rows. It does not create
`PB-100.kicad_pcb`, Gerbers, drill files, pick-place files, BOM/CPL order
packages, manufacturing ZIP files, fabrication packages, panel outputs, or PCBA
orders.

## Scope

| Item | Local footprint | Evidence |
|---|---|---|
| Selected input and output MOSFET | `PB100:PG-HSOF-8-1_TOLL_Infineon` | Infineon IAUT300N08S5N012ATMA2 data sheet PG-HSOF-8-1 TOLL footprint |
| Historical 60 V input footprint | `PB100:PG-HSOF-8-1_TOLL_Infineon` | Infineon package evidence retained only for audit history |
| Controlled 80 V alternatives | selected TOLL footprint for IAUT300N08S5N014ATMA1; LFPAK56E footprint requires review for BUK7J2R4-80MX | Alternative A is same-footprint; alternative B is deliberately non-drop-in |

## Engineering Closeout

- Why the blockers existed: PB-100 had source-identified TOLL and LFPAK88
  package classes but no project-local footprint evidence for high-current
  input reverse protection or OUT2 escape use.
- Candidate comparison: `IAUT300N08S5N012ATMA2` TOLL is the selected 80 V baseline.
  `IAUT300N08S5N014` 80 V TOLL and `BUK7J2R4-80M` 80 V LFPAK56E preserve the
  voltage class but are non-drop-in. Former 60 V TOLL and PowerPAK paths are
  rejected for Rev.1 population.
- Recommended solution: bind the selected TOLL footprint to Q1 and
  Q101-Q110 while retaining unselected footprints only as auditable evidence.
- Symbol/footprint compatibility: `PB-100-symbol-footprint-pad-map.csv`
  verifies that the selected TOLL drain pad is named `Tab` to match
  `PB100_POWER_NMOS_TOLL_80V`; pin 1 is gate and pins 2 through 8 are source.
- Datasheet evidence: Infineon `IAUT300N08S5N012ATMA2` is an automotive
  AEC-Q101 MOSFET in PG-HSOF-8-1 TOLL with pin 1 gate, pins 2 through 8 source,
  and Tab drain.
- Why these components: the selected TOLL keeps the approved 80 V class for
  both the input and generic outputs without changing the architecture.
- Why not alternative A: IAUT300N08S5N014ATMA1 is same-footprint but still
  needs renewed electrical SOA gate-charge thermal BOM and source review.
- Why not alternative B: BUK7J2R4-80M LFPAK56E has a different footprint and
  electrical/thermal model, so it is not a drop-in substitute.
- Expected lifetime: both MOSFET classes are automotive-qualified; field
  lifetime still depends on junction temperature, copper spreading, fuse
  coordination, and load profile.
- Operating margin: generated SOA hot-loss and transient records now close the
  pre-layout selected-TOLL claim; extracted copper and prototype temperature
  remain later physical gates.
- Maximum junction temperature: both datasheets list 175 °C junction limits.
  PB-100 design limits must remain below that with derating.
- Availability: the selected Infineon part is active/preferred with a documented
  authorized-distributor consignment route; live JLCPCB/PCBWay and stock must
  be rechecked before BOM lock.
- Automotive qualification: both candidate classes are AEC-Q101 automotive
  MOSFET evidence paths.
- LCSC availability: the selected TOLL and both 80 V alternatives require a
  fresh production snapshot before population.
- PCBWay/JLC compatibility: both are factory SMT power packages. Initial
  segmented paste apertures are present in the local footprints; AOI,
  wettable-flank, thermal-via, solder-void, and first-article inspection notes
  remain layout/DFM review items.
- Cost impact: the selected TOLL is the BOM direction; exact unit consignment
  and extended-part cost remains an order-date sourcing gate.
- Thermal impact: footprints expose large copper pads but do not close copper
  spreading, via field, or enclosure heat path.
- Production impact: the selected TOLL drain pad uses 42 segmented paste-only
  apertures; solder-voiding controls and vendor DFM still remain before any
  pick-place or PCBA order output. The LFPAK88 footprint remains historical
  and is not an assembly substitution.
- Field reliability: the common selected 80 V TOLL path reduces substitution
  ambiguity; field margin still depends on SOA, overshoot and temperature.
- Known risks: TOLL footprint symmetry, pin-1 orientation, thermal-via fields,
  solder voiding, OUT2 SOA, input reverse FET heating, and sourcing stock risk
  remain layout/BOM gates.

## Remaining PB Footprint Blockers

No PB-100 footprint-binding inventory rows remain open. KiCad board import is
still blocked by thermal/current layout model and controlled schematic symbol
promotion gates. This closeout does not authorize PCB layout or manufacturing
output.
