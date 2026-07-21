from __future__ import annotations

from .common import (
    OUTPUT_FREEZE_REVIEW_COLUMNS,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_TVS_LOAD_DUMP_FREEZE_REVIEW_ITEMS,
    REQUIRED_TVS_OVERSHOOT_CLOSEOUT_PRECHECKS,
    REQUIRED_TVS_OVERSHOOT_ESCAPE_CHECKS,
    REQUIRED_TVS_OVERSHOOT_VALIDATION_CHECKS,
    TVS_LOAD_DUMP_MARGIN_TRACE_COLUMNS,
    TVS_OVERSHOOT_CLOSEOUT_PRECHECK_COLUMNS,
    TVS_OVERSHOOT_ESCAPE_CHECKLIST_COLUMNS,
    TVS_OVERSHOOT_VALIDATION_PRECHECK_COLUMNS,
    csv,
    fail,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def validate_tvs_candidate_consistency() -> None:
    stale_tvs_source = "https://www.mccsemi.com/products/esd-protection-and-power-tvs/tvs/SM8S33A"
    for relative_path in (
        "hardware/power-board/PB-100/PB-100-symbol-capture-worklist.csv",
        "hardware/power-board/PB-100/PB-100-power-path-candidates.csv",
        "hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv",
    ):
        text = read_text(REPO_ROOT / relative_path)
        if stale_tvs_source in text:
            fail(f"{relative_path} must not use MCC SM8S33A as active TVS source")

    active_tvs_paths = (
        "hardware/power-board/PB-100/PB-100-symbol-capture-worklist.csv",
        "hardware/power-board/PB-100/PB-100-power-path-candidates.csv",
        "hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv",
        "hardware/power-board/PB-100/PB-100-schematic-instance-plan.csv",
        "hardware/power-board/PB-100/PB-100-preliminary-validation.md",
        "hardware/power-board/PB-100/PB-100-kicad-footprint-plan.csv",
        "hardware/power-board/PB-100/PB-100-protection-validation.csv",
        "hardware/power-board/PB-100/PB-100-logic-power-rails.md",
        "hardware/power-board/PB-100/PB-100-input-power-design-values.csv",
        "hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv",
        "hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv",
        "hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv",
    )
    for relative_path in active_tvs_paths:
        text = read_text(REPO_ROOT / relative_path)
        if "SM8S33A-class" in text:
            fail(f"{relative_path} must use active SM8S33AHM3-class TVS wording")
        if "SM8S33AHE3-class" in text or "SM8S33AHE3_A/I-class" in text:
            fail(f"{relative_path} must not treat Vishay HE3 TVS as the active baseline")
        if "SM8S33AHM3" not in text:
            fail(f"{relative_path} must reference active SM8S33AHM3 TVS evidence")


def validate_tvs_load_dump_margin_trace() -> None:
    path = PB100_DIR / "PB-100-tvs-load-dump-margin-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS/load-dump margin trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TVS_LOAD_DUMP_MARGIN_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "TPS48110 high-side controller",
        "IAUT300N08S5N012ATMA2 output MOSFET",
        "SIDR626LDP and IAUTN06S5N008 historical paths",
        "IAUT300N08S5N012ATMA2 input reverse MOSFET",
        "LM74700QDBVRQ1 ideal-diode controller",
        "LM5164QDDATQ1 buck",
        "LM5013-Q1 buck alternate",
        "TPS54360B-Q1 buck alternate",
        "TPS2HB35 direct smart switch",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        protected_item = row["Protected item"].strip()
        if protected_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate protected item {protected_item}")
        if protected_item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown protected item {protected_item}")
        rows_by_item[protected_item] = row
        for column in TVS_LOAD_DUMP_MARGIN_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values())
        for token in ("SM8S33AHM3", "59.45 V"):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: TVS margin row must include {token}")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS margin items: "
            f"{', '.join(missing_items)}"
        )

    historical_text = " ".join(
        rows_by_item["SIDR626LDP and IAUTN06S5N008 historical paths"].values()
    ).lower()
    for token in ("60 v", "rejected", "history", "59.45 v"):
        if token not in historical_text:
            fail(f"historical 60 V paths must preserve {token}")

    for protected_item in (
        "IAUT300N08S5N012ATMA2 output MOSFET",
        "IAUT300N08S5N012ATMA2 input reverse MOSFET",
    ):
        selected_text = " ".join(rows_by_item[protected_item].values()).lower()
        for token in ("80 v", "selected", "20.55 v", "bounded"):
            if token not in selected_text:
                fail(f"{protected_item} must preserve selected 80 V margin evidence: {token}")

    smart_switch_text = " ".join(rows_by_item["TPS2HB35 direct smart switch"].values()).lower()
    for token in ("40 v", "deferred by adr-0011", "future adr", "lower-clamp"):
        if token not in smart_switch_text:
            fail(f"TPS2HB35 TVS margin row must preserve {token}")

    for protected_item in (
        "TPS48110 high-side controller",
        "LM5164QDDATQ1 buck",
        "LM5013-Q1 buck alternate",
    ):
        margin_state = rows_by_item[protected_item]["Margin state"].lower()
        if "pass" not in margin_state or "margin" not in margin_state:
            fail(f"{protected_item} must remain pass-with-margin against active HM3 TVS")

    protection_text = read_text(PB100_DIR / "PB-100-protection-validation.csv")
    for token in (
        "SM8S33AHM3/I TVS",
        "59.45V bounded stress",
        "IAUT300N08S5N012ATMA2 output MOSFET",
        "Selected with 20.55V bounded margin",
        "Rejected Rev.1 baseline",
    ):
        if token not in protection_text:
            fail(f"protection validation must preserve {token}")


