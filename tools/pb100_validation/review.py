from __future__ import annotations

from .common import (
    ALLOWED_CAPTURE_STATUSES,
    CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM,
    DISALLOWED_LAYOUT_SUFFIXES,
    FAULT_RESPONSE_MATRIX_COLUMNS,
    KICAD_DIR,
    PB100_DIR,
    POST_PROTOTYPE_VALIDATION_GATE_COLUMNS,
    Path,
    REPO_ROOT,
    REQUIRED_CAPTURE_WORK_ITEMS,
    REQUIRED_FAULT_IDS,
    REQUIRED_RELEASE_MANIFEST_ARTIFACTS,
    REVIEW_RELEASE_MANIFEST_COLUMNS,
    SCHEMATIC_CAPTURE_WORK_QUEUE_COLUMNS,
    TEST_POINT_PLAN_COLUMNS,
    VALIDATION_HOOK_NAMES,
    csv,
    fail,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def validate_test_point_plan() -> None:
    path = PB100_DIR / "PB-100-test-point-plan.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 test point plan: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in TEST_POINT_PLAN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    manifest_rows = list(csv.DictReader((PB100_DIR / "PB-100-kicad-sheet-manifest.csv").open(newline="", encoding="utf-8")))
    manifest_sheets = {row["Sheet file"].strip() for row in manifest_rows}
    output_rows = list(csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8")))
    outputs = {row["Output"].strip() for row in output_rows}
    b2b_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    b2b_nets = {row["Net"].strip() for row in b2b_rows}

    required_nets = {
        "GND",
        "VBAT_RAW",
        "VBAT_REV_PROT",
        "VBAT_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "VBAT_SENSE",
        "IIN_SENSE",
        "PB_5V_OUT",
        "PB_PWR_GOOD",
        "LB_3V3_IO",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "CAN1_TX_DISABLE_CMD",
        "CAN1_TX_DISABLED_STATUS",
    }
    for output in outputs:
        required_nets.update({f"{output}_CTL", f"{output}_FLT", f"{output}_IMON", f"{output}_FUSED"})

    seen_refs = set()
    seen_nets = set()
    for expected_index, row in enumerate(rows, 1):
        row_number = expected_index + 1
        test_point_ref = row["Test point ref"].strip()
        net = row["Net"].strip()
        sheet = row["Sheet"].strip()
        if test_point_ref in seen_refs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate test point ref {test_point_ref}")
        seen_refs.add(test_point_ref)
        if test_point_ref != f"TP{expected_index:03d}":
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: test point refs must be "
                f"contiguous TP###, expected TP{expected_index:03d}"
            )
        if net in seen_nets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate test-point net {net}")
        seen_nets.add(net)
        if sheet not in manifest_sheets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown sheet {sheet}")
        for column in ("Signal class", "Requirement", "Population", "Access intent", "Validation target", "Placement status"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        placement_status = row["Placement status"].lower()
        if "schematic-review only" not in placement_status or "tbd" not in placement_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: placement status must remain schematic-review only/TBD")
        if "final" in placement_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: test point placement must not be final")
        if net == "CAN1_TX_ROUTE":
            fail("CAN1_TX_ROUTE must not receive a test point in Rev.1 default planning")
        if net == "CAN1_RX_ROUTE" and "dnp unless" not in row["Population"].lower():
            fail("CAN1_RX_ROUTE test point row must remain DNP unless CAN1 crosses PB-100")
        if net.endswith("_CTL") or net.endswith("_FLT") or net.endswith("_IMON"):
            if net not in b2b_nets:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: {net} is missing from JPB1 pin map")
        if net.endswith("_FUSED"):
            if "no pcb test pad locked" not in row["Population"].lower():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: fused outputs must avoid locked PCB test pads")
            if "high-current" not in row["Access intent"].lower():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: fused outputs need guarded high-current access intent")

    missing_nets = sorted(required_nets - seen_nets)
    if missing_nets:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required test-point nets: "
            f"{', '.join(missing_nets)}"
        )


def validate_fault_response_matrix() -> None:
    path = PB100_DIR / "PB-100-fault-response-matrix.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 fault response matrix: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in FAULT_RESPONSE_MATRIX_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    seen_fault_ids = set()
    for row_number, row in enumerate(rows, 2):
        fault_id = row["Fault ID"].strip()
        if fault_id in seen_fault_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Fault ID {fault_id}")
        seen_fault_ids.add(fault_id)
        if fault_id not in REQUIRED_FAULT_IDS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Fault ID {fault_id}")
        for column in FAULT_RESPONSE_MATRIX_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if not any(keyword in row_text for keyword in ("disable", "disabled", "off", "derate", "refuse", "block")):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: fault response must include a safe action")
        if "log" not in row["Firmware response"].lower() and fault_id not in {"PBFLT-THERM-HIGH"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: firmware response must include logging")
        if "role" in row_text and "role-agnostic" not in row_text and "role names" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role references must preserve role-agnostic behavior")
        if fault_id == "PBFLT-CAN1-TX":
            if "dnp/open" not in row_text or "future adr" not in row_text:
                fail("CAN1 TX fault response must keep DNP/open and future ADR explicit")
        if fault_id == "PBFLT-OUT2-INRUSH" and "soa" not in row_text:
            fail("OUT2 inrush fault response must reference SOA")
        if fault_id == "PBFLT-B2B-MISMATCH" and "accessory role assumptions" not in row_text:
            fail("B2B mismatch fault response must reject accessory role assumptions")
        validation_artifacts = [artifact.strip() for artifact in row["Validation artifact"].split(";")]
        for artifact in validation_artifacts:
            if not (
                artifact.startswith("PB-100-")
                or artifact.startswith("docs/")
                or artifact.startswith("production/")
            ):
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: validation artifact "
                    f"must be PB-100*, docs/*, or production/*: {artifact}"
                )

    missing_fault_ids = sorted(REQUIRED_FAULT_IDS - seen_fault_ids)
    if missing_fault_ids:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing fault IDs: "
            f"{', '.join(missing_fault_ids)}"
        )


