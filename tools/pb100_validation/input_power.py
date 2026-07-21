from __future__ import annotations

from .common import (
    INPUT_POWER_DESIGN_VALUE_COLUMNS,
    INPUT_REVERSE_PACKAGE_TRACE_COLUMNS,
    INPUT_REVERSE_Q1_CLOSEOUT_PRECHECK_COLUMNS,
    INPUT_REVERSE_Q1_DERIVATION_PRECHECK_COLUMNS,
    INPUT_REVERSE_Q1_FREEZE_CHECKLIST_COLUMNS,
    OUTPUT_FREEZE_REVIEW_COLUMNS,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_INPUT_POWER_ITEMS,
    REQUIRED_INPUT_REVERSE_FREEZE_REVIEW_ITEMS,
    REQUIRED_INPUT_REVERSE_Q1_CLOSEOUT_PRECHECKS,
    REQUIRED_INPUT_REVERSE_Q1_DERIVATION_CHECKS,
    REQUIRED_INPUT_REVERSE_Q1_FREEZE_CHECKS,
    csv,
    fail,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def validate_input_power_design_values() -> None:
    path = PB100_DIR / "PB-100-input-power-design-values.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input-power design values: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_POWER_DESIGN_VALUE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    allowed_nets = {
        "VBAT_RAW",
        "VBAT_REV_PROT",
        "VBAT_PROT",
        "LM74700_VCAP",
        "INPUT_PROT_EN",
        "INPUT_FET_GATE",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "IIN_MON_A0",
        "IIN_MON_A1",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
    }
    seen_items = set()
    for row_number, row in enumerate(rows, 2):
        design_item = row["Design item"].strip()
        if design_item not in REQUIRED_INPUT_POWER_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid design item {design_item}")
        if design_item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate design item {design_item}")
        seen_items.add(design_item)
        validate_no_role_tokens_in_row(path, row_number, row)
        for column in ("Block", "Related net", "Candidate direction", "Freeze dependency", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        expected_status = (
            "Open under ADR-0016"
            if design_item == "TVS clamp selection"
            else "Selected final pre-layout"
        )
        if row["Value status"].strip() != expected_status:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                f"input-power value must be {expected_status}"
            )
        dependency = row["Freeze dependency"].lower()
        if not any(token in dependency for token in ("freeze", "release", "gate", "validat", "review")):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze/release dependency must remain explicit")
        for net_name in [part.strip() for part in row["Related net"].split(";")]:
            if net_name not in allowed_nets:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown input-power net {net_name}")
        if design_item == "Q1 package and copper path":
            row_text = " ".join(row.values())
            if not all(token in row_text for token in ("IAUT300N08S5N012ATMA2", "TOLL", "80 V", "40 A")):
                fail("Q1 package and copper path must keep selected 80 V TOLL and 40 A review explicit")
        if design_item == "Shunt value and power rating":
            row_text = " ".join(row.values()).lower()
            for token in ("four-terminal", "0.5m", "60a", "30mv", "1.8w", "40a", "0.8w"):
                if token not in row_text:
                    fail(f"input shunt design row must preserve {token} assumption")

    missing_items = sorted(REQUIRED_INPUT_POWER_ITEMS - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input-power design items: "
            f"{', '.join(missing_items)}"
        )


