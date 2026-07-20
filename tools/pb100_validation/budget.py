from __future__ import annotations

from .common import (
    BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECK_COLUMNS,
    BOARD_CURRENT_BUDGET_FREEZE_REVIEW_COLUMNS,
    BOARD_CURRENT_BUDGET_TRACE_COLUMNS,
    BOARD_CURRENT_BUDGET_VALUE_DERIVATION_PRECHECK_COLUMNS,
    BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKLIST_COLUMNS,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECKS,
    REQUIRED_BOARD_CURRENT_BUDGET_FREEZE_REVIEW_ITEMS,
    REQUIRED_BOARD_CURRENT_BUDGET_VALUE_DERIVATION_CHECKS,
    REQUIRED_BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKS,
    csv,
    fail,
    json,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def validate_board_current_budget_trace() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_CURRENT_BUDGET_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_checks = {
        "Main fuse target",
        "Board continuous target",
        "Default configuration limit",
        "Total input telemetry range",
        "Shunt operating point",
        "Output limit oversubscription",
    }
    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check = row["Check"].strip()
        if check in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Check {check}")
        if check not in required_checks:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current-budget check {check}")
        rows_by_check[check] = row
        for column in BOARD_CURRENT_BUDGET_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "schematic freeze" not in row_text and check != "Default configuration limit":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: remaining work must reference schematic freeze")

    missing_checks = sorted(required_checks - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current-budget checks: "
            f"{', '.join(missing_checks)}"
        )

    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    power_budget = capabilities["power_budget"]
    if power_budget["main_fuse_target_a"] != 50:
        fail("PB-100 capability manifest must keep 50 A main fuse target")
    if power_budget["board_continuous_target_a"] != 40:
        fail("PB-100 capability manifest must keep 40 A board continuous target")
    if power_budget["default_total_current_limit_a"] != 40:
        fail("PB-100 capability manifest must keep 40 A default total-current limit")
    if config_example["power_budget"]["total_current_limit_a"] != 40:
        fail("config example must keep 40 A total_current_limit_a")

    output_limit_sum = sum(output["target_current_limit_a"] for output in capabilities["outputs"])
    if output_limit_sum != 82:
        fail(f"PB-100 output current-limit sum must remain 82 A, got {output_limit_sum} A")
    if "IIN_SENSE" not in capabilities["telemetry"]["current_signals"]:
        fail("PB-100 capability manifest must expose IIN_SENSE total-current telemetry")

    current_rows = list(csv.DictReader((PB100_DIR / "PB-100-current-telemetry-map.csv").open(newline="", encoding="utf-8")))
    total_current_row = next((row for row in current_rows if row["Signal"].strip() == "IIN_SENSE"), None)
    if total_current_row is None:
        fail("current telemetry map must include IIN_SENSE")
    total_current_text = " ".join(total_current_row.values())
    for token in ("0-60", "0.5mΩ", "40A"):
        if token not in total_current_text:
            fail(f"IIN_SENSE telemetry map row must include {token}")

    input_power_text = read_text(PB100_DIR / "PB-100-input-power-design-values.csv")
    for token in ("0.5mΩ", "20mV at 40A", "0.8W board-budget"):
        if token not in input_power_text:
            fail(f"input power design values must include {token}")

    trace_text = read_text(path)
    for token in ("50 A", "40 A", "0-60 A", "0.5 mOhm", "82 A", "configuration separate from firmware"):
        if token not in trace_text:
            fail(f"board-current budget trace must include {token}")


def validate_board_current_budget_freeze_review() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_CURRENT_BUDGET_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_BOARD_CURRENT_BUDGET_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown board-current review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate board-current review item {review_item}")
        rows_by_item[review_item] = row
        for column in BOARD_CURRENT_BUDGET_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if review_item == "Layout authorization boundary":
            if "no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text:
                fail("board-current freeze review must block PCB layout explicitly")
        if review_item == "Firmware configuration budget":
            if "total_current_limit_a" not in row_text or "configuration stays separate from firmware" not in row_text:
                fail("board-current freeze review must keep config/firmware separation explicit")

    missing_items = sorted(REQUIRED_BOARD_CURRENT_BUDGET_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing board-current review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "50 A",
        "40 A",
        "0.5mΩ",
        "20mV at 40A",
        "0.8W",
        "30mV at 60A",
        "1.8W",
        "82 A",
        "Q1",
        "TOLL",
        "LFPAK88",
        "dual PowerPAK",
        "Kelvin",
        "ADC or I2C",
        "configuration stays separate from firmware",
        "No PCB layout copper geometry",
        "PB-100.kicad_pcb",
    ):
        if token not in review_text:
            fail(f"board-current budget freeze review must include {token}")

    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    power_budget = capabilities["power_budget"]
    if power_budget["main_fuse_target_a"] != 50:
        fail("board-current freeze review requires 50 A main fuse target")
    if power_budget["board_continuous_target_a"] != 40:
        fail("board-current freeze review requires 40 A board continuous target")
    if power_budget["default_total_current_limit_a"] != 40:
        fail("board-current freeze review requires 40 A default total-current limit")
    output_limit_sum = sum(output["target_current_limit_a"] for output in capabilities["outputs"])
    if output_limit_sum != 82:
        fail(f"board-current freeze review expects 82 A output oversubscription, got {output_limit_sum} A")

    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    if config_example["power_budget"]["total_current_limit_a"] != 40:
        fail("board-current freeze review requires config example 40 A total_current_limit_a")

    input_power_text = read_text(PB100_DIR / "PB-100-input-power-design-values.csv")
    for token in ("0.5mΩ", "20mV at 40A", "0.8W board-budget", "30mV at 60A", "Kelvin"):
        if token not in input_power_text:
            fail(f"input power design values must support board-current freeze review token {token}")

    board_current_text = read_text(PB100_DIR / "PB-100-board-current-budget-trace.csv")
    for token in ("50 A", "40 A", "0-60 A", "0.5 mOhm", "82 A", "configuration separate from firmware"):
        if token not in board_current_text:
            fail(f"board-current trace must support freeze review token {token}")

    kicad_prep_text = read_text(PB100_DIR / "PB-100-kicad-prep.md").lower()
    for token in ("copper", "current-carrying", "layout"):
        if token not in kicad_prep_text:
            fail(f"KiCad prep must retain board-current layout blocker token {token}")


def validate_board_current_budget_design_calculation() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-design-calculation.md"
    text = read_text(path)
    lower_text = text.lower()
    for token in ("not a pcb layout package", "no pcb layout copper geometry", "pb-100.kicad_pcb"):
        if token not in lower_text:
            fail(f"{path.relative_to(REPO_ROOT)} must keep no-layout boundary token: {token}")
    for token in (
        "50 A",
        "40 A",
        "0-60 A",
        "0.5 mΩ",
        "82 A",
        "Configuration stays separate from firmware",
        "Kelvin",
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "20 mV at 40 A",
        "0.8 W at 40 A",
        "25 mV at 50 A",
        "1.25 W at 50 A",
        "30 mV at 60 A",
        "1.8 W at 60 A",
        "Pfet = I^2 * Rds(on) * 2.0",
        "BUK7S1R2-80M",
        "selected 80 V LFPAK88",
        "LFPAK88",
        "3.84 W",
        "IAUTN08S5N012L",
        "BUK7J2R4-80M",
        "retained in historical decision artifacts only",
        "Every 1 mΩ",
        "1.6 W at 40 A",
        "2.5 W at 50 A",
        "3.6 W at 60 A",
    ):
        if token not in text:
            fail(f"board-current design calculation must include {token}")


def validate_board_current_budget_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown board-current check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate board-current check {check_id}")
        rows_by_check[check_id] = row
        for column in BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_BOARD_CURRENT_BUDGET_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing board-current checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "ADR-0008",
        "50A main harness fuse",
        "40 A board continuous-current target",
        "40 A default total_current_limit_a",
        "0-60 A telemetry range",
        "82 A summed output limits",
        "VBAT_RAW",
        "INPUT_REVERSE_FET",
        "VBAT_REV_PROT",
        "0.5mΩ",
        "VBAT_PROT",
        "MAXI",
        "6mm2 / 10AWG",
        "BUK7S1R2-80M",
        "selected BUK7S1R2-80M 80 V LFPAK88",
        "LFPAK88",
        "3.84 W at 40 A",
        "IAUTN08S5N012L 80 V TOLL",
        "BUK7J2R4-80M 80 V LFPAK56E",
        "former IAUTN06S5N008 and SIDR626LDP 60 V paths are rejected",
        "TOTAL_CURRENT_SHUNT",
        "20mV and 0.8W at 40A",
        "25mV and 1.25W at 50A",
        "30mV and 1.8W at 60A",
        "Kelvin",
        "1.6W at 40A",
        "2.5W at 50A",
        "3.6W at 60A",
        "power_budget",
        "stale telemetry denial",
        "configuration separate from firmware",
        "TOTAL_CURRENT_MONITOR",
        "IIN_SENSE",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "high-current copper",
        "shunt copper",
        "Q1 copper",
    ):
        if token not in checklist_text:
            fail(f"board-current budget value freeze checklist must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-board-current-budget-design-calculation.md")
    for token in ("20 mV at 40 A", "0.8 W at 40 A", "1.6 W at 40 A", "3.6 W at 60 A"):
        if token not in design_text:
            fail(f"board-current design calculation must support value checklist token {token}")

    firmware_text = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_power_budget.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_rule_runtime.c"),
        )
    )
    for token in (
        "total_current_limit_a",
        "40",
        "shed_priority_order",
        "test_denies_output_over_budget",
        "test_shed_order_uses_configured_priority_order",
        "stale",
    ):
        if token not in firmware_text:
            fail(f"firmware/config budget evidence must support board-current checklist token {token}")


