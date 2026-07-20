# PB-100 MOSFET Package Footprint Binding Closeout 2026-07-20

Status: Footprint-binding evidence update

Selection update: Product Owner subsequently selected `BUK7S1R2-80M` 80 V
LFPAK88 for Q1 and Q101-Q110. The TOLL and PowerPAK 60 V footprint work below
is retained as package evidence only and does not define the Rev.1 assembly
baseline.

This closeout binds the remaining PB-100 MOSFET package rows. It does not create
`PB-100.kicad_pcb`, Gerbers, drill files, pick-place files, BOM/CPL order
packages, manufacturing ZIP files, fabrication packages, panel outputs, or PCBA
orders.

## Scope

| Item | Local footprint | Evidence |
|---|---|---|
| Selected input and output MOSFET | `PB100:LFPAK88_SOT1235_Nexperia` | Nexperia BUK7S1R2-80M data sheet LFPAK88 SOT1235 footprint |
| Historical 60 V input footprint | `PB100:PG-HSOF-8-1_TOLL_Infineon` | Infineon package evidence retained only for audit history |
| Controlled 80 V alternatives | TOLL or LFPAK56E footprint TBD per exact MPN | IAUTN08S5N012L and BUK7J2R4-80M are non-drop-in alternatives |

## Engineering Closeout

- Why the blockers existed: PB-100 had source-identified TOLL and LFPAK88
  package classes but no project-local footprint evidence for high-current
  input reverse protection or OUT2 escape use.
- Candidate comparison: `BUK7S1R2-80M` LFPAK88 is the selected 80 V baseline.
  `IAUTN08S5N012L` 80 V TOLL and `BUK7J2R4-80M` 80 V LFPAK56E preserve the
  voltage class but are non-drop-in. Former 60 V TOLL and PowerPAK paths are
  rejected for Rev.1 population.
- Recommended solution: bind the selected LFPAK88 footprint to Q1 and
  Q101-Q110 while retaining unselected footprints only as auditable evidence.
- Symbol/footprint compatibility: `PB-100-symbol-footprint-pad-map.csv`
  verifies that the TOLL drain pad is named `Tab` to match
  `PB100_INPUT_NMOS_TOLL_PRELIM` and the LFPAK88 mounting-base drain pad is
  named `mb` to match `PB100_POWER_NMOS_ESCAPE_PRELIM`.
- Datasheet evidence: Infineon IAUTN06S5N008 is an automotive AEC-Q101 MOSFET
  in PG-HSOF-8-1 with pin 1 gate, pins 2-8 source, and tab drain. Nexperia
  BUK7S1R2-80M is an automotive AEC-Q101 MOSFET in LFPAK88 SOT1235 with pin 1
  gate, pins 2-4 source, and mounting base drain.
- Why these components: the selected LFPAK88 keeps the approved 80 V class for
  both the input and generic outputs without changing the architecture.
- Why not alternative A: IAUTN08S5N012L TOLL needs a different footprint and
  renewed thermal, stencil and pin-map review.
- Why not alternative B: BUK7J2R4-80M LFPAK56E has a different footprint and
  electrical/thermal model, so it is not a drop-in substitute.
- Expected lifetime: both MOSFET classes are automotive-qualified; field
  lifetime still depends on junction temperature, copper spreading, fuse
  coordination, and load profile.
- Operating margin: no new SOA claim is made by footprint binding. TOLL/LFPAK88
  selection must still prove current, transient, and thermal margin.
- Maximum junction temperature: both datasheets list 175 °C junction limits.
  PB-100 design limits must remain below that with derating.
- Availability: LFPAK88 keeps Nexperia package-source evidence; live
  JLCPCB/PCBWay and authorized-distributor availability must be rechecked
  before BOM lock.
- Automotive qualification: both candidate classes are AEC-Q101 automotive
  MOSFET evidence paths.
- LCSC availability: the selected LFPAK88 and both 80 V alternatives require a
  fresh production snapshot before population.
- PCBWay/JLC compatibility: both are factory SMT power packages. Initial
  segmented paste apertures are present in the local footprints; AOI,
  wettable-flank, thermal-via, solder-void, and first-article inspection notes
  remain layout/DFM review items.
- Cost impact: LFPAK88 is now the BOM direction; exact unit and extended-part
  cost remains a sourcing gate.
- Thermal impact: footprints expose large copper pads but do not close copper
  spreading, via field, or enclosure heat path.
- Production impact: solid drain-pad paste has been removed from the TOLL and
  LFPAK88 drain copper pads and replaced with segmented paste-only apertures;
  solder-voiding controls and vendor DFM still remain before any pick-place or
  PCBA order output.
- Field reliability: the common selected 80 V LFPAK88 path reduces substitution
  ambiguity; field margin still depends on SOA, overshoot and temperature.
- Known risks: TOLL footprint symmetry, pin-1 orientation, thermal-via fields,
  solder voiding, OUT2 SOA, input reverse FET heating, and sourcing stock risk
  remain layout/BOM gates.

## Remaining PB Footprint Blockers

No PB-100 footprint-binding inventory rows remain open. KiCad board import is
still blocked by thermal/current layout model and controlled schematic symbol
promotion gates. This closeout does not authorize PCB layout or manufacturing
output.