def validate_input_reverse_package_trace() -> None:
    path = PB100_DIR / "PB-100-input-reverse-package-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse package trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_REVERSE_PACKAGE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "Controller gate path",
        "Rejected 60 V TOLL history",
        "Selected 80 V TOLL path",
        "80 V alternatives",
        "Current measurement boundary",
        "Assembly sourcing gate",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        item = row["Trace item"].strip()
        if item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate trace item {item}")
        if item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown trace item {item}")
        rows_by_item[item] = row
        for column in INPUT_REVERSE_PACKAGE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        lifecycle_text = " ".join(row.values()).lower()
        if not any(token in lifecycle_text for token in ("schematic freeze", "review", "release", "substitution")):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: lifecycle dependency must remain explicit")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input reverse trace items: "
            f"{', '.join(missing_items)}"
        )

    trace_text = read_text(path)
    for token in (
        "IAUTN06S5N008ATMA1",
        "60 V",
        "TOLL",
        "0.76 mOhm",
        "2.43 W",
        "40 A",
        "IAUT300N08S5N012ATMA2",
        "80 V",
        "LFPAK88",
        "1.2 mOhm",
        "4.032 W",
        "IAUT300N08S5N014",
        "BUK7J2R4-80M",
        "not approved substitutes",
        "0.5mΩ",
        "VBAT_REV_PROT",
        "IIN_SHUNT_HI/IIN_SHUNT_LO",
        "JLCPCB PCBWay",
    ):
        if token not in trace_text:
            fail(f"input reverse package trace must include {token}")

    controller_text = " ".join(rows_by_item["Controller gate path"].values())
    for token in ("LM74700QDBVRQ1", "INPUT_FET_GATE", "controller-unpowered off"):
        if token not in controller_text:
            fail(f"input reverse controller trace must include {token}")

    selected_text = " ".join(rows_by_item["Selected 80 V TOLL path"].values())
    for token in ("IAUT300N08S5N012ATMA2", "ADR-0016", "40 A", "production-source"):
        if token not in selected_text:
            fail(f"selected 80 V Q1 trace must include {token}")

    alternatives_text = " ".join(rows_by_item["80 V alternatives"].values())
    for token in ("IAUT300N08S5N014", "BUK7J2R4-80M", "non-drop-in", "rejected"):
        if token not in alternatives_text:
            fail(f"80 V Q1 alternatives trace must include {token}")

    input_doc = read_text(PB100_DIR / "PB-100-input-reverse-protection.md")
    for token in (
        "IAUT300N08S5N012ATMA2",
        "80 V TOLL",
        "IAUT300N08S5N014",
        "BUK7J2R4-80M",
        "not approved Rev.1 assembly substitutions",
    ):
        if token not in input_doc:
            fail(f"input reverse strategy document must include {token}")

    thermal_rows = list(csv.DictReader((PB100_DIR / "PB-100-thermal-estimates.csv").open(newline="", encoding="utf-8")))
    thermal_by_path = {row["Path"].strip(): row for row in thermal_rows}
    expected_thermal = {
        "IAUT300N08S5N012ATMA2 80 V input reverse MOSFET": ("40", "0.0012", "4.032"),
        "IAUT300N08S5N014 80 V input reverse alternate": ("40", "0.0014", "4.704"),
        "BUK7J2R4-80M 80 V input reverse alternate": ("40", "0.0024", "7.68"),
    }
    for thermal_path, (current, rds, dissipation) in expected_thermal.items():
        row = thermal_by_path.get(thermal_path)
        if row is None:
            fail(f"thermal estimates must include {thermal_path}")
        if row["Current A"].strip() != current:
            fail(f"{thermal_path} current must remain {current}")
        if row["Rds or Ron ohm"].strip() != rds:
            fail(f"{thermal_path} Rds must remain {rds}")
        if row["Estimated dissipation W"].strip() != dissipation:
            fail(f"{thermal_path} dissipation must remain {dissipation}")

    pin_contract_rows = list(csv.DictReader((PB100_DIR / "PB-100-input-protection-pin-contract.csv").open(newline="", encoding="utf-8")))
    q1_nets = {row["Planned net"].strip() for row in pin_contract_rows if row["Ref"].strip() == "Q1"}
    if q1_nets != {"VBAT_RAW", "VBAT_REV_PROT", "INPUT_FET_GATE"}:
        fail("Q1 input pin contract must map VBAT_RAW VBAT_REV_PROT and INPUT_FET_GATE")

    input_power_text = read_text(PB100_DIR / "PB-100-input-power-design-values.csv")
    for token in ("IAUT300N08S5N012ATMA2 80 V PG-HSOF-8-1 TOLL", "4.032 W at 40 A", "0.5mΩ"):
        if token not in input_power_text:
            fail(f"input power values must preserve input reverse token {token}")

    protection_text = read_text(PB100_DIR / "PB-100-protection-validation.csv")
    for token in (
        "IAUT300N08S5N012ATMA2 input reverse MOSFET,80V VDS",
        "80V selection retained; PBREL-006 Conditional",
        "Rejected Rev.1 baseline",
    ):
        if token not in protection_text:
            fail(f"protection validation must preserve input reverse token {token}")

    checked_paths = (
        PB100_DIR / "PB-100-symbol-mpn-readiness.csv",
        PB100_DIR / "PB-100-kicad-footprint-plan.csv",
        REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv",
        REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv",
        REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv",
        REPO_ROOT / "docs" / "production" / "component-family-shortlist.md",
    )
    for checked_path in checked_paths:
        checked_text = read_text(checked_path)
        for token in ("IAUT300N08S5N012ATMA2", "IAUT300N08S5N014", "BUK7J2R4-80M"):
            if token not in checked_text:
                fail(f"{checked_path.relative_to(REPO_ROOT)} must retain input reverse alternate {token}")


