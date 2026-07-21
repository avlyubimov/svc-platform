#!/usr/bin/env python3
"""Generate reproducible Q2-C100 pre-FAB copper and inductance screens.

The arithmetic in this file deliberately does not claim IPC ampacity, thermal
qualification, extracted inductance, or fabrication approval.  It makes the
known geometry assumptions and lower-bound copper losses reviewable while the
supplier-stackup thermal/field-solver/DFM work remains open.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COUPON = ROOT / "hardware" / "power-board" / "PB-100" / "qualification" / "Q2-C100"
CSV_PATH = COUPON / "Q2-C100-pre-fab-screening.csv"
REPORT_PATH = COUPON / "Q2-C100-pre-fab-screening.md"

CURRENT_A = 40.0
COPPER_TEMPERATURE_C = 150.0
OUTER_COPPER_MM = 0.070
MIN_HOLE_WALL_COPPER_MM = 0.025
POWER_VIA_DRILL_MM = 0.600
COPPER_RESISTIVITY_20_OHM_M = 1.724e-8
COPPER_TEMPERATURE_COEFFICIENT_PER_C = 0.00393
RAW_VOLTAGE_V = 101.0
PEAK_ACCEPTANCE_V = 120.0
POST_MILLER_ID_FALL_US = 0.41


@dataclass(frozen=True)
class Corridor:
    identifier: str
    description: str
    length_mm: float
    width_mm: float
    layers: int
    current_a: float
    note: str


CORRIDORS = (
    Corridor("RAW_MAIN_PAIR", "RAW terminal to QDUT approach", 16.00, 7.00, 2, 40.0, "F.Cu + B.Cu assumed to share equally"),
    Corridor("RAW_QDUT_NECK_FCU", "RAW approach to QDUT drain land", 5.45, 6.50, 1, 40.0, "F.Cu only; package spreading omitted"),
    Corridor("COMMON_SPINE_PAIR", "Common-source vertical spine", 14.00, 6.00, 2, 40.0, "F.Cu + B.Cu assumed to share equally"),
    Corridor("SYSTEM_QREV_NECK_FCU", "QREV drain land to output spine", 5.45, 8.00, 1, 40.0, "F.Cu only; package spreading omitted"),
    Corridor("SYSTEM_MAIN_PAIR", "Output approach to SYSTEM_OUT terminal", 18.00, 7.00, 2, 40.0, "F.Cu + B.Cu assumed to share equally"),
    Corridor("FORCED_BRANCH_PAIR", "Common spine to forced-load terminal", 30.00, 6.00, 2, 40.0, "FORCED-B only; F.Cu + B.Cu equal-sharing assumption"),
    Corridor("SOURCE_BUS_HALF", "One half of a TOLL source collection bus", 3.60, 4.00, 1, 20.0, "Symmetric 20 A half-bus assumption; must be field-checked"),
)


def hot_resistivity() -> float:
    return COPPER_RESISTIVITY_20_OHM_M * (
        1.0 + COPPER_TEMPERATURE_COEFFICIENT_PER_C * (COPPER_TEMPERATURE_C - 20.0)
    )


def corridor_row(corridor: Corridor) -> dict[str, str]:
    cross_section_mm2 = corridor.width_mm * OUTER_COPPER_MM * corridor.layers
    resistance_20_ohm = COPPER_RESISTIVITY_20_OHM_M * (corridor.length_mm / 1000.0) / (cross_section_mm2 * 1e-6)
    resistance_hot_ohm = hot_resistivity() * (corridor.length_mm / 1000.0) / (cross_section_mm2 * 1e-6)
    return {
        "ID": corridor.identifier,
        "Description": corridor.description,
        "Current_A": f"{corridor.current_a:.2f}",
        "Length_mm": f"{corridor.length_mm:.2f}",
        "Width_mm": f"{corridor.width_mm:.2f}",
        "Copper_layers": str(corridor.layers),
        "Cross_section_mm2": f"{cross_section_mm2:.4f}",
        "Current_density_A_per_mm2": f"{corridor.current_a / cross_section_mm2:.2f}",
        "R20_mOhm": f"{resistance_20_ohm * 1e3:.4f}",
        "R150_mOhm": f"{resistance_hot_ohm * 1e3:.4f}",
        "P150_W": f"{corridor.current_a**2 * resistance_hot_ohm:.4f}",
        "Status": "SCREEN_ONLY",
        "Boundary": corridor.note,
    }


def generated_rows() -> list[dict[str, str]]:
    rows = [corridor_row(corridor) for corridor in CORRIDORS]

    source_cross_section = 7.0 * 0.80 * OUTER_COPPER_MM
    rows.append(
        {
            "ID": "SOURCE_LEADS_AGGREGATE",
            "Description": "Seven parallel 0.8 mm source spokes per TOLL",
            "Current_A": "40.00",
            "Length_mm": "3.65",
            "Width_mm": "5.60 aggregate",
            "Copper_layers": "1",
            "Cross_section_mm2": f"{source_cross_section:.4f}",
            "Current_density_A_per_mm2": f"{CURRENT_A / source_cross_section:.2f}",
            "R20_mOhm": "N/A",
            "R150_mOhm": "N/A",
            "P150_W": "N/A",
            "Status": "SCREEN_ONLY",
            "Boundary": "Equal lead sharing is not assumed; package and bus spreading require field/thermal review",
        }
    )

    via_barrel_area_mm2 = math.pi * POWER_VIA_DRILL_MM * MIN_HOLE_WALL_COPPER_MM
    rows.append(
        {
            "ID": "POWER_VIA_ROW_MIN_PLATING",
            "Description": "One five-via transfer row at minimum hole-wall copper",
            "Current_A": "40.00",
            "Length_mm": "2.00 board thickness",
            "Width_mm": "0.60 drill",
            "Copper_layers": "5 barrels",
            "Cross_section_mm2": f"{5.0 * via_barrel_area_mm2:.4f}",
            "Current_density_A_per_mm2": f"{CURRENT_A / (5.0 * via_barrel_area_mm2):.2f}",
            "R20_mOhm": "N/A",
            "R150_mOhm": "N/A",
            "P150_W": "N/A",
            "Status": "CONDITIONAL",
            "Boundary": "Conservative one-row screen; actual current sharing and finished plating require supplier proof",
        }
    )
    return rows


def render_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    fieldnames = list(rows[0])
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_report(rows: list[dict[str, str]]) -> str:
    straight_ids = {
        "RAW_MAIN_PAIR",
        "RAW_QDUT_NECK_FCU",
        "COMMON_SPINE_PAIR",
        "SYSTEM_QREV_NECK_FCU",
        "SYSTEM_MAIN_PAIR",
    }
    straight_rows = [row for row in rows if row["ID"] in straight_ids]
    total_hot_resistance_mohm = sum(float(row["R150_mOhm"]) for row in straight_rows)
    total_hot_loss_w = sum(float(row["P150_W"]) for row in straight_rows)
    voltage_headroom_v = PEAK_ACCEPTANCE_V - RAW_VOLTAGE_V
    didt_a_per_s = CURRENT_A / (POST_MILLER_ID_FALL_US * 1e-6)
    absolute_loop_ceiling_nh = voltage_headroom_v / didt_a_per_s * 1e9
    via_barrel_area_mm2 = math.pi * POWER_VIA_DRILL_MM * MIN_HOLE_WALL_COPPER_MM
    hot_factor = hot_resistivity() / COPPER_RESISTIVITY_20_OHM_M

    return f"""# Q2-C100 Pre-FAB Screening