def resolve_review_artifact(path_text: str) -> Path:
    if path_text.startswith("docs/") or path_text.startswith("production/") or path_text.startswith("hardware/"):
        return REPO_ROOT / path_text
    return PB100_DIR / path_text


def expand_reference_token(token: str) -> set[str]:
    token = token.strip()
    if not token:
        return set()
    if ".." not in token:
        return {token}
    start, end = [part.strip() for part in token.split("..", 1)]
    start_prefix = "".join(character for character in start if not character.isdigit())
    end_prefix = "".join(character for character in end if not character.isdigit())
    if start_prefix != end_prefix:
        return {token}
    start_digits = "".join(character for character in start if character.isdigit())
    end_digits = "".join(character for character in end if character.isdigit())
    if not start_digits or not end_digits:
        return {token}
    width = max(len(start_digits), len(end_digits))
    return {
        f"{start_prefix}{number:0{width}d}"
        for number in range(int(start_digits), int(end_digits) + 1)
    }


def refs_from_cell(cell: str) -> set[str]:
    references = set()
    for token in cell.split(";"):
        references.update(expand_reference_token(token))
    return references


def validate_schematic_capture_work_queue() -> None:
    path = PB100_DIR / "PB-100-schematic-capture-work-queue.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty schematic capture work queue: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SCHEMATIC_CAPTURE_WORK_QUEUE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    manifest_rows = list(csv.DictReader((PB100_DIR / "PB-100-kicad-sheet-manifest.csv").open(newline="", encoding="utf-8")))
    manifest_sheets = {row["Sheet file"].strip() for row in manifest_rows}
    allowed_sheets = manifest_sheets | {"cross-sheet-review"}
    sheet_reference_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-sheet-reference-map.csv").open(newline="", encoding="utf-8"))
    )
    refs_by_sheet: dict[str, set[str]] = {}
    for sheet_row in sheet_reference_rows:
        sheet_file = sheet_row["Sheet file"].strip()
        ref = sheet_row["Ref"].strip()
        if ref == "TP1..TPn":
            continue
        refs_by_sheet.setdefault(sheet_file, set()).add(ref)

    seen_work_items = set()
    sheets_with_queue_rows = set()
    refs_covered_by_sheet: dict[str, set[str]] = {}
    for row_number, row in enumerate(rows, 2):
        work_item = row["Work item"].strip()
        sheet_file = row["Sheet file"].strip()
        if work_item in seen_work_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Work item {work_item}")
        seen_work_items.add(work_item)
        if work_item not in REQUIRED_CAPTURE_WORK_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Work item {work_item}")
        if sheet_file not in allowed_sheets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown sheet file {sheet_file}")
        sheets_with_queue_rows.add(sheet_file)
        if sheet_file in manifest_sheets:
            sheet_path = KICAD_DIR / sheet_file if sheet_file == "PB-100.kicad_sch" else KICAD_DIR / "sheets" / sheet_file
            sheet_text = read_text(sheet_path)
            if f"Work queue: {work_item}" not in sheet_text:
                fail(
                    f"{sheet_path.relative_to(REPO_ROOT)} must contain Work queue marker "
                    f"for {work_item}"
                )
        if row["Capture status"].strip() not in ALLOWED_CAPTURE_STATUSES:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Capture status {row['Capture status'].strip()}")
        for column in (
            "Capture scope",
            "Required refs",
            "Primary source artifacts",
            "Blocker",
            "Freeze close evidence",
            "Layout boundary",
        ):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        layout_boundary = row["Layout boundary"].lower()
        if "no " not in layout_boundary or "layout" not in layout_boundary:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: layout boundary must explicitly block layout")
        if "manufacturing output" in layout_boundary and "no " not in layout_boundary:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: manufacturing output must be blocked")
        for artifact in [part.strip() for part in row["Primary source artifacts"].split(";")]:
            artifact_path = resolve_review_artifact(artifact)
            if not artifact_path.exists():
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: missing source artifact "
                    f"{artifact}"
                )
        row_refs = refs_from_cell(row["Required refs"])
        refs_covered_by_sheet.setdefault(sheet_file, set()).update(row_refs)
        if "Q1" in row_refs:
            row_text = " ".join(row.values())
            if not all(token in row_text for token in ("INPUT_REVERSE_FET", "BUK7S1R2-80M", "LFPAK88", "40 A")):
                fail("Q1 capture work must keep selected 80 V LFPAK88 and 40 A review explicit")
        if work_item == "CAP-CAN1":
            row_text = " ".join(row.values()).lower()
            if "dnp/open" not in row_text or "future adr" not in row_text:
                fail("CAN1 capture work must keep DNP/open and future ADR explicit")
        if work_item == "CAP-TOP":
            row_text = " ".join(row.values()).lower()
            if "linked" not in row["Capture status"].lower():
                fail("top-level capture work must mark child sheet links complete")
            if "child sheets linked" not in row_text or "erc/netlist" not in row_text:
                fail("top-level capture work must keep child-link and ERC/netlist evidence")
        if work_item == "CAP-TP" and "footprint" not in row["Blocker"].lower():
            fail("test point capture work must keep footprint/placement blocker explicit")

    rows_by_work_item = {row["Work item"].strip(): row for row in rows}
    for work_item, tokens in CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM.items():
        work_row = rows_by_work_item[work_item]
        source_artifacts = work_row["Primary source artifacts"]
        for token in tokens:
            if token not in source_artifacts:
                fail(f"capture work queue {work_item} must include source artifact {token}")
        sheet_file = work_row["Sheet file"].strip()
        if sheet_file in manifest_sheets:
            sheet_path = KICAD_DIR / sheet_file if sheet_file == "PB-100.kicad_sch" else KICAD_DIR / "sheets" / sheet_file
            sheet_text = read_text(sheet_path)
            for token in tokens:
                if token not in sheet_text:
                    fail(f"{sheet_path.relative_to(REPO_ROOT)} must mention source artifact {token}")

    missing_work_items = sorted(REQUIRED_CAPTURE_WORK_ITEMS - seen_work_items)
    if missing_work_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing capture work items: "
            f"{', '.join(missing_work_items)}"
        )
    missing_sheets = sorted(manifest_sheets - sheets_with_queue_rows)
    if missing_sheets:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing KiCad sheet work rows: "
            f"{', '.join(missing_sheets)}"
        )
    for sheet_file, expected_refs in refs_by_sheet.items():
        missing_refs = sorted(expected_refs - refs_covered_by_sheet.get(sheet_file, set()))
        if missing_refs:
            fail(
                f"{path.relative_to(REPO_ROOT)} does not cover refs on {sheet_file}: "
                f"{', '.join(missing_refs)}"
            )


