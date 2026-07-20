from __future__ import annotations

from .common import (
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_THERMAL_TELEMETRY_CLOSEOUT_PRECHECKS,
    REQUIRED_THERMAL_TELEMETRY_FREEZE_REVIEW_ITEMS,
    REQUIRED_THERMAL_TELEMETRY_VALUE_DERIVATION_CHECKS,
    REQUIRED_THERMAL_TELEMETRY_VALUE_FREEZE_CHECKS,
    THERMAL_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS,
    THERMAL_TELEMETRY_FREEZE_REVIEW_COLUMNS,
    THERMAL_TELEMETRY_TRACE_COLUMNS,
    THERMAL_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS,
    THERMAL_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS,
    csv,
    fail,
    json,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def validate_thermal_telemetry_trace() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in THERMAL_TELEMETRY_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_signals_by_zone = {
        "PCB reference": "TEMP_PCB",
        "Power zone A": "TEMP_PWR_A",
        "Power zone B": "TEMP_PWR_B",
    }
    rows_by_zone: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        zone = row["Thermal zone"].strip()
        if zone in rows_by_zone:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal zone {zone}")
        if zone not in expected_signals_by_zone:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal zone {zone}")
        rows_by_zone[zone] = row
        for column in THERMAL_TELEMETRY_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Signal"].strip() != expected_signals_by_zone[zone]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: {zone} signal mismatch")
        row_text = " ".join(row.values())
        for token in (
            "NTCGS103JF103FT8",
            "10k",
            "150C",
            "AEC-Q200",
            "LB ADC",
            "85C warn 105C cutoff 75C recovery",
            "configuration",
            "schematic freeze",
        ):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: thermal trace row must include {token}")

    missing_zones = sorted(set(expected_signals_by_zone) - set(rows_by_zone))
    if missing_zones:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal zones: "
            f"{', '.join(missing_zones)}"
        )

    thermal_map_rows = list(csv.DictReader((PB100_DIR / "PB-100-thermal-telemetry-map.csv").open(newline="", encoding="utf-8")))
    map_by_signal = {row["Signal"].strip(): row for row in thermal_map_rows}
    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    capability_signals = set(capabilities["telemetry"]["thermal_signals"])
    for signal in expected_signals_by_zone.values():
        if signal not in capability_signals:
            fail(f"{signal} must be exposed in PB-100 capability manifest")
        map_row = map_by_signal.get(signal)
        if map_row is None:
            fail(f"thermal telemetry map must include {signal}")
        map_text = " ".join(map_row.values())
        for token in ("NTCGS103JF103FT8", "-40 to 150", "LB ADC", "85C warn 105C cutoff 75C recovery"):
            if token not in map_text:
                fail(f"thermal telemetry map row {signal} must include {token}")

    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    for zone_key in ("pcb", "power_zone_a", "power_zone_b"):
        zone_config = config_example["thermal"][zone_key]
        if zone_config != {"warn_c": 85, "cutoff_c": 105, "recovery_c": 75}:
            fail(f"config thermal thresholds for {zone_key} must remain 85/105/75")

    thermal_doc = read_text(PB100_DIR / "PB-100-thermal-telemetry.md")
    for token in ("configuration/calibration values", "Missing, saturated, or implausible", "Output Manager", "85 °C warn"):
        if token not in thermal_doc:
            fail(f"thermal telemetry strategy must preserve {token}")

    firmware_readme = read_text(REPO_ROOT / "firmware" / "README.md").lower()
    for token in ("thermal protection", "thermal system safety", "cutoff/stale", "telemetry"):
        if token not in firmware_readme:
            fail(f"firmware README must keep thermal safety coverage token: {token}")


