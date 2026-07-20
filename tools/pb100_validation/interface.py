from __future__ import annotations

from .common import (
    B2B_INTERFACE_CLOSEOUT_PRECHECK_COLUMNS,
    B2B_INTERFACE_FREEZE_CHECKLIST_COLUMNS,
    B2B_INTERFACE_TRACE_COLUMNS,
    B2B_LB100_PIN_AUDIT_COLUMNS,
    B2B_RESOURCE_BINDING_COLUMNS,
    KICAD_DIR,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_B2B_INTERFACE_CLOSEOUT_PRECHECKS,
    REQUIRED_B2B_INTERFACE_FREEZE_CHECKS,
    REQUIRED_B2B_LB100_PIN_AUDIT_ITEMS,
    VALIDATION_TRACEABILITY_COLUMNS,
    csv,
    fail,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)
from .release import (
    pbrel_id_by_gate,
)


def validate_b2b_interface_trace() -> None:
    path = PB100_DIR / "PB-100-b2b-interface-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B interface trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_INTERFACE_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_items = {
        "Connector candidate",
        "Power status and grounds",
        "Output control fault and current",
        "Board telemetry and PB bus",
        "CAN1 safety crossing",
        "Expansion and reserve",
    }
    rows_by_item: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        item = row["Trace item"].strip()
        if item in rows_by_item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate trace item {item}")
        if item not in required_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown trace item {item}")
        rows_by_item[item] = row
        for column in B2B_INTERFACE_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "schematic freeze" not in " ".join(row.values()).lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")

    missing_items = sorted(required_items - rows_by_item.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing B2B trace items: "
            f"{', '.join(missing_items)}"
        )

    connector_text = " ".join(rows_by_item["Connector candidate"].values())
    for token in ("FX18-100P-0.8SV10", "FX18-100S-0.8SV20", "No connector placement"):
        if token not in connector_text:
            fail(f"B2B connector trace must include {token}")

    pin_map_path = PB100_DIR / "PB-100-b2b-pin-map.csv"
    validate_csv(pin_map_path)
    pin_rows = list(csv.DictReader(pin_map_path.open(newline="", encoding="utf-8")))
    if len(pin_rows) != 100:
        fail(f"{pin_map_path.relative_to(REPO_ROOT)} must contain exactly 100 JPB1 pins")

    pins = sorted(int(row["Pin"].strip()) for row in pin_rows)
    if pins != list(range(1, 101)):
        fail(f"{pin_map_path.relative_to(REPO_ROOT)} must define contiguous pins 1-100")
    if any(row["Connector"].strip() != "JPB1" for row in pin_rows):
        fail(f"{pin_map_path.relative_to(REPO_ROOT)} must use connector JPB1 for every pin")

    def rows_for_pin_span(start: int, end: int) -> list[dict[str, str]]:
        return [row for row in pin_rows if start <= int(row["Pin"].strip()) <= end]

    def nets_for_pin_span(start: int, end: int) -> set[str]:
        return {row["Net"].strip() for row in rows_for_pin_span(start, end)}

    power_row = rows_by_item["Power status and grounds"]
    if power_row["Pin span"].strip() != "1-19":
        fail("B2B power/status trace must cover JPB1 pins 1-19")
    power_rows = rows_for_pin_span(1, 19)
    if sum(1 for row in power_rows if row["Net"].strip() == "GND") != 10:
        fail("B2B pin map must keep ten GND return pins in pins 1-19")
    if sum(1 for row in power_rows if row["Net"].strip() == "AGND") != 2:
        fail("B2B pin map must keep two AGND return pins in pins 1-19")
    if sum(1 for row in power_rows if row["Net"].strip() == "PB_5V_OUT") != 4:
        fail("B2B pin map must keep four PB_5V_OUT pins in pins 1-19")
    if sum(1 for row in power_rows if row["Net"].strip() == "LB_3V3_IO") != 2:
        fail("B2B pin map must keep two LB_3V3_IO pins in pins 1-19")
    if "PB_PWR_GOOD" not in nets_for_pin_span(1, 19):
        fail("B2B pin map must expose PB_PWR_GOOD in pins 1-19")
    if "PB_PWR_GOOD inactive" not in " ".join(power_row.values()):
        fail("B2B power trace must keep PB_PWR_GOOD inactive-until-valid behavior")

    output_row = rows_by_item["Output control fault and current"]
    if output_row["Pin span"].strip() != "21-50":
        fail("B2B output trace must cover JPB1 pins 21-50")
    output_nets = nets_for_pin_span(21, 50)
    expected_output_nets = {
        f"OUT{output}_{suffix}"
        for output in range(1, 11)
        for suffix in ("CTL", "FLT", "IMON")
    }
    missing_output_nets = sorted(expected_output_nets - output_nets)
    if missing_output_nets:
        fail(f"B2B output trace pin span is missing nets: {', '.join(missing_output_nets)}")
    if "role mapping stays in configuration" not in " ".join(output_row.values()).lower():
        fail("B2B output trace must preserve configuration-owned role mapping")

    telemetry_row = rows_by_item["Board telemetry and PB bus"]
    if telemetry_row["Pin span"].strip() != "51-66":
        fail("B2B telemetry trace must cover JPB1 pins 51-66")
    expected_telemetry_nets = {
        "VBAT_SENSE",
        "IIN_SENSE",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "PB_FAULT",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
        "PB_ID_ADC",
        "ADC_REF",
    }
    missing_telemetry_nets = sorted(expected_telemetry_nets - nets_for_pin_span(51, 66))
    if missing_telemetry_nets:
        fail(f"B2B telemetry trace pin span is missing nets: {', '.join(missing_telemetry_nets)}")
    for token in expected_telemetry_nets:
        if token not in telemetry_row["Signals"]:
            fail(f"B2B telemetry trace must include signal {token}")
    if "calibration stays outside firmware constants" not in " ".join(telemetry_row.values()).lower():
        fail("B2B telemetry trace must keep calibration outside firmware constants")

    can_row = rows_by_item["CAN1 safety crossing"]
    if can_row["Pin span"].strip() != "67-70":
        fail("B2B CAN1 trace must cover JPB1 pins 67-70")
    expected_can_nets = {"CAN1_TX_DISABLE_CMD", "CAN1_TX_DISABLED_STATUS", "CAN1_RX_ROUTE", "CAN1_TX_ROUTE"}
    missing_can_nets = sorted(expected_can_nets - nets_for_pin_span(67, 70))
    if missing_can_nets:
        fail(f"B2B CAN1 trace pin span is missing nets: {', '.join(missing_can_nets)}")
    can_text = " ".join(can_row.values()).lower()
    if "dnp/open" not in can_text or "future adr" not in can_text or "disabled-status" not in can_text:
        fail("B2B CAN1 trace must preserve DNP/open future-ADR disabled-status boundary")

    expansion_row = rows_by_item["Expansion and reserve"]
    if expansion_row["Pin span"].strip() != "71-100":
        fail("B2B expansion trace must cover JPB1 pins 71-100")
    expansion_nets = nets_for_pin_span(71, 100)
    expected_expansion_tokens = {
        "CAN2",
        "LIN",
        "RS485",
        "UART",
        "EXT_ADC",
        "EXT_DIG",
        "EXT_5V_EN",
        "SPARE_01..SPARE_16",
    }
    expansion_text = " ".join(expansion_row.values())
    for token in expected_expansion_tokens:
        if token not in expansion_text:
            fail(f"B2B expansion trace must include {token}")
    expected_spares = {f"SPARE_{index:02d}" for index in range(1, 17)}
    missing_spares = sorted(expected_spares - expansion_nets)
    if missing_spares:
        fail(f"B2B expansion trace pin span is missing reserves: {', '.join(missing_spares)}")