def validate_input_reverse_freeze_review() -> None:
    path = PB100_DIR / "PB-100-input-reverse-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse freeze review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_FREEZE_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_INPUT_REVERSE_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown input reverse review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate input reverse review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_INPUT_REVERSE_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input reverse review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "LM74700-Q1",
        "INPUT_FET_GATE",
        "controller-unpowered off state",
        "LM74502-Q1",
        "IAUTN06S5N008ATMA1",
        "Rejected 60 V",
        "IAUT300N08S5N012ATMA2",
        "80 V TOLL",
        "4.032W at 40A",
        "IAUT300N08S5N014",
        "BUK7J2R4-80M",
        "controlled alternatives",
        "VBAT_REV_PROT",
        "VBAT_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "HM3 TVS",
        "JLCPCB PCBWay",
        "critical alternatives",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in review_text:
            fail(f"input reverse freeze review must include {token}")

    trace_text = read_text(PB100_DIR / "PB-100-input-reverse-package-trace.csv")
    for token in ("IAUTN06S5N008ATMA1", "IAUT300N08S5N012ATMA2", "IAUT300N08S5N014", "BUK7J2R4-80M", "40 A", "JLCPCB PCBWay"):
        if token not in trace_text:
            fail(f"input reverse package trace must support freeze review token {token}")

    pin_contract_text = read_text(PB100_DIR / "PB-100-input-protection-pin-contract.csv")
    for token in ("Q1", "VBAT_RAW", "VBAT_REV_PROT", "INPUT_FET_GATE", "IIN_SHUNT_HI", "IIN_SHUNT_LO"):
        if token not in pin_contract_text:
            fail(f"input protection pin contract must support freeze review token {token}")

    tvs_margin_text = read_text(PB100_DIR / "PB-100-tvs-load-dump-margin-trace.csv")
    for token in ("IAUTN06S5N008", "60 V", "IAUT300N08S5N012ATMA2", "80 V", "SM8S33AHM3/I"):
        if token not in tvs_margin_text:
            fail(f"TVS margin trace must support input reverse freeze review token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    for token in ("INPUT_REVERSE_FET", "TOLL", "IAUT300N08S5N012ATMA2", "IAUT300N08S5N014", "BUK7J2R4-80M"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support input reverse freeze review token {token}")


def validate_input_reverse_q1_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-input-reverse-q1-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse Q1 freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_REVERSE_Q1_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_INPUT_REVERSE_Q1_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown input reverse Q1 check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate input reverse Q1 check {check_id}")
        rows_by_check[check_id] = row
        for column in INPUT_REVERSE_Q1_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if check_id == "Q1-FRZ-002" and ("input_fet_gate" not in row_text or "turn-off timing" not in row_text):
            fail("Q1 gate checklist row must keep INPUT_FET_GATE and turn-off timing explicit")
        if check_id == "Q1-FRZ-003" and not all(
            token in row_text for token in ("iautn06s5n008atma1", "dual sidr626ldp", "not approved")
        ):
            fail("Q1 rejected-60V checklist row must keep historical paths and exclusion explicit")
        if check_id == "Q1-FRZ-004" and not all(
            token in row_text for token in ("iaut300n08s5n012atma2", "80 v", "toll", "4.032w at 40a")
        ):
            fail("Q1 selected checklist row must keep IAUT300N08S5N012ATMA2 80 V TOLL explicit")
        if check_id == "Q1-FRZ-005" and not all(
            token in row_text for token in ("iaut300n08s5n014atma1", "buk7j2r4-80mx", "controlled")
        ):
            fail("Q1 alternatives checklist row must preserve two controlled 80 V alternatives")
        if check_id == "Q1-FRZ-006" and ("vbat_rev_prot" not in row_text or "iin_shunt_hi" not in row_text or "vbat_prot" not in row_text):
            fail("Q1 measurement sequence checklist row must keep protected telemetry sequence explicit")
        if check_id == "Q1-FRZ-009" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("Q1 no-layout checklist row must block PCB layout explicitly")

    missing_checks = sorted(REQUIRED_INPUT_REVERSE_Q1_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input reverse Q1 checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "LM74700-Q1",
        "LM74502-Q1",
        "INPUT_FET_GATE",
        "IAUTN06S5N008ATMA1",
        "not approved Rev.1 assembly substitutions",
        "IAUT300N08S5N012ATMA2",
        "80 V TOLL",
        "4.032W at 40A",
        "IAUT300N08S5N014ATMA1",
        "BUK7J2R4-80MX",
        "controlled alternatives",
        "VBAT_REV_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "VBAT_PROT",
        "40 A thermal",
        "JLCPCB PCBWay",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in checklist_text:
            fail(f"input reverse Q1 freeze checklist must include {token}")


def validate_input_reverse_q1_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-input-reverse-q1-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse Q1 derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_REVERSE_Q1_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_INPUT_REVERSE_Q1_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Q1 derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Q1 derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in INPUT_REVERSE_Q1_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if derivation_id == "Q1-DER-002" and ("equation 1" not in row_text or "0.1uf" not in row_text):
            fail("Q1 derivation precheck must include VCAP Equation 1 and 0.1uF minimum")
        if derivation_id == "Q1-DER-003" and ("gate" not in row_text or "anode" not in row_text or "disabled" not in row_text):
            fail("Q1 derivation precheck must keep gate default-off conditions explicit")
        if derivation_id == "Q1-DER-005" and ("0.5mω" not in row_text or "1.25mω" not in row_text):
            fail("Q1 derivation precheck must include 40 A RDS(on) operating window")
        if derivation_id == "Q1-DER-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("Q1 derivation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_INPUT_REVERSE_Q1_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing Q1 derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI LM74700-Q1",
        "LM74502-Q1",
        "INPUT_FET_GATE",
        "LM74700_VCAP",
        "Equation 1",
        "6.6V",
        "0.1uF",
        "10 times MOSFET CISS",
        "20mV",
        "50mV",
        "-11mV",
        "0.5mΩ",
        "1.25mΩ",
        "IAUT300N08S5N012ATMA2",
        "80V TOLL",
        "IAUT300N08S5N014",
        "BUK7J2R4-80M",
        "60V paths are rejected",
        "SM8S33AHM3/I",
        "VBAT_REV_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "VBAT_PROT",
        "JLCPCB PCBWay",
        "PB-100.kicad_pcb",
    ):
        if token not in precheck_text:
            fail(f"input reverse Q1 derivation precheck must include {token}")


