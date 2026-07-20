from __future__ import annotations

from .common import (
    CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECK_COLUMNS,
    CAN1_DEFAULT_DISABLE_DERIVATION_PRECHECK_COLUMNS,
    CAN1_DEFAULT_DISABLE_FREEZE_CHECKLIST_COLUMNS,
    CAN1_PRODUCTION_DNP_REVIEW_COLUMNS,
    CAN1_RESET_BENCH_CHECKLIST_COLUMNS,
    CAN1_SAFETY_VERIFICATION_COLUMNS,
    CAN1_TX_DISABLE_TRACE_COLUMNS,
    KICAD_DIR,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECKS,
    REQUIRED_CAN1_DEFAULT_DISABLE_DERIVATION_CHECKS,
    REQUIRED_CAN1_DEFAULT_DISABLE_FREEZE_CHECKS,
    REQUIRED_CAN1_PRODUCTION_DNP_REVIEW_ITEMS,
    REQUIRED_CAN1_RESET_BENCH_CHECKS,
    REQUIRED_CAN1_SAFETY_REQUIREMENTS,
    csv,
    fail,
    json,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def validate_can1_tx_disable_trace() -> None:
    path = PB100_DIR / "PB-100-can1-tx-disable-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 TX-disable trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CAN1_TX_DISABLE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "Policy baseline",
        "TX missing-link",
        "Disable command default",
        "Disabled status readback",
        "RX independence",
        "Firmware listen-only",
        "Production ownership",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        item = row["Trace item"].strip()
        if item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate trace item {item}")
        if item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown trace item {item}")
        rows_by_item[item] = row
        for column in CAN1_TX_DISABLE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "schematic freeze" not in " ".join(row.values()).lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 trace items: "
            f"{', '.join(missing_items)}"
        )

    trace_text = read_text(path)
    for token in (
        "ADR-0002",
        "Architecture v1.0",
        "configuration cannot enable TX",
        "future ADR",
        "explicit hardware action",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "DNP/open",
        "no default-populated TX",
        "CAN1_TX_DISABLE_CMD",
        "U_CAN1",
        "hardware pull",
        "LB-100 is reset unpowered or absent",
        "CAN1_TX_DISABLED_STATUS",
        "physical disabled state",
        "not firmware-only",
        "CAN1_RX_ROUTE",
        "listen-only RX",
        "firmware/services/can_safety.c",
        "CAN1 TX denied",
        "CAN2 expansion TX remains separate",
        "CAN1_TX_DISABLE",
        "Default DNP/open",
        "JLCPCB PCBWay",
    ):
        if token not in trace_text:
            fail(f"CAN1 TX-disable trace must include {token}")

    safety_rows = list(csv.DictReader((PB100_DIR / "PB-100-can1-safety-verification.csv").open(newline="", encoding="utf-8")))
    safety_by_requirement = {row["Requirement"].strip(): row for row in safety_rows}
    for requirement in REQUIRED_CAN1_SAFETY_REQUIREMENTS:
        if requirement not in safety_by_requirement:
            fail(f"CAN1 safety matrix must include {requirement}")
    tx_path_text = " ".join(safety_by_requirement["TX physical path"].values()).lower()
    for token in ("can1_tx_route", "dnp/open", "no default-populated tx", "future-adr"):
        if token not in tx_path_text:
            fail(f"CAN1 TX physical path safety row must include {token}")
    status_text = " ".join(safety_by_requirement["Disabled status"].values()).lower()
    if "physical disabled state" not in status_text or "not firmware-only" not in status_text:
        fail("CAN1 disabled-status safety row must require physical non-firmware-only readback")
    firmware_row_text = " ".join(safety_by_requirement["Firmware safety"].values()).lower()
    if "listen-only" not in firmware_row_text or "blocks tx" not in firmware_row_text:
        fail("CAN1 firmware safety row must keep listen-only TX block explicit")

    net_domain_rows = list(csv.DictReader((PB100_DIR / "PB-100-schematic-net-domain-plan.csv").open(newline="", encoding="utf-8")))
    net_domain_by_pattern = {row["Net pattern"].strip(): row for row in net_domain_rows}
    expected_net_defaults = {
        "CAN1_TX_DISABLE_CMD": "Disable asserted by hardware pull",
        "CAN1_TX_DISABLED_STATUS": "Asserted when disabled",
        "CAN1_RX_ROUTE": "DNP unless CAN1 crosses PB-100",
        "CAN1_TX_ROUTE": "DNP/open by default",
    }
    for net_pattern, expected_default in expected_net_defaults.items():
        row = net_domain_by_pattern.get(net_pattern)
        if row is None:
            fail(f"CAN1 net-domain plan must include {net_pattern}")
        if row["Default state"].strip() != expected_default:
            fail(f"CAN1 net-domain default for {net_pattern} must remain {expected_default}")

    b2b_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    b2b_nets = {row["Net"].strip() for row in b2b_rows}
    for net in expected_net_defaults:
        if net not in b2b_nets:
            fail(f"CAN1 signal {net} must remain visible in JPB1 pin map")

    capabilities = json.loads(read_text(REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"))
    can1 = capabilities["safety"]["can1"]
    if can1["vehicle_can_read_only_default"] is not True:
        fail("PB-100 capability manifest must keep CAN1 vehicle_can_read_only_default true")
    if can1["tx_route_population"] != "DNP/open":
        fail("PB-100 capability manifest must keep CAN1 tx_route_population DNP/open")
    if can1["tx_requires_future_adr"] is not True:
        fail("PB-100 capability manifest must keep CAN1 tx_requires_future_adr true")
    if can1["hardware_action_required_for_tx"] is not True:
        fail("PB-100 capability manifest must keep CAN1 hardware_action_required_for_tx true")
    if can1["disabled_status_signal"] != "CAN1_TX_DISABLED_STATUS":
        fail("PB-100 capability manifest must keep CAN1 disabled status signal")

    firmware_text = read_text(REPO_ROOT / "firmware" / "services" / "can_safety.c")
    for token in ("SVC_CAN_TX_DENY", "SVC_CAN_PORT_CAN2_EXPANSION", "SVC_CAN_TX_ALLOW"):
        if token not in firmware_text:
            fail(f"CAN safety firmware must include {token}")
    firmware_tests = read_text(REPO_ROOT / "firmware" / "tests" / "test_can_safety.c")
    for token in (
        "test_can1_tx_is_denied_when_disabled_status_true",
        "test_can1_tx_is_denied_when_disabled_status_false",
        "test_can2_tx_is_allowed_for_expansion",
    ):
        if token not in firmware_tests:
            fail(f"CAN safety tests must include {token}")

    checked_texts = {
        "CAN1 TX-disable input": read_text(PB100_DIR / "PB-100-can1-tx-disable.md"),
        "CAN safety doc": read_text(REPO_ROOT / "docs" / "can" / "can-safety.md"),
        "BOM map": read_text(REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv"),
        "Factory BOM": read_text(REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv"),
        "Assembly recheck": read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv"),
        "Sourcing evidence": read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv"),
        "Assembly readiness": read_text(PB100_DIR / "PB-100-assembly-readiness-trace.csv"),
        "Test plan": read_text(REPO_ROOT / "docs" / "testing" / "test-plan.md"),
    }
    for label, text in checked_texts.items():
        lower_text = text.lower()
        if "can1" not in lower_text:
            fail(f"{label} must retain CAN1 safety content")
        if label in {"BOM map", "Factory BOM", "Assembly recheck", "Sourcing evidence", "Assembly readiness"}:
            for token in ("dnp/open", "no default-populated"):
                if token not in lower_text:
                    fail(f"{label} must retain CAN1 {token} production boundary")


def validate_can1_safety_verification() -> None:
    path = PB100_DIR / "PB-100-can1-safety-verification.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 safety verification matrix: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CAN1_SAFETY_VERIFICATION_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_requirement: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        requirement = row["Requirement"].strip()
        if requirement not in REQUIRED_CAN1_SAFETY_REQUIREMENTS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 requirement {requirement}")
        if requirement in rows_by_requirement:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 requirement {requirement}")
        rows_by_requirement[requirement] = row
        for column in CAN1_SAFETY_VERIFICATION_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "enabled by default" in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 TX must not be enabled/populated by default")
        if "default-populated tx" in row_text and "no default-populated tx" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 TX must not be default-populated")
        if requirement != "Future TX change process" and "configuration only" in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 TX cannot be changed by configuration only")

    missing_requirements = sorted(REQUIRED_CAN1_SAFETY_REQUIREMENTS - rows_by_requirement.keys())
    if missing_requirements:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 requirements: "
            f"{', '.join(missing_requirements)}"
        )

    tx_row_text = " ".join(rows_by_requirement["TX physical path"].values()).lower()
    if "can1_tx_route" not in tx_row_text or "dnp/open" not in tx_row_text or "future-adr" not in tx_row_text:
        fail("CAN1 TX physical path verification must keep CAN1_TX_ROUTE DNP/open and future-ADR explicit")
    disable_row_text = " ".join(rows_by_requirement["Disable command"].values()).lower()
    if "disable asserted" not in disable_row_text or "reset" not in disable_row_text or "unpowered" not in disable_row_text:
        fail("CAN1 disable command verification must keep reset/unpowered disable explicit")
    status_row_text = " ".join(rows_by_requirement["Disabled status"].values()).lower()
    if "disabled state" not in status_row_text:
        fail("CAN1 disabled-status verification must require physical disabled-state readback")
    bom_row_text = " ".join(rows_by_requirement["DNP BOM ownership"].values()).lower()
    if "dnp/open" not in bom_row_text or "default" not in bom_row_text:
        fail("CAN1 DNP BOM verification must keep default DNP/open explicit")
    future_row_text = " ".join(rows_by_requirement["Future TX change process"].values()).lower()
    if "future adr" not in future_row_text or "hardware action" not in future_row_text:
        fail("CAN1 future TX process must require future ADR and hardware action")


def validate_can1_production_dnp_review() -> None:
    path = PB100_DIR / "PB-100-can1-production-dnp-review.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 production DNP review: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CAN1_PRODUCTION_DNP_REVIEW_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        review_item = row["Review item"].strip()
        if review_item not in REQUIRED_CAN1_PRODUCTION_DNP_REVIEW_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 review item {review_item}")
        if review_item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 review item {review_item}")
        rows_by_item[review_item] = row
        for column in CAN1_PRODUCTION_DNP_REVIEW_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if review_item in {"Physical missing link", "Factory DNP ownership"}:
            if "dnp/open" not in row_text or "no default-populated" not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 DNP rows must keep no-default-populated TX explicit")
        if review_item == "Future change process":
            if "future adr" not in row_text or "hardware action" not in row_text or "configuration" not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 future process must block configuration-only TX enable")

    missing_items = sorted(REQUIRED_CAN1_PRODUCTION_DNP_REVIEW_ITEMS - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 production DNP review items: "
            f"{', '.join(missing_items)}"
        )

    review_text = read_text(path)
    for token in (
        "JP_CAN1",
        "U_CAN1",
        "DNP/open",
        "no default-populated",
        "future ADR",
        "explicit hardware action",
        "physical disabled state",
        "not firmware-only",
        "CAN2 expansion TX remains separate",
        "Configuration alone cannot enable vehicle-CAN TX",
        "Do not enable vehicle-CAN TX through configuration only",
    ):
        if token not in review_text:
            fail(f"CAN1 production DNP review must include {token}")

    tx_row_text = " ".join(rows_by_item["Physical missing link"].values()).lower()
    if "can1_tx_route" not in tx_row_text or "jp_can1" not in tx_row_text:
        fail("CAN1 production DNP review must bind JP_CAN1 to CAN1_TX_ROUTE")
    gate_row_text = " ".join(rows_by_item["Default disabled gate"].values()).lower()
    if "can1_tx_disable_cmd" not in gate_row_text or "u_can1" not in gate_row_text or "reset" not in gate_row_text:
        fail("CAN1 production DNP review must bind U_CAN1 disable default to reset/unpowered state")
    status_row_text = " ".join(rows_by_item["Physical status readback"].values()).lower()
    if "can1_tx_disabled_status" not in status_row_text or "physical disabled state" not in status_row_text:
        fail("CAN1 production DNP review must bind disabled-status readback to physical state")
    rx_row_text = " ".join(rows_by_item["RX independence"].values()).lower()
    if "can1_rx_route" not in rx_row_text or "listen-only rx" not in rx_row_text:
        fail("CAN1 production DNP review must keep RX independent for listen-only RX")

    production_texts = {
        "Factory BOM": read_text(REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv"),
        "Symbol BOM map": read_text(REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv"),
        "Assembly recheck": read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv"),
        "Assembly readiness": read_text(PB100_DIR / "PB-100-assembly-readiness-trace.csv"),
    }
    for label, text in production_texts.items():
        lower_text = text.lower()
        for token in ("can1_tx_disable", "dnp/open", "no default-populated"):
            if token not in lower_text:
                fail(f"{label} must retain CAN1 production DNP token {token}")

    firmware_readme = read_text(REPO_ROOT / "firmware" / "README.md").lower()
    if "can1" not in firmware_readme or "listen-only" not in firmware_readme or "can2" not in firmware_readme:
        fail("firmware README must keep CAN1 listen-only and CAN2 expansion boundary")
    firmware_tests = read_text(REPO_ROOT / "firmware" / "tests" / "test_can_safety.c")
    for token in (
        "test_can1_tx_is_denied_when_disabled_status_true",
        "test_can1_tx_is_denied_when_disabled_status_false",
        "test_can2_tx_is_allowed_for_expansion",
    ):
        if token not in firmware_tests:
            fail(f"CAN1 production DNP review requires firmware test {token}")


def validate_can1_default_disable_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-can1-default-disable-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 default-disable freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CAN1_DEFAULT_DISABLE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_CAN1_DEFAULT_DISABLE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 freeze check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 freeze check {check_id}")
        rows_by_check[check_id] = row
        for column in CAN1_DEFAULT_DISABLE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE rows must keep DNP/open explicit")
        if "configuration" in row_text and "cannot enable tx" not in row_text and "do not use firmware capability configuration" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: configuration must not enable CAN1 TX")

    missing_checks = sorted(REQUIRED_CAN1_DEFAULT_DISABLE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 freeze checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "ADR-0002",
        "read-only by default",
        "future ADR",
        "explicit hardware action",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "0Ω 0603",
        "DNP/open",
        "no default-populated vehicle-CAN TX path",
        "U_CAN1",
        "SN74LVC1G125-Q1",
        "OE high disabled",
        "47k",
        "CAN1_TX_DISABLE_CMD",
        "LB_3V3_IO",
        "TXD recessive",
        "transceiver VIO",
        "CAN1_TX_DISABLED_STATUS",
        "1k",
        "100k",
        "1nF DNP",
        "not firmware-only",
        "physical disabled state",
        "DNP link detect",
        "CAN1_RX_ROUTE",
        "listen-only RX",
        "can_safety",
        "CAN2 expansion TX remains separate",
        "vehicle_can_read_only_default",
        "hardware_action_required_for_tx",
        "PB-BENCH-012",
        "CAN1-RST-001",
        "CAN1-RST-006",
        "no vehicle-CAN transmit frame",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"CAN1 default-disable freeze checklist must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-can1-tx-disable-design-calculation.md")
    for token in ("0 Ω 0603", "SN74LVC1G125-Q1", "47 kΩ", "1 kΩ", "100 kΩ", "1 nF DNP"):
        if token not in design_text:
            fail(f"CAN1 design calculation must support checklist token {token}")

    reset_text = read_text(PB100_DIR / "PB-100-can1-reset-bench-checklist.csv")
    for token in ("PB-BENCH-012", "no vehicle-CAN transmit frame", "not from firmware-only"):
        if token not in reset_text:
            fail(f"CAN1 reset bench checklist must support freeze checklist token {token}")


def validate_can1_default_disable_derivation_precheck() -> None:
    path = PB100_DIR / "PB-100-can1-default-disable-derivation-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 default-disable derivation precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CAN1_DEFAULT_DISABLE_DERIVATION_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        derivation_id = row["Derivation ID"].strip()
        if derivation_id not in REQUIRED_CAN1_DEFAULT_DISABLE_DERIVATION_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 derivation item {derivation_id}")
        if derivation_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 derivation item {derivation_id}")
        rows_by_id[derivation_id] = row
        for column in CAN1_DEFAULT_DISABLE_DERIVATION_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE derivation rows must keep DNP/open explicit")
        if "configuration" in row_text and "cannot enable tx" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 configuration rows must state configuration cannot enable TX")

    missing_items = sorted(REQUIRED_CAN1_DEFAULT_DISABLE_DERIVATION_CHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 derivation items: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "ADR-0002",
        "read-only by default",
        "configuration cannot enable TX",
        "future ADR",
        "explicit hardware action",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "0Ω 0603",
        "0 Ω 0603",
        "DNP/open",
        "no default-populated vehicle-CAN TX path",
        "normally-open solder bridge",
        "U_CAN1",
        "SN74LVC1G125-Q1",
        "OE high disabled",
        "47 kΩ",
        "47k",
        "CAN1_TX_DISABLE_CMD",
        "LB_3V3_IO",
        "TXD recessive",
        "transceiver VIO",
        "CAN1_TX_DISABLED_STATUS",
        "1 kΩ",
        "1k",
        "100 kΩ",
        "100k",
        "1 nF DNP",
        "1nF DNP",
        "not firmware-only",
        "physical disabled state",
        "DNP link detect",
        "CAN1_RX_ROUTE",
        "listen-only RX",
        "can_safety",
        "CAN2 expansion TX remains separate",
        "vehicle_can_read_only_default",
        "tx_route_population DNP/open",
        "tx_requires_future_adr",
        "hardware_action_required_for_tx",
        "PB-BENCH-012",
        "CAN1-RST-001",
        "CAN1-RST-006",
        "no vehicle-CAN transmit frame",
        "factory_bom_draft.csv",
        "pb100_symbol_bom_map.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "JLCPCB/PCBWay",
        "DNP 0R",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "CAN1 TX route layout",
        "jumper footprint",
        "fabrication package",
    ):
        if token not in precheck_text:
            fail(f"CAN1 default-disable derivation precheck must include {token}")

    design_text = read_text(PB100_DIR / "PB-100-can1-tx-disable-design-calculation.md")
    for token in ("0 Ω 0603", "SN74LVC1G125-Q1", "47 kΩ", "1 kΩ", "100 kΩ", "1 nF DNP"):
        if token not in design_text:
            fail(f"CAN1 design calculation must support derivation token {token}")

    reset_text = read_text(PB100_DIR / "PB-100-can1-reset-bench-checklist.csv")
    for token in ("PB-BENCH-012", "no vehicle-CAN transmit frame", "future ADR", "explicit hardware action"):
        if token not in reset_text:
            fail(f"CAN1 reset bench checklist must support derivation token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    for token in ("CAN1_TX_DISABLE", "DNP/open", "no default-populated TX", "future ADR"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support CAN1 derivation token {token}")


def validate_can1_default_disable_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-can1-default-disable-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 default-disable closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE rows must keep DNP/open explicit")
        if "configuration" in row_text and "cannot enable tx" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 configuration rows must state configuration cannot enable TX")
        if precheck_id == "CAN1-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("CAN1 closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_CAN1_DEFAULT_DISABLE_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "ADR-0002",
        "read-only by default",
        "configuration cannot enable TX",
        "future ADR plus explicit hardware action",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "DNP/open",
        "no default-populated vehicle-CAN TX path",
        "0Ω 0603",
        "normally-open solder bridge",
        "U_CAN1",
        "SN74LVC1G125-Q1",
        "OE high disabled",
        "47k",
        "CAN1_TX_DISABLE_CMD",
        "enable command",
        "TXD",
        "recessive",
        "CAN1_TX_DISABLED_STATUS",
        "1k",
        "100k",
        "1nF DNP",
        "firmware-only",
        "DNP link detect",
        "CAN1_RX_ROUTE",
        "CAN2 expansion TX remains separate",
        "can_safety",
        "vehicle_can_read_only_default true",
        "tx_route_population DNP/open",
        "tx_requires_future_adr true",
        "hardware_action_required_for_tx true",
        "PB-BENCH-012",
        "CAN1-RST-001",
        "CAN1-RST-006",
        "CAN1_TX_DISABLE",
        "JLCPCB PCBWay",
        "PB-100-assembly-readiness-trace.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "CAN1 TX route layout",
        "jumper footprint lock",
        "fabrication package",
    ):
        if token not in precheck_text:
            fail(f"CAN1 default-disable closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-can1-default-disable-freeze-checklist.csv": ("CAN1-FRZ-001", "CAN1-FRZ-010"),
        "PB-100-can1-default-disable-derivation-precheck.csv": ("CAN1-DER-001", "CAN1-DER-010"),
        "PB-100-can1-production-dnp-review.csv": ("Physical missing link", "Future change process"),
        "PB-100-can1-reset-bench-checklist.csv": ("CAN1-RST-001", "CAN1-RST-006"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"CAN1 closeout precheck requires {supporting_artifact} token {token}")


def validate_can1_reset_bench_checklist() -> None:
    path = PB100_DIR / "PB-100-can1-reset-bench-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty CAN1 reset bench checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in CAN1_RESET_BENCH_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_CAN1_RESET_BENCH_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown CAN1 reset check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate CAN1 reset check {check_id}")
        rows_by_check[check_id] = row
        for column in CAN1_RESET_BENCH_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE checks must keep DNP/open explicit")
        if "vehicle-can transmit" in row_text and "no vehicle-can transmit" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 checks must prohibit vehicle-CAN transmit frames")
        if check_id == "CAN1-RST-004" and "not from firmware-only" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: disabled status must reject firmware-only evidence")
        if check_id == "CAN1-RST-006" and ("future adr" not in row_text or "explicit hardware action" not in row_text):
            fail("CAN1 future TX checklist row must require future ADR plus explicit hardware action")

    missing_checks = sorted(REQUIRED_CAN1_RESET_BENCH_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing CAN1 reset checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "PB-BENCH-012",
        "CAN1_TX_DISABLE_CMD",
        "CAN1_TX_DISABLED_STATUS",
        "CAN1_TX_ROUTE",
        "JP_CAN1",
        "U_CAN1",
        "DNP/open",
        "47k",
        "1k/100k",
        "no vehicle-CAN transmit frame",
        "future ADR",
        "explicit hardware action",
    ):
        if token not in checklist_text:
            fail(f"CAN1 reset bench checklist must include {token}")


def validate_can1_capture_contract() -> None:
    can1_doc = read_text(PB100_DIR / "PB-100-can1-tx-disable.md").lower()
    for token in (
        "jp_can1",
        "u_can1",
        "dnp/open",
        "no default-populated tx",
        "physical disabled state",
        "configuration cannot enable",
        "future adr",
        "explicit hardware action",
    ):
        if token not in can1_doc:
            fail(f"PB-100 CAN1 TX-disable document must include {token}")

    production_review = read_text(PB100_DIR / "PB-100-can1-production-dnp-review.csv").lower()
    for token in ("jp_can1", "u_can1", "dnp/open", "no default-populated", "firmware-only"):
        if token not in production_review:
            fail(f"CAN1 production DNP review must include {token}")

    reset_checklist = read_text(PB100_DIR / "PB-100-can1-reset-bench-checklist.csv").lower()
    for token in (
        "pb-bench-012",
        "reset",
        "unpowered",
        "dnp/open",
        "physical disabled",
        "no vehicle-can transmit frame",
        "future adr",
        "explicit hardware action",
    ):
        if token not in reset_checklist:
            fail(f"CAN1 reset bench checklist must include {token}")

    can1_sheet = read_text(KICAD_DIR / "sheets" / "can1-safety.kicad_sch").lower()
    for token in (
        "jp_can1",
        "u_can1",
        "dnp/open",
        "no default-populated tx",
        "physical disabled state",
        "pb-100-can1-production-dnp-review.csv",
        "pb-100-can1-reset-bench-checklist.csv",
    ):
        if token not in can1_sheet:
            fail(f"CAN1 safety KiCad sheet capture notes must include {token}")

    if '(lib_id "pb100:pb100_can1_tx_disable_prelim")' in can1_sheet:
        fail("JP_CAN1 and U_CAN1 must not use the generic CAN1_TX_DISABLE preliminary symbol")
    for reference, concrete_symbol in (
        ("JP_CAN1", "PB100:PB100_CAN1_TX_DNP_LINK_PRELIM"),
        ("U_CAN1", "PB100:PB100_SN74LVC1G125_Q1_DBV_PRELIM"),
    ):
        reference_marker = f'(property "reference" "{reference.lower()}"'
        symbol_marker = f'(lib_id "{concrete_symbol.lower()}")'
        reference_index = can1_sheet.find(reference_marker)
        if reference_index < 0:
            fail(f"CAN1 safety sheet is missing reference {reference}")
        symbol_index = can1_sheet.rfind("(lib_id", 0, reference_index)
        if symbol_index < 0 or symbol_marker not in can1_sheet[symbol_index:reference_index]:
            fail(f"{reference} must use concrete symbol {concrete_symbol}")
    if '(property "reference" "jp_can1"' in can1_sheet and "(dnp yes)" not in can1_sheet:
        fail("JP_CAN1 must remain DNP/open in the CAN1 safety sheet")
    if "can1_tx_gate_out" not in can1_sheet:
        fail("CAN1 safety sheet must expose CAN1_TX_GATE_OUT between U_CAN1 and JP_CAN1")

    bom_map = read_text(REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv").lower()
    for token in ("can1_tx_disable", "default dnp/open", "no default-populated"):
        if token not in bom_map:
            fail(f"CAN1 symbol BOM map must include {token}")
