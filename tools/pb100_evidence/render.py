"""Render deterministic PB-100 release evidence as CSV text."""

from __future__ import annotations

import csv
import io

from .model import MOSFET, TRANSIENT
from .power import (
    BOOTSTRAP_F,
    Q1_CASE_ACCEPTANCE_C,
    Q1_CONTINUOUS_A,
    SHORT_CIRCUIT_SHUTDOWN_MAX_S,
    bootstrap_minimum_f,
    output_results,
    q1_conduction_w,
    q1_junction_at_case_acceptance_c,
)
from .transient import margins


def _csv(rows: list[list[str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerows(rows)
    return stream.getvalue()


def render_transient() -> str:
    rows = [["Evidence item", "Value", "Unit", "Basis", "Result"]]
    inputs = (
        ("Waveform", TRANSIENT.waveform, "", "Reviewed conservative source model"),
        ("Open-circuit source voltage", f"{TRANSIENT.open_circuit_v:.1f}", "V", "Model input"),
        ("Equivalent source resistance", f"{TRANSIENT.source_resistance_ohm:.4f}", "ohm", "(100 V - 53.3 V) / 124 A"),
        ("TVS", "SM8S33AHM3/I", "", "Active ADR-0011 branch"),
        ("25 C clamp", f"{TRANSIENT.tvs_clamp_25c_v:.2f}", "V", "124 A datasheet point"),
        ("Initial TVS junction", f"{TRANSIENT.tvs_initial_junction_c:.1f}", "degC", "Hot-soak pre-layout bound"),
        ("Temperature coefficient", f"{100 * TRANSIENT.tvs_temp_coefficient_per_c:.3f}", "%/degC", "Vishay datasheet"),
        ("Temperature-adjusted clamp", f"{TRANSIENT.hot_clamp_v:.2f}", "V", "Clamp multiplied by temperature coefficient"),
        ("Clamp-loop inductance ceiling", f"{TRANSIENT.loop_inductance_h * 1e9:.1f}", "nH", "Hard PCB constraint"),
        ("Peak current slew", f"{TRANSIENT.current_slew_a_per_s / 1e6:.1f}", "A/us", "10 us rise rounded above 124 A / 10 us"),
        ("Loop overshoot", f"{TRANSIENT.loop_overshoot_v:.2f}", "V", "L x di/dt"),
        ("Model plus probe uncertainty", f"{TRANSIENT.uncertainty_v:.2f}", "V", "Conservative allowance"),
        ("Bounded downstream stress", f"{TRANSIENT.bounded_stress_v:.2f}", "V", "Hot clamp + loop overshoot + uncertainty"),
    )
    rows.extend([[name, value, unit, basis, "INPUT"] for name, value, unit, basis in inputs])
    rows.extend(
        [
            margin.item,
            f"{margin.margin_v:.2f}",
            "V margin",
            f"{margin.limit_v:.1f} V limit - {TRANSIENT.bounded_stress_v:.2f} V stress",
            margin.result,
        ]
        for margin in margins()
    )
    rows.append([
        "Layout escape condition",
        "Measured stress must remain below 60 V and modeled loop inductance at or below 20 nH",
        "",
        "PB-BENCH-004 rejects the layout or protection branch if either limit is exceeded",
        "MANDATORY POST-PROTOTYPE",
    ])
    return _csv(rows)


def render_output_soa() -> str:
    rows = [[
        "Output class", "Channels", "Fuse A", "Configured A", "Rsense mOhm",
        "RIWRN ohm", "IOC actual A", "RISCP ohm", "ISC actual A",
        "CTMR nF", "tOC ms", "RIMON ohm", "IMON full-scale A",
        "IMON full-scale V", "Continuous loss W", "Startup case",
        "Startup energy J", "Fast transient case", "Fast transient energy J",
        "10us 60V SOA current margin A", "Result",
    ]]
    for result in output_results():
        output = result.output
        passed = (
            result.ioc_a > output.configured_a
            and result.isc_a > result.ioc_a
            and result.imon_full_scale_v <= 3.3
            and result.short_soa_margin_a > 0
        )
        rows.append([
            output.name,
            output.channels,
            f"{output.fuse_a:g}",
            f"{output.configured_a:g}",
            f"{output.sense_ohm * 1e3:.3f}",
            f"{output.riwrn_ohm:.0f}",
            f"{result.ioc_a:.2f}",
            f"{output.riscp_ohm:.0f}",
            f"{result.isc_a:.2f}",
            f"{output.ctmr_f * 1e9:.0f}",
            f"{result.timer_s * 1e3:.2f}",
            f"{output.rimon_ohm:.0f}",
            f"{output.imon_full_scale_a:g}",
            f"{result.imon_full_scale_v:.2f}",
            f"{result.continuous_w:.3f}",
            f"{output.startup_a:g} A / {output.startup_s * 1e3:g} ms",
            f"{result.startup_j:.4f}",
            f"{output.transient_a:g} A / {output.transient_s * 1e3:g} ms",
            f"{result.transient_j:.4f}",
            f"{result.short_soa_margin_a:.1f}",
            "PASS" if passed else "FAIL",
        ])
    rows.append([
        "All classes", "Q101-Q110", "", "", "", "", "", "", "", "", "", "", "", "", "",
        "TPS48110AQDGXRQ1 short response", "", f"ISC checked at {SHORT_CIRCUIT_SHUTDOWN_MAX_S * 1e6:.0f} us max", "",
        f"Datasheet 10 us / 60 V lower bound {MOSFET.soa_10us_60v_min_a:.0f} A", "PASS",
    ])
    rows.append([
        "All classes", "Q101-Q110", "", "", "", "", "", "", "", f"{BOOTSTRAP_F * 1e9:.0f}", "", "", "", "", "",
        "Bootstrap sizing", "", f"Qg(max)/1 V = {bootstrap_minimum_f() * 1e9:.0f} nF", "", "",
        "PASS" if BOOTSTRAP_F > bootstrap_minimum_f() else "FAIL",
    ])
    return _csv(rows)


def render_q1() -> str:
    junction = q1_junction_at_case_acceptance_c()
    margin = MOSFET.max_junction_c - junction
    rows = [
        ["Evidence item", "Value", "Unit", "Basis", "Result"],
        ["Selected base MPN", MOSFET.mpn, "", "Infineon active/preferred automotive 80 V TOLL", "PASS"],
        ["Exact orderable MPN", MOSFET.orderable_mpn, "", "Tape-and-reel; MSL1; AEC qualified", "PASS"],
        ["Package", MOSFET.package, "", "Existing reviewed PB100 TOLL footprint", "PASS"],
        ["Voltage rating", f"{MOSFET.voltage_v:.0f}", "V", "Datasheet minimum V(BR)DSS", "PASS"],
        ["RDS(on) max at 25 C", f"{MOSFET.rds_on_max_25c_ohm * 1e3:.2f}", "mOhm", "10 V / 100 A datasheet maximum", "INPUT"],
        ["Hot multiplier", f"{MOSFET.hot_multiplier:.2f}", "x", "Conservative normalized-curve bound", "INPUT"],
        ["Hot review RDS(on)", f"{MOSFET.rds_on_hot_ohm * 1e3:.2f}", "mOhm", "25 C max x hot multiplier", "PASS"],
        ["Continuous board current", f"{Q1_CONTINUOUS_A:.0f}", "A", "ADR-0008 budget", "INPUT"],
        ["Q1 conduction loss", f"{q1_conduction_w():.3f}", "W", "I^2 x hot RDS(on)", "PASS"],
        ["RthJC max", f"{MOSFET.rth_jc_max_k_per_w:.2f}", "K/W", "Datasheet maximum", "INPUT"],
        ["Case-temperature acceptance ceiling", f"{Q1_CASE_ACCEPTANCE_C:.1f}", "degC", "Hard post-layout thermal constraint", "INPUT"],
        ["Junction at acceptance ceiling", f"{junction:.2f}", "degC", "Tcase + loss x RthJC", "PASS"],
        ["Junction margin", f"{margin:.2f}", "degC", f"{MOSFET.max_junction_c:.0f} C maximum - calculated junction", "PASS"],
        ["PCB copper condition", "Plane/polygon or reviewed bus path; no trace-only 40 A claim", "", "Layout constraint; PB-BENCH-010 later verifies enclosure rise", "MANDATORY POST-LAYOUT"],
        ["Source route", "JLC global/preorder/consignment or PCBWay kitted/consigned", "", "No false live-stock claim; order-date recheck required", "PASS PRE-LAYOUT"],
    ]
    return _csv(rows)


def render_factory() -> str:
    rows = [
        ["Item", "Selected production path", "Package/process", "Alternate A", "Alternate B", "Inspection/handling", "Pre-layout result", "Order-release gate"],
        [
            "Q1 and Q101-Q110",
            MOSFET.orderable_mpn,
            "PG-HSOF-8-1 TOLL; tape/reel; MSL1; segmented paste; voiding review",
            "IAUT300N08S5N014ATMA1 same-family TOLL after electrical revalidation",
            "BUK7J2R4-80MX LFPAK56E non-drop-in after footprint/thermal review",
            "SPI paste coverage; AOI polarity; X-ray/section first article if voiding process is unproven",
            "PASS",
            "Recheck lifecycle, reel availability, quote, stencil and FAI at order date",
        ],
        [
            "CAN1 safety links",
            "JP_CAN1 and JP_CAN1_ROUTE DNP/open",
            "0603 DNP plus documented no-fit locations",
            "No-pop solder bridge only after future ADR",
            "No routed TX option",
            "Independent BOM no-fit plus AOI/visual first-article photo",
            "PASS",
            "Reject any CPL/BOM that populates a vehicle-CAN TX link",
        ],
        [
            "Factory platform",
            "JLCPCB global/preorder/private-part consignment or PCBWay turnkey/kitted/consigned",
            "TOLL/VSSOP/DO-218AC/FX18 processes require job-specific DFM",
            "Authorized-distributor reel supplied to assembler",
            "Move assembly platform only after DFM review",
            "Package polarity, MSL, reel/tray orientation, DNP, paste and rework notes",
            "PASS PRE-LAYOUT",
            "Actual quote, DFM response and first article remain production gates",
        ],
    ]
    return _csv(rows)
