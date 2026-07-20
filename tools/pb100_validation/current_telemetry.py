from __future__ import annotations

from .common import (
    CURRENT_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS,
    CURRENT_TELEMETRY_FREEZE_REVIEW_COLUMNS,
    CURRENT_TELEMETRY_TRACE_COLUMNS,
    CURRENT_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS,
    CURRENT_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_CURRENT_TELEMETRY_CLOSEOUT_PRECHECKS,
    REQUIRED_CURRENT_TELEMETRY_FREEZE_REVIEW_ITEMS,
    REQUIRED_CURRENT_TELEMETRY_VALUE_DERIVATION_CHECKS,
    REQUIRED_CURRENT_TELEMETRY_VALUE_FREEZE_CHECKS,
    csv,
    fail,
    json,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def validate_current_telemetry_trace() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CURRENT_TELEMETRY_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_groups = {
        "OUT2 high-current telemetry": ("0-30", {"OUT2_IMON"}),
        "OUT1 medium 12A telemetry": ("0-20", {"OUT1_IMON"}),
        "Medium 8A telemetry": ("0-15", {"OUT3_IMON", "OUT4_IMON", "OUT6_IMON", "OUT7_IMON", "OUT10_IMON"}),
        "Low 4A telemetry": ("0-8", {"OUT5_IMON", "OUT8_IMON", "OUT9_IMON"}),
        "Total input telemetry": ("0-60", {"IIN_SENSE"}),
    }
    rows_by_group: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        group = row["Measurement group"].strip()
        if group in rows_by_group:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate measurement group {group}")
        if group not in expected_groups:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown measurement group {group}")
        rows_by_group[group] = row
        for column in CURRENT_TELEMETRY_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        expected_range, expected_signals = expected_groups[group]
        if row["Range target A"].strip() != expected_range:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: range must be {expected_range}")
        if set(row["Signals"].split()) != expected_signals:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: signals must be {' '.join(sorted(expected_signals))}")
        row_text = " ".join(row.values()).lower()
        for token in ("schematic freeze", "calibration"):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: current telemetry row must include {token}")

    missing_groups = sorted(set(expected_groups) - set(rows_by_group))
    if missing_groups:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing telemetry groups: "
            f"{', '.join(missing_groups)}"
        )

    map_rows = list(csv.DictReader((PB100_DIR / "PB-100-current-telemetry-map.csv").open(newline="", encoding="utf-8")))
    map_by_signal = {row["Signal"].strip(): row for row in map_rows}
    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    capability_signals = set(capabilities["telemetry"]["current_signals"])
    expected_all_signals = set().union(*(signals for _, signals in expected_groups.values()))
    if not expected_all_signals <= capability_signals:
        fail("current telemetry trace signals must be exposed in PB-100 capability manifest")

    for expected_range, signals in expected_groups.values():
        for signal in signals:
            row = map_by_signal.get(signal)
            if row is None:
                fail(f"current telemetry map must include {signal}")
            if row["Range A"].strip() != expected_range:
                fail(f"{signal} current telemetry map range must be {expected_range}")
            if signal == "IIN_SENSE":
                row_text = " ".join(row.values())
                for token in ("0.5mΩ", "40A", "60A"):
                    if token not in row_text:
                        fail(f"IIN_SENSE map row must preserve {token}")

    trace_text = read_text(path)
    for token in ("0.5 mOhm", "40 A budget", "stale-telemetry safe-off", "ADC or I2C"):
        if token not in trace_text:
            fail(f"current telemetry trace must include {token}")

    firmware_readme = read_text(REPO_ROOT / "firmware" / "README.md").lower()
    for token in ("telemetry snapshot", "staleness", "stale-data fail", "safe behavior"):
        if token not in firmware_readme:
            fail(f"firmware README must keep telemetry safety coverage token: {token}")


