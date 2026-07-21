"""PB-100 ISO 16750-2 load-dump electrical and thermal screening model."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import exp, log

from .model import LOAD_DUMP, TVS


@dataclass(frozen=True)
class LoadDumpResult:
    source_voltage_v: float
    source_resistance_ohm: float
    duration_s: float
    initial_junction_c: float
    peak_current_a: float
    peak_clamp_v: float
    peak_power_w: float
    energy_j: float
    zth_jm_c_per_w: float
    peak_junction_c: float
    recommended_margin_v: float
    result: str


def transient_thermal_impedance(duration_s: float) -> float:
    return sum(
        resistance * (1.0 - exp(-duration_s / time_constant))
        for resistance, time_constant in zip(
            TVS.foster_thermal_resistances_c_per_w,
            TVS.foster_thermal_time_constants_s,
            strict=True,
        )
    )


def _electrical_point(source_voltage_v: float, junction_c: float, source_resistance_ohm: float) -> tuple[float, float]:
    temperature_factor = 1.0 + TVS.temp_coefficient_per_c * (
        junction_c - TVS.reference_temperature_c
    )
    vbr_v = TVS.vbr_max_25c_v * temperature_factor + TVS.voltage_uncertainty_v
    dynamic_resistance_ohm = TVS.dynamic_resistance_25c_ohm * temperature_factor
    current_a = max(
        0.0,
        (source_voltage_v - vbr_v) / (source_resistance_ohm + dynamic_resistance_ohm),
    )
    clamp_v = vbr_v + current_a * dynamic_resistance_ohm + TVS.loop_overshoot_v
    return current_a, clamp_v


def evaluate_corner(
    source_voltage_v: float,
    source_resistance_ohm: float,
    duration_s: float,
    initial_junction_c: float,
) -> LoadDumpResult:
    step_s = min(0.0001, duration_s / 1000.0)
    steps = round(duration_s / step_s)
    thermal_states_c = [0.0] * len(TVS.foster_thermal_resistances_c_per_w)
    peak_current_a = 0.0
    peak_clamp_v = 0.0
    peak_power_w = 0.0
    peak_junction_c = initial_junction_c
    energy_j = 0.0

    for step in range(steps + 1):
        time_s = step * step_s
        source_at_time_v = LOAD_DUMP.battery_voltage_v + (
            source_voltage_v - LOAD_DUMP.battery_voltage_v
        ) * exp(-log(10.0) * time_s / duration_s)
        junction_c = initial_junction_c + sum(thermal_states_c)
        # The part is already outside its characterized range above TJ(max).
        # Holding the electrical temperature factor at TJ(max) avoids claiming
        # accuracy after failure while retaining the dissipated-energy screen.
        electrical_junction_c = min(junction_c, TVS.max_junction_c)
        current_a, clamp_v = _electrical_point(
            source_at_time_v,
            electrical_junction_c,
            source_resistance_ohm,
        )
        power_w = current_a * clamp_v
        peak_current_a = max(peak_current_a, current_a)
        peak_clamp_v = max(peak_clamp_v, clamp_v)
        peak_power_w = max(peak_power_w, power_w)
        peak_junction_c = max(peak_junction_c, junction_c)
        if step == steps:
            break
        energy_j += power_w * step_s
        for index, (resistance, time_constant) in enumerate(
            zip(
                TVS.foster_thermal_resistances_c_per_w,
                TVS.foster_thermal_time_constants_s,
                strict=True,
            )
        ):
            decay = exp(-step_s / time_constant)
            thermal_states_c[index] = (
                thermal_states_c[index] * decay
                + power_w * resistance * (1.0 - decay)
            )

    recommended_margin_v = TVS.lm74700_recommended_max_v - peak_clamp_v
    result = "FAIL" if (
        peak_junction_c >= TVS.max_junction_c
        or recommended_margin_v < LOAD_DUMP.required_recommended_margin_v
    ) else "SCREENING PASS"
    return LoadDumpResult(
        source_voltage_v=source_voltage_v,
        source_resistance_ohm=source_resistance_ohm,
        duration_s=duration_s,
        initial_junction_c=initial_junction_c,
        peak_current_a=peak_current_a,
        peak_clamp_v=peak_clamp_v,
        peak_power_w=peak_power_w,
        energy_j=energy_j,
        zth_jm_c_per_w=transient_thermal_impedance(duration_s),
        peak_junction_c=peak_junction_c,
        recommended_margin_v=recommended_margin_v,
        result=result,
    )


def load_dump_results() -> tuple[LoadDumpResult, ...]:
    return tuple(
        evaluate_corner(source_voltage_v, source_resistance_ohm, duration_s, initial_junction_c)
        for source_voltage_v, source_resistance_ohm, duration_s, initial_junction_c in product(
            LOAD_DUMP.source_voltages_v,
            LOAD_DUMP.source_resistances_ohm,
            LOAD_DUMP.durations_s,
            LOAD_DUMP.initial_junctions_c,
        )
    )
