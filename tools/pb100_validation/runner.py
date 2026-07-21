from __future__ import annotations

from . import (
    kicad,
    symbols,
    release,
    pin_contracts,
    outputs,
    input_power,
    logic_power,
    can,
    budget,
    current_telemetry,
    thermal_telemetry,
    factory,
    garage,
    protection,
    interface,
    review,
    release_evidence,
)
from . import common
from .common import PB100_DIR, REPO_ROOT, fail, register_validation_hooks, validate_csv


CHECKS = (
    kicad.validate_kicad_scaffold,
    kicad.validate_kicad_cli_checks,
    symbols.validate_symbol_library,
    kicad.validate_kicad_no_role_tokens,
    symbols.validate_instance_plan,
    symbols.validate_symbol_mpn_readiness,
    symbols.validate_symbol_trace_provenance,
    symbols.validate_symbol_capture_worklist,
    symbols.validate_symbol_capture_progress,
    symbols.validate_symbol_pin_evidence,
    symbols.validate_symbol_footprint_pad_map,
    symbols.validate_large_mosfet_paste_segmentation,
    symbols.validate_input_reverse_fet_symbol_evidence,
    symbols.validate_jpb1_symbol_from_pin_map,
    symbols.validate_instance_symbol_map,
    symbols.validate_sheet_reference_map,
    symbols.validate_kicad_sheet_manifest,
    symbols.validate_net_domain_plan,
    symbols.validate_bom_symbol_map,
    symbols.validate_schematic_readiness_dashboard,
    release.validate_schematic_freeze_gap_register,
    release.validate_engineering_blocker_closeout,
    release.validate_schematic_review_closeout,
    release.validate_staged_release_readiness,
    release.validate_board_release_blocker_register,
    release.validate_board_print_closure_matrix,
    release_evidence.validate_q2_maximum_bound_qualification,
    release_evidence.validate_five_blocker_release_evidence,
    review.validate_schematic_capture_work_queue,
    review.validate_schematic_capture_plan,
    review.validate_review_release_manifest,
    review.validate_schematic_readiness_review,
    review.validate_schematic_package,
    review.validate_test_plan_traceability,
    review.validate_post_prototype_validation_gate,
    pin_contracts.validate_output_channel_pin_contract,
    pin_contracts.validate_output_controller_pin_template,
    outputs.validate_output_net_expansion,
    outputs.validate_low_current_output_baseline_trace,
    outputs.validate_low_current_output_freeze_review,
    outputs.validate_high_medium_output_baseline_trace,
    outputs.validate_high_medium_output_freeze_review,
    outputs.validate_output_stage_value_freeze_checklist,
    outputs.validate_output_stage_value_derivation_precheck,
    outputs.validate_output_stage_closeout_precheck,
    pin_contracts.validate_input_and_power_pin_templates,
    pin_contracts.validate_input_protection_pin_contract,
    pin_contracts.validate_logic_power_design_placeholders,
    outputs.validate_output_stage_design_values,
    input_power.validate_input_power_design_values,
    input_power.validate_input_reverse_package_trace,
    input_power.validate_input_reverse_freeze_review,
    input_power.validate_input_reverse_q1_freeze_checklist,
    input_power.validate_input_reverse_q1_derivation_precheck,
    input_power.validate_input_reverse_q1_closeout_precheck,
    budget.validate_board_current_budget_trace,
    budget.validate_board_current_budget_freeze_review,
    budget.validate_board_current_budget_design_calculation,
    budget.validate_board_current_budget_value_freeze_checklist,
    budget.validate_board_current_budget_value_derivation_precheck,
    budget.validate_board_current_budget_closeout_precheck,
    current_telemetry.validate_current_telemetry_trace,
    current_telemetry.validate_current_telemetry_freeze_review,
    current_telemetry.validate_current_telemetry_value_freeze_checklist,
    current_telemetry.validate_current_telemetry_value_derivation_precheck,
    current_telemetry.validate_current_telemetry_closeout_precheck,
    thermal_telemetry.validate_thermal_telemetry_trace,
    thermal_telemetry.validate_thermal_telemetry_freeze_review,
    thermal_telemetry.validate_thermal_telemetry_value_freeze_checklist,
    thermal_telemetry.validate_thermal_telemetry_value_derivation_precheck,
    thermal_telemetry.validate_thermal_telemetry_closeout_precheck,
    logic_power.validate_logic_power_rail_trace,
    logic_power.validate_logic_power_design_values,
    logic_power.validate_logic_power_freeze_review,
    logic_power.validate_logic_power_value_freeze_checklist,
    logic_power.validate_logic_power_value_derivation_precheck,
    logic_power.validate_logic_power_closeout_precheck,
    can.validate_can1_tx_disable_trace,
    can.validate_can1_safety_verification,
    can.validate_can1_production_dnp_review,
    can.validate_can1_default_disable_freeze_checklist,
    can.validate_can1_default_disable_derivation_precheck,
    can.validate_can1_default_disable_closeout_precheck,
    can.validate_can1_reset_bench_checklist,
    can.validate_can1_capture_contract,
    factory.validate_assembly_sourcing_recheck,
    factory.validate_assembly_readiness_trace,
    factory.validate_factory_assembly_freeze_checklist,
    factory.validate_factory_assembly_sourcing_precheck,
    factory.validate_factory_assembly_closeout_precheck,
    garage.validate_garage_connector_fuse_plan,
    garage.validate_garage_install_freeze_checklist,
    garage.validate_garage_install_sourcing_precheck,
    garage.validate_garage_install_closeout_precheck,
    factory.validate_sourcing_evidence_snapshot,
    protection.validate_tvs_candidate_consistency,
    protection.validate_tvs_load_dump_margin_trace,
    protection.validate_tvs_load_dump_freeze_review,
    protection.validate_tvs_overshoot_escape_checklist,
    protection.validate_tvs_overshoot_validation_precheck,
    protection.validate_tvs_overshoot_closeout_precheck,
    thermal_telemetry.validate_thermal_telemetry_baseline,
    interface.validate_b2b_interface_trace,
    interface.validate_b2b_connector_candidate,
    interface.validate_b2b_lb100_pin_audit_checklist,
    interface.validate_b2b_interface_freeze_checklist,
    interface.validate_b2b_interface_closeout_precheck,
    interface.validate_b2b_resource_binding,
    interface.validate_validation_traceability,
    review.validate_test_point_plan,
    review.validate_fault_response_matrix,
    review.validate_net_naming_contract,
)

