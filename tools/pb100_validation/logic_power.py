from __future__ import annotations

from .common import (
    LOGIC_POWER_CLOSEOUT_PRECHECK_COLUMNS,
    LOGIC_POWER_DESIGN_VALUE_COLUMNS,
    LOGIC_POWER_RAIL_TRACE_COLUMNS,
    LOGIC_POWER_VALUE_DERIVATION_PRECHECK_COLUMNS,
    LOGIC_POWER_VALUE_FREEZE_CHECKLIST_COLUMNS,
    OUTPUT_FREEZE_REVIEW_COLUMNS,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_LOGIC_POWER_CLOSEOUT_PRECHECKS,
    REQUIRED_LOGIC_POWER_FREEZE_REVIEW_ITEMS,
    REQUIRED_LOGIC_POWER_VALUE_DERIVATION_CHECKS,
    REQUIRED_LOGIC_POWER_VALUE_FREEZE_CHECKS,
    REQUIRED_LOGIC_POWER_VALUE_ITEMS,
    csv,
    fail,
    json,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
    validate_not_final_value_status,
)


def validate_logic_power_design_values() -> None:
    path = PB100_DIR / "PB-100-logic-power-design-values.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power design values: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_DESIGN_VALUE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    allowed_nets = {
        "VBAT_PROT",
        "BUCK_EN_UVLO",
        "BUCK_RON_SET",
        "BUCK_FB",
        "BUCK_BST",
        "BUCK_SW",
        "L1",
        "PB_5V_OUT",
        "PB_PWR_GOOD",
    }
    seen_items = set()
    for row_number, row in enumerate(rows, 2):
        design_item = row["Design item"].strip()
        if design_item not in REQUIRED_LOGIC_POWER_VALUE_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid design item {design_item}")
        if design_item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate design item {design_item}")
        seen_items.add(design_item)
        validate_no_role_tokens_in_row(path, row_number, row)
        for column in ("Related net", "Candidate direction", "Freeze dependency", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_not_final_value_status(path, row_number, row["Value status"])
        if "schematic freeze" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")
        related_net = row["Related net"].strip()
        if related_net not in allowed_nets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power net/ref {related_net}")
        if design_item == "Higher-current fallback" and "LM5013-Q1" not in " ".join(row.values()):
            fail("logic-power higher-current fallback must preserve LM5013-Q1-class option")
        if related_net == "PB_5V_OUT" and "accessory" in " ".join(row.values()).lower() and "must not" not in " ".join(row.values()).lower():
            fail("PB_5V_OUT rows must not allow accessory loads")

    missing_items = sorted(REQUIRED_LOGIC_POWER_VALUE_ITEMS - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power design items: "
            f"{', '.join(missing_items)}"
        )


def validate_logic_power_freeze_review() -> None:
    path = PB100_DIR / "PB-100-logic-power-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power freeze review: {path.relative_to(REPO_ROOT)}")

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
        if review_item not in REQUIRED_LOGIC_POWER_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate logic-power review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_LOGIC_POWER_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "LM5164-Q1-class",
        "100 V 1 A",
        "LM5013-Q1-class",
        "TPS54360B-Q1-class",
        "TVS margin",
        "VBAT_PROT",
        "VBAT_RAW",
        "PB_5V_OUT",
        "1000 mA",
        "accessory loads",
        "BUCK_EN_UVLO",
        "OUT1..OUT10",
        "LB_3V3_IO",
        "BUCK_RON_SET",
        "BUCK_FB",
        "BUCK_BST",
        "BUCK_SW",
        "L1",
        "CIN",
        "COUT",
        "AEC-Q200",
        "PB_PWR_GOOD",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "LM5164QDDATQ1",
        "SO PowerPAD",
        "JLCPCB PCBWay",
        "critical alternatives",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in review_text:
            fail(f"logic-power freeze review must include {token}")

    rail_text = read_text(PB100_DIR / "PB-100-logic-power-rail-trace.csv")
    for token in (
        "LM5164-Q1-class 100 V 1 A",
        "LM5013-Q1-class 100 V fallback",
        "TPS54360B-Q1-class 60 V path remains conditional",
        "PB_5V_OUT must not power accessory loads",
        "PB_PWR_GOOD",
        "default off",
    ):
        if token not in rail_text:
            fail(f"logic power rail trace must support freeze review token {token}")

    budget_text = read_text(PB100_DIR / "PB-100-logic-power-budget.csv")
    for token in ("Initial total", "1000", "LM5013-Q1-class"):
        if token not in budget_text:
            fail(f"logic power budget must support freeze review token {token}")

    design_text = read_text(PB100_DIR / "PB-100-logic-power-design-values.csv")
    for token in (
        "BUCK_EN_UVLO",
        "BUCK_RON_SET",
        "BUCK_FB",
        "BUCK_BST",
        "BUCK_SW",
        "PB_PWR_GOOD",
        "TBD not final",
        "No layout geometry before freeze",
    ):
        if token not in design_text:
            fail(f"logic power design values must support freeze review token {token}")

    pin_template_text = read_text(PB100_DIR / "PB-100-logic-buck-pin-template.csv")
    for token in ("VIN", "EN/UVLO", "RON", "FB", "PGOOD", "BST", "SW", "EP"):
        if token not in pin_template_text:
            fail(f"logic buck pin template must support freeze review token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    for token in ("LOGIC_BUCK", "LOGIC_BUCK_INDUCTOR", "LM5164QDDATQ1", "LM5013-Q1", "TPS54360B-Q1"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support logic-power freeze review token {token}")