def validate_schematic_capture_plan() -> None:
    path = PB100_DIR / "PB-100-schematic-capture-plan.md"
    text = read_text(path)
    lower_text = text.lower()
    if "does not authorize pcb\nlayout" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must explicitly avoid PCB layout authorization")
    if "do not create `pb-100.kicad_pcb`" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must block PB-100.kicad_pcb creation")

    queue_path = PB100_DIR / "PB-100-schematic-capture-work-queue.csv"
    queue_rows = list(csv.DictReader(queue_path.open(newline="", encoding="utf-8")))
    rows_by_work_item = {row["Work item"].strip(): row for row in queue_rows}
    plan_lines = text.splitlines()
    for work_item, tokens in CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM.items():
        if work_item not in rows_by_work_item:
            fail(f"{queue_path.relative_to(REPO_ROOT)} is missing capture work item {work_item}")
        sheet_file = rows_by_work_item[work_item]["Sheet file"].strip()
        sheet_lines = [line for line in plan_lines if f"`{sheet_file}`" in line]
        if not sheet_lines:
            fail(f"{path.relative_to(REPO_ROOT)} must include capture row for {sheet_file}")
        sheet_text = " ".join(sheet_lines)
        for token in tokens:
            if token not in sheet_text:
                fail(f"{path.relative_to(REPO_ROOT)} {sheet_file} row must include {token}")