def validate_board_current_budget_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in BOARD_CURRENT_BUDGET_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_BOARD_CURRENT_BUDGET_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown board-current derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate board-current derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in BOARD_CURRENT_BUDGET_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_items = sorted(REQUIRED_BOARD_CURRENT_BUDGET_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing board-current derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "ADR-0008",
        "50A main harness fuse",
        "50 A main fuse",
        "40 A board continuous-current target",
        "40 A default total_current_limit_a",
        "82 A summed output limits",
        "configuration separate from firmware",
        "VBAT_RAW",
        "INPUT_REVERSE_FET",
        "VBAT_REV_PROT",
        "TOTAL_CURRENT_SHUNT",
        "0.5mΩ",
        "VBAT_PROT",
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "20mV and 0.8W at 40A",
        "25mV and 1.25W at 50A",
        "30mV and 1.8W at 60A",
        "BUK7S1R2-80M",
        "selected BUK7S1R2-80M 80 V LFPAK88",
        "LFPAK88",
        "2.4mΩ",
        "3.84 W at 40 A",
        "IAUTN08S5N012L 80 V TOLL",
        "BUK7J2R4-80M 80 V LFPAK56E",
        "former 60 V paths are rejected",
        "Every 1 mΩ",
        "1.6 W at 40 A",
        "2.5 W at 50 A",
        "6mm2 / 10AWG",
        "MAXI",
        "total_current_limit_a",
        "power_budget",
        "PB-BENCH-010",
        "PB-BENCH-006",
        "stale telemetry denial",
        "IIN_SENSE",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "0-60 A",
        "Kelvin",
        "ADC or I2C",
        "INPUT_CONNECTOR",
        "MAIN_FUSE_HOLDER",
        "factory_bom_draft.csv",
        "garage_bom_draft.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "high-current copper",
        "shunt copper",
        "Q1 copper",
    ):
        if token not in precheck_text:
            fail(f"board-current budget value derivation precheck must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-board-current-budget-design-calculation.md")
    for token in ("20 mV at 40 A", "0.8 W at 40 A", "1.6 W at 40 A", "3.6 W at 60 A"):
        if token not in design_text:
            fail(f"board-current design calculation must support derivation token {token}")

    firmware_text = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_power_budget.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_rule_runtime.c"),
        )
    )
    for token in ("total_current_limit_a", "40", "test_denies_output_over_budget", "stale"):
        if token not in firmware_text:
            fail(f"firmware/config budget evidence must support board-current derivation token {token}")


