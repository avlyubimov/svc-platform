from __future__ import annotations

from .common import (
    HIGH_MEDIUM_OUTPUT_BASELINE_TRACE_COLUMNS,
    LOW_CURRENT_OUTPUT_BASELINE_TRACE_COLUMNS,
    OUTPUT_FREEZE_REVIEW_COLUMNS,
    OUTPUT_NET_EXPANSION_COLUMNS,
    OUTPUT_STAGE_CLOSEOUT_PRECHECK_COLUMNS,
    OUTPUT_STAGE_DESIGN_VALUE_COLUMNS,
    OUTPUT_STAGE_VALUE_DERIVATION_PRECHECK_COLUMNS,
    OUTPUT_STAGE_VALUE_FREEZE_CHECKLIST_COLUMNS,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_HIGH_MEDIUM_OUTPUT_FREEZE_REVIEW_ITEMS,
    REQUIRED_LOW_CURRENT_OUTPUT_FREEZE_REVIEW_ITEMS,
    REQUIRED_OUTPUT_STAGE_CLASSES,
    REQUIRED_OUTPUT_STAGE_CLOSEOUT_PRECHECKS,
    REQUIRED_OUTPUT_STAGE_ITEMS,
    REQUIRED_OUTPUT_STAGE_VALUE_DERIVATION_CHECKS,
    REQUIRED_OUTPUT_STAGE_VALUE_FREEZE_CHECKS,
    csv,
    fail,
    json,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def output_controller_template_net_patterns() -> set[str]:
    path = PB100_DIR / "PB-100-output-controller-pin-template.csv"
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    return {row["Net pattern"].strip() for row in rows}


def validate_output_net_expansion() -> None:
    path = PB100_DIR / "PB-100-output-net-expansion.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output net expansion: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_NET_EXPANSION_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    output_matrix_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8"))
    )
    expected_outputs = {row["Output"].strip() for row in output_matrix_rows}
    expected_patterns = {
        pattern for pattern in output_controller_template_net_patterns() if pattern.startswith("OUTn_")
    } | {"OUTn_LOAD", "OUTn_FUSED"}
    b2b_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    b2b_nets = {row["Net"].strip() for row in b2b_rows}
    manifest_rows = list(csv.DictReader((PB100_DIR / "PB-100-kicad-sheet-manifest.csv").open(newline="", encoding="utf-8")))
    manifest_sheets = {row["Sheet file"].strip() for row in manifest_rows}

    seen_pairs = set()
    for row_number, row in enumerate(rows, 2):
        output = row["Output"].strip()
        pattern = row["Net pattern"].strip()
        expanded_net = row["Expanded net"].strip()
        if output not in expected_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output {output}")
        if pattern not in expected_patterns:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unexpected net pattern {pattern}")
        expected_net = pattern.replace("OUTn", output)
        if expanded_net != expected_net:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: expected expanded net "
                f"{expected_net}, got {expanded_net}"
            )
        pair = (output, pattern)
        if pair in seen_pairs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate expansion {output}/{pattern}")
        seen_pairs.add(pair)
        validate_no_role_tokens_in_row(path, row_number, row)
        primary_sheet = row["Primary sheet"].strip()
        if primary_sheet not in manifest_sheets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Primary sheet {primary_sheet}")
        for column in ("Source artifact", "Default state", "Safety rule"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if pattern in {"OUTn_CTL", "OUTn_FLT", "OUTn_IMON"} and expanded_net not in b2b_nets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: {expanded_net} is missing from JPB1 pin map")
        if pattern == "OUTn_CTL" and "configuration" not in row["Safety rule"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: control nets must preserve configuration mapping")
        if pattern in {"OUTn_LOAD", "OUTn_FUSED"} and "off" not in row["Default state"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: output power nets must default off")
        if pattern.startswith("OUTn_") and "OUTn" in expanded_net:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: expanded net still contains OUTn")

    expected_pairs = {(output, pattern) for output in expected_outputs for pattern in expected_patterns}
    missing_pairs = sorted(expected_pairs - seen_pairs)
    extra_pairs = sorted(seen_pairs - expected_pairs)
    if missing_pairs:
        formatted = ", ".join(f"{output}/{pattern}" for output, pattern in missing_pairs)
        fail(f"{path.relative_to(REPO_ROOT)} is missing expansions: {formatted}")
    if extra_pairs:
        formatted = ", ".join(f"{output}/{pattern}" for output, pattern in extra_pairs)
        fail(f"{path.relative_to(REPO_ROOT)} has extra expansions: {formatted}")


def validate_output_stage_design_values() -> None:
    path = PB100_DIR / "PB-100-output-stage-design-values.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output-stage design values: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_STAGE_DESIGN_VALUE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    allowed_patterns = output_controller_template_net_patterns() | {"OUTn_LOAD"}
    seen_items: dict[str, set[str]] = {output_class: set() for output_class in REQUIRED_OUTPUT_STAGE_CLASSES}
    class_text: dict[str, list[str]] = {output_class: [] for output_class in REQUIRED_OUTPUT_STAGE_CLASSES}
    for row_number, row in enumerate(rows, 2):
        output_class = row["Output class"].strip()
        design_item = row["Design item"].strip()
        if output_class not in REQUIRED_OUTPUT_STAGE_CLASSES:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid output class {output_class}")
        if design_item not in REQUIRED_OUTPUT_STAGE_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid design item {design_item}")
        if design_item in seen_items[output_class]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate {output_class}/{design_item}")
        seen_items[output_class].add(design_item)
        class_text[output_class].append(" ".join(row.values()))
        validate_no_role_tokens_in_row(path, row_number, row)
        for column in ("Applies to", "Related net pattern", "Candidate direction", "Freeze dependency", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Value status"].strip() != "Selected final pre-layout":
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                "output design value must be Selected final pre-layout"
            )
        if "freeze" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must remain explicit")
        related_patterns = [part.strip() for part in row["Related net pattern"].split(";")]
        if not related_patterns:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing related net pattern")
        for pattern in related_patterns:
            if pattern not in allowed_patterns:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output "
                    f"net pattern {pattern}"
                )
        if output_class == "High current" and "OUT2" not in row["Applies to"]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: high-current rows must apply to OUT2")

    for output_class, items in seen_items.items():
        missing_items = sorted(REQUIRED_OUTPUT_STAGE_ITEMS - items)
        if missing_items:
            fail(
                f"{path.relative_to(REPO_ROOT)} is missing {output_class} design items: "
                f"{', '.join(missing_items)}"
            )
    if "SOA" not in " ".join(class_text["High current"]):
        fail("high-current output-stage design values must keep OUT2 SOA explicit")
    if "external controller" not in " ".join(class_text["Low current"]).lower():
        fail("low-current output-stage design values must preserve external-controller baseline")


def validate_output_stage_value_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-output-stage-value-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output-stage value freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_STAGE_VALUE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_OUTPUT_STAGE_VALUE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output-stage value check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output-stage value check {check_id}")
        rows_by_check[check_id] = row
        for column in OUTPUT_STAGE_VALUE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if check_id == "OUTVAL-002" and ("out2" not in row_text or "soa" not in row_text or "escape path" not in row_text):
            fail("OUT2 output-stage checklist row must keep SOA and escape path explicit")
        if check_id == "OUTVAL-004" and ("no direct 40 v smart-switch rail" not in row_text or "adr" not in row_text):
            fail("low-current output-stage checklist row must keep no-direct-40V-smart-switch ADR boundary")
        if check_id == "OUTVAL-006" and ("default-off" not in row_text or "reset" not in row_text):
            fail("output gate-drive checklist row must keep default-off reset boundary")
        if check_id == "OUTVAL-007" and ("0-30a" not in row_text or "0-20a" not in row_text or "0-8a" not in row_text):
            fail("output telemetry checklist row must keep all class telemetry ranges")
        if check_id == "OUTVAL-009" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("output no-layout checklist row must block PCB layout explicitly")

    missing_checks = sorted(REQUIRED_OUTPUT_STAGE_VALUE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing output-stage value checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "TPS48110AQDGXRQ1",
        "OUT2",
        "20A fuse",
        "18A configured limit",
        "30A 100ms",
        "80A 4ms",
        "95.91A 5us",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "OUTn_PU",
        "OUTn_PD",
        "OUTn_CS_P",
        "OUTn_CS_N",
        "0-30A",
        "0-20A",
        "0-8A",
        "IAUT300N08S5N012ATMA2",
        "80V",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in checklist_text:
            fail(f"output-stage value freeze checklist must include {token}")


def validate_output_stage_value_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-output-stage-value-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output-stage value derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_STAGE_VALUE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_OUTPUT_STAGE_VALUE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in OUTPUT_STAGE_VALUE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if derivation_id == "OUTDRV-004" and ("equation 6" not in row_text or "riwrn" not in row_text):
            fail("output derivation precheck must include RIWRN Equation 6")
        if derivation_id == "OUTDRV-005" and ("equation 7" not in row_text or "9.95ms" not in row_text):
            fail("output derivation precheck must include TMR Equation 7 and selected 9.95ms timing")
        if derivation_id == "OUTDRV-006" and ("equation 11" not in row_text or "riscp" not in row_text):
            fail("output derivation precheck must include RISCP Equation 11")
        if derivation_id == "OUTDRV-007" and ("equation 12" not in row_text or "equation 13" not in row_text):
            fail("output derivation precheck must include IMON Equations 12 and 13")
        if derivation_id == "OUTDRV-010" and ("no-layout" not in row_text and "pb-100.kicad_pcb" not in row_text):
            fail("output derivation precheck must keep no-layout boundary explicit")

    missing_items = sorted(REQUIRED_OUTPUT_STAGE_VALUE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing output-stage derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI TPS4811-Q1",
        "TPS48110Q1EVM",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "OUTn_BST",
        "Equation 1",
        "Equation 4",
        "Equation 6",
        "Equation 7",
        "Equation 11",
        "Equation 12",
        "Equation 13",
        "OUT2",
        "18A",
        "12A",
        "8A",
        "4A",
        "0-30A",
        "0-20A",
        "0-8A",
        "ADR-0011",
        "no direct 40V smart-switch rail",
        "PB-100.kicad_pcb",
    ):
        if token not in precheck_text:
            fail(f"output-stage value derivation precheck must include {token}")


def validate_output_stage_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-output-stage-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output-stage closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_STAGE_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_OUTPUT_STAGE_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in OUTPUT_STAGE_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if precheck_id == "OUTCLS-002" and ("out2" not in row_text or "out5" not in row_text or "out10" not in row_text):
            fail("output closeout class-map row must cover OUT2, low-current, and OUT10 classes")
        if precheck_id == "OUTCLS-008" and ("adr-0011" not in row_text or "no direct 40 v smart-switch rail" not in row_text):
            fail("output closeout low-current row must preserve ADR-0011 no-direct-40V-smart-switch boundary")
        if precheck_id == "OUTCLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("output closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_OUTPUT_STAGE_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing output closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "TI TPS4811-Q1",
        "TPS48110AQDGXRQ1",
        "TPS48110Q1EVM",
        "Equation 1",
        "Equation 4",
        "Equation 6",
        "Equation 7",
        "Equation 11",
        "Equation 12",
        "Equation 13",
        "High current",
        "Medium current",
        "Low current",
        "OUT2",
        "OUT10",
        "OUT5",
        "OUT8",
        "OUT9",
        "20A fuse",
        "18A configured limit",
        "15A/12A",
        "10A/8A",
        "5A fuse",
        "4A configured limit",
        "OV threshold divider",
        "Current warning threshold",
        "Short-circuit threshold",
        "Fault timer",
        "Bootstrap capacitor",
        "Gate drive resistors",
        "Current sense topology",
        "Inductive clamp strategy",
        "Value status Selected final pre-layout",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "RSET",
        "RSNS",
        "VOS_SET",
        "RIWRN",
        "RISCP",
        "CTMR",
        "9.95ms",
        "OUTn_BST",
        "OUTn_PU",
        "OUTn_PD",
        "OUTn_CTL",
        "OUTn_INP",
        "default-off",
        "reset",
        "gate pull-down",
        "Qg_total",
        "C1",
        "OUTn_CS_P",
        "OUTn_CS_N",
        "OUTn_IMON",
        "0-30A",
        "0-20A",
        "0-8A",
        "LB-100 ADC",
        "OUT2 SOA",
        "fuse energy",
        "30A 100ms",
        "80A 4ms",
        "95.91A 5us",
        "IAUT300N08S5N012ATMA2",
        "80V",
        "PB-100-tvs-load-dump-margin-trace.csv",
        "PB-100-mosfet-voltage-margin-review.md",
        "ADR-0011",
        "external-controller",
        "IAUT300N08S5N012ATMA2 80V N-MOSFET",
        "no direct 40 V smart-switch rail",
        "no direct 40V smart-switch rail",
        "output-channel-template.kicad_sch",
        "outputs-1-10.kicad_sch",
        "PB-100-output-net-expansion.csv",
        "PB-100-schematic-instance-symbol-map.csv",
        "OUT1 through OUT10",
        "generic OUTn names",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "MOSFET placement",
        "fuse placement",
        "connector placement",
        "high-current copper",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"output-stage closeout precheck must include {token}")

    design_rows = list(csv.DictReader((PB100_DIR / "PB-100-output-stage-design-values.csv").open(newline="", encoding="utf-8")))
    seen_items: dict[str, set[str]] = {output_class: set() for output_class in REQUIRED_OUTPUT_STAGE_CLASSES}
    for row in design_rows:
        output_class = row["Output class"].strip()
        if output_class in seen_items:
            seen_items[output_class].add(row["Design item"].strip())
            if row["Value status"].strip() != "Selected final pre-layout":
                fail(
                    "output-stage closeout precheck requires generated values to be "
                    "selected final pre-layout"
                )
    for output_class, items in seen_items.items():
        missing_items = sorted(REQUIRED_OUTPUT_STAGE_ITEMS - items)
        if missing_items:
            fail(
                f"output-stage closeout precheck requires {output_class} design values to include: "
                f"{', '.join(missing_items)}"
            )

    freeze_text = read_text(PB100_DIR / "PB-100-output-stage-value-freeze-checklist.csv")
    derivation_text = read_text(PB100_DIR / "PB-100-output-stage-value-derivation-precheck.csv")
    for token in ("OUTVAL-002", "OUTVAL-004", "OUTVAL-009"):
        if token not in freeze_text:
            fail(f"output-stage closeout precheck requires freeze checklist token {token}")
    for token in ("OUTDRV-004", "OUTDRV-005", "OUTDRV-006", "OUTDRV-007", "OUTDRV-010"):
        if token not in derivation_text:
            fail(f"output-stage closeout precheck requires derivation token {token}")


def validate_low_current_output_baseline_trace() -> None:
    path = PB100_DIR / "PB-100-low-current-output-baseline-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty low-current output baseline trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOW_CURRENT_OUTPUT_BASELINE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_outputs = {"OUT5", "OUT8", "OUT9"}
    rows_by_output: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        output = row["Output"].strip()
        if output in rows_by_output:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output {output}")
        if output not in expected_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unexpected low-current output {output}")
        rows_by_output[output] = row
        for column in LOW_CURRENT_OUTPUT_BASELINE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values())
        for token in (
            "Low current",
            "5",
            "4",
            "TPS48110AQDGXRQ1 plus selected IAUT300N08S5N012ATMA2 80V TOLL N-MOSFET",
            "configuration only",
            "no direct 40 V smart-switch rail",
            "future ADR",
            "schematic freeze",
        ):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: low-current row must include {token}")

    missing_outputs = sorted(expected_outputs - rows_by_output.keys())
    if missing_outputs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing low-current outputs: "
            f"{', '.join(missing_outputs)}"
        )

    matrix_rows = list(csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8")))
    matrix_by_output = {row["Output"].strip(): row for row in matrix_rows}
    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    capability_by_output = {row["id"]: row for row in capabilities["outputs"]}
    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    config_by_output = {row["id"]: row for row in config_example["outputs"]}

    for output in sorted(expected_outputs):
        trace_row = rows_by_output[output]
        matrix_row = matrix_by_output.get(output)
        capability_row = capability_by_output.get(output)
        config_row = config_by_output.get(output)
        if matrix_row is None or capability_row is None or config_row is None:
            fail(f"{output} must exist in matrix, capability manifest, and config example")
        if matrix_row["Class"].strip() != "Low current":
            fail(f"{output} must remain Low current in output channel matrix")
        if matrix_row["Initial switch direction"].strip() != trace_row["Switch architecture"].strip():
            fail(f"{output} switch architecture must match output channel matrix")
        if int(matrix_row["Target fuse A"]) != int(trace_row["Fuse target A"]):
            fail(f"{output} fuse target must match output channel matrix")
        if int(matrix_row["Target current limit A"]) != int(trace_row["Current limit A"]):
            fail(f"{output} current limit must match output channel matrix")
        if capability_row["class"] != "Low current":
            fail(f"{output} must remain Low current in capability manifest")
        if capability_row["target_fuse_a"] != int(trace_row["Fuse target A"]):
            fail(f"{output} capability fuse target must match low-current trace")
        if capability_row["target_current_limit_a"] != int(trace_row["Current limit A"]):
            fail(f"{output} capability current limit must match low-current trace")
        if config_row["fuse_a"] != int(trace_row["Fuse target A"]):
            fail(f"{output} config example fuse must match low-current trace")
        if config_row["current_limit_a"] != int(trace_row["Current limit A"]):
            fail(f"{output} config example current limit must match low-current trace")

    output_contract_text = read_text(PB100_DIR / "PB-100-output-channel-pin-contract.csv")
    for output in sorted(expected_outputs):
        if f"{output}_CTL" not in output_contract_text or f"{output}_IMON" not in output_contract_text:
            fail(f"output pin contract must include {output} control and current telemetry nets")

    low_current_design_rows = [
        row
        for row in csv.DictReader((PB100_DIR / "PB-100-output-stage-design-values.csv").open(newline="", encoding="utf-8"))
        if row["Output class"].strip() == "Low current"
    ]
    if len(low_current_design_rows) != len(REQUIRED_OUTPUT_STAGE_ITEMS):
        fail("low-current output-stage design values must cover every required design item")
    low_current_text = " ".join(" ".join(row.values()) for row in low_current_design_rows).lower()
    if "external controller baseline" not in low_current_text or "no direct 40 v smart-switch rail" not in low_current_text:
        fail("low-current design values must keep external-controller baseline and no direct 40 V rail explicit")


def parse_space_separated_outputs(value: str) -> list[str]:
    return [part.strip() for part in value.split() if part.strip()]


def validate_high_medium_output_baseline_trace() -> None:
    path = PB100_DIR / "PB-100-high-medium-output-baseline-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty high/medium output baseline trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in HIGH_MEDIUM_OUTPUT_BASELINE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_groups = {
        "High current": {
            "outputs": ["OUT2"],
            "class": "High current",
            "fuses": "20",
            "limits": "18",
        },
        "Medium current 12A": {
            "outputs": ["OUT1"],
            "class": "Medium current",
            "fuses": "15",
            "limits": "12",
        },
        "Medium current 8A": {
            "outputs": ["OUT3", "OUT4", "OUT6", "OUT7", "OUT10"],
            "class": "Medium current",
            "fuses": "10",
            "limits": "8",
        },
    }
    rows_by_group: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        group = row["Output group"].strip()
        if group in rows_by_group:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output group {group}")
        if group not in expected_groups:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unexpected output group {group}")
        rows_by_group[group] = row
        for column in HIGH_MEDIUM_OUTPUT_BASELINE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values())
        for token in ("TPS48110AQDGXRQ1 plus selected IAUT300N08S5N012ATMA2 80V TOLL MOSFET", "layout"):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: high/medium row must include {token}")

    missing_groups = sorted(set(expected_groups) - set(rows_by_group))
    if missing_groups:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing output groups: "
            f"{', '.join(missing_groups)}"
        )

    matrix_rows = list(csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8")))
    matrix_by_output = {row["Output"].strip(): row for row in matrix_rows}
    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    capability_by_output = {row["id"]: row for row in capabilities["outputs"]}
    config_example = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "config-example.json"))
    config_by_output = {row["id"]: row for row in config_example["outputs"]}

    covered_outputs: set[str] = set()
    for group, expected in expected_groups.items():
        row = rows_by_group[group]
        outputs = parse_space_separated_outputs(row["Outputs"])
        if outputs != expected["outputs"]:
            fail(f"{group} outputs must be {' '.join(expected['outputs'])}")
        if row["Capability class"].strip() != expected["class"]:
            fail(f"{group} class must be {expected['class']}")
        if row["Fuse targets A"].strip() != expected["fuses"]:
            fail(f"{group} fuse target must be {expected['fuses']}")
        if row["Current limits A"].strip() != expected["limits"]:
            fail(f"{group} current limit must be {expected['limits']}")
        covered_outputs.update(outputs)
        for output in outputs:
            matrix_row = matrix_by_output.get(output)
            capability_row = capability_by_output.get(output)
            config_row = config_by_output.get(output)
            if matrix_row is None or capability_row is None or config_row is None:
                fail(f"{output} must exist in matrix, capability manifest, and config example")
            if matrix_row["Class"].strip() != expected["class"]:
                fail(f"{output} must remain {expected['class']} in output channel matrix")
            if matrix_row["Initial switch direction"].strip() != "TPS48110AQDGXRQ1 plus selected IAUT300N08S5N012ATMA2 80V TOLL N-MOSFET":
                fail(f"{output} must keep TPS48110 external MOSFET switch direction")
            if int(matrix_row["Target fuse A"]) != int(expected["fuses"]):
                fail(f"{output} fuse target must match high/medium trace")
            if int(matrix_row["Target current limit A"]) != int(expected["limits"]):
                fail(f"{output} current limit must match high/medium trace")
            if capability_row["class"] != expected["class"]:
                fail(f"{output} must remain {expected['class']} in capability manifest")
            if capability_row["target_fuse_a"] != int(expected["fuses"]):
                fail(f"{output} capability fuse target must match high/medium trace")
            if capability_row["target_current_limit_a"] != int(expected["limits"]):
                fail(f"{output} capability current limit must match high/medium trace")
            if config_row["fuse_a"] != int(expected["fuses"]):
                fail(f"{output} config example fuse must match high/medium trace")
            if config_row["current_limit_a"] != int(expected["limits"]):
                fail(f"{output} config example current limit must match high/medium trace")
            if f"{output}_IMON" not in row["Telemetry path"]:
                fail(f"{output} telemetry path must include {output}_IMON")

    if covered_outputs != {"OUT1", "OUT2", "OUT3", "OUT4", "OUT6", "OUT7", "OUT10"}:
        fail("high/medium trace must cover OUT1 OUT2 OUT3 OUT4 OUT6 OUT7 OUT10")

    high_design_text = " ".join(
        " ".join(row.values())
        for row in csv.DictReader((PB100_DIR / "PB-100-output-stage-design-values.csv").open(newline="", encoding="utf-8"))
        if row["Output class"].strip() == "High current"
    )
    medium_design_text = " ".join(
        " ".join(row.values())
        for row in csv.DictReader((PB100_DIR / "PB-100-output-stage-design-values.csv").open(newline="", encoding="utf-8"))
        if row["Output class"].strip() == "Medium current"
    )
    if "OUT2" not in high_design_text or "SOA" not in high_design_text:
        fail("high-current design values must keep OUT2 SOA explicit")
    for token in ("Current sense topology", "Gate drive resistors", "Inductive clamp strategy"):
        if token not in high_design_text or token not in medium_design_text:
            fail(f"high/medium output-stage design values must include {token}")
    if "OUT1 OUT3 OUT4 OUT6 OUT7 OUT10" not in medium_design_text:
        fail("medium-current design values must keep the medium output set explicit")