Status: `CALCULATION SCREEN COMPLETE / THERMAL, EXTRACTION AND FAB-REVIEW OPEN`

This report is generated by `tools/generate_q2_coupon_prefab_screening.py`.
It is an auditable arithmetic screen, not an IPC-2152 ampacity claim, a thermal
simulation, a field-solver extraction, supplier DFM approval, or permission to
fabricate or energize Q2-C100.

## Fixed inputs

- qualification current: `{CURRENT_A:.1f} A`;
- copper temperature used only for resistance: `{COPPER_TEMPERATURE_C:.0f} degC`;
- outer-layer finished copper target: `{OUTER_COPPER_MM * 1000:.0f} um`;
- copper resistivity at 20 degC: `{COPPER_RESISTIVITY_20_OHM_M:.4e} ohm*m`;
- copper temperature coefficient: `{COPPER_TEMPERATURE_COEFFICIENT_PER_C:.5f} /degC`;
- calculated 150 degC resistivity multiplier: `{hot_factor:.4f}`;
- power via drill and minimum specified wall copper: `{POWER_VIA_DRILL_MM:.2f} mm / {MIN_HOLE_WALL_COPPER_MM * 1000:.0f} um`;
- raw drain and waveform acceptance ceiling: `{RAW_VOLTAGE_V:.0f} V / {PEAK_ACCEPTANCE_V:.0f} V`;
- provisional maximum post-Miller current-fall bound from ADR-0018: `{POST_MILLER_ID_FALL_US:.2f} us`.