def validate_review_release_manifest() -> None:
    path = PB100_DIR / "PB-100-review-release-manifest.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 review release manifest: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in REVIEW_RELEASE_MANIFEST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    allowed_statuses = {"Frozen", "Ready", "Closed", "Conditional", "Open"}
    seen_artifacts = set()
    for row_number, row in enumerate(rows, 2):
        artifact = row["Artifact"].strip()
        if artifact in seen_artifacts:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate artifact {artifact}")
        seen_artifacts.add(artifact)
        for column in REVIEW_RELEASE_MANIFEST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Required for freeze"].strip() != "Required":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: release manifest artifacts must be Required")
        if row["Status"].strip() not in allowed_statuses:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Status {row['Status'].strip()}")
        artifact_path = REPO_ROOT / artifact
        if not artifact_path.exists():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing release artifact {artifact}")
        if artifact_path.is_file():
            name = artifact_path.name.lower()
            suffix = artifact_path.suffix.lower()
            if name.endswith(".kicad_pcb-bak") or suffix in DISALLOWED_LAYOUT_SUFFIXES:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: release manifest must not include layout artifact {artifact}")
        hook = row["Validation hook"].strip()
        if hook.startswith("validate_") and hook not in VALIDATION_HOOK_NAMES:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown validation hook {hook}")

    missing_artifacts = sorted(REQUIRED_RELEASE_MANIFEST_ARTIFACTS - seen_artifacts)
    if missing_artifacts:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing release artifacts: "
            f"{', '.join(missing_artifacts)}"
        )


