# Rev.1 EVT PCB Renders

These KiCad renders document the current board states. They are review aids;
release authority remains in the board-specific checklists. LB-100 alone is
`EVT-FAB-AUTHORIZED` for five bare test PCBs. No image authorizes assembly,
PB-100, motorcycle use or production.

| Board | Top | Bottom | Captured state |
|---|---|---|---|
| FB-100 | [top](FB-100-rev1-evt-top.png) | [bottom](FB-100-rev1-evt-bottom.png) | Four-layer connectivity-complete routing with stackup-derived USB pair and GND zones; fab review and supplier DFM remain open |
| LB-100 | [top](LB-100-rev1-evt-top.png), [isometric](LB-100-rev1-evt-isometric.png) | [bottom](LB-100-rev1-evt-bottom.png) | Connectivity-complete six-layer EVT board with 2,274 segments, 409 standard through vias, four GND zones, six-layer E73 keepout and zero refilled DRC errors/unconnected items |
| PB-100 | [CAN1/FOG top](PB-100-rev1-evt-can1-top.png) | [CAN1/FOG bottom](PB-100-rev1-evt-can1-bottom.png) | Partial PCB with the CAN1 safety island and protected FOG cable entry routed; power routing is not present |

The images were generated on 2026-07-22 from the tracked `.kicad_pcb` files
with KiCad CLI 10.0.4. KiCad renders the FB-100 GND zones from the tracked zone
definitions; the tracked board is not modified only for rendering. Regenerate
the board renders from the repository root with:

```bash
mkdir -p docs/assets/pcb-renders
kicad-cli pcb render hardware/front-board/FB-100/kicad/FB-100.kicad_pcb -o docs/assets/pcb-renders/FB-100-rev1-evt-top.png --side top --width 1800 --height 1000 --background opaque --quality high
kicad-cli pcb render hardware/front-board/FB-100/kicad/FB-100.kicad_pcb -o docs/assets/pcb-renders/FB-100-rev1-evt-bottom.png --side bottom --width 1800 --height 1000 --background opaque --quality high
kicad-cli pcb render hardware/logic-board/LB-100/kicad/LB-100.kicad_pcb -o docs/assets/pcb-renders/LB-100-rev1-evt-top.png --side top --width 1800 --height 1200 --background opaque --quality high
kicad-cli pcb render hardware/logic-board/LB-100/kicad/LB-100.kicad_pcb -o docs/assets/pcb-renders/LB-100-rev1-evt-bottom.png --side bottom --width 1800 --height 1200 --background opaque --quality high
kicad-cli pcb render hardware/logic-board/LB-100/kicad/LB-100.kicad_pcb -o docs/assets/pcb-renders/LB-100-rev1-evt-isometric.png --side top --width 1800 --height 1200 --background opaque --quality high --perspective --floor --rotate 325,0,35
kicad-cli pcb render hardware/power-board/PB-100/kicad/PB-100.kicad_pcb -o docs/assets/pcb-renders/PB-100-rev1-evt-can1-top.png --side top --width 1800 --height 1080 --background opaque --quality high
kicad-cli pcb render hardware/power-board/PB-100/kicad/PB-100.kicad_pcb -o docs/assets/pcb-renders/PB-100-rev1-evt-can1-bottom.png --side bottom --width 1800 --height 1080 --background opaque --quality high
```

No Gerber, drill, BOM/CPL, pick-and-place, manufacturing ZIP, or other board
order artifact is stored in this image directory. The separately controlled
LB-100 bare-PCB EVT package is under
`hardware/logic-board/LB-100/manufacturing/evt-rev1/`.