def validate_thermal_telemetry_freeze_review() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in THERMAL_TELEMETRY_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_THERMAL_TELEMETRY_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal telemetry review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal telemetry review item {review_item}")
        rows_by_item[review_item] = row
        for column in THERMAL_TELEMETRY_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if review_item == "Configuration thresholds" and "configuration" not in row_text:
            fail("thermal telemetry freeze review must keep thresholds in configuration")
        if review_item == "Firmware fail-safe" and "stale" not in row_text:
            fail("thermal telemetry freeze review must keep stale telemetry fail-safe behavior")

    missing_items = sorted(REQUIRED_THERMAL_TELEMETRY_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal telemetry review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "NTCGS103JF103FT8",
        "10k",
        "150C",
        "AEC-Q200",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "85C warn 105C cutoff",
        "75C recovery",
        "LB_3V3_IO ADC",
        "self-heating",
        "configuration and calibration data not firmware constants",
        "Stale thermal telemetry",
        "test_stale_thermal_telemetry_forces_cutoff",
        "PB-BENCH-009",
        "Do not place sensors or thermal copper before schematic freeze",
    ):
        if token not in review_text:
            fail(f"thermal telemetry freeze review must include {token}")

    thermal_doc = read_text(PB100_DIR / "PB-100-thermal-telemetry.md")
    for token in ("NTCGS103JF103FT8", "10 kΩ", "3435 K", "150 °C", "self-heating", "configuration/calibration"):
        if token not in thermal_doc:
            fail(f"thermal telemetry strategy must support freeze review token {token}")

    thermal_map_text = read_text(PB100_DIR / "PB-100-thermal-telemetry-map.csv")
    for token in ("TEMP_PCB", "TEMP_PWR_A", "TEMP_PWR_B", "-40 to 150", "85C warn 105C cutoff 75C recovery"):
        if token not in thermal_map_text:
            fail(f"thermal telemetry map must support freeze review token {token}")

    config_text = read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json")
    for token in ("\"warn_c\": 85", "\"cutoff_c\": 105", "\"recovery_c\": 75"):
        if token not in config_text:
            fail(f"thermal config example must support freeze review token {token}")

    firmware_joined = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "tests" / "test_thermal_service.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_system_safety.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_config_validator.c"),
        )
    )
    for token in (
        "test_default_thermal_config_is_valid",
        "test_invalid_thermal_config_is_rejected",
        "test_thermal_derate_publishes_event_without_disabling_outputs",
        "test_thermal_cutoff_disables_active_outputs",
        "test_stale_thermal_telemetry_disables_active_outputs",
        "test_stale_thermal_telemetry_forces_cutoff",
    ):
        if token not in firmware_joined:
            fail(f"firmware tests must retain thermal freeze review token {token}")


def validate_thermal_telemetry_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in THERMAL_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_THERMAL_TELEMETRY_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal telemetry check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal telemetry check {check_id}")
        rows_by_check[check_id] = row
        for column in THERMAL_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_checks = sorted(REQUIRED_THERMAL_TELEMETRY_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal telemetry checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "NTCGS103JF103FT8",
        "10k",
        "150C",
        "AEC-Q200",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "4.7kΩ",
        "LB_3V3_IO",
        "10kΩ NTC",
        "1kΩ",
        "10nF",
        "0.95 V at 75 °C",
        "0.78 V at 85 °C",
        "0.52 V at 105 °C",
        "224µA",
        "0.50mW",
        "0.31mW",
        "ADC settling",
        "85C warn 105C cutoff 75C recovery",
        "telemetry.thermal",
        "10000Ω",
        "3435 K",
        "4700Ω",
        "1000Ω",
        "1000 ms",
        "-40 to 150 °C",
        "test_stale_thermal_telemetry_forces_cutoff",
        "PB-BENCH-009",
        "THERMAL_NTC",
        "JLCPCB PCBWay",
        "TMP117/TMP112",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"thermal telemetry value freeze checklist must include {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-thermal-telemetry-design-calculation.md")
    for token in ("4.7 kΩ", "1 kΩ", "10 nF", "0.78 V", "0.52 V", "0.50 mW", "3435 K"):
        if token not in calculation_text:
            fail(f"thermal telemetry design calculation must support checklist token {token}")

    config_text = read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json")
    for token in ("\"warn_c\": 85", "\"cutoff_c\": 105", "\"recovery_c\": 75"):
        if token not in config_text:
            fail(f"thermal config example must support value checklist token {token}")