def validate_current_telemetry_freeze_review() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CURRENT_TELEMETRY_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_CURRENT_TELEMETRY_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current telemetry review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate current telemetry review item {review_item}")
        rows_by_item[review_item] = row
        for column in CURRENT_TELEMETRY_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if review_item == "Calibration configuration" and "not firmware constants" not in row_text:
            fail("current telemetry freeze review must keep calibration out of firmware constants")
        if review_item == "Stale telemetry safe fault" and "safe" not in row_text:
            fail("current telemetry freeze review must keep stale telemetry fail-safe behavior")

    missing_items = sorted(REQUIRED_CURRENT_TELEMETRY_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current telemetry review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "0.5mΩ",
        "20mV at 40A",
        "30mV at 60A",
        "±40.96mV",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "Kelvin",
        "IIN_SENSE",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
        "ADC I2C",
        "OUT1_IMON",
        "OUT10_IMON",
        "configuration data not firmware constants",
        "stale-telemetry denial",
        "PB-BENCH-005",
        "PB-BENCH-006",
        "PB-BENCH-010",
    ):
        if token not in review_text:
            fail(f"current telemetry freeze review must include {token}")

    current_doc = read_text(PB100_DIR / "PB-100-current-telemetry.md")
    for token in ("0.5 mΩ", "20 mV", "0.8 W", "30 mV", "1.8 W", "±40.96 mV"):
        if token not in current_doc:
            fail(f"current telemetry strategy must support freeze review token {token}")

    net_domain_text = read_text(PB100_DIR / "PB-100-schematic-net-domain-plan.csv")
    for token in ("IIN_SHUNT_HI", "IIN_SHUNT_LO", "Kelvin", "IIN_SENSE"):
        if token not in net_domain_text:
            fail(f"net-domain plan must support current telemetry freeze review token {token}")

    b2b_binding_text = read_text(PB100_DIR / "PB-100-b2b-lb100-resource-binding.csv")
    for token in ("ADC", "I2C", "IIN_SENSE", "PB_I2C_SCL", "PB_I2C_SDA"):
        if token not in b2b_binding_text:
            fail(f"B2B resource binding must support current telemetry freeze review token {token}")

    firmware_joined = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "tests" / "test_telemetry.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_rule_runtime.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_system_safety.c"),
        )
    )
    for token in (
        "test_total_current_power_budget_input",
        "test_telemetry_wrapper_denies_stale_matching_rule",
        "test_invalid_telemetry_forces_cutoff",
        "test_stale_telemetry_forces_cutoff",
    ):
        if token not in firmware_joined:
            fail(f"firmware tests must retain current telemetry safe-fault token {token}")


def validate_current_telemetry_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CURRENT_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_CURRENT_TELEMETRY_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current telemetry check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate current telemetry check {check_id}")
        rows_by_check[check_id] = row
        for column in CURRENT_TELEMETRY_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_checks = sorted(REQUIRED_CURRENT_TELEMETRY_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current telemetry checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "0.5mΩ",
        "CSS4J-4026R-L500F",
        "20mV at 40A",
        "0.8W",
        "30mV at 60A",
        "1.8W",
        "81.92A",
        "±40.96mV",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "85 V VBUS",
        "2.7 V to 5.5 V",
        "16 I2C addresses",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "Kelvin",
        "10Ω",
        "1nF C0G",
        "A1 = GND",
        "A0 = GND",
        "0x40",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "LB_3V3_IO",
        "4.7kΩ to 10kΩ",
        "DNP",
        "PB_I2C_INT",
        "47kΩ",
        "diagnostic",
        "VBAT_PROT",
        "1kΩ",
        "1nF 100V",
        "OUT1_IMON",
        "OUT10_IMON",
        "0-30A",
        "0-20A",
        "0-15A",
        "0-8A",
        "telemetry.total_current",
        "telemetry.output_current",
        "500µΩ",
        "40960µV",
        "1000 ms",
        "60000 mA",
        "calibration data not firmware constants",
        "PB-BENCH-005",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "stale-telemetry denial",
        "total_current_limit_a 40",
        "TOTAL_CURRENT_MONITOR",
        "TOTAL_CURRENT_SHUNT",
        "JLCPCB PCBWay",
        "1.0mΩ fallback",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"current telemetry value freeze checklist must include {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-current-telemetry-design-calculation.md")
    for token in ("500 µΩ", "40960 µV", "1000 ms", "60000 mA", "0x40", "10 Ω", "1 nF"):
        if token not in calculation_text:
            fail(f"current telemetry design calculation must support checklist token {token}")

    config_text = read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json")
    for token in ('"shunt_microohm": 500', '"stale_timeout_ms": 1000', '"plausible_max_ma": 60000'):
        if token not in config_text:
            fail(f"config example must support current telemetry checklist token {token}")


