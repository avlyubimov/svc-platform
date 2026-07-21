"""Render deterministic PB-100 release evidence as CSV text."""

from __future__ import annotations

import csv
import io

from .model import LOAD_DUMP, LOAD_DUMP_THERMAL_STATES, MOSFET, SURGE_STOPPER, TVS
from .power import (
    BOOTSTRAP_F,
    Q1_AMBIENT_C,
    Q1_CONTINUOUS_A,
    Q1_TARGET_JUNCTION_C,
    SHORT_CIRCUIT_SHUTDOWN_MAX_S,
    bootstrap_minimum_f,
    output_results,
    q1_conduction_w,
    q1_max_ambient_to_junction_k_per_w,
)
from .transient import load_dump_results


def _csv(rows: list[list[str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerows(rows)
    return stream.getvalue()


def render_transient() -> str:
    rows = [[
        "Us V", "Ri ohm", "td ms", "Initial Tj C", "Peak TVS current A",
        "Peak clamp V", "Peak TVS power W", "TVS energy J", "Typical ZthJM C/W",
        "Predicted peak Tj C", "Margin to LM74700 60 V", "Result", "Basis",
    ]]
    basis = (
        f"ISO 16750-2 Test A envelope; {TVS.mpn} max VBR/clamp/tolerance; "
        "temperature coefficient and self-heating; typical Vishay ZthJM Foster fit; "
        f"{LOAD_DUMP.pulse_count} pulses at {LOAD_DUMP.pulse_interval_s:.0f} s require final validation"
    )
    for result in load_dump_results():
        rows.append([
            f"{result.source_voltage_v:.0f}",
            f"{result.source_resistance_ohm:g}",
            f"{result.duration_s * 1000:.0f}",
            f"{result.initial_junction_c:.0f}",
            f"{result.peak_current_a:.2f}",
            f"{result.peak_clamp_v:.2f}",
            f"{result.peak_power_w:.1f}",
            f"{result.energy_j:.2f}",
            f"{result.zth_jm_c_per_w:.3f}",
            f"{result.peak_junction_c:.1f}",
            f"{result.recommended_margin_v:.2f}",
            result.result,
            basis,
        ])
    return _csv(rows)


def render_surge_stopper() -> str:
    rows = [[
        "Us V", "Ri ohm", "td ms", "Rise time ms", "Thermal state", "Ambient C",
        "Preload current A", "Initial Tj C", "OV cutoff min V",
        "OV cutoff nominal V", "OV cutoff max V", "Q2 linear-mode ID A",
        "OV deglitch us", "Input rise during OV delay V",
        "Pre-layout commutation overshoot allowance V", "Protected-node peak budget V",
        "Protected MOSFET rating V", "Protected-node margin V",
        "Fully-enhanced Q2 VDS V", "Deglitch conduction energy J",
        "Qgd max nC", "Miller transition bound us",
        "Miller VDS-rise energy bound J", "Qgs max nC",
        "Post-Miller ID-fall bound us", "Post-Miller ID-fall energy bound J",
        "Complete linear-transition bound us", "Complete transition energy bound J",
        "SOA reference VDS V", "SOA reference pulse us",
        "Temperature-derated SOA current limit A", "SOA current margin x",
        "Pulse count", "Pulse spacing s", "Q2 VDS margin V", "Load response",
        "Protected-node screen", "SOA screen", "Result", "Basis",
    ]]
    basis = (
        "TI ISO 16750-2 Test A rise time is 5-10ms; input slew uses the full "
        "Us-minus-UA change over tr. Protected peak budget equals maximum OV threshold "
        "plus input rise during 7us deglitch plus a 4.5V pre-layout commutation allowance. "
        "Q2 stays fully enhanced during deglitch. Miller VDS rise uses maximum 40nC Qgd "
        "and post-Miller ID fall conservatively uses the complete maximum 52nC Qgs, both "
        "with minimum 128mA HGATE sink. "
        "Infineon Tc=25C single-pulse 1us SOA curve uses a conservative digitized "
        "500A lower bound at 101V scaled by junction-temperature headroom to 175C. "
        "Qg segments are design-specified at 75V/123A and not production-tested, so this "
        "charge envelope is provisional rather than a qualified maximum-bound trajectory"
    )
    for source_voltage_v in LOAD_DUMP.source_voltages_v:
        for source_resistance_ohm in LOAD_DUMP.source_resistances_ohm:
            linear_mode_current_a = SURGE_STOPPER.continuous_current_a
            fully_enhanced_vds_v = (
                linear_mode_current_a * SURGE_STOPPER.cutoff_mosfet_rds_on_hot_ohm
            )
            deglitch_energy_j = (
                fully_enhanced_vds_v
                * linear_mode_current_a
                * SURGE_STOPPER.hgate_turnoff_delay_max_s
            )
            miller_energy_j = (
                source_voltage_v
                * linear_mode_current_a
                * SURGE_STOPPER.miller_transition_s
            )
            current_fall_energy_j = (
                source_voltage_v
                * linear_mode_current_a
                * 0.5
                * SURGE_STOPPER.post_miller_current_fall_s
            )
            for duration_s in LOAD_DUMP.durations_s:
                for rise_time_s in LOAD_DUMP.rise_times_s:
                    input_rise_v = SURGE_STOPPER.input_rise_during_ov_delay_v(
                        source_voltage_v,
                        LOAD_DUMP.battery_voltage_v,
                        rise_time_s,
                    )
                    protected_peak_v = SURGE_STOPPER.protected_node_peak_budget_v(
                        source_voltage_v,
                        LOAD_DUMP.battery_voltage_v,
                        rise_time_s,
                    )
                    protected_margin_v = (
                        SURGE_STOPPER.protected_mosfet_voltage_v - protected_peak_v
                    )
                    for thermal_state in LOAD_DUMP_THERMAL_STATES:
                        initial_junction_c = SURGE_STOPPER.steady_initial_junction_c(
                            thermal_state.ambient_c,
                            thermal_state.preload_current_a,
                        )
                        soa_current_limit_a = SURGE_STOPPER.soa_current_limit_a(
                            initial_junction_c
                        )
                        soa_margin = soa_current_limit_a / linear_mode_current_a
                        protected_node_passed = protected_margin_v > 0.0
                        soa_screen_passed = (
                            SURGE_STOPPER.cutoff_max_v <= 55.0
                            and SURGE_STOPPER.cutoff_mosfet_voltage_v > source_voltage_v
                            and protected_node_passed
                            and SURGE_STOPPER.linear_transition_s
                            <= SURGE_STOPPER.cutoff_mosfet_soa_reference_pulse_s
                            and soa_margin >= 1.5
                        )
                        rows.append([
                        f"{source_voltage_v:.0f}",
                        f"{source_resistance_ohm:g}",
                        f"{duration_s * 1000:.0f}",
                        f"{rise_time_s * 1000:.0f}",
                        thermal_state.name,
                        f"{thermal_state.ambient_c:.0f}",
                        f"{thermal_state.preload_current_a:.0f}",
                        f"{initial_junction_c:.0f}",
                        f"{SURGE_STOPPER.cutoff_min_v:.2f}",
                        f"{SURGE_STOPPER.cutoff_nominal_v:.2f}",
                        f"{SURGE_STOPPER.cutoff_max_v:.2f}",
                        f"{linear_mode_current_a:.2f}",
                        f"{SURGE_STOPPER.hgate_turnoff_delay_max_s * 1e6:.2f}",
                        f"{input_rise_v:.4f}",
                        f"{SURGE_STOPPER.protected_node_overshoot_allowance_v:.2f}",
                        f"{protected_peak_v:.2f}",
                        f"{SURGE_STOPPER.protected_mosfet_voltage_v:.0f}",
                        f"{protected_margin_v:.2f}",
                        f"{fully_enhanced_vds_v:.3f}",
                        f"{deglitch_energy_j:.6f}",
                        f"{SURGE_STOPPER.cutoff_mosfet_gate_drain_charge_max_c * 1e9:.0f}",
                        f"{SURGE_STOPPER.miller_transition_s * 1e6:.2f}",
                        f"{miller_energy_j:.6f}",
                        f"{SURGE_STOPPER.cutoff_mosfet_gate_source_charge_max_c * 1e9:.0f}",
                        f"{SURGE_STOPPER.post_miller_current_fall_s * 1e6:.2f}",
                        f"{current_fall_energy_j:.6f}",
                        f"{SURGE_STOPPER.linear_transition_s * 1e6:.2f}",
                        f"{miller_energy_j + current_fall_energy_j:.6f}",
                        f"{SURGE_STOPPER.cutoff_mosfet_soa_reference_voltage_v:.0f}",
                        f"{SURGE_STOPPER.cutoff_mosfet_soa_reference_pulse_s * 1e6:.0f}",
                        f"{soa_current_limit_a:.2f}",
                        f"{soa_margin:.2f}",
                        f"{LOAD_DUMP.pulse_count}",
                        f"{LOAD_DUMP.pulse_interval_s:.0f}",
                        f"{SURGE_STOPPER.cutoff_mosfet_voltage_v - source_voltage_v:.2f}",
                        "DISCONNECT",
                        "PASS" if protected_node_passed else "FAIL",
                        "PASS" if soa_screen_passed else "FAIL",
                        "CONDITIONAL PRE-LAYOUT" if soa_screen_passed else "FAIL",
                        basis,
                    ])
    return _csv(rows)


def render_q2() -> str:
    current_a = SURGE_STOPPER.continuous_current_a
    loss_25c_w = current_a**2 * SURGE_STOPPER.cutoff_mosfet_rds_on_max_25c_ohm
    loss_hot_w = current_a**2 * SURGE_STOPPER.cutoff_mosfet_rds_on_hot_ohm
    target_junction_c = 150.0
    ambient_c = 125.0
    maximum_path = SURGE_STOPPER.target_full_thermal_path_k_per_w
    hot_initial_junction_c = SURGE_STOPPER.steady_initial_junction_c(
        ambient_c,
        current_a,
    )
    hot_soa_limit_a = SURGE_STOPPER.soa_current_limit_a(hot_initial_junction_c)
    hot_soa_margin = hot_soa_limit_a / current_a
    protected_peak_v = SURGE_STOPPER.protected_node_peak_budget_v(
        max(LOAD_DUMP.source_voltages_v),
        LOAD_DUMP.battery_voltage_v,
        min(LOAD_DUMP.rise_times_s),
    )
    protected_margin_v = SURGE_STOPPER.protected_mosfet_voltage_v - protected_peak_v
    rows = [
        ["Evidence item", "Value", "Unit", "Basis", "Result"],
        ["Exact orderable MPN", SURGE_STOPPER.cutoff_mosfet_mpn, "", "Infineon automotive 150 V TOLL", "PASS"],
        ["Voltage rating", f"{SURGE_STOPPER.cutoff_mosfet_voltage_v:.0f}", "V", "Datasheet minimum V(BR)DSS", "PASS"],
        ["RDS(on) max at 25 C", f"{SURGE_STOPPER.cutoff_mosfet_rds_on_max_25c_ohm * 1e3:.2f}", "mOhm", "10 V / 100 A datasheet maximum", "INPUT"],
        ["Hot multiplier", f"{SURGE_STOPPER.cutoff_mosfet_hot_multiplier:.2f}", "x", "Conservative bound from datasheet typical RDS(on)-versus-Tj curve", "INPUT"],
        ["Hot review RDS(on)", f"{SURGE_STOPPER.cutoff_mosfet_rds_on_hot_ohm * 1e3:.2f}", "mOhm", "25 C maximum times hot multiplier", "PASS PRE-LAYOUT"],
        ["Continuous input current", f"{current_a:.0f}", "A", "ADR-0008 board-current budget", "INPUT"],
        ["Q2 conduction loss at 25 C maximum", f"{loss_25c_w:.3f}", "W", "I^2 times 25 C maximum RDS(on)", "PASS"],
        ["Q2 hot conduction loss", f"{loss_hot_w:.3f}", "W", "I^2 times hot review RDS(on)", "PASS PRE-LAYOUT"],
        ["RthJC max", f"{SURGE_STOPPER.cutoff_mosfet_rth_jc_max_k_per_w:.2f}", "K/W", "Datasheet maximum", "INPUT"],
        ["Ambient design point", f"{ambient_c:.1f}", "degC", "Worst-case enclosure ambient requirement", "INPUT"],
        ["Target junction ceiling", f"{target_junction_c:.1f}", "degC", f"Design target below {SURGE_STOPPER.cutoff_mosfet_max_junction_c:.0f} C device maximum", "PASS PRE-LAYOUT"],
        ["Maximum full thermal path", f"{maximum_path:.2f}", "K/W", "(Tj target - ambient) / Q2 hot conduction loss", "POST-LAYOUT LIMIT"],
        ["Hot steady initial junction", f"{hot_initial_junction_c:.1f}", "degC", "Tambient + I^2 RDS(on)hot times target full thermal path", "INPUT TO SOA"],
        ["Maximum gate-drain charge", f"{SURGE_STOPPER.cutoff_mosfet_gate_drain_charge_max_c * 1e9:.0f}", "nC", "Datasheet Qgd maximum; design-specified at 75 V / 123 A", "CONDITIONAL INPUT"],
        ["Maximum gate-source charge", f"{SURGE_STOPPER.cutoff_mosfet_gate_source_charge_max_c * 1e9:.0f}", "nC", "Complete datasheet Qgs maximum conservatively bounds the post-Miller current-fall charge; design-specified at 75 V / 123 A", "CONDITIONAL INPUT"],
        ["OV deglitch maximum", f"{SURGE_STOPPER.hgate_turnoff_delay_max_s * 1e6:.2f}", "us", "Q2 remains fully enhanced during the controller deglitch interval", "SEPARATE FROM LINEAR MODE"],
        ["Miller transition bound", f"{SURGE_STOPPER.miller_transition_s * 1e6:.2f}", "us", "Qgd maximum divided by minimum HGATE sink current", "PROVISIONAL"],
        ["Post-Miller current-fall bound", f"{SURGE_STOPPER.post_miller_current_fall_s * 1e6:.2f}", "us", "Complete Qgs maximum divided by minimum HGATE sink current", "PROVISIONAL"],
        ["Complete linear-transition bound", f"{SURGE_STOPPER.linear_transition_s * 1e6:.2f}", "us", "Miller VDS-rise plus post-Miller ID-fall charge envelope", "PROVISIONAL"],
        ["ISO load-dump rise-time range", "5-10", "ms", "TI application brief Table 1", "INPUT"],
        ["Pre-layout commutation overshoot allowance", f"{SURGE_STOPPER.protected_node_overshoot_allowance_v:.2f}", "V", "Reserved above OV threshold plus input rise; post-layout extraction must remain within this allocation", "DESIGN LIMIT"],
        ["Worst protected-node peak budget", f"{protected_peak_v:.2f}", "V", "Maximum OV threshold plus 101 V / 5 ms input rise during 7 us delay plus commutation allowance", "PROVISIONAL PASS"],
        ["Protected-node margin to 80 V Q1", f"{protected_margin_v:.2f}", "V", "Selected protected MOSFET rating minus worst protected-node peak budget", "PROVISIONAL PASS"],
        ["Hot-corner SOA current limit", f"{hot_soa_limit_a:.2f}", "A", "Conservative 101 V / 1 us curve bound derated from 25 C to the 150 C initial junction", "PROVISIONAL"],
        ["Hot-corner SOA margin", f"{hot_soa_margin:.2f}", "x", "Temperature-derated current limit divided by 40 A", "PROVISIONAL PASS"],
        ["Repeated-pulse condition", f"{LOAD_DUMP.pulse_count} pulses / {LOAD_DUMP.pulse_interval_s:.0f} s spacing", "", "Generated corners include 150 C initial junction after steady 40 A preload", "CONDITIONAL PRE-LAYOUT"],
        ["Pre-layout gate status", "Conditional", "", "Qgd/Qgs are not guaranteed at the 101 V / 40 A corner and graph-derived SOA needs a qualified maximum-bound trajectory", "BLOCKED"],
        ["Physical verification boundary", "Extracted copper thermal interface enclosure and common-source overshoot", "", "Post-layout evidence and PB-BENCH-004 must verify dynamic SOA and recovery", "MANDATORY POST-LAYOUT"],
    ]
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
    maximum_path = q1_max_ambient_to_junction_k_per_w()
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
        ["Cooling architecture", "Passive PCB copper plus thermal pad to metal enclosure", "", "Active cooling is not selected", "PASS PRE-LAYOUT"],
        ["Ambient design point", f"{Q1_AMBIENT_C:.1f}", "degC", "Worst-case enclosure ambient requirement", "INPUT"],
        ["Target junction ceiling", f"{Q1_TARGET_JUNCTION_C:.1f}", "degC", f"Design target below {MOSFET.max_junction_c:.0f} C device maximum", "PASS PRE-LAYOUT"],
        ["Maximum full thermal path", f"{maximum_path:.2f}", "K/W", "(Tj target - ambient) / Q1 conduction loss", "POST-LAYOUT LIMIT"],
        ["PCB copper condition", "Plane/polygon plus passive enclosure heat path; no trace-only 40 A claim", "", "Layout extraction and PB-BENCH-010 verify the full thermal path", "MANDATORY POST-LAYOUT"],
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
            "U1 active cutoff and Q2 raw-side MOSFET",
            "LM74930QRGERQ1 plus IAUTN15S6N025ATMA1",
            "VQFN-24 RGE plus PG-HSOF-8-1 TOLL; exposed-pad and segmented-paste review",
            "LM74800-Q1 family plus 150 V automotive TOLL after full revalidation",
            "LM74900-Q1 family plus 150 V automotive LFPAK after full revalidation",
            "SPI exposed-pad/paste coverage; AOI polarity; Q2 voiding and first-article review",
            "PASS PRE-LAYOUT",
            "Recheck exact suffix, quote, DFM, extracted SOA and first article before prototype release",
        ],
        [
            "D1 legacy TVS footprint",
            "SM8S33AHM3/I DNP; not an approved load-dump solution",
            "DO-218AC footprint retained unpopulated for controlled engineering evidence",
            "SLD8S33A rejected comparison only",
            "DM8W33AQ-13 and SM8S33A-Q rejected comparisons only",
            "Independent BOM no-fit plus AOI/visual first-article verification",
            "PASS DNP",
            "Reject any BOM or CPL that populates D1 as the Rev.1 load-dump solution",
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
            "TOLL/VSSOP/VQFN-24 RGE/DO-218AC DNP/FX18 processes require job-specific DFM",
            "Authorized-distributor reel supplied to assembler",
            "Move assembly platform only after DFM review",
            "Package polarity, MSL, reel/tray orientation, DNP, paste and rework notes",
            "PASS PRE-LAYOUT",
            "Actual quote, DFM response and first article remain production gates",
        ],
    ]
    return _csv(rows)