def validate_thermal_telemetry_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in THERMAL_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_THERMAL_TELEMETRY_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal telemetry derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal telemetry derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in THERMAL_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if derivation_id == "THERM-DER-002" and ("rntc =" not in row_text or "exp" not in row_text):
            fail("thermal telemetry derivation precheck must include NTC beta equation")
        if derivation_id == "THERM-DER-003" and "vadc =" not in row_text:
            fail("thermal telemetry derivation precheck must include ADC divider equation")
        if derivation_id == "THERM-DER-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("thermal telemetry derivation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_THERMAL_TELEMETRY_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal telemetry derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TDK NTCGS103JF103FT8",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "RNTC = R25 * exp(B * (1/T - 1/T25))",
        "R25 10000Ω",
        "3435 K",
        "-40 °C to 150 °C",
        "VADC = 3.3 V * RNTC / (4.7 kΩ + RNTC)",
        "4.7kΩ",
        "10kΩ NTC",
        "0.95 V at 75 °C",
        "0.78 V at 85 °C",
        "0.52 V at 105 °C",
        "PNTC = I^2 * RNTC",
        "224µA",
        "0.50mW",
        "0.31mW",
        "1kΩ",
        "10nF X7R",
        "LB ADC",
        "LB_3V3_IO",
        "telemetry.thermal",
        "4700Ω",
        "1000Ω",
        "10 nF",
        "1000 ms",
        "85C warn 105C cutoff 75C recovery",
        "test_stale_thermal_telemetry_forces_cutoff",
        "PB-BENCH-009",
        "THERMAL_NTC",
        "JLCPCB PCBWay",
        "TMP117/TMP112",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in precheck_text:
            fail(f"thermal telemetry value derivation precheck must include {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-thermal-telemetry-design-calculation.md")
    for token in ("VADC", "0.78 V", "0.52 V", "0.50 mW", "3435 K"):
        if token not in calculation_text:
            fail(f"thermal telemetry design calculation must support derivation token {token}")