def validate_high_medium_output_freeze_review() -> None:
    path = PB100_DIR / "PB-100-high-medium-output-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty high/medium output freeze review: {path.relative_to(REPO_ROOT)}")

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
        if review_item not in REQUIRED_HIGH_MEDIUM_OUTPUT_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown high/medium output review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate high/medium output review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_HIGH_MEDIUM_OUTPUT_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing high/medium output review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "TPS48110AQDGXRQ1",
        "OUT2",
        "20A fuse",
        "18A configured limit",
        "30A 100ms",
        "80A 4ms",
        "95.91A 5us",
        "OUT2 escape path",
        "OUT1",
        "OUT3 OUT4 OUT6 OUT7 OUT10",
        "OUTn_PU",
        "OUTn_PD",
        "OUTn_CTL",
        "OUTn_CS_P",
        "OUTn_CS_N",
        "OUTn_IMON",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "OUTn_LOAD",
        "No PCB layout",
    ):
        if token not in review_text:
            fail(f"high/medium output freeze review must include {token}")

    for token in (
        "PB-100-high-medium-output-baseline-trace.csv",
        "PB-100-output-controller-pin-template.csv",
        "PB-100-output-stage-design-values.csv",
        "PB-100-current-telemetry-freeze-review.csv",
        "PB-100-thermal-telemetry-freeze-review.csv",
    ):
        if token not in review_text:
            fail(f"high/medium output freeze review must cite {token}")

    high_medium_text = read_text(PB100_DIR / "PB-100-high-medium-output-baseline-trace.csv")
    for token in ("OUT2", "OUT1", "OUT3 OUT4 OUT6 OUT7 OUT10", "TPS48110AQDGXRQ1 plus selected IAUT300N08S5N012ATMA2 80V TOLL MOSFET"):
        if token not in high_medium_text:
            fail(f"high/medium baseline trace must support freeze review token {token}")

    soa_text = read_text(PB100_DIR / "PB-100-out2-soa-envelope.csv")
    for token in ("30", "100 ms", "80", "4 ms", "95.91", "5 us max"):
        if token not in soa_text:
            fail(f"OUT2 SOA envelope must support freeze review token {token}")

    firmware_tests = read_text(REPO_ROOT / "firmware" / "tests" / "test_output_manager.c")
    for token in ("test_init_keeps_all_outputs_off", "test_invalid_telemetry_is_denied"):
        if token not in firmware_tests:
            fail(f"output manager tests must retain high/medium freeze review token {token}")


