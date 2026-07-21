"""PB-100 output and Q1 electrical calculations."""

from __future__ import annotations

from dataclasses import dataclass

from .model import MOSFET, OUTPUT_CLASSES, OutputClass


RSET_OHM = 100.0
VOS_SET_WORST_V = 0.0002
TMR_CHARGE_A = 82e-6
TMR_TRIP_V = 1.2
BOOTSTRAP_F = 470e-9
BOOTSTRAP_ALLOWED_DIP_V = 1.0
Q1_CASE_ACCEPTANCE_C = 125.0
Q1_CONTINUOUS_A = 40.0
SHORT_CIRCUIT_SHUTDOWN_MAX_S = 5e-6


@dataclass(frozen=True)
class OutputResult:
    output: OutputClass
    ioc_a: float
    isc_a: float
    timer_s: float
    imon_full_scale_v: float
    continuous_w: float
    startup_w: float
    startup_j: float
    transient_w: float
    transient_j: float
    short_soa_margin_a: float


def calculate_output(output: OutputClass) -> OutputResult:
    ioc_a = (
        11.9 * RSET_OHM / output.riwrn_ohm - VOS_SET_WORST_V
    ) / output.sense_ohm
    isc_a = (output.riscp_ohm + 464.0) * 15.6e-6 / output.sense_ohm
    timer_s = output.ctmr_f * TMR_TRIP_V / TMR_CHARGE_A
    imon_full_scale_v = (
        output.imon_full_scale_a * output.sense_ohm + VOS_SET_WORST_V
    ) * 0.9 * output.rimon_ohm / RSET_OHM
    continuous_w = output.configured_a**2 * MOSFET.rds_on_hot_ohm
    startup_w = output.startup_a**2 * MOSFET.rds_on_hot_ohm
    transient_w = output.transient_a**2 * MOSFET.rds_on_hot_ohm
    return OutputResult(
        output=output,
        ioc_a=ioc_a,
        isc_a=isc_a,
        timer_s=timer_s,
        imon_full_scale_v=imon_full_scale_v,
        continuous_w=continuous_w,
        startup_w=startup_w,
        startup_j=startup_w * output.startup_s,
        transient_w=transient_w,
        transient_j=transient_w * output.transient_s,
        short_soa_margin_a=MOSFET.soa_10us_60v_min_a - isc_a,
    )


def output_results() -> tuple[OutputResult, ...]:
    return tuple(calculate_output(output) for output in OUTPUT_CLASSES)


def bootstrap_minimum_f() -> float:
    return MOSFET.gate_charge_max_c / BOOTSTRAP_ALLOWED_DIP_V


def q1_conduction_w() -> float:
    return Q1_CONTINUOUS_A**2 * MOSFET.rds_on_hot_ohm


def q1_junction_at_case_acceptance_c() -> float:
    return Q1_CASE_ACCEPTANCE_C + q1_conduction_w() * MOSFET.rth_jc_max_k_per_w