def validate_tvs_load_dump_freeze_review() -> None:
    path = PB100_DIR / "PB-100-tvs-load-dump-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS/load-dump freeze review: {path.relative_to(REPO_ROOT)}")

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
        if review_item not in REQUIRED_TVS_LOAD_DUMP_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown TVS/load-dump review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate TVS/load-dump review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_TVS_LOAD_DUMP_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS/load-dump review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "53.3 V clamp at 124 A",
        "59.45 V bounded stress",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "TPS48110",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "100 V",
        "SIDR626LDP",
        "IAUTN06S5N008",
        "60 V",
        "rejected Rev.1 assembly paths",
        "overshoot",
        "IAUT300N08S5N012ATMA2",
        "80 V",
        "selected for Q1 and Q101 through Q110",
        "20.55 V bounded headroom",
        "TPS54360B-Q1",
        "TPS2HB35",
        "ADR-0011",
        "lower-clamp",
        "OV divider",
        "buck input network",
        "JLCPCB PCBWay",
        "critical alternatives",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in review_text:
            fail(f"TVS/load-dump freeze review must include {token}")

    margin_text = read_text(PB100_DIR / "PB-100-tvs-load-dump-margin-trace.csv")
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "59.45 V bounded hot clamp-loop stress",
        "Rejected Rev.1 baseline",
        "IAUT300N08S5N012ATMA2",
        "Selected; pass with 20.55 V margin",
        "TPS54360B-Q1",
        "TPS2HB35",
        "Deferred by ADR-0011",
    ):
        if token not in margin_text:
            fail(f"TVS margin trace must support freeze review token {token}")

    protection_text = read_text(PB100_DIR / "PB-100-protection-validation.csv")
    for token in (
        "SM8S33AHM3/I TVS",
        "59.45V bounded stress",
        "Rejected Rev.1 baseline",
        "Selected with 20.55V bounded margin",
        "Optional future alternate",
        "TPS54360B-Q1",
    ):
        if token not in protection_text:
            fail(f"protection validation must support TVS freeze review token {token}")

    input_values_text = read_text(PB100_DIR / "PB-100-input-power-design-values.csv")
    for token in ("SM8S33AHM3/I", "MCC SM8S33A EOL", "Vishay HE3 NFD", "downstream absolute maximum margin"):
        if token not in input_values_text:
            fail(f"input power values must support TVS freeze review token {token}")

    output_values_text = read_text(PB100_DIR / "PB-100-output-stage-design-values.csv")
    if "OV threshold divider" not in output_values_text or "TVS/load-dump margin" not in output_values_text:
        fail("output stage design values must preserve TVS OV dependency")

    logic_values_text = read_text(PB100_DIR / "PB-100-logic-power-design-values.csv")
    for token in ("Input filter", "surge-tolerant input capacitance", "load-dump stress"):
        if token not in logic_values_text:
            fail(f"logic power design values must support TVS freeze review token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    for token in ("INPUT_TVS", "SM8S33AHM3/I", "SLD8S33A", "DM8W33AQ-13", "SM8S33A-Q"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support TVS freeze review token {token}")


def validate_tvs_overshoot_escape_checklist() -> None:
    path = PB100_DIR / "PB-100-tvs-overshoot-escape-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS overshoot escape checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TVS_OVERSHOOT_ESCAPE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_TVS_OVERSHOOT_ESCAPE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown TVS overshoot check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate TVS overshoot check {check_id}")
        rows_by_check[check_id] = row
        for column in TVS_OVERSHOOT_ESCAPE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_checks = sorted(REQUIRED_TVS_OVERSHOOT_ESCAPE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS overshoot checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "AEC-Q101",
        "53.3 V raw clamp at 124 A",
        "59.45 V bounded stress",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "60 V",
        "0.55 V recommended headroom",
        "5.55 V absolute headroom",
        "80 V",
        "20.55 V bounded headroom",
        "100 V",
        "40.55 V bounded headroom",
        "SIDR626LDP",
        "IAUTN06S5N008",
        "historical evidence",
        "not permitted Rev.1 assembly substitutions",
        "overshoot",
        "IAUT300N08S5N012ATMA2",
        "PG-HSOF-8-1 TOLL",
        "1.2 mOhm",
        "selected for Q1 and Q101 through Q110",
        "TPS48110",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "TPS2HB35",
        "ADR-0011",
        "lower-clamp",
        "OV divider",
        "buck input network",
        "VBAT_PROT",
        "INPUT_TVS",
        "JLCPCB PCBWay",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"TVS overshoot escape checklist must include {token}")

    margin_text = read_text(PB100_DIR / "PB-100-tvs-load-dump-margin-trace.csv")
    for token in (
        "SM8S33AHM3/I",
        "59.45 V bounded hot clamp-loop stress",
        "Rejected Rev.1 baseline",
        "IAUT300N08S5N012ATMA2",
        "Selected; pass with 20.55 V margin",
    ):
        if token not in margin_text:
            fail(f"TVS margin trace must support overshoot checklist token {token}")

    voltage_review_text = read_text(PB100_DIR / "PB-100-mosfet-voltage-margin-review.md")
    for token in ("60 V", "80 V", "0.55 V", "20.55 V", "59.45 V", "overshoot"):
        if token not in voltage_review_text:
            fail(f"MOSFET voltage-margin review must support TVS overshoot token {token}")


