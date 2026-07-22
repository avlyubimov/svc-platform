#!/usr/bin/env python3
"""Generate the PB-100 cable-entry circuit for the dual fog switch."""

from __future__ import annotations

import argparse
from pathlib import Path

from generate_lb_fb_schematics import Schematic, c, passive


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "hardware/power-board/PB-100/kicad/sheets/fog-switch-entry.kicad_sch"
SYMBOL_LIBRARY = ROOT / "hardware/power-board/PB-100/kicad/lib/PB100.kicad_sym"


def build() -> Schematic:
    schematic = Schematic(
        "PB-100",
        "PB-100 Dual Fog Switch Cable Entry",
        (
            "Work queue: CAP-FOG. ADR-0021 cable-entry boundary. Contact 1 is SW_COMMON; contacts 2/3 are the independent "
            "FOG_A_SW_IN/FOG_B_SW_IN requests. D_FOG1 is the primary protector at the PB entry. "
            "R_FOG_GND is fitted for the default dry-contact assembly. R_FOG_12V and F_FOG_12V are "
            "mutually exclusive DNP parts for a measured 12 V switch. Do not finalize the loom or "
            "manufacturing package before offline switch measurement and routed pulse/return review."
        ),
        paper="A4",
    )
    schematic.add(
        c(
            "JFOG1",
            "SEALED_DTM_3WAY_PIGTAIL_ENTRY",
            "PB100:FOG_PIGTAIL_1x03_P3.50mm",
            "../PB-100-fog-switch-interface.md",
            [
                ("1", "SW_COMMON", "SW_COMMON", "passive"),
                ("2", "FOG_A_SW_IN", "FOG_A_SW_IN", "passive"),
                ("3", "FOG_B_SW_IN", "FOG_B_SW_IN", "passive"),
            ],
        )
    )
    schematic.add(
        c(
            "D_FOG1",
            "ESD2CANFD24DBZRQ1",
            "PB100:SOT-23-3_DBZ_TI",
            "https://www.ti.com/lit/ds/symlink/esd2can24-q1.pdf",
            [
                ("1", "IO1", "FOG_A_SW_IN", "passive"),
                ("2", "IO2", "FOG_B_SW_IN", "passive"),
                ("3", "GND", "GND", "passive"),
            ],
        )
    )
    schematic.add(
        passive(
            "R_FOG_GND",
            "0R FOG dry-contact common DEFAULT",
            "PB100:R0603_DNP_LINK_1608Metric",
            "SW_COMMON",
            "GND",
            "../PB-100-fog-switch-interface.md",
        )
    )
    schematic.add(
        c(
            "R_FOG_12V",
            "0R FOG 12V common DNP",
            "PB100:R0603_DNP_LINK_1608Metric",
            "../PB-100-fog-switch-interface.md",
            [("1", "1", "SW_COMMON", "passive"), ("2", "2", "SW_12V_FUSED", "passive")],
            dnp=True,
        )
    )
    schematic.add(
        c(
            "F_FOG_12V",
            "nanoASMDC010F 0.10A 60V DNP",
            "PB100:PPTC_1206_3216Metric",
            "https://www.littelfuse.com/products/polyswitch-resettable-pptcs/surface-mount/nanoasmdc",
            [("1", "VBAT_PROT", "VBAT_PROT", "passive"), ("2", "SW_12V_FUSED", "SW_12V_FUSED", "passive")],
            dnp=True,
        )
    )
    return schematic


def library_blocks(schematic: Schematic) -> tuple[str, ...]:
    return tuple(
        schematic._library_symbol(component, qualified=False)
        for component in schematic.components
    )


def updated_library_text(schematic: Schematic) -> str:
    content = SYMBOL_LIBRARY.read_text(encoding="utf-8")
    missing_blocks = [block for block in library_blocks(schematic) if block not in content]
    if not missing_blocks:
        return content
    if not content.endswith("\n)\n"):
        raise ValueError(f"unexpected symbol-library ending: {SYMBOL_LIBRARY.relative_to(ROOT)}")
    return content[:-3] + "\n" + "\n".join(missing_blocks) + "\n)\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    schematic = build()
    content = schematic.render()
    library_content = updated_library_text(schematic)
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != content:
            print(f"stale generated file: {OUTPUT.relative_to(ROOT)}")
            return 1
        if SYMBOL_LIBRARY.read_text(encoding="utf-8") != library_content:
            print(f"missing generated fog symbols: {SYMBOL_LIBRARY.relative_to(ROOT)}")
            return 1
        return 0
    OUTPUT.write_text(content, encoding="utf-8")
    SYMBOL_LIBRARY.write_text(library_content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