def validate_logic_power_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-logic-power-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_LOGIC_POWER_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power freeze check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate logic-power freeze check {check_id}")
        rows_by_check[check_id] = row
        for column in LOGIC_POWER_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_checks = sorted(REQUIRED_LOGIC_POWER_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power freeze checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "LM5164-Q1-class",
        "100 V 1 A",
        "LM5013-Q1-class",
        "100 V 3.5 A",
        "TPS54360B-Q1-class",
        "TVS margin",
        "PB_5V_OUT",
        "1000 mA",
        "500 mA LB-100",
        "accessory loads",
        "VBAT_PROT",
        "VBAT_RAW",
        "2.2µF 100V X7R",
        "10µF 100V",
        "BUCK_EN_UVLO",
        "332kΩ",
        "100kΩ",
        "6.48V rising UVLO",
        "4.75V shutdown",
        "OUT1..OUT10",
        "LB_3V3_IO",
        "BUCK_RON_SET",
        "41.2kΩ",
        "300kHz",
        "BUCK_FB",
        "158kΩ",
        "49.9kΩ",
        "5.0V",
        "1.2V reference",
        "BUCK_BST",
        "2.2nF 50V X7R",
        "L1",
        "47µH",
        "AEC-Q200",
        "Isat at least 2.2A",
        "Irms at least 1.2A",
        "COUT",
        "2x22µF 10V X7R",
        "DC-bias",
        "PB_PWR_GOOD",
        "47kΩ",
        "10nF DNP",
        "BUCK_SW",
        "DNP RC snubber",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "JLCPCB PCBWay",
        "LM5164QDDATQ1",
        "LM5164QDDARQ1",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"logic-power value freeze checklist must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-logic-power-design-values.csv")
    for token in ("41.2kΩ", "158kΩ", "49.9kΩ", "47µH", "PB_PWR_GOOD", "TBD not final"):
        if token not in design_text:
            fail(f"logic-power design values must support freeze checklist token {token}")

    calculation_text = read_text(PB100_DIR / "PB-100-logic-power-design-calculation.md")
    for token in ("6.48 V", "4.75 V", "2.2 nF", "47 µH", "47 kΩ"):
        if token not in calculation_text:
            fail(f"logic-power design calculation must support freeze checklist token {token}")

    lb_precheck_text = read_text(REPO_ROOT / "hardware" / "logic-board" / "LB-100" / "LB-100-power-budget-precheck.md")
    for token in ("500 mA", "PB_5V_OUT", "LM5013-Q1-class", "PB_PWR_GOOD"):
        if token not in lb_precheck_text:
            fail(f"LB-100 power-budget precheck must support logic-power freeze checklist token {token}")


