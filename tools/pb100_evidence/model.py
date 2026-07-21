"""Reviewed constants used by the PB-100 release-evidence calculations.

These values deliberately live outside the validator.  The generator calculates
review artifacts from one source of truth; the validator checks that the checked-
in artifacts are fresh and satisfy release invariants.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mosfet:
    mpn: str
    orderable_mpn: str
    package: str
    voltage_v: float
    rds_on_max_25c_ohm: float
    hot_multiplier: float
    gate_charge_max_c: float
    rth_jc_max_k_per_w: float
    max_junction_c: float
    soa_10us_60v_min_a: float
    datasheet: str

    @property
    def rds_on_hot_ohm(self) -> float:
        return self.rds_on_max_25c_ohm * self.hot_multiplier


@dataclass(frozen=True)
class OutputClass:
    name: str
    channels: str
    fuse_a: float
    configured_a: float
    startup_a: float
    startup_s: float
    transient_a: float
    transient_s: float
    sense_ohm: float
    riwrn_ohm: float
    riscp_ohm: float
    ctmr_f: float
    rimon_ohm: float
    imon_full_scale_a: float


@dataclass(frozen=True)
class TransientModel:
    waveform: str
    open_circuit_v: float
    tvs_clamp_25c_v: float
    tvs_test_current_a: float
    tvs_initial_junction_c: float
    tvs_temp_coefficient_per_c: float
    reference_temperature_c: float
    loop_inductance_h: float
    current_slew_a_per_s: float
    uncertainty_v: float
    lm74700_recommended_max_v: float
    lm74700_absolute_max_v: float
    mosfet_limit_v: float
    controller_limit_v: float

    @property
    def source_resistance_ohm(self) -> float:
        return (self.open_circuit_v - self.tvs_clamp_25c_v) / self.tvs_test_current_a

    @property
    def hot_clamp_v(self) -> float:
        delta_c = self.tvs_initial_junction_c - self.reference_temperature_c
        return self.tvs_clamp_25c_v * (1 + self.tvs_temp_coefficient_per_c * delta_c)

    @property
    def loop_overshoot_v(self) -> float:
        return self.loop_inductance_h * self.current_slew_a_per_s

    @property
    def bounded_stress_v(self) -> float:
        return self.hot_clamp_v + self.loop_overshoot_v + self.uncertainty_v


MOSFET = Mosfet(
    mpn="IAUT300N08S5N012",
    orderable_mpn="IAUT300N08S5N012ATMA2",
    package="PG-HSOF-8-1 (TOLL)",
    voltage_v=80.0,
    rds_on_max_25c_ohm=0.0012,
    # Conservative pre-layout multiplier read from the normalized RDS(on) curve.
    hot_multiplier=2.1,
    gate_charge_max_c=231e-9,
    rth_jc_max_k_per_w=0.4,
    max_junction_c=175.0,
    # Conservative digitized lower bound from the 25 C, 10 us SOA curve.
    soa_10us_60v_min_a=200.0,
    datasheet=(
        "https://www.infineon.com/assets/row/public/documents/10/49/"
        "infineon-iaut300n08s5n012-datasheet-en.pdf"
    ),
)


OUTPUT_CLASSES = (
    OutputClass(
        name="High current",
        channels="OUT2",
        fuse_a=20.0,
        configured_a=18.0,
        startup_a=30.0,
        startup_s=0.100,
        transient_a=80.0,
        transient_s=0.004,
        sense_ohm=0.0005,
        riwrn_ohm=67_300.0,
        riscp_ohm=2_610.0,
        ctmr_f=680e-9,
        rimon_ohm=12_100.0,
        imon_full_scale_a=60.0,
    ),
    OutputClass(
        name="Medium current 15 A",
        channels="OUT1",
        fuse_a=15.0,
        configured_a=12.0,
        startup_a=20.0,
        startup_s=0.100,
        transient_a=50.0,
        transient_s=0.004,
        sense_ohm=0.001,
        riwrn_ohm=49_900.0,
        riscp_ohm=3_400.0,
        ctmr_f=680e-9,
        rimon_ohm=12_100.0,
        imon_full_scale_a=30.0,
    ),
    OutputClass(
        name="Medium current 10 A",
        channels="OUT3 OUT4 OUT6 OUT7 OUT10",
        fuse_a=10.0,
        configured_a=8.0,
        startup_a=13.0,
        startup_s=0.100,
        transient_a=35.0,
        transient_s=0.004,
        sense_ohm=0.0015,
        riwrn_ohm=49_900.0,
        riscp_ohm=3_830.0,
        ctmr_f=680e-9,
        rimon_ohm=12_100.0,
        imon_full_scale_a=20.0,
    ),
    OutputClass(
        name="Low current 5 A",
        channels="OUT5 OUT8 OUT9",
        fuse_a=5.0,
        configured_a=4.0,
        startup_a=6.5,
        startup_s=0.100,
        transient_a=17.5,
        transient_s=0.004,
        sense_ohm=0.003,
        riwrn_ohm=49_900.0,
        riscp_ohm=3_740.0,
        ctmr_f=680e-9,
        rimon_ohm=12_100.0,
        imon_full_scale_a=10.0,
    ),
)


TRANSIENT = TransientModel(
    waveform="100 V open-circuit 10/1000 us bounded source",
    open_circuit_v=100.0,
    tvs_clamp_25c_v=53.3,
    tvs_test_current_a=124.0,
    tvs_initial_junction_c=125.0,
    tvs_temp_coefficient_per_c=0.00091,
    reference_temperature_c=25.0,
    loop_inductance_h=20e-9,
    current_slew_a_per_s=15e6,
    uncertainty_v=1.0,
    lm74700_recommended_max_v=60.0,
    lm74700_absolute_max_v=65.0,
    mosfet_limit_v=80.0,
    controller_limit_v=100.0,
)