def validate_board_current_budget_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-board-current-budget-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-current budget closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown board-current closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate board-current closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "BUDGET-CLS-005" and ("vshunt" not in row_text or "pshunt" not in row_text):
            fail("board-current closeout shunt row must include Vshunt and Pshunt formulas")
        if precheck_id == "BUDGET-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("board-current closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_BOARD_CURRENT_BUDGET_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing board-current closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "ADR-0008",
        "50A main harness fuse",
        "40 A board continuous-current target",
        "40 A default total_current_limit_a",
        "0-60 A telemetry range",
        "82 A summed output limits",
        "configuration separate from firmware",
        "50 A MAXI fuse",
        "VBAT_RAW",
        "INPUT_REVERSE_FET",
        "VBAT_REV_PROT",
        "TOTAL_CURRENT_SHUNT",
        "0.5mΩ",
        "VBAT_PROT",
        "6mm2 / 10AWG",
        "BUK7S1R2-80M",
        "selected BUK7S1R2-80M 80 V LFPAK88",
        "LFPAK88",
        "3.84 W at 40 A",
        "IAUTN08S5N012L 80 V TOLL",
        "BUK7J2R4-80M 80 V LFPAK56E",
        "former IAUTN06S5N008 and SIDR626LDP 60 V paths are rejected",
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "20mV and 0.8W at 40A",
        "25mV and 1.25W at 50A",
        "30mV and 1.8W at 60A",
        "Kelvin",
        "1.6W at 40A",
        "2.5W at 50A",
        "3.6W at 60A",
        "power_budget",
        "total_current_limit_a",
        "startup refusal",
        "load shedding",
        "stale telemetry denial",
        "TOTAL_CURRENT_MONITOR",
        "IIN_SENSE",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "ADC or I2C",
        "summed per-output IMON alone is not acceptable",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "INPUT_CONNECTOR",
        "MAIN_FUSE_HOLDER",
        "factory_bom_draft.csv",
        "garage_bom_draft.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "pb100_sourcing_evidence_snapshot.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "high-current copper",
        "shunt copper",
        "Q1 copper",
        "connector placement",
        "fabrication package",
    ):
        if token not in precheck_text:
            fail(f"board-current budget closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-board-current-budget-value-freeze-checklist.csv": ("BUDGET-FRZ-001", "BUDGET-FRZ-010"),
        "PB-100-board-current-budget-value-derivation-precheck.csv": ("BUDGET-DER-001", "BUDGET-DER-010"),
        "PB-100-board-current-budget-freeze-review.csv": ("Main fuse and input connector", "Layout authorization boundary"),
        "PB-100-current-telemetry-closeout-precheck.csv": ("TOTAL_CURRENT_SHUNT", "IIN_SENSE"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"board-current closeout precheck requires {supporting_artifact} token {token}")