def validate_logic_power_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-logic-power-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_LOGIC_POWER_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate logic-power derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in LOGIC_POWER_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if derivation_id == "LOGIC-DER-004" and ("vin =" not in row_text or "uvlo" not in row_text):
            fail("logic-power derivation precheck must include UVLO threshold equation")
        if derivation_id == "LOGIC-DER-005" and ("fsw" not in row_text or "rron" not in row_text):
            fail("logic-power derivation precheck must include RON frequency equation")
        if derivation_id == "LOGIC-DER-006" and ("vout =" not in row_text or "1.2v" not in row_text):
            fail("logic-power derivation precheck must include feedback equation and 1.2V reference")
        if derivation_id == "LOGIC-DER-010" and ("pb-100.kicad_pcb" not in row_text or "manufacturing" not in row_text):
            fail("logic-power derivation precheck must block layout and manufacturing outputs")

    missing_items = sorted(REQUIRED_LOGIC_POWER_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI LM5164-Q1",
        "6 V to 100 V input 1 A",
        "TI LM5013-Q1",
        "100 V 3.5 A",
        "TPS54360B-Q1",
        "60 V conditional alternate",
        "PB_5V_OUT",
        "1000 mA",
        "500 mA LB-100",
        "accessory loads",
        "VBAT_PROT",
        "VBAT_RAW",
        "2.2µF 100V X7R",
        "0.1µF",
        "10µF 100V",
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "332kΩ",
        "100kΩ",
        "6.48 V rising UVLO",
        "4.75 V shutdown",
        "OUT1..OUT10",
        "LB_3V3_IO",
        "fSW ≈ VOUT × 2500 / RRON(kΩ)",
        "41.2kΩ",
        "300kHz",
        "VOUT = VFB × (1 + RFB_TOP / RFB_BOT)",
        "158kΩ",
        "49.9kΩ",
        "5.0V",
        "1.2V",
        "2.2nF 50V X7R",
        "PB_PWR_GOOD",
        "47kΩ",
        "10nF DNP",
        "47µH",
        "AEC-Q200",
        "Isat at least 2.2A",
        "Irms at least 1.2A",
        "2x22µF 10V X7R",
        "DC-bias",
        "DNP RC snubber",
        "JLCPCB PCBWay",
        "LM5164QDDATQ1",
        "LM5164QDDARQ1",
        "LOGIC_BUCK_INDUCTOR",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in precheck_text:
            fail(f"logic-power value derivation precheck must include {token}")

    checklist_text = read_text(PB100_DIR / "PB-100-logic-power-value-freeze-checklist.csv")
    for token in ("LOGIC-FRZ-004", "LOGIC-FRZ-005", "LOGIC-FRZ-006", "LOGIC-FRZ-007"):
        if token not in checklist_text:
            fail(f"logic-power value freeze checklist must support derivation token {token}")


def validate_logic_power_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-logic-power-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic-power closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_LOGIC_POWER_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown logic-power closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate logic-power closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in LOGIC_POWER_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "LOGIC-CLS-002" and ("pb_5v_out" not in row_text or "accessory loads" not in row_text):
            fail("logic-power closeout load budget row must keep PB_5V_OUT accessory-load boundary")
        if precheck_id == "LOGIC-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("logic-power closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_LOGIC_POWER_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic-power closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "LM5164-Q1-class",
        "100 V 1 A",
        "LM5013-Q1-class",
        "100 V 3.5 A",
        "TPS54360B-Q1-class",
        "TVS margin",
        "PBREL-007",
        "PB_5V_OUT",
        "1000 mA",
        "500 mA LB-100",
        "500 mA PB-side",
        "accessory loads",
        "hardware/logic-board/LB-100/LB-100-power-budget-precheck.md",
        "VBAT_PROT",
        "U3 VIN",
        "VBAT_RAW",
        "2.2µF 100V X7R",
        "0.1µF",
        "10µF 100V",
        "PB-100-tvs-overshoot-closeout-precheck.csv",
        "BUCK_EN_UVLO",
        "332kΩ",
        "100kΩ",
        "6.48 V rising UVLO",
        "4.75 V shutdown",
        "OUT1..OUT10",
        "LB_3V3_IO",
        "PB_PWR_GOOD",
        "BUCK_RON_SET",
        "41.2kΩ",
        "300kHz",
        "BUCK_FB",
        "158kΩ",
        "49.9kΩ",
        "5.0V",
        "1.2V reference",
        "BUCK_BST",
        "2.2nF 50V X7R",
        "L1",
        "47µH",
        "AEC-Q200",
        "Isat at least 2.2A",
        "Irms at least 1.2A",
        "COUT",
        "2x22µF 10V X7R",
        "DC-bias",
        "47kΩ",
        "10nF DNP",
        "BUCK_SW",
        "DNP RC snubber",
        "switch-node ringing",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "JLCPCB PCBWay",
        "LM5164QDDATQ1",
        "LM5164QDDARQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "U3 placement",
        "L1 placement",
        "switch-node copper",
        "thermal-pad vias",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"logic-power closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-logic-power-value-freeze-checklist.csv": ("LOGIC-FRZ-002", "LOGIC-FRZ-010"),
        "PB-100-logic-power-value-derivation-precheck.csv": ("LOGIC-DER-004", "LOGIC-DER-010"),
        "PB-100-logic-power-design-values.csv": ("BUCK_EN_UVLO", "TBD not final", "PB_PWR_GOOD"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"logic-power closeout precheck requires {supporting_artifact} token {token}")


def validate_logic_power_rail_trace() -> None:
    path = PB100_DIR / "PB-100-logic-power-rail-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic power rail trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_RAIL_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "Buck regulator",
        "Buck input rail",
        "Buck output rail",
        "Power good",
        "Safe default off",
        "Higher-current fallback",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        item = row["Trace item"].strip()
        if item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate trace item {item}")
        if item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown trace item {item}")
        rows_by_item[item] = row
        for column in LOGIC_POWER_RAIL_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if "schematic freeze" not in " ".join(row.values()).lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic power trace items: "
            f"{', '.join(missing_items)}"
        )

    trace_text = read_text(path)
    for token in (
        "LM5164-Q1-class 100 V 1 A",
        "LM5013-Q1-class 100 V fallback",
        "PB_5V_OUT must not power accessory loads",
        "PB_PWR_GOOD",
        "default off",
        "TPS54360B-Q1-class 60 V path remains conditional",
    ):
        if token not in trace_text:
            fail(f"logic power rail trace must include {token}")

    budget_rows = list(csv.DictReader((PB100_DIR / "PB-100-logic-power-budget.csv").open(newline="", encoding="utf-8")))
    initial_total = next((row for row in budget_rows if row["Load"].strip() == "Initial total"), None)
    if initial_total is None or initial_total["Current mA"].strip() != "1000":
        fail("logic power budget must keep 1000 mA initial total")
    if "LM5013-Q1" not in initial_total["Notes"]:
        fail("logic power budget must keep LM5013-Q1 fallback note")

    placeholder_text = read_text(PB100_DIR / "PB-100-logic-power-design-placeholders.csv")
    for token in ("Preferred LM5164-Q1 class", "LM5013-Q1 remains higher-current alternate", "Must not connect to raw unfused input"):
        if token not in placeholder_text:
            fail(f"logic power placeholders must include {token}")

    design_values_text = read_text(PB100_DIR / "PB-100-logic-power-design-values.csv")
    for token in ("PB_5V_OUT must not power accessory loads", "LM5013-Q1-class", "Outputs default off"):
        if token not in design_values_text:
            fail(f"logic power design values must include {token}")

    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    board_signals = set(capabilities["telemetry"]["board_signals"])
    if "PB_PWR_GOOD" not in board_signals:
        fail("PB-100 capability manifest must expose PB_PWR_GOOD board signal")

    firmware_readme = read_text(REPO_ROOT / "firmware" / "README.md").lower()
    for token in ("runtime boot", "outputs off", "hardware capability"):
        if token not in firmware_readme:
            fail(f"firmware README must keep runtime boot safety token: {token}")