## Copper screen result

The five named straight correlation-path corridors sum to a lower-bound hot
resistance of `{total_hot_resistance_mohm:.4f} mOhm` and `{total_hot_loss_w:.4f} W`
at 40 A. This deliberately excludes TOLL lands, source buses/spokes, via
barrels, REDCUBE contacts, copper spreading, unequal layer sharing and external
fixture conductors. It therefore cannot be used as the coupon temperature rise
or as a 40 A pass result.

The source connection is no longer a single serial 0.8 mm neck. Every one of
the seven TOLL source pads has a separate 0.8 mm spoke into a 4.0 mm collection
bus. Their aggregate geometric cross-section is `{7 * 0.8 * OUTER_COPPER_MM:.4f} mm^2`,
but current sharing remains a simulation/inspection item.

At the minimum `{MIN_HOLE_WALL_COPPER_MM * 1000:.0f} um` hole-wall copper, one
0.60 mm via barrel has `{via_barrel_area_mm2:.4f} mm^2` copper cross-section.
The conservative screen in the CSV assumes that one five-via row carries all
40 A; the supplier must confirm finished plating and the field solver must
confirm sharing between the two rows.

## Loop-inductance bound

The 120 V waveform acceptance ceiling leaves only `{voltage_headroom_v:.1f} V`
above 101 V. If 40 A falls in the provisional `{POST_MILLER_ID_FALL_US:.2f} us`
bound, `L <= deltaV/(dI/dt)` gives an absolute `{absolute_loop_ceiling_nh:.2f} nH`
ceiling before probe uncertainty and other overshoot contributors. This is not
an extracted value or a design pass. The complete coupon plus fixture and
measurement loop must be extracted with the selected stackup, and the
uncertainty-expanded measured peak must still satisfy the 120 V acceptance
criterion.

## Required closeout

`FAB-REVIEW` remains open until all of the following exist:

1. Supplier-confirmed stackup, finished copper/plating tolerances, press-fit
   compatibility and DFM disposition.
2. DC current-density and electrothermal field solution covering TOLL lands,
   source fanout, every layer transition, terminals and the external fixture.
3. Extracted commutation/measurement-loop inductance including connector,
   busbar, load, supply return and probe attachments.
4. Independent review of solver models, boundary conditions, mesh convergence,
   material properties and safety margins.
5. The selected Micro-Fit header 2.0 mm fit/DFM, exact rated instrument/probe
   MPNs, effective CTRL_VS capacitance proof and the full interlocked
   laboratory safety system required by the fabrication gate.

The row-by-row calculations and their explicit assumptions are in
`Q2-C100-pre-fab-screening.csv`.
"""


def expected_files() -> dict[Path, str]:
    rows = generated_rows()
    return {
        CSV_PATH: render_csv(rows),
        REPORT_PATH: render_report(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when committed outputs are stale")
    args = parser.parse_args()

    stale: list[Path] = []
    for path, content in expected_files().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        else:
            path.write_text(content, encoding="utf-8")

    if stale:
        relative = ", ".join(str(path.relative_to(ROOT)) for path in stale)
        raise SystemExit(f"ERROR: stale Q2-C100 pre-FAB screening output: {relative}")
    if not args.check:
        print("Generated Q2-C100 pre-FAB screening evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