def validate_thermal_telemetry_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-thermal-telemetry-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty thermal telemetry closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in THERMAL_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_THERMAL_TELEMETRY_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown thermal telemetry closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate thermal telemetry closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in THERMAL_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "THERM-CLS-002" and ("rntc =" not in row_text or "vadc =" not in row_text):
            fail("thermal telemetry closeout value row must include RNTC and VADC equations")
        if precheck_id == "THERM-CLS-004" and "pntc" not in row_text:
            fail("thermal telemetry closeout self-heating row must include PNTC")
        if precheck_id == "THERM-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("thermal telemetry closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_THERMAL_TELEMETRY_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing thermal telemetry closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TDK NTCGS103JF103FT8",
        "10k",
        "150C",
        "AEC-Q200",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "THERMAL_NTC",
        "JLCPCB PCBWay",
        "TMP117/TMP112",
        "RNTC = R25 * exp(B * (1/T - 1/T25))",
        "VADC = 3.3 V * RNTC / (4.7 kΩ + RNTC)",
        "R25 10000Ω",
        "3435 K",
        "4.7kΩ",
        "LB_3V3_IO",
        "10kΩ NTC",
        "1kΩ",
        "10nF X7R",
        "0.95 V at 75 °C",
        "0.78 V at 85 °C",
        "0.52 V at 105 °C",
        "OUT2",
        "input reverse hot zone",
        "medium-output or logic-buck hot zone",
        "PNTC = I^2 * RNTC",
        "224µA",
        "0.50mW",
        "0.31mW",
        "LB ADC",
        "ADC settling",
        "external ADC/mux",
        "telemetry.thermal",
        "4700Ω",
        "1000Ω",
        "10 nF",
        "1000 ms",
        "85C warn 105C cutoff 75C recovery",
        "-40 to 150 °C",
        "PBFLT-THERM-HIGH",
        "PBFLT-THERM-STALE",
        "test_stale_thermal_telemetry_forces_cutoff",
        "test_stale_thermal_telemetry_disables_active_outputs",
        "PB-BENCH-009",
        "PB-100-symbol-mpn-readiness.csv",
        "production/bom/factory_bom_draft.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "telemetry.kicad_sch",
        "CAP-TEL",
        "PB-100-thermal-telemetry-map.csv",
        "PB-100-thermal-telemetry-value-freeze-checklist.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "sensor placement",
        "thermal copper",
        "board outline",
    ):
        if token not in precheck_text:
            fail(f"thermal telemetry closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-thermal-telemetry-value-freeze-checklist.csv": ("THERM-FRZ-001", "THERM-FRZ-010"),
        "PB-100-thermal-telemetry-value-derivation-precheck.csv": ("THERM-DER-001", "THERM-DER-010"),
        "PB-100-thermal-telemetry-freeze-review.csv": ("Sensor class", "Bench validation path"),
        "PB-100-b2b-lb100-resource-binding.csv": ("TEMP_PCB", "TEMP_PWR_A", "TEMP_PWR_B"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"thermal telemetry closeout precheck requires {supporting_artifact} token {token}")


def validate_thermal_telemetry_baseline() -> None:
    map_path = PB100_DIR / "PB-100-thermal-telemetry-map.csv"
    validate_csv(map_path)
    rows = list(csv.DictReader(map_path.open(newline="", encoding="utf-8")))
    rows_by_signal = {row["Signal"].strip(): row for row in rows}
    required_signals = {"TEMP_PCB", "TEMP_PWR_A", "TEMP_PWR_B"}
    missing_signals = sorted(required_signals - rows_by_signal.keys())
    if missing_signals:
        fail(
            f"{map_path.relative_to(REPO_ROOT)} is missing thermal signals: "
            f"{', '.join(missing_signals)}"
        )

    for signal in sorted(required_signals):
        row = rows_by_signal[signal]
        row_text = " ".join(row.values())
        for token in ("NTCGS103JF103FT8", "10k", "150", "85C", "105C", "75C", "TBD"):
            if token not in row_text:
                fail(
                    f"{map_path.relative_to(REPO_ROOT)} thermal row {signal} "
                    f"must include {token}"
                )
        if row["Telemetry path"].strip() != "LB ADC":
            fail(f"{map_path.relative_to(REPO_ROOT)} thermal row {signal} must use LB ADC")

    checked_paths = (
        PB100_DIR / "PB-100-thermal-telemetry.md",
        PB100_DIR / "PB-100-symbol-mpn-readiness.csv",
        PB100_DIR / "PB-100-symbol-capture-worklist.csv",
        PB100_DIR / "PB-100-schematic-instance-plan.csv",
        PB100_DIR / "PB-100-kicad-footprint-plan.csv",
        REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv",
        REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv",
        REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv",
        REPO_ROOT / "docs" / "production" / "component-family-shortlist.md",
    )
    for path in checked_paths:
        text = read_text(path)
        if "NTCGS103JF103FT8" not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must reference the TDK thermal NTC candidate")

    thermal_doc = read_text(PB100_DIR / "PB-100-thermal-telemetry.md")
    for token in ("85 °C warn", "105 °C cutoff", "75 °C recovery"):
        if token not in thermal_doc:
            fail(f"thermal telemetry strategy must document default threshold {token}")

    evidence_rows = list(
        csv.DictReader((REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv").open(newline="", encoding="utf-8"))
    )
    thermal_evidence = next((row for row in evidence_rows if row["Symbol key"].strip() == "THERMAL_NTC"), None)
    if thermal_evidence is None:
        fail("missing THERMAL_NTC sourcing evidence row")
    evidence_text = " ".join(thermal_evidence.values()).lower()
    for token in ("ntcgs103jf103ft8", "aec-q200", "150c", "open:", "vishay"):
        if token not in evidence_text:
            fail(f"THERMAL_NTC sourcing evidence must explicitly track {token}")