def validate_b2b_connector_candidate() -> None:
    required_tokens = (
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "100",
        "0.8",
    )
    checked_paths = (
        PB100_DIR / "PB-100-symbol-mpn-readiness.csv",
        PB100_DIR / "PB-100-symbol-capture-worklist.csv",
        PB100_DIR / "PB-100-schematic-instance-plan.csv",
        PB100_DIR / "PB-100-kicad-footprint-plan.csv",
        PB100_DIR / "PB-100-schematic-freeze-gap-register.csv",
        PB100_DIR / "PB-100-schematic-package.md",
        KICAD_DIR / "sheets" / "b2b-interface.kicad_sch",
        REPO_ROOT / "production" / "bom" / "factory_bom_draft.csv",
        REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv",
        REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv",
        REPO_ROOT / "docs" / "production" / "component-family-shortlist.md",
    )
    for path in checked_paths:
        text = read_text(path)
        for token in required_tokens:
            if token not in text:
                fail(f"{path.relative_to(REPO_ROOT)} must reference B2B connector candidate token {token}")

    evidence_rows = list(
        csv.DictReader((REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv").open(newline="", encoding="utf-8"))
    )
    b2b_evidence = next((row for row in evidence_rows if row["Symbol key"].strip() == "B2B_CONNECTOR"), None)
    if b2b_evidence is None:
        fail("missing B2B_CONNECTOR sourcing evidence row")
    evidence_text = " ".join(b2b_evidence.values()).lower()
    for token in ("20mm", "500", "open:", "vibration", "assembly"):
        if token not in evidence_text:
            fail(f"B2B_CONNECTOR sourcing evidence must explicitly track {token}")


def validate_b2b_lb100_pin_audit_checklist() -> None:
    path = PB100_DIR / "PB-100-b2b-lb100-pin-audit-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B LB-100 pin audit checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_LB100_PIN_AUDIT_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_audit: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        audit_id = row["Audit ID"].strip()
        if audit_id not in REQUIRED_B2B_LB100_PIN_AUDIT_ITEMS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown B2B audit item {audit_id}")
        if audit_id in rows_by_audit:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate B2B audit item {audit_id}")
        rows_by_audit[audit_id] = row
        for column in B2B_LB100_PIN_AUDIT_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if audit_id == "B2B-AUD-002" and "16 adc" not in row_text:
            fail("B2B ADC audit must require at least 16 ADC-capable inputs or reviewed mux strategy")
        if audit_id == "B2B-AUD-003" and ("default low" not in row_text or "role-specific" not in row_text):
            fail("B2B output audit must keep default-low and role-free boundaries")
        if audit_id == "B2B-AUD-005" and ("can1_tx_route" not in row_text or "dnp/open" not in row_text or "future-adr" not in row_text):
            fail("B2B CAN1 audit must keep CAN1_TX_ROUTE DNP/open and future-ADR gated")
        if audit_id == "B2B-AUD-007" and ("footprint drawing" not in row_text or "stack height" not in row_text):
            fail("B2B FX18 audit must require footprint drawing and stack-height review")
        if audit_id == "B2B-AUD-009" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("B2B no-layout audit must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_B2B_LB100_PIN_AUDIT_ITEMS - rows_by_audit.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing B2B audit items: "
            f"{', '.join(missing_items)}"
        )

    audit_text = read_text(path)
    for token in (
        "STM32H563",
        "LQFP-100",
        "Exact LB-100 pinout",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "vibration",
        "assembly handling",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in audit_text:
            fail(f"B2B LB-100 pin audit checklist must include {token}")


def validate_b2b_interface_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-b2b-interface-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B interface freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_INTERFACE_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_B2B_INTERFACE_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown B2B freeze check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate B2B freeze check {check_id}")
        rows_by_check[check_id] = row
        for column in B2B_INTERFACE_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if check_id == "B2B-FRZ-001" and ("fx18-100p-0.8sv10" not in row_text or "stack" not in row_text):
            fail("B2B connector freeze check must cover FX18 pair and stack evidence")
        if check_id == "B2B-FRZ-003" and ("role-specific" not in row_text or "default-low" not in row_text):
            fail("B2B output freeze check must keep role-free default-low output behavior")
        if check_id == "B2B-FRZ-005" and (
            "can1_tx_route" not in row_text or "dnp/open" not in row_text or "future adr" not in row_text
        ):
            fail("B2B CAN1 freeze check must keep CAN1_TX_ROUTE DNP/open and future ADR gated")
        if check_id == "B2B-FRZ-007" and (
            "stm32h563" not in row_text or "lqfp-100" not in row_text or "exact lb-100" not in row_text
        ):
            fail("B2B MCU freeze check must require exact STM32H563 LQFP-100 LB-100 pinout audit")
        if check_id == "B2B-FRZ-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("B2B freeze checklist must explicitly block PCB layout")

    missing_checks = sorted(REQUIRED_B2B_INTERFACE_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing B2B interface freeze checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "PB_5V_OUT",
        "LB_3V3_IO",
        "OUT1_CTL",
        "OUT10_IMON",
        "IIN_SENSE",
        "TEMP_PWR_A",
        "PB_I2C_SCL",
        "CAN1_TX_DISABLE_CMD",
        "CAN1_TX_DISABLED_STATUS",
        "CAN1_RX_ROUTE",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "future ADR",
        "STM32H563",
        "LQFP-100",
        "PB-100-b2b-lb100-pin-audit-checklist.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
    ):
        if token not in checklist_text:
            fail(f"B2B interface freeze checklist must include {token}")


def validate_b2b_interface_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-b2b-interface-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B interface closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_INTERFACE_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_B2B_INTERFACE_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown B2B closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate B2B closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in B2B_INTERFACE_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        if "can1_tx_route" in row_text and "dnp/open" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1_TX_ROUTE rows must keep DNP/open explicit")
        if precheck_id == "B2B-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("B2B closeout no-layout row must block PCB layout explicitly")

    missing_items = sorted(REQUIRED_B2B_INTERFACE_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing B2B closeout prechecks: "
            f"{', '.join(missing_items)}"
        )

    precheck_text = read_text(path)
    for token in (
        "JPB1",
        "100-position",
        "0.8 mm",
        "PB-100-b2b-pin-map.csv",
        "100 JPB1 pins",
        "PB-100-b2b-lb100-resource-binding.csv",
        "PB-100-b2b-lb100-pin-binding-precheck.md",
        "PB-100-b2b-lb100-pin-audit-checklist.csv",
        "PB-100-b2b-interface-freeze-checklist.csv",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "20 mm",
        "footprint drawing",
        "courtyard",
        "pin-1",
        "stack height",
        "vibration retention",
        "assembly handling",
        "tray",
        "JLCPCB PCBWay",
        "STM32H563",
        "LQFP-100",
        "Exact LB-100 pinout",
        "16 ADC",
        "external ADC/mux",
        "10 GPIO/PWM",
        "default-low",
        "PB_PWR_GOOD",
        "PB_WAKE_REQ",
        "OUT1_CTL",
        "OUT10_IMON",
        "IIN_SENSE",
        "TEMP_PWR_A",
        "PB_I2C_SCL",
        "PB_I2C_SDA",
        "PB_I2C_INT",
        "CAN1_TX_DISABLE_CMD",
        "CAN1_TX_DISABLED_STATUS",
        "CAN1_RX_ROUTE",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "future ADR",
        "CAN2",
        "LIN",
        "RS485",
        "UART",
        "EXT_ADC",
        "architecture review",
        "PB_5V_OUT",
        "LB_3V3_IO",
        "PB_PWR_GOOD",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "connector placement",
        "board outline",
        "stack-height lock",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"B2B interface closeout precheck must include {token}")

    pin_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    if len(pin_rows) != 100:
        fail("B2B closeout precheck requires PB-100-b2b-pin-map.csv to contain 100 JPB1 pins")

    audit_text = read_text(PB100_DIR / "PB-100-b2b-lb100-pin-audit-checklist.csv")
    for token in ("STM32H563", "LQFP-100", "16 ADC", "FX18-100P-0.8SV10", "FX18-100S-0.8SV20"):
        if token not in audit_text:
            fail(f"B2B pin audit checklist must support closeout precheck token {token}")


def parse_pin_span_set(value: str) -> set[str]:
    pins: set[str] = set()
    for part in value.split(";"):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = [piece.strip() for piece in token.split("-", 1)]
            start = int(start_text)
            end = int(end_text)
            pins.update(str(pin) for pin in range(start, end + 1))
        else:
            pins.add(token)
    return pins


def validate_b2b_resource_binding() -> None:
    path = PB100_DIR / "PB-100-b2b-lb100-resource-binding.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty B2B LB-100 resource binding: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in B2B_RESOURCE_BINDING_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_pins = {
        "Ground and analog return": set(str(pin) for pin in range(1, 13)),
        "Protected 5V supply to LB-100": set(str(pin) for pin in range(13, 17)),
        "LB 3V3 IO reference to PB-100": set(str(pin) for pin in range(17, 19)),
        "Power-good and wake status": set(str(pin) for pin in range(19, 21)),
        "Output control commands": set(str(pin) for pin in range(21, 31)),
        "Output fault inputs": set(str(pin) for pin in range(31, 41)),
        "Per-output current telemetry": set(str(pin) for pin in range(41, 51)),
        "Board analog telemetry and identity": {"51", "52", "53", "54", "55", "60", "66"},
        "Board fault summary": {"56"},
        "PB-side monitor bus and interrupt": set(str(pin) for pin in range(57, 60)),
        "Future SPI monitor bus": set(str(pin) for pin in range(61, 66)),
        "CAN1 safety crossing": set(str(pin) for pin in range(67, 71)),
        "CAN2 expansion route": set(str(pin) for pin in range(71, 73)),
        "LIN RS485 and UART expansion": set(str(pin) for pin in range(73, 80)),
        "External ADC digital and 5V enable": set(str(pin) for pin in range(80, 85)),
        "Spare reserve pins": set(str(pin) for pin in range(85, 101)),
    }
    required_tokens = {
        "Output control commands": ("OUT1_CTL..OUT10_CTL", "GPIO/PWM"),
        "Output fault inputs": ("OUT1_FLT..OUT10_FLT", "GPIO input"),
        "Per-output current telemetry": ("OUT1_IMON..OUT10_IMON", "ADC"),
        "Board analog telemetry and identity": ("VBAT_SENSE", "IIN_SENSE", "TEMP_PCB", "PB_ID_ADC", "ADC"),
        "Board fault summary": ("PB_FAULT", "GPIO input"),
        "PB-side monitor bus and interrupt": ("PB_I2C_SCL", "PB_I2C_SDA", "I2C", "interrupt"),
        "CAN1 safety crossing": ("CAN1_TX_ROUTE", "DNP/open", "FDCAN", "future-ADR"),
        "CAN2 expansion route": ("CAN2_RX_ROUTE", "CAN2_TX_ROUTE", "FDCAN"),
        "LIN RS485 and UART expansion": ("LIN_TX", "RS485_DE", "UART"),
        "Spare reserve pins": ("SPARE_01..SPARE_16", "reserve"),
    }

    pin_map_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    pin_map_pins = {row["Pin"].strip() for row in pin_map_rows}
    seen_items = set()
    covered_pins: set[str] = set()
    for row_number, row in enumerate(rows, 2):
        item = row["Binding item"].strip()
        if item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate binding item {item}")
        seen_items.add(item)
        if item not in expected_pins:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown binding item {item}")
        for column in B2B_RESOURCE_BINDING_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_pins = parse_pin_span_set(row["JPB1 pins"])
        if row_pins != expected_pins[item]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unexpected pin set for {item}")
        covered_pins.update(row_pins)
        row_text = " ".join(row.values())
        if "No exact STM32H5" not in row_text and "No MCU pin assignment" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: must avoid exact STM32H5 pin assignment")
        for token in required_tokens.get(item, ()):
            if token not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing token {token}")

    missing_items = sorted(set(expected_pins) - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing binding items: "
            f"{', '.join(missing_items)}"
        )
    if covered_pins != pin_map_pins:
        missing_pins = sorted(pin_map_pins - covered_pins, key=int)
        extra_pins = sorted(covered_pins - pin_map_pins, key=int)
        fail(
            "B2B LB-100 resource binding pin coverage mismatch: "
            f"missing={missing_pins}, extra={extra_pins}"
        )


def validate_validation_traceability() -> None:
    path = PB100_DIR / "PB-100-validation-traceability.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 validation traceability register: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in VALIDATION_TRACEABILITY_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    tracked_gates = set(pbrel_id_by_gate())
    seen_test_ids = set()
    gates_with_tests: dict[str, list[dict[str, str]]] = {gate: [] for gate in tracked_gates}
    allowed_phases = {"Schematic review", "Schematic plus bench", "Production review"}
    for row_number, row in enumerate(rows, 2):
        test_id = row["Test ID"].strip()
        freeze_gate = row["Freeze gate"].strip()
        if test_id in seen_test_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Test ID {test_id}")
        seen_test_ids.add(test_id)
        if not test_id.startswith("PBVAL-"):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Test ID must start with PBVAL-")
        if freeze_gate not in tracked_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown freeze gate {freeze_gate}")
        if row["Validation phase"].strip() not in allowed_phases:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Validation phase {row['Validation phase'].strip()}")
        for column in VALIDATION_TRACEABILITY_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        row_text = " ".join(row.values()).lower()
        if "before layout" in row_text and "schematic freeze" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: layout boundary must reference schematic freeze")
        if freeze_gate == "CAN1 safety policy":
            if "dnp/open" not in row_text or "read-only" not in row_text or "future adr" not in row_text:
                fail("CAN1 validation trace must keep DNP/open read-only and future ADR explicit")
            if "pb-100-can1-production-dnp-review.csv" not in row_text:
                fail("CAN1 validation trace must include production DNP review")
            if "pb-100-can1-default-disable-freeze-checklist.csv" not in row_text:
                fail("CAN1 validation trace must include default-disable freeze checklist")
            if "pb-100-can1-default-disable-derivation-precheck.csv" not in row_text:
                fail("CAN1 validation trace must include default-disable derivation precheck")
            if "pb-100-can1-default-disable-closeout-precheck.csv" not in row_text:
                fail("CAN1 validation trace must include default-disable closeout precheck")
        if freeze_gate == "Board current budget":
            if "pb-100-board-current-budget-freeze-review.csv" not in row_text:
                fail("Board current validation trace must include 40 A freeze review")
            if "pb-100-board-current-budget-design-calculation.md" not in row_text:
                fail("Board current validation trace must include design calculation")
            if "pb-100-board-current-budget-value-freeze-checklist.csv" not in row_text:
                fail("Board current validation trace must include value freeze checklist")
            if "pb-100-board-current-budget-value-derivation-precheck.csv" not in row_text:
                fail("Board current validation trace must include value derivation precheck")
            if "pb-100-board-current-budget-closeout-precheck.csv" not in row_text:
                fail("Board current validation trace must include closeout precheck")
        if freeze_gate == "Current telemetry":
            if "pb-100-current-telemetry-freeze-review.csv" not in row_text:
                fail("Current telemetry validation trace must include freeze review")
            if "pb-100-current-telemetry-value-freeze-checklist.csv" not in row_text:
                fail("Current telemetry validation trace must include value freeze checklist")
            if "pb-100-current-telemetry-value-derivation-precheck.csv" not in row_text:
                fail("Current telemetry validation trace must include value derivation precheck")
            if "pb-100-current-telemetry-closeout-precheck.csv" not in row_text:
                fail("Current telemetry validation trace must include closeout precheck")
        if freeze_gate == "Thermal telemetry":
            if "pb-100-thermal-telemetry-freeze-review.csv" not in row_text:
                fail("Thermal telemetry validation trace must include freeze review")
            if "pb-100-thermal-telemetry-value-freeze-checklist.csv" not in row_text:
                fail("Thermal telemetry validation trace must include value freeze checklist")
            if "pb-100-thermal-telemetry-value-derivation-precheck.csv" not in row_text:
                fail("Thermal telemetry validation trace must include value derivation precheck")
            if "pb-100-thermal-telemetry-closeout-precheck.csv" not in row_text:
                fail("Thermal telemetry validation trace must include closeout precheck")
        if freeze_gate == "High/medium output stage":
            if "pb-100-high-medium-output-freeze-review.csv" not in row_text:
                fail("High/medium output validation trace must include freeze review")
            if "pb-100-output-stage-value-freeze-checklist.csv" not in row_text:
                fail("High/medium output validation trace must include value freeze checklist")
            if "pb-100-output-stage-value-derivation-precheck.csv" not in row_text:
                fail("High/medium output validation trace must include value derivation precheck")
            if "pb-100-output-stage-closeout-precheck.csv" not in row_text:
                fail("High/medium output validation trace must include closeout precheck")
        if freeze_gate == "Low-current output stage":
            if "pb-100-low-current-output-freeze-review.csv" not in row_text:
                fail("Low-current output validation trace must include freeze review")
            if "pb-100-output-stage-value-freeze-checklist.csv" not in row_text:
                fail("Low-current output validation trace must include value freeze checklist")
            if "pb-100-output-stage-value-derivation-precheck.csv" not in row_text:
                fail("Low-current output validation trace must include value derivation precheck")
            if "pb-100-output-stage-closeout-precheck.csv" not in row_text:
                fail("Low-current output validation trace must include closeout precheck")
        if freeze_gate == "Input reverse protection":
            if "pb-100-input-reverse-freeze-review.csv" not in row_text:
                fail("Input reverse validation trace must include freeze review")
            if "pb-100-input-reverse-q1-freeze-checklist.csv" not in row_text:
                fail("Input reverse validation trace must include Q1 freeze checklist")
            if "pb-100-input-reverse-q1-derivation-precheck.csv" not in row_text:
                fail("Input reverse validation trace must include Q1 derivation precheck")
            if "pb-100-input-reverse-q1-closeout-precheck.csv" not in row_text:
                fail("Input reverse validation trace must include Q1 closeout precheck")
        if freeze_gate == "Input reverse protection":
            if "q1" not in row_text or "40 a" not in row_text:
                fail("Input reverse validation trace must keep Q1 and 40 A explicit")
        if freeze_gate == "TVS/load-dump protection":
            if "pb-100-tvs-load-dump-freeze-review.csv" not in row_text:
                fail("TVS/load-dump validation trace must include freeze review")
            if "pb-100-tvs-overshoot-escape-checklist.csv" not in row_text:
                fail("TVS/load-dump validation trace must include overshoot escape checklist")
            if "pb-100-tvs-overshoot-validation-precheck.csv" not in row_text:
                fail("TVS/load-dump validation trace must include overshoot validation precheck")
            if "selected 80 v" not in row_text or "clamp-loop overshoot" not in row_text:
                fail("TVS/load-dump validation trace must keep selected 80 V clamp-loop overshoot explicit")
        if freeze_gate == "Logic power rails":
            if "pb-100-logic-power-freeze-review.csv" not in row_text:
                fail("Logic power validation trace must include freeze review")
            if "pb-100-logic-power-value-freeze-checklist.csv" not in row_text:
                fail("Logic power validation trace must include value freeze checklist")
            if "pb-100-logic-power-value-derivation-precheck.csv" not in row_text:
                fail("Logic power validation trace must include value derivation precheck")
            if "pb-100-logic-power-closeout-precheck.csv" not in row_text:
                fail("Logic power validation trace must include closeout precheck")
            if "pb_5v_out" not in row_text or "uvlo" not in row_text:
                fail("Logic power validation trace must keep PB_5V_OUT and UVLO explicit")
        if freeze_gate == "Factory assembly readiness":
            if "sourcing recheck" not in row_text:
                fail("Factory assembly validation trace must require sourcing recheck")
            if "pb-100-factory-assembly-freeze-checklist.csv" not in row_text:
                fail("Factory assembly validation trace must include factory assembly freeze checklist")
            if "pb-100-factory-assembly-sourcing-precheck.csv" not in row_text:
                fail("Factory assembly validation trace must include factory assembly sourcing precheck")
            if "pb-100-factory-assembly-closeout-precheck.csv" not in row_text:
                fail("Factory assembly validation trace must include factory assembly closeout precheck")
        if freeze_gate == "Garage assembly readiness":
            if "garage" not in row_text:
                fail("Garage assembly validation trace must keep garage scope explicit")
            if "pb-100-garage-install-freeze-checklist.csv" not in row_text:
                fail("Garage assembly validation trace must include garage install freeze checklist")
            if "pb-100-garage-install-sourcing-precheck.csv" not in row_text:
                fail("Garage assembly validation trace must include garage install sourcing precheck")
            if "pb-100-garage-install-closeout-precheck.csv" not in row_text:
                fail("Garage assembly validation trace must include garage install closeout precheck")
        gates_with_tests[freeze_gate].append(row)

    required_primary_artifacts = {
        "CAN1 safety policy": "PB-100-can1-tx-disable-trace.csv",
        "Board current budget": "PB-100-board-current-budget-trace.csv",
        "Board-to-board interface": "PB-100-b2b-interface-trace.csv",
        "High/medium output stage": "PB-100-high-medium-output-baseline-trace.csv",
        "Low-current output stage": "PB-100-low-current-output-baseline-trace.csv",
        "Input reverse protection": "PB-100-input-reverse-package-trace.csv",
        "TVS/load-dump protection": "PB-100-tvs-load-dump-margin-trace.csv",
        "Logic power rails": "PB-100-logic-power-rail-trace.csv",
        "Current telemetry": "PB-100-current-telemetry-trace.csv",
        "Thermal telemetry": "PB-100-thermal-telemetry-trace.csv",
        "Factory assembly readiness": "PB-100-assembly-readiness-trace.csv",
        "Garage assembly readiness": "PB-100-assembly-readiness-trace.csv",
    }
    for freeze_gate, token in required_primary_artifacts.items():
        if not any(token in row["Primary artifact"] for row in gates_with_tests[freeze_gate]):
            fail(f"validation traceability for {freeze_gate} must include {token}")
    if not any(
        "PB-100-b2b-lb100-resource-binding.csv" in row["Primary artifact"]
        for row in gates_with_tests["Board-to-board interface"]
    ):
        fail("validation traceability for Board-to-board interface must include PB-100-b2b-lb100-resource-binding.csv")
    if not any(
        "PB-100-b2b-lb100-pin-audit-checklist.csv" in row["Primary artifact"]
        for row in gates_with_tests["Board-to-board interface"]
    ):
        fail("validation traceability for Board-to-board interface must include PB-100-b2b-lb100-pin-audit-checklist.csv")
    if not any(
        "PB-100-b2b-interface-freeze-checklist.csv" in row["Primary artifact"]
        for row in gates_with_tests["Board-to-board interface"]
    ):
        fail("validation traceability for Board-to-board interface must include PB-100-b2b-interface-freeze-checklist.csv")
    if not any(
        "PB-100-b2b-interface-closeout-precheck.csv" in row["Primary artifact"]
        for row in gates_with_tests["Board-to-board interface"]
    ):
        fail("validation traceability for Board-to-board interface must include PB-100-b2b-interface-closeout-precheck.csv")

    missing_gates = sorted(gate for gate, gate_rows in gates_with_tests.items() if not gate_rows)
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing validation rows for gates: "
            f"{', '.join(missing_gates)}"
        )
