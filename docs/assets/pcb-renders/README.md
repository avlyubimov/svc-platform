# Rev.1 EVT PCB Renders

These top- and bottom-side KiCad renders document the current `EVT-LAYOUT-AUTHORIZED`
layout state. They are review aids only and do not authorize fabrication,
assembly, ordering, or production use.

| Board | Top | Bottom | Captured state |
|---|---|---|---|
| FB-100 | [top](FB-100-rev1-evt-top.png) | [bottom](FB-100-rev1-evt-bottom.png) | Four-layer connectivity-complete routing with stackup-derived USB pair and GND zones; fab review and supplier DFM remain open |
| LB-100 | [top](LB-100-rev1-evt-top.png) | [bottom](LB-100-rev1-evt-bottom.png) | First routing iteration; open connections and fab-review items remain |
| PB-100 | [CAN1/FOG top](PB-100-rev1-evt-can1-top.png) | [CAN1/FOG bottom](PB-100-rev1-evt-can1-bottom.png) | Partial PCB with the CAN1 safety island and protected FOG cable entry routed; power routing is not present |

The images were generated on 2026-07-22 from the tracked `.kicad_pcb` files
with KiCad CLI 10.0.4. The FB-100 images use a temporary copy refilled by the
DRC command so the tracked board is not modified only for rendering. Regenerate
the board renders from the repository root with:

```bash
mkdir -p docs/assets/pcb-renders
kicad-cli pcb render hardware/front-board/FB-100/kicad/FB-100.kicad_pcb -o docs/assets/pcb-renders/FB-100-rev1-evt-top.png --side top --width 1800 --height 1000 --background opaque --quality high
kicad-cli pcb render hardware/front-board/FB-100/kicad/FB-100.kicad_pcb -o docs/assets/pcb-renders/FB-100-rev1-evt-bottom.png --side bottom --width 1800 --height 1000 --background opaque --quality high
kicad-cli pcb render hardware/logic-board/LB-100/kicad/LB-100.kicad_pcb -o docs/assets/pcb-renders/LB-100-rev1-evt-top.png --side top --width 1800 --height 1200 --background opaque --quality high
kicad-cli pcb render hardware/logic-board/LB-100/kicad/LB-100.kicad_pcb -o docs/assets/pcb-renders/LB-100-rev1-evt-bottom.png --side bottom --width 1800 --height 1200 --background opaque --quality high
kicad-cli pcb render hardware/power-board/PB-100/kicad/PB-100.kicad_pcb -o docs/assets/pcb-renders/PB-100-rev1-evt-can1-top.png --side top --width 1800 --height 1080 --background opaque --quality high
kicad-cli pcb render hardware/power-board/PB-100/kicad/PB-100.kicad_pcb -o docs/assets/pcb-renders/PB-100-rev1-evt-can1-bottom.png --side bottom --width 1800 --height 1080 --background opaque --quality high
```

No Gerber, drill, BOM/CPL, pick-and-place, manufacturing ZIP, or other board
order artifact is stored in this directory.