def validate_tvs_overshoot_validation_precheck() -> None:
    path = PB100_DIR / "PB-100-tvs-overshoot-validation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS overshoot validation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TVS_OVERSHOOT_VALIDATION_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        validation_id = row["Validation ID"].strip()
        if validation_id not in REQUIRED_TVS_OVERSHOOT_VALIDATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown TVS validation item {validation_id}")
        if validation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate TVS validation item {validation_id}")
        rows_by_id[validation_id] = row
        for column in TVS_OVERSHOOT_VALIDATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if validation_id == "TVS-VAL-002" and ("vstress" not in row_text or "lloop" not in row_text):
            fail("TVS validation precheck must include overshoot stress method")
        if validation_id == "TVS-VAL-006" and ("probe" not in row_text or "bandwidth" not in row_text):
            fail("TVS validation precheck must include measurement probe bandwidth")
        if validation_id == "TVS-VAL-007" and ("parasitic" not in row_text or "inductance" not in row_text):
            fail("TVS validation precheck must include simulation parasitic inductance")
        if validation_id == "TVS-VAL-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("TVS validation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_TVS_OVERSHOOT_VALIDATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS validation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "53.3 V raw clamp at 124 A",
        "59.45 V bounded stress",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "Vstress = Vclamp + Lloop * di/dt",
        "SIDR626LDP",
        "IAUTN06S5N008",
        "IAUT300N08S5N012ATMA2",
        "PG-HSOF-8-1 TOLL",
        "80 V",
        "20.55 V bounded headroom",
        "100 V",
        "TPS48110",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "VBAT_RAW",
        "VBAT_PROT",
        "probe bandwidth",
        "fixture inductance",
        "parasitics",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "JLCPCB PCBWay",
        "PB-100.kicad_pcb",
    ):
        if token not in precheck_text:
            fail(f"TVS overshoot validation precheck must include {token}")


def validate_tvs_overshoot_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-tvs-overshoot-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty TVS overshoot closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TVS_OVERSHOOT_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_TVS_OVERSHOOT_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown TVS closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate TVS closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in TVS_OVERSHOOT_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "TVS-CLS-002" and ("vstress" not in row_text or "lloop" not in row_text):
            fail("TVS closeout method row must keep Vstress and Lloop explicit")
        if precheck_id == "TVS-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("TVS closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_TVS_OVERSHOOT_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing TVS closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "SM8S33AHM3/I",
        "HM3 DO-218AC",
        "AEC-Q101",
        "53.3 V raw clamp at 124 A",
        "59.45 V bounded stress",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "60 V MOSFET exclusion bridge",
        "rejected historical evidence",
        "Vstress = Vclamp + Lloop * di/dt",
        "probe fixture parasitics",
        "source impedance",
        "SIDR626LDP",
        "IAUTN06S5N008",
        "IAUT300N08S5N012ATMA2",
        "PG-HSOF-8-1 TOLL",
        "80 V is selected for Q1 and Q101 through Q110 with 20.55 V bounded headroom",
        "TPS48110",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "TPS2HB35",
        "ADR-0011",
        "future ADR",
        "OV divider",
        "buck input network",
        "input filter capacitor",
        "value-bearing-sheet promotion items",
        "VBAT_PROT",
        "INPUT_TVS",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "JLCPCB PCBWay",
        "at least two viable alternates",
        "input-protection.kicad_sch",
        "CAP-INP",
        "PB-100-test-point-plan.csv",
        "PB-100-protection-validation.csv",
        "docs/testing/test-plan.md",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "D1 placement",
        "pulse-current return copper",
        "via strategy",
        "thermal relief",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"TVS overshoot closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-tvs-overshoot-escape-checklist.csv": ("TVS-FRZ-002", "TVS-FRZ-009"),
        "PB-100-tvs-overshoot-validation-precheck.csv": ("TVS-VAL-002", "TVS-VAL-010"),
        "PB-100-tvs-load-dump-freeze-review.csv": ("60V MOSFET historical rejection", "Layout authorization boundary"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"TVS closeout precheck requires {supporting_artifact} token {token}")
