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
class LoadDumpRequirement:
    source_voltages_v: tuple[float, ...]
    source_resistances_ohm: tuple[float, ...]
    durations_s: tuple[float, ...]
    initial_junctions_c: tuple[float, ...]
    battery_voltage_v: float
    pulse_count: int
    pulse_interval_s: float
    required_recommended_margin_v: float


@dataclass(frozen=True)
class TvsModel:
    mpn: str
    vbr_max_25c_v: float
    clamp_max_25c_v: float
    clamp_test_current_a: float
    temp_coefficient_per_c: float
    reference_temperature_c: float
    max_junction_c: float
    loop_inductance_h: float
    current_slew_a_per_s: float
    voltage_uncertainty_v: float
    foster_thermal_resistances_c_per_w: tuple[float, ...]
    foster_thermal_time_constants_s: tuple[float, ...]
    lm74700_recommended_max_v: float
    lm74700_absolute_max_v: float
    mosfet_limit_v: float
    controller_limit_v: float
    datasheet: str

    @property
    def dynamic_resistance_25c_ohm(self) -> float:
        return (self.clamp_max_25c_v - self.vbr_max_25c_v) / self.clamp_test_current_a

    @property
    def loop_overshoot_v(self) -> float:
        return self.loop_inductance_h * self.current_slew_a_per_s


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


LOAD_DUMP = LoadDumpRequirement(
    source_voltages_v=(79.0, 101.0),
    source_resistances_ohm=(0.5, 4.0),
    durations_s=(0.040, 0.400),
    initial_junctions_c=(25.0, 125.0),
    battery_voltage_v=13.5,
    pulse_count=10,
    pulse_interval_s=60.0,
    required_recommended_margin_v=5.0,
)


TVS = TvsModel(
    mpn="SM8S33AHM3/I",
    vbr_max_25c_v=40.6,
    clamp_max_25c_v=53.3,
    clamp_test_current_a=124.0,
    temp_coefficient_per_c=0.00091,
    reference_temperature_c=25.0,
    max_junction_c=175.0,
    loop_inductance_h=20e-9,
    current_slew_a_per_s=15e6,
    voltage_uncertainty_v=1.0,
    # Three-term Foster fit to the typical junction-to-mount transient thermal
    # impedance curve in Vishay document 98647, revision 14-Oct-2025.  Typical
    # data is useful for screening but cannot close a worst-case release gate.
    foster_thermal_resistances_c_per_w=(0.06, 0.12, 0.17),
    foster_thermal_time_constants_s=(0.0004, 0.010, 0.150),
    lm74700_recommended_max_v=60.0,
    lm74700_absolute_max_v=65.0,
    mosfet_limit_v=80.0,
    controller_limit_v=100.0,
    datasheet="https://www.vishay.com/docs/98647/sm8s85ahm3.pdf",
)