VALIDATION_MODULES = (
    common,
    kicad,
    symbols,
    release,
    pin_contracts,
    outputs,
    input_power,
    logic_power,
    can,
    budget,
    current_telemetry,
    thermal_telemetry,
    factory,
    garage,
    protection,
    interface,
    review,
    release_evidence,
)

register_validation_hooks(
    {
        name
        for module in VALIDATION_MODULES
        for name, value in vars(module).items()
        if name.startswith("validate_") and callable(value)
    }
)


def _check_registry() -> None:
    check_names = [check.__name__ for check in CHECKS]
    duplicate_names = sorted(
        name for name in set(check_names) if check_names.count(name) > 1
    )
    if duplicate_names:
        fail(f"duplicate PB-100 checks in runner: {', '.join(duplicate_names)}")
    invalid_checks = sorted(
        check.__name__
        for check in CHECKS
        if not check.__module__.startswith("pb100_validation.")
    )
    if invalid_checks:
        fail(f"PB-100 checks outside validation package: {', '.join(invalid_checks)}")


def main() -> int:
    _check_registry()
    csv_paths = sorted(PB100_DIR.glob("*.csv")) + sorted(
        (REPO_ROOT / "production" / "bom").glob("*.csv")
    )
    for csv_path in csv_paths:
        validate_csv(csv_path)
    for check in CHECKS:
        check()
    print("PB-100 validation passed")
    return 0
