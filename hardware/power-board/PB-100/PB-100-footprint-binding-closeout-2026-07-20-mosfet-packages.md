# PB-100 MOSFET Package Footprint Binding Closeout 2026-07-20

Status: Footprint-binding evidence update

This closeout binds the remaining PB-100 MOSFET package rows. It does not create
`PB-100.kicad_pcb`, Gerbers, drill files, pick-place files, BOM/CPL order
packages, manufacturing ZIP files, fabrication packages, panel outputs, or PCBA
orders.

## Scope

| Item | Local footprint | Evidence |
|---|---|---|
| Input reverse MOSFET | `PB100:PG-HSOF-8-1_TOLL_Infineon` | Infineon PG-HSOF-8-1 footprint drawing and IAUTN06S5N008 datasheet |
| Input reverse MOSFET alternate | `PB100:LFPAK88_SOT1235_Nexperia` | Nexperia BUK7S1R2-80M datasheet LFPAK88 SOT1235 footprint |
| OUT2 escape MOSFET | Both local TOLL and LFPAK88 footprints | Escape row now has package evidence but final use still depends on OUT2 SOA selection |

## Engineering Closeout

- Why the blockers existed: PB-100 had source-identified TOLL and LFPAK88
  package classes but no project-local footprint evidence for high-current
  input reverse protection or OUT2 escape use.
- Candidate comparison: `IAUTN06S5N008` TOLL keeps the preferred low-RDS(on)
  60 V automotive MOSFET path. `BUK7S1R2-80M` LFPAK88 keeps an 80 V escape path
  for overshoot/SOA margin. The default PowerPAK output MOSFET remains valid
  where OUT2 SOA does not require the larger package.
- Recommended solution: bind both TOLL and LFPAK88 footprints locally while
  keeping final OUT2 package selection in the SOA/thermal review gate.
- Datasheet evidence: Infineon IAUTN06S5N008 is an automotive AEC-Q101 MOSFET
  in PG-HSOF-8-1 with pin 1 gate, pins 2-8 source, and tab drain. Nexperia
  BUK7S1R2-80M is an automotive AEC-Q101 MOSFET in LFPAK88 SOT1235 with pin 1
  gate, pins 2-4 source, and mounting base drain.
- Why these components: they preserve high-current and high-voltage escape
  capability without changing the generic output architecture.
- Why not alternative A: do not replace the default output MOSFET everywhere
  with TOLL because area, paste, copper, thermal, and sourcing cost all increase.
- Why not alternative B: do not force LFPAK88 as default because it is an escape
  package whose SOA benefit must be weighed against source risk and layout area.
- Expected lifetime: both MOSFET classes are automotive-qualified; field
  lifetime still depends on junction temperature, copper spreading, fuse
  coordination, and load profile.
- Operating margin: no new SOA claim is made by footprint binding. TOLL/LFPAK88
  selection must still prove current, transient, and thermal margin.
- Maximum junction temperature: both datasheets list 175 °C junction limits.
  PB-100 design limits must remain below that with derating.
- Availability: TOLL keeps existing `C20190986` sourcing evidence and LFPAK88
  keeps Nexperia package-source evidence. Current JLCPCB/PCBWay availability
  must be rechecked before BOM lock.
- Automotive qualification: both candidate classes are AEC-Q101 automotive
  MOSFET evidence paths.
- LCSC availability: TOLL has an existing candidate row; LFPAK88 must be
  rechecked before population.
- PCBWay/JLC compatibility: both are factory SMT power packages but need paste
  aperture, AOI, wettable-flank, thermal-via, and first-article inspection notes.
- Cost impact: no BOM change until a package is selected for a populated symbol.
- Thermal impact: footprints expose large copper pads but do not close copper
  spreading, via field, or enclosure heat path.
- Production impact: paste segmentation and solder-voiding controls remain DFM
  gates before any pick-place or PCBA order output.
- Field reliability: keeping both local footprints avoids a late footprint
  scramble while preserving the default/escape decision boundary.
- Known risks: TOLL footprint symmetry, pin-1 orientation, LFPAK88 mounting-base
  drain paste pattern, OUT2 SOA, input reverse FET heating, and sourcing stock
  risk remain layout/BOM gates.

## Remaining PB Footprint Blockers

No PB-100 footprint-binding inventory rows remain open. KiCad board import is
still blocked by mechanical envelope, thermal/current layout model, and
controlled schematic symbol promotion gates. This closeout does not authorize
PCB layout or manufacturing output.