def validate_schematic_readiness_review() -> None:
    path = PB100_DIR / "PB-100-schematic-readiness-review.md"
    text = read_text(path)
    lower_text = text.lower()
    if "does not authorize pcb layout" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must explicitly avoid PCB layout authorization")
    for artifact in sorted(REQUIRED_RELEASE_MANIFEST_ARTIFACTS):
        if artifact not in text:
            fail(f"{path.relative_to(REPO_ROOT)} review packet must include {artifact}")
    for tokens in CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM.values():
        for token in tokens:
            if token not in text:
                fail(f"{path.relative_to(REPO_ROOT)} review packet must include trace artifact {token}")


def validate_schematic_package() -> None:
    path = PB100_DIR / "PB-100-schematic-package.md"
    text = read_text(path)
    lower_text = text.lower()
    if "not a pcb layout package" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must explicitly avoid PCB layout scope")
    for artifact in sorted(REQUIRED_RELEASE_MANIFEST_ARTIFACTS):
        if artifact == "hardware/power-board/PB-100/PB-100-schematic-package.md":
            continue
        if artifact not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include release artifact {artifact}")


def validate_test_plan_traceability() -> None:
    path = REPO_ROOT / "docs" / "testing" / "test-plan.md"
    text = read_text(path)
    required_trace_artifacts = (
        "ADR-0013-pb-100-prelayout-vs-postprototype-validation.md",
        "PB-100-post-prototype-validation-gate.csv",
        "PB-100-logic-power-rail-trace.csv",
        "PB-100-logic-power-freeze-review.csv",
        "PB-100-high-medium-output-baseline-trace.csv",
        "PB-100-high-medium-output-freeze-review.csv",
        "PB-100-low-current-output-baseline-trace.csv",
        "PB-100-low-current-output-freeze-review.csv",
        "PB-100-output-stage-value-freeze-checklist.csv",
        "PB-100-output-stage-value-derivation-precheck.csv",
        "PB-100-output-stage-closeout-precheck.csv",
        "PB-100-can1-tx-disable-trace.csv",
        "PB-100-can1-production-dnp-review.csv",
        "PB-100-can1-default-disable-freeze-checklist.csv",
        "PB-100-can1-default-disable-derivation-precheck.csv",
        "PB-100-can1-reset-bench-checklist.csv",
        "PB-100-input-reverse-package-trace.csv",
        "PB-100-input-reverse-freeze-review.csv",
        "PB-100-input-reverse-q1-freeze-checklist.csv",
        "PB-100-input-reverse-q1-derivation-precheck.csv",
        "PB-100-input-reverse-q1-closeout-precheck.csv",
        "PB-100-tvs-load-dump-margin-trace.csv",
        "PB-100-tvs-load-dump-freeze-review.csv",
        "PB-100-tvs-overshoot-escape-checklist.csv",
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "PB-100-logic-power-rail-trace.csv",
        "PB-100-logic-power-freeze-review.csv",
        "PB-100-logic-power-value-freeze-checklist.csv",
        "PB-100-logic-power-value-derivation-precheck.csv",
        "PB-100-logic-power-closeout-precheck.csv",
        "PB-100-current-telemetry-trace.csv",
        "PB-100-current-telemetry-freeze-review.csv",
        "PB-100-current-telemetry-value-freeze-checklist.csv",
        "PB-100-current-telemetry-value-derivation-precheck.csv",
        "PB-100-current-telemetry-closeout-precheck.csv",
        "PB-100-board-current-budget-trace.csv",
        "PB-100-board-current-budget-freeze-review.csv",
        "PB-100-board-current-budget-design-calculation.md",
        "PB-100-board-current-budget-value-freeze-checklist.csv",
        "PB-100-board-current-budget-value-derivation-precheck.csv",
        "PB-100-thermal-telemetry-trace.csv",
        "PB-100-thermal-telemetry-freeze-review.csv",
        "PB-100-thermal-telemetry-value-freeze-checklist.csv",
        "PB-100-thermal-telemetry-value-derivation-precheck.csv",
        "PB-100-thermal-telemetry-closeout-precheck.csv",
        "PB-100-b2b-interface-trace.csv",
        "PB-100-b2b-lb100-resource-binding.csv",
        "PB-100-b2b-lb100-pin-audit-checklist.csv",
        "PB-100-b2b-interface-freeze-checklist.csv",
        "PB-100-b2b-interface-closeout-precheck.csv",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-factory-assembly-freeze-checklist.csv",
        "PB-100-factory-assembly-sourcing-precheck.csv",
        "PB-100-factory-assembly-closeout-precheck.csv",
        "PB-100-garage-install-freeze-checklist.csv",
        "PB-100-garage-install-sourcing-precheck.csv",
        "PB-100-garage-install-closeout-precheck.csv",
    )
    for token in required_trace_artifacts:
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include trace artifact {token}")
    for bench_id in (f"PB-BENCH-{index:03d}" for index in range(1, 16)):
        if bench_id not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include bench test {bench_id}")
    lower_text = text.lower()
    if "do not run first-power" not in lower_text or "motorcycle" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must keep motorcycle first-power safety boundary")
    if "can1 listen-only" not in lower_text or "no vehicle-can transmit frame" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must keep CAN1 listen-only bench test")