def validate_low_current_output_freeze_review() -> None:
    path = PB100_DIR / "PB-100-low-current-output-freeze-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty low-current output freeze review: {path.relative_to(REPO_ROOT)}")

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
        if review_item not in REQUIRED_LOW_CURRENT_OUTPUT_FREEZE_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown low-current output review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate low-current output review item {review_item}")
        rows_by_item[review_item] = row
        for column in OUTPUT_FREEZE_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_items = sorted(REQUIRED_LOW_CURRENT_OUTPUT_FREEZE_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing low-current output review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "ADR-0011",
        "OUT5",
        "OUT8",
        "OUT9",
        "5A fuse",
        "4A configured current limit",
        "TPS48110AQDGXRQ1",
        "IAUT300N08S5N012ATMA2 80V external N-MOSFET",
        "no direct 40V smart-switch rail",
        "future ADR",
        "OUTn_CTL",
        "OUTn_PU",
        "OUTn_PD",
        "OUT5_IMON",
        "OUT8_IMON",
        "OUT9_IMON",
        "0-8A",
        "OUTn_IWRN_SET",
        "OUTn_ISCP_SET",
        "OUTn_TMR",
        "configuration and rules",
    ):
        if token not in review_text:
            fail(f"low-current output freeze review must include {token}")

    low_current_text = read_text(PB100_DIR / "PB-100-low-current-output-baseline-trace.csv")
    for token in ("OUT5", "OUT8", "OUT9", "no direct 40 V smart-switch rail", "future ADR"):
        if token not in low_current_text:
            fail(f"low-current baseline trace must support freeze review token {token}")

    design_values_text = read_text(PB100_DIR / "PB-100-output-stage-design-values.csv")
    for token in ("Low current", "OUT5 OUT8 OUT9", "No direct 40 V smart-switch rail"):
        if token not in design_values_text:
            fail(f"output-stage design values must support low-current freeze review token {token}")

    firmware_joined = "\n".join(
        (
            read_text(REPO_ROOT / "firmware" / "tests" / "test_role_resolver.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_rule_runtime.c"),
            read_text(REPO_ROOT / "firmware" / "tests" / "test_output_manager.c"),
        )
    )
    for token in ("test_missing_role_is_reported", "test_fault_dispatch_runs_before_rule_actions", "test_init_keeps_all_outputs_off"):
        if token not in firmware_joined:
            fail(f"firmware tests must retain low-current freeze review token {token}")