def validate_input_reverse_q1_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-input-reverse-q1-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input reverse Q1 closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_REVERSE_Q1_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_INPUT_REVERSE_Q1_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Q1 closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Q1 closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in INPUT_REVERSE_Q1_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "Q1-CLS-005" and not all(
            token in row_text
            for token in (
                "iaut300n08s5n012atma2",
                "iaut300n08s5n014atma1",
                "buk7j2r4-80mx",
                "60 v paths are rejected",
            )
        ):
            fail("Q1 closeout package row must keep selected and two 80 V alternate paths explicit")
        if precheck_id == "Q1-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("Q1 closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_INPUT_REVERSE_Q1_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing Q1 closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI LM74700-Q1",
        "LM74700QDBVRQ1",
        "LM74502-Q1",
        "Equation 1",
        "TDRV_EN",
        "C(VCAP)",
        "V(VCAP_UVLOR)",
        "300uA",
        "0.1uF",
        "VCAP",
        "CISS",
        "EN",
        "VCAP-to-ANODE",
        "GATE internally connected to ANODE",
        "INPUT_FET_GATE",
        "20mV forward regulation",
        "50mV conduction",
        "-11mV reverse-current shutdown",
        "VBAT_RAW",
        "VBAT_REV_PROT",
        "VBAT_PROT",
        "0.5mΩ to 1.25mΩ",
        "RDS(on)",
        "40A",
        "IAUT300N08S5N012ATMA2",
        "80 V",
        "PG-HSOF-8-1 TOLL",
        "1.2mΩ",
        "4.032W at 40A",
        "IAUT300N08S5N014ATMA1",
        "BUK7J2R4-80MX",
        "controlled 80 V alternatives",
        "60 V paths are rejected",
        "SM8S33AHM3/I",
        "TVS",
        "ADR-0016",
        "energy",
        "transient thermal",
        "PBREL-007",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "0.5mΩ shunt",
        "50A fuse",
        "JLCPCB PCBWay",
        "at least two alternatives",
        "input-protection.kicad_sch",
        "CAP-INP",
        "PB-100-input-power-design-values.csv",
        "PB-100-input-protection-pin-contract.csv",
        "PB-100-input-controller-pin-template.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Q1 placement",
        "high-current copper",
        "thermal relief",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"input reverse Q1 closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-input-reverse-q1-freeze-checklist.csv": ("Q1-FRZ-003", "Q1-FRZ-009"),
        "PB-100-input-reverse-q1-derivation-precheck.csv": ("Q1-DER-002", "Q1-DER-010"),
        "PB-100-input-reverse-package-trace.csv": ("IAUT300N08S5N012ATMA2", "IAUT300N08S5N014", "BUK7J2R4-80M"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"Q1 closeout precheck requires {supporting_artifact} token {token}")