def validate_post_prototype_validation_gate() -> None:
    path = PB100_DIR / "PB-100-post-prototype-validation-gate.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty post-prototype validation gate: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in POST_PROTOTYPE_VALIDATION_GATE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_bench_ids = {f"PB-BENCH-{index:03d}" for index in range(1, 16)}
    seen_bench_ids = set()
    for row_number, row in enumerate(rows, 2):
        bench_id = row["Bench ID"].strip()
        if bench_id in seen_bench_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Bench ID {bench_id}")
        seen_bench_ids.add(bench_id)
        if bench_id not in expected_bench_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Bench ID {bench_id}")
        for column in POST_PROTOTYPE_VALIDATION_GATE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        requires_board = row["Requires assembled board"].strip()
        if requires_board not in {"Yes", "Board optional"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid assembled-board requirement")
        if row["Status"].strip() != "Deferred post-prototype":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: post-prototype status must remain deferred")
        blocks = row["Blocks until complete"].lower()
        if "first motorcycle power" not in blocks or "production release" not in blocks:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: post-prototype gate must block motorcycle power and production release")
        pre_layout_artifact = row["Pre-layout artifact"].strip()
        if pre_layout_artifact.startswith("docs/"):
            artifact_path = REPO_ROOT / pre_layout_artifact
        else:
            artifact_path = PB100_DIR / pre_layout_artifact
        if not artifact_path.exists():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: missing pre-layout artifact "
                f"{pre_layout_artifact}"
            )

    missing_bench_ids = sorted(expected_bench_ids - seen_bench_ids)
    if missing_bench_ids:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing post-prototype bench IDs: "
            f"{', '.join(missing_bench_ids)}"
        )


def validate_net_naming_contract() -> None:
    path = PB100_DIR / "PB-100-net-naming.md"
    text = read_text(path)
    warning = (
        "Do not use names such as `FOG_LEFT`, `SEAT`, `USB`, `CHIGEE`, `DVR`, or\n"
        "`BRAKE` in PB-100 schematic nets."
    )
    text_without_warning = text.replace(warning, "")
    for forbidden_token in ("FOG", "SEAT", "USB", "CHIGEE", "DVR", "BRAKE"):
        if forbidden_token in text_without_warning:
            fail(f"role token appears outside net-naming warning: {forbidden_token}")
    if "CAN1_TX_ROUTE` | DNP/open" not in text:
        fail("CAN1_TX_ROUTE must remain DNP/open by default in net naming contract")