def validate_current_telemetry_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CURRENT_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_CURRENT_TELEMETRY_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current telemetry derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate current telemetry derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in CURRENT_TELEMETRY_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if derivation_id == "CUR-DER-001" and ("vshunt" not in row_text or "pshunt" not in row_text):
            fail("current telemetry derivation precheck must include shunt voltage and power formulas")
        if derivation_id == "CUR-DER-008" and ("telemetry.total_current" not in row_text or "firmware constants" not in row_text):
            fail("current telemetry derivation precheck must keep calibration out of firmware constants")
        if derivation_id == "CUR-DER-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("current telemetry derivation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_CURRENT_TELEMETRY_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current telemetry derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "0.5mΩ",
        "40A gives 20mV",
        "50A gives 25mV",
        "60A gives 30mV",
        "81.92A",
        "40.96mV",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "±40.96mV",
        "±163.84mV",
        "-0.3V to +85V",
        "2.7V to 5.5V",
        "16 I2C addresses",
        "LB_3V3_IO",
        "0x40",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "10Ω",
        "1nF C0G",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "4.7kΩ to 10kΩ",
        "PB_I2C_INT",
        "47kΩ",
        "VBAT_PROT",
        "VBAT_RAW",
        "1kΩ",
        "1nF 100V",
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "OUT1_IMON",
        "OUT10_IMON",
        "0-30A",
        "0-20A",
        "0-15A",
        "0-8A",
        "telemetry.total_current",
        "telemetry.output_current",
        "500µΩ",
        "40960µV",
        "1000 ms",
        "60000 mA",
        "PB-BENCH-005",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "total_current_limit_a 40",
        "JLCPCB PCBWay",
        "CSS4J-4026R-L500F",
        "1.0mΩ fallback",
        "Isabellenhuette BVN/BAS",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in precheck_text:
            fail(f"current telemetry value derivation precheck must include {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-current-telemetry-design-calculation.md")
    for token in ("Vshunt", "Pshunt", "500 µΩ", "40960 µV", "0x40", "10 Ω", "1 nF"):
        if token not in calculation_text:
            fail(f"current telemetry design calculation must support derivation token {token}")


def validate_current_telemetry_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-current-telemetry-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty current telemetry closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CURRENT_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_CURRENT_TELEMETRY_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown current telemetry closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate current telemetry closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in CURRENT_TELEMETRY_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "CUR-CLS-001" and ("vshunt" not in row_text or "pshunt" not in row_text):
            fail("current telemetry closeout shunt row must include Vshunt and Pshunt formulas")
        if precheck_id == "CUR-CLS-006" and (
            "out2" not in row_text or "out10" not in row_text or "external adc/mux" not in row_text
        ):
            fail("current telemetry closeout IMON row must cover output ranges and external ADC/mux escape")
        if precheck_id == "CUR-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("current telemetry closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_CURRENT_TELEMETRY_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing current telemetry closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "Vshunt = I * Rshunt",
        "Pshunt = I^2 * Rshunt",
        "0.5mΩ",
        "40A gives 20mV",
        "50A gives 25mV",
        "60A gives 30mV",
        "81.92A",
        "40.96mV",
        "TOTAL_CURRENT_SHUNT",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "±40.96mV",
        "±163.84mV",
        "-0.3V to +85V",
        "2.7V to 5.5V",
        "16 I2C addresses",
        "TOTAL_CURRENT_MONITOR",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "Kelvin",
        "10Ω",
        "1nF C0G",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
        "A1 = GND",
        "A0 = GND",
        "0x40",
        "LB_3V3_IO",
        "4.7kΩ to 10kΩ",
        "47kΩ",
        "VBAT_PROT",
        "VBAT_RAW",
        "SM8S33AHM3/I",
        "1kΩ",
        "1nF 100V",
        "85 V VBUS",
        "60 V overshoot",
        "OUT1_IMON",
        "OUT10_IMON",
        "OUT2 0-30A",
        "OUT1 0-20A",
        "0-15A",
        "0-8A",
        "16 ADC",
        "external ADC/mux",
        "RIMON",
        "telemetry.total_current",
        "telemetry.output_current",
        "500µΩ",
        "40960µV",
        "stale_timeout_ms 1000",
        "plausible_max_ma 60000",
        "total_current_limit_a 40",
        "stale-telemetry denial",
        "PB-BENCH-005",
        "PB-BENCH-006",
        "PB-BENCH-010",
        "40 A board budget",
        "PBFLT-CUR-STALE",
        "PBFLT-BUDGET",
        "CSS4J-4026R-L500F",
        "1.0mΩ fallback",
        "Isabellenhuette BVN/BAS",
        "AEC-Q200",
        "JLCPCB PCBWay",
        "PB-100-current-monitor-pin-template.csv",
        "PB-100-symbol-pin-evidence.csv",
        "PB-100-symbol-mpn-readiness.csv",
        "telemetry.kicad_sch",
        "CAP-TEL",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "shunt placement",
        "Kelvin routing",
        "monitor footprint",
        "board outline",
    ):
        if token not in precheck_text:
            fail(f"current telemetry closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-current-telemetry-value-freeze-checklist.csv": ("CUR-FRZ-001", "CUR-FRZ-010"),
        "PB-100-current-telemetry-value-derivation-precheck.csv": ("CUR-DER-001", "CUR-DER-010"),
        "PB-100-current-telemetry-freeze-review.csv": ("Total shunt range", "Bench validation path"),
        "PB-100-b2b-lb100-resource-binding.csv": ("IIN_SENSE", "PB_I2C_SCL", "PB_I2C_SDA"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"current telemetry closeout precheck requires {supporting_artifact} token {token}")
