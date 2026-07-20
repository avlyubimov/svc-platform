#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PB100_DIR = REPO_ROOT / "hardware" / "power-board" / "PB-100"
LB100_DIR = REPO_ROOT / "hardware" / "logic-board" / "LB-100"
FB100_DIR = REPO_ROOT / "hardware" / "front-board" / "FB-100"
ORDER_READINESS = REPO_ROOT / "production" / "board-order" / "three_board_jlcpcb_order_readiness.csv"
LAYOUT_RULES = REPO_ROOT / "production" / "board-order" / "three_board_layout_rules.md"
LAYOUT_START_READINESS = (
    REPO_ROOT / "production" / "board-order" / "three_board_layout_start_readiness.csv"
)
FOOTPRINT_BINDING_STATUS = (
    REPO_ROOT / "production" / "board-order" / "three_board_footprint_binding_status.csv"
)
MECHANICAL_ENVELOPE_STATUS = (
    REPO_ROOT / "production" / "board-order" / "three_board_mechanical_envelope_status.csv"
)
PB100_FREEZE = PB100_DIR / "PB-100-schematic-freeze-checklist.md"
ADR_0014 = REPO_ROOT / "docs" / "adr" / "ADR-0014-lb-fb-baseline-requirements.md"

MANUFACTURING_SUFFIXES = {
    ".drl",
    ".gbr",
    ".gbl",
    ".gbo",
    ".gbs",
    ".gko",
    ".gm1",
    ".gtl",
    ".gto",
    ".gts",
    ".kicad_pos",
    ".pos",
    ".xln",
}
MANUFACTURING_NAME_FRAGMENTS = (
    "gerber",
    "drill",
    "pick-place",
    "pick_and_place",
    "pickplace",
    "placement",
)

FREEZE_CHECKLISTS = {
    "LB-100": LB100_DIR / "LB-100-schematic-freeze-checklist.md",
    "FB-100": FB100_DIR / "FB-100-schematic-freeze-checklist.md",
}
BLOCKER_REGISTERS = {
    "LB-100": LB100_DIR / "LB-100-board-release-blocker-register.csv",
    "FB-100": FB100_DIR / "FB-100-board-release-blocker-register.csv",
}
MANIFESTS = {
    "LB-100": LB100_DIR / "LB-100-review-release-manifest.csv",
    "FB-100": FB100_DIR / "FB-100-review-release-manifest.csv",
}
LAYOUT_START_CHECKLISTS = {
    "PB-100": PB100_DIR / "PB-100-pcb-layout-start-checklist.csv",
    "LB-100": LB100_DIR / "LB-100-pcb-layout-start-checklist.csv",
    "FB-100": FB100_DIR / "FB-100-pcb-layout-start-checklist.csv",
}
FOOTPRINT_BINDING_INVENTORIES = {
    "PB-100": PB100_DIR / "PB-100-footprint-binding-inventory.csv",
    "LB-100": LB100_DIR / "LB-100-footprint-binding-inventory.csv",
    "FB-100": FB100_DIR / "FB-100-footprint-binding-inventory.csv",
}
MECHANICAL_ENVELOPE_INVENTORIES = {
    "PB-100": PB100_DIR / "PB-100-mechanical-envelope-inventory.csv",
    "LB-100": LB100_DIR / "LB-100-mechanical-envelope-inventory.csv",
    "FB-100": FB100_DIR / "FB-100-mechanical-envelope-inventory.csv",
}
SCHEMATIC_REVIEW_CLOSEOUTS = {
    "LB-100": LB100_DIR / "LB-100-schematic-review-closeout.md",
    "FB-100": FB100_DIR / "FB-100-schematic-review-closeout.md",
}
LB100_CONTRACTS = (
    LB100_DIR / "LB-100-jpb1-resource-budget.csv",
    LB100_DIR / "LB-100-rail-tree-precheck.csv",
)
LB100_PIN_BINDING = LB100_DIR / "LB-100-stm32h563-pin-binding-precheck.csv"
LB100_SOURCING = LB100_DIR / "LB-100-mcu-sourcing-precheck.csv"
LB100_COMPONENT_SOURCING = LB100_DIR / "LB-100-component-sourcing-precheck.csv"
LB100_CLOSEOUTS = (
    LB100_DIR / "LB-100-communication-safety-precheck.csv",
    LB100_DIR / "LB-100-service-storage-sensor-precheck.csv",
)
LB100_RAIL_BUDGET_CLOSEOUT = LB100_DIR / "LB-100-rail-budget-closeout-precheck.csv"
FB100_CONTRACTS = (
    FB100_DIR / "FB-100-interface-signal-plan.csv",
    FB100_DIR / "FB-100-ui-mechanical-precheck.csv",
)
FB100_SOURCING = FB100_DIR / "FB-100-component-sourcing-precheck.csv"
FB100_INTERFACE_PINOUT = FB100_DIR / "FB-100-interface-pinout-closeout.csv"
FB100_CLOSEOUTS = (
    FB100_DIR / "FB-100-usb-service-closeout-precheck.csv",
    FB100_DIR / "FB-100-ui-control-closeout-precheck.csv",
    FB100_DIR / "FB-100-mechanical-envelope-precheck.csv",
)
REQUIRED_BLOCKER_PREFIX = {
    "LB-100": "LBREL-",
    "FB-100": "FBREL-",
}
REQUIRED_ORDER_BOARDS = {"PB-100", "LB-100", "FB-100"}
ORDER_COLUMNS = (
    "Board",
    "Board path",
    "Requirements state",
    "Schematic freeze state",
    "KiCad schematic state",
    "PCB layout state",
    "Fabrication output state",
    "Assembly output state",
    "Order state",
    "Blocking evidence",
    "Next action",
)
LAYOUT_START_READINESS_COLUMNS = (
    "Board",
    "Freeze state",
    "Layout planning state",
    "KiCad board import state",
    "Footprint binding state",
    "Mechanical envelope state",
    "Assembly/DFM baseline",
    "Fabrication/assembly output state",
    "Order state",
    "Blocking evidence",
    "Next action",
)
LAYOUT_START_CHECKLIST_COLUMNS = (
    "Gate",
    "Status",
    "Evidence",
    "Decision",
    "Blocked action",
)
FOOTPRINT_BINDING_STATUS_COLUMNS = (
    "Board",
    "Inventory",
    "Evidence source",
    "KiCad symbol state",
    "Open footprint items",
    "Board import state",
    "Blocked action",
)
FOOTPRINT_BINDING_INVENTORY_COLUMNS = (
    "Footprint item",
    "Assembly owner",
    "Preferred MPN or class",
    "Package or mechanical class",
    "Footprint source",
    "KiCad footprint binding state",
    "Drawing review state",
    "Alternatives",
    "Board-import impact",
    "Next action",
)
MECHANICAL_ENVELOPE_STATUS_COLUMNS = (
    "Board",
    "Inventory",
    "Evidence source",
    "Open mechanical items",
    "Board import state",
    "Blocked action",
)
MECHANICAL_ENVELOPE_INVENTORY_COLUMNS = (
    "Mechanical item",
    "Scope",
    "Evidence",
    "Current state",
    "Review state",
    "Board-import impact",
    "Next action",
)
BLOCKER_COLUMNS = (
    "Gate",
    "Blocker ID",
    "Status",
    "Blocking evidence",
    "Required close evidence",
    "Next engineering action",
    "Layout impact",
)
MANIFEST_COLUMNS = (
    "Artifact",
    "Category",
    "Freeze role",
    "Required for freeze",
    "Validation hook",
    "Status",
)
LB100_RESOURCE_COLUMNS = (
    "Resource group",
    "JPB1 pins",
    "Signals",
    "LB-100 resource requirement",
    "Current state",
    "Required close evidence",
    "Blocked action",
)
LB100_RAIL_COLUMNS = (
    "Rail",
    "Source",
    "Load scope",
    "Budget state",
    "Active budget mA",
    "Sleep/deep-sleep boundary",
    "Required close evidence",
    "Blocked action",
)
FB100_SIGNAL_COLUMNS = (
    "Signal group",
    "Signal",
    "Direction",
    "Owner",
    "Default state",
    "Requirement",
    "Current state",
    "Required close evidence",
    "Blocked action",
)
FB100_MECHANICAL_COLUMNS = (
    "Check ID",
    "Scope",
    "Required evidence",
    "Current state",
    "Pass condition",
    "Blocked action",
)
SOURCING_COLUMNS = (
    "Symbol key",
    "Assembly owner",
    "Preferred MPN or class",
    "JLCPCB part",
    "Primary source",
    "Secondary source",
    "Evidence date",
    "Evidence result",
    "Open blocker",
    "Status",
)
LB100_PIN_BINDING_COLUMNS = (
    "Scope",
    "JPB1 pin",
    "Net",
    "STM32H563VITx LQFP100 pin",
    "Package position",
    "Peripheral or pin evidence",
    "Default or population rule",
    "Review status",
    "Open blocker",
    "Blocked action",
)
GENERIC_CLOSEOUT_COLUMNS = (
    "Check ID",
    "Scope",
    "Evidence",
    "Close result",
    "Status",
    "Blocked action",
)
FB100_INTERFACE_PINOUT_COLUMNS = (
    "Connector",
    "Pin",
    "Signal",
    "Direction",
    "Owner",
    "Default state",
    "Close evidence",
    "Status",
    "Blocked action",
)
LB100_RAIL_BUDGET_CLOSEOUT_COLUMNS = (
    "Budget item",
    "Rail",
    "Population",
    "Active budget mA",
    "Service or peak budget mA",
    "Sleep boundary",
    "Source evidence",
    "Close result",
    "Status",
    "Blocked action",
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(REPO_ROOT)}")


def validate_csv(path: Path) -> list[dict[str, str]]:
    try:
        rows = list(csv.reader(path.open(newline="", encoding="utf-8")))
    except FileNotFoundError:
        fail(f"missing required CSV: {path.relative_to(REPO_ROOT)}")
    if not rows:
        fail(f"empty CSV: {path.relative_to(REPO_ROOT)}")
    expected_width = len(rows[0])
    for row_number, row_values in enumerate(rows, 1):
        if len(row_values) != expected_width:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                f"expected {expected_width} columns, got {len(row_values)}"
            )
    return list(csv.DictReader(path.open(newline="", encoding="utf-8")))


def validate_s_expression_balance(path: Path) -> None:
    text = read_text(path)
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        else:
            if character == '"':
                in_string = True
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth < 0:
                    fail(f"negative parenthesis depth in {path.relative_to(REPO_ROOT)}")
    if depth != 0 or in_string:
        fail(
            f"unbalanced S-expression in {path.relative_to(REPO_ROOT)}: "
            f"depth={depth}, in_string={in_string}"
        )


def checklist_status(path: Path) -> str:
    for line in read_text(path).splitlines():
        if line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    fail(f"{path.relative_to(REPO_ROOT)} must contain Status")


def checklist_gates(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if len(cells) != 4 or cells[0] in {"Gate", "---"}:
            continue
        rows.append(
            {
                "Gate": cells[0],
                "Status": cells[1],
                "Evidence": cells[2],
                "Close condition": cells[3],
            }
        )
    if not rows:
        fail(f"{path.relative_to(REPO_ROOT)} must include required gates")
    return rows


def manufacturing_files(board_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in board_dir.rglob("*"):
        if not path.is_file():
            continue
        lowered_name = path.name.lower()
        if path.suffix.lower() in MANUFACTURING_SUFFIXES:
            files.append(path)
            continue
        if path.suffix.lower() == ".zip" and any(fragment in lowered_name for fragment in MANUFACTURING_NAME_FRAGMENTS):
            files.append(path)
    return sorted(files)


def layout_files(board_dir: Path) -> list[Path]:
    return sorted(board_dir.rglob("*.kicad_pcb"))


def validate_no_layout_before_freeze(board: str, board_dir: Path, status: str) -> None:
    pcbs = layout_files(board_dir)
    manufacturing = manufacturing_files(board_dir)
    if status != "Closed" and pcbs:
        fail(f"{board} has PCB layout before schematic freeze: {pcbs[0].relative_to(REPO_ROOT)}")
    if status != "Closed" and manufacturing:
        fail(f"{board} has manufacturing output before schematic freeze: {manufacturing[0].relative_to(REPO_ROOT)}")


def validate_no_manufacturing_outputs_before_order(board: str, board_dir: Path) -> None:
    manufacturing = manufacturing_files(board_dir)
    if manufacturing:
        fail(
            f"{board} has manufacturing output before order review: "
            f"{manufacturing[0].relative_to(REPO_ROOT)}"
        )


def validate_adr_0014() -> None:
    text = read_text(ADR_0014)
    for token in (
        "Accepted",
        "LB-100",
        "FB-100",
        "STM32H563",
        "PB_5V_OUT",
        "CAN1",
        "read-only",
        "does not authorize PCB layout",
        "Gerbers",
        "JLCPCB",
    ):
        if token not in text:
            fail(f"{ADR_0014.relative_to(REPO_ROOT)} must include {token}")


def validate_checklist(board: str, path: Path) -> None:
    text = read_text(path)
    lower_text = text.lower()
    normalized_text = " ".join(text.split())
    status = checklist_status(path)
    if status == "Open" and ("does not" not in lower_text or "pcb layout" not in lower_text):
        fail(f"{path.relative_to(REPO_ROOT)} must block PCB layout while open")
    if status == "Closed":
        for token in ("does not authorize", "Gerbers", "drills", "pick-place", "BOM/CPL", "PCBA orders"):
            if token not in text and token not in normalized_text:
                fail(f"{path.relative_to(REPO_ROOT)} must keep manufacturing-output boundary token {token}")
    if "board-release-blocker-register.csv" not in text:
        fail(f"{path.relative_to(REPO_ROOT)} must reference blocker register")
    gates = checklist_gates(path)
    if not any(row["Status"] == "Closed" for row in gates):
        fail(f"{path.relative_to(REPO_ROOT)} must have closed baseline gates")
    if status == "Open" and not any(row["Status"] == "Conditional" for row in gates):
        fail(f"{path.relative_to(REPO_ROOT)} must have conditional close gates")
    if status == "Closed":
        open_gates = [row["Gate"] for row in gates if row["Status"] != "Closed"]
        if open_gates:
            fail(f"{path.relative_to(REPO_ROOT)} has non-closed gates: {', '.join(open_gates)}")
        closeout_path = SCHEMATIC_REVIEW_CLOSEOUTS[board]
        if str(closeout_path.relative_to(REPO_ROOT)) not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must reference {closeout_path.relative_to(REPO_ROOT)}")
    if board == "LB-100":
        required_gates = {"MCU and pin binding", "Power tree and sleep budget", "PB-100 interface", "CAN and expansion safety"}
    else:
        required_gates = {"LB-100 interface", "USB service and ESD", "Indicators and controls", "Mechanical and enclosure interface"}
    seen_gates = {row["Gate"] for row in gates}
    missing = sorted(required_gates - seen_gates)
    if missing:
        fail(f"{path.relative_to(REPO_ROOT)} is missing gates: {', '.join(missing)}")


def validate_blocker_register(board: str, path: Path) -> None:
    rows = validate_csv(path)
    if not rows:
        fail(f"empty blocker register: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in BLOCKER_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    prefix = REQUIRED_BLOCKER_PREFIX[board]
    seen_ids = set()
    for row_number, row in enumerate(rows, 2):
        blocker_id = row["Blocker ID"].strip()
        if blocker_id in seen_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Blocker ID {blocker_id}")
        seen_ids.add(blocker_id)
        if not blocker_id.startswith(prefix):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocker ID must start with {prefix}")
        if row["Status"].strip() not in {"Open", "Conditional", "Closed"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blockers must be Open Conditional or Closed")
        for column in BLOCKER_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if row["Status"].strip() == "Closed" and "closed" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: closed blocker must explain closed evidence")
        impact = row["Layout impact"].lower()
        if "layout" not in impact:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Layout impact must block layout")
        if row["Status"].strip() != "Closed" and "block" not in impact:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: active Layout impact must block layout")


def validate_manifest(path: Path) -> None:
    rows = validate_csv(path)
    if not rows:
        fail(f"empty manifest: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in MANIFEST_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    seen_artifacts = set()
    for row_number, row in enumerate(rows, 2):
        artifact = row["Artifact"].strip()
        if artifact in seen_artifacts:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Artifact {artifact}")
        seen_artifacts.add(artifact)
        for column in MANIFEST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Required for freeze"].strip() != "Required":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: artifact must be Required")
        if not (REPO_ROOT / artifact).exists():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing artifact {artifact}")
    if "docs/adr/ADR-0014-lb-fb-baseline-requirements.md" not in seen_artifacts:
        fail(f"{path.relative_to(REPO_ROOT)} must include ADR-0014")


def validate_contract_csv(path: Path, required_columns: tuple[str, ...], required_tokens: tuple[str, ...]) -> None:
    rows = validate_csv(path)
    if not rows:
        fail(f"empty contract CSV: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in required_columns if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    text = read_text(path)
    for token in required_tokens:
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")
    for row_number, row in enumerate(rows, 2):
        for column in required_columns:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        blocked = row["Blocked action"].lower()
        if "do not" not in blocked:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocked action must be explicit")


def validate_sourcing_precheck(path: Path, required_tokens: tuple[str, ...]) -> None:
    rows = validate_csv(path)
    if not rows:
        fail(f"empty sourcing precheck: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in SOURCING_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    text = read_text(path)
    for token in required_tokens:
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")
    for row_number, row in enumerate(rows, 2):
        for column in SOURCING_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Assembly owner"].strip() not in {"Factory", "Garage", "Factory or DNP"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid assembly owner")
        if row["Status"].strip() not in {"Conditional", "Ready", "Frozen"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid sourcing status")
        if row["Evidence date"].strip() != "2026-07-20":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: evidence date must match current recheck date")
        for column in ("Primary source", "Secondary source"):
            if not row[column].strip().startswith(("https://", "http://")):
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: {column} must be a URL")
        if "open" not in row["Open blocker"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Open blocker must explicitly remain open")


def validate_generic_closeout_csv(path: Path, required_tokens: tuple[str, ...]) -> None:
    rows = validate_csv(path)
    if not rows:
        fail(f"empty closeout CSV: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in GENERIC_CLOSEOUT_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    text = read_text(path)
    for token in required_tokens:
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")
    for row_number, row in enumerate(rows, 2):
        for column in GENERIC_CLOSEOUT_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Status"].strip() != "Closed":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: closeout rows must be Closed")
        if "closed" not in row["Close result"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Close result must explain closure")
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocked action must be explicit")
    if "No-layout boundary" not in text and "Manufacturing boundary" not in text:
        fail(f"{path.relative_to(REPO_ROOT)} must include a no-layout or manufacturing boundary row")


def validate_lb100_pin_binding() -> None:
    path = LB100_PIN_BINDING
    rows = validate_csv(path)
    if not rows:
        fail(f"empty LB-100 pin binding: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in LB100_PIN_BINDING_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    text = read_text(path)
    for token in (
        "STM32H563VITx.xml",
        "DBVersion V3.0",
        "Package LQFP100",
        "IONb 80",
        "OUT1_CTL",
        "OUT10_IMON",
        "PB_I2C_SCL",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "USB_DM",
        "SWDIO",
        "BOOT0",
    ):
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")

    jpb1_pins = {str(pin) for pin in range(1, 101)}
    seen_jpb1 = set()
    seen_package_positions = set()
    seen_mcu_pins = set()
    for row_number, row in enumerate(rows, 2):
        for column in LB100_PIN_BINDING_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        status = row["Review status"].strip()
        if status not in {"Closed", "Conditional", "Reserved"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Review status")
        blocked = row["Blocked action"].lower()
        if "do not" not in blocked:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocked action must be explicit")
        jpb1_pin = row["JPB1 pin"].strip()
        if jpb1_pin != "N/A":
            if jpb1_pin not in jpb1_pins:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid JPB1 pin {jpb1_pin}")
            if jpb1_pin in seen_jpb1:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate JPB1 pin {jpb1_pin}")
            seen_jpb1.add(jpb1_pin)
        mcu_pin = row["STM32H563VITx LQFP100 pin"].strip()
        package_position = row["Package position"].strip()
        if mcu_pin != "No MCU pin":
            if package_position in {"N/A", ""}:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: exact MCU pin requires package position")
            if package_position in seen_package_positions:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate package position {package_position}")
            if mcu_pin in seen_mcu_pins:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate MCU pin {mcu_pin}")
            seen_package_positions.add(package_position)
            seen_mcu_pins.add(mcu_pin)
    missing_jpb1 = sorted(jpb1_pins - seen_jpb1, key=int)
    if missing_jpb1:
        fail(f"{path.relative_to(REPO_ROOT)} is missing JPB1 pins: {', '.join(missing_jpb1)}")


def validate_fb100_interface_pinout() -> None:
    path = FB100_INTERFACE_PINOUT
    rows = validate_csv(path)
    if not rows:
        fail(f"empty FB-100 interface pinout: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in FB100_INTERFACE_PINOUT_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    text = read_text(path)
    for token in (
        "JFB1",
        "USB_D_P",
        "USB_D_N",
        "USB_CC1",
        "USB_CC2",
        "USB_VBUS_SENSE",
        "CH_LED_1",
        "CH_LED_10",
        "SERVICE_BTN",
        "RESET_BTN",
        "OLED_SCL",
        "OLED_SDA",
        "Do not connect VBUS to system rails",
    ):
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")
    seen_pins = set()
    for row_number, row in enumerate(rows, 2):
        for column in FB100_INTERFACE_PINOUT_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Connector"].strip() != "JFB1":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: connector must be JFB1")
        pin = row["Pin"].strip()
        if pin in seen_pins:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate JFB1 pin {pin}")
        seen_pins.add(pin)
        if row["Status"].strip() != "Closed":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pinout rows must be Closed")
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocked action must be explicit")
    expected = {str(pin) for pin in range(1, 25)}
    missing = sorted(expected - seen_pins, key=int)
    if missing:
        fail(f"{path.relative_to(REPO_ROOT)} is missing JFB1 pins: {', '.join(missing)}")


def validate_lb100_rail_budget_closeout() -> None:
    path = LB100_RAIL_BUDGET_CLOSEOUT
    rows = validate_csv(path)
    if not rows:
        fail(f"empty LB-100 rail budget closeout: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in LB100_RAIL_BUDGET_CLOSEOUT_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    text = read_text(path)
    for token in (
        "PB_5V_OUT",
        "219.2",
        "415.2",
        "500 mA",
        "no-back-power",
        "CAN1 TX",
        "No-layout boundary",
    ):
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")
    seen_items = set()
    for row_number, row in enumerate(rows, 2):
        item = row["Budget item"].strip()
        if item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Budget item {item}")
        seen_items.add(item)
        for column in LB100_RAIL_BUDGET_CLOSEOUT_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Status"].strip() != "Closed":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: rail budget rows must be Closed")
        if "closed" not in row["Close result"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Close result must explain closure")
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocked action must be explicit")
    for item in ("Base sustained total", "Service peak total", "No-layout boundary"):
        if item not in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)} must include {item}")


def validate_order_readiness() -> None:
    rows = validate_csv(ORDER_READINESS)
    missing_columns = [column for column in ORDER_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{ORDER_READINESS.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    seen_boards = set()
    for row_number, row in enumerate(rows, 2):
        board = row["Board"].strip()
        seen_boards.add(board)
        if board not in REQUIRED_ORDER_BOARDS:
            fail(f"{ORDER_READINESS.relative_to(REPO_ROOT)}:{row_number}: unknown board {board}")
        board_path = REPO_ROOT / row["Board path"].strip()
        if not board_path.exists():
            fail(f"{ORDER_READINESS.relative_to(REPO_ROOT)}:{row_number}: missing board path")
        if row["Order state"].strip() != "NO-GO":
            fail(f"{ORDER_READINESS.relative_to(REPO_ROOT)}:{row_number}: order must remain NO-GO until every board closes")
        for token in ("No PCB layout", "No fabrication outputs", "No assembly outputs"):
            if token not in " ".join(row.values()):
                fail(f"{ORDER_READINESS.relative_to(REPO_ROOT)}:{row_number}: must keep {token}")
        for token in (
            f"{board}-pcb-layout-start-checklist.csv",
            "footprint binding",
            "mechanical envelope",
            "do not generate JLCPCB/PCBWay outputs",
        ):
            if token not in " ".join(row.values()):
                fail(f"{ORDER_READINESS.relative_to(REPO_ROOT)}:{row_number}: must include {token}")
    missing_boards = sorted(REQUIRED_ORDER_BOARDS - seen_boards)
    if missing_boards:
        fail(f"{ORDER_READINESS.relative_to(REPO_ROOT)} is missing boards: {', '.join(missing_boards)}")


def validate_layout_rules() -> None:
    text = read_text(LAYOUT_RULES)
    for token in (
        "Status: Active",
        "Evidence date: 2026-07-20",
        "https://jlcpcb.com/capabilities/pcb-capabilities",
        "https://jlcpcb.com/capabilities/pcb-assembly-capabilities",
        "https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html",
        "https://www.pcbway.com/pcb_prototype/Panel_Requirements_for_Assembly.html",
        "0.15 mm / 0.15 mm",
        "0.30 mm",
        "0.60 mm",
        "0402",
        "0603",
        "fiducials",
        "PB-100 high-current paths",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "USB-C",
        "Manufacturing outputs remain blocked",
    ):
        if token not in text:
            fail(f"{LAYOUT_RULES.relative_to(REPO_ROOT)} must include {token}")
    for token in (
        "does not create KiCad PCB layout files",
        "Gerbers",
        "drills",
        "pick-place",
        "BOM/CPL",
        "manufacturing ZIP",
        "PCBA orders",
    ):
        if token not in text:
            fail(f"{LAYOUT_RULES.relative_to(REPO_ROOT)} must keep output boundary token {token}")


def board_dir(board: str) -> Path:
    if board == "PB-100":
        return PB100_DIR
    if board == "LB-100":
        return LB100_DIR
    if board == "FB-100":
        return FB100_DIR
    fail(f"unknown board {board}")


def validate_layout_start_readiness() -> None:
    rows = validate_csv(LAYOUT_START_READINESS)
    missing_columns = [column for column in LAYOUT_START_READINESS_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    seen_boards = set()
    for row_number, row in enumerate(rows, 2):
        board = row["Board"].strip()
        seen_boards.add(board)
        if board not in REQUIRED_ORDER_BOARDS:
            fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)}:{row_number}: unknown board {board}")
        if row["Freeze state"].strip() != "Closed":
            fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)}:{row_number}: freeze must be Closed")
        if row["Layout planning state"].strip() != "READY":
            fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)}:{row_number}: layout planning must be READY")
        if row["KiCad board import state"].strip() != "BLOCKED":
            fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)}:{row_number}: KiCad board import must remain BLOCKED")
        if not row["Footprint binding state"].startswith("OPEN"):
            fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)}:{row_number}: footprint binding must be OPEN")
        if not row["Mechanical envelope state"].startswith("OPEN"):
            fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)}:{row_number}: mechanical envelope must be OPEN")
        if not row["Assembly/DFM baseline"].startswith("READY"):
            fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)}:{row_number}: assembly DFM baseline must be READY")
        if row["Order state"].strip() != "NO-GO":
            fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)}:{row_number}: order must remain NO-GO")
        row_text = " ".join(row.values())
        for token in (
            f"No {board}.kicad_pcb",
            "no Gerbers",
            "drills",
            "pick-place",
            "BOM/CPL",
            "manufacturing ZIP",
            f"{board}-pcb-layout-start-checklist.csv",
            f"{board}-footprint-binding-inventory.csv",
            f"{board}-mechanical-envelope-inventory.csv",
            "three_board_footprint_binding_status.csv",
            "three_board_mechanical_envelope_status.csv",
            "footprint binding",
            "mechanical envelope",
        ):
            if token not in row_text:
                fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)}:{row_number}: must include {token}")
        current_layout_files = layout_files(board_dir(board))
        if current_layout_files:
            fail(
                f"{board} has KiCad board import while layout-start checklist is blocked: "
                f"{current_layout_files[0].relative_to(REPO_ROOT)}"
            )
        validate_no_manufacturing_outputs_before_order(board, board_dir(board))
    missing_boards = sorted(REQUIRED_ORDER_BOARDS - seen_boards)
    if missing_boards:
        fail(f"{LAYOUT_START_READINESS.relative_to(REPO_ROOT)} is missing boards: {', '.join(missing_boards)}")


def validate_layout_start_checklist(board: str, path: Path) -> None:
    rows = validate_csv(path)
    missing_columns = [column for column in LAYOUT_START_CHECKLIST_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    rows_by_gate = {row["Gate"].strip(): row for row in rows}
    required_gates = {
        "Schematic freeze",
        "KiCad schematic value review",
        "Footprint binding",
        "Mechanical envelope",
        "DFM/DRC baseline",
        "Manufacturing output boundary",
    }
    missing_gates = sorted(required_gates - set(rows_by_gate))
    if missing_gates:
        fail(f"{path.relative_to(REPO_ROOT)} is missing gates: {', '.join(missing_gates)}")
    expected_status = {
        "Schematic freeze": "Closed",
        "KiCad schematic value review": "Closed",
        "Footprint binding": "Open",
        "Mechanical envelope": "Open",
        "DFM/DRC baseline": "Ready",
        "Manufacturing output boundary": "Closed",
    }
    for gate, status in expected_status.items():
        if rows_by_gate[gate]["Status"].strip() != status:
            fail(f"{path.relative_to(REPO_ROOT)}:{gate}: expected {status}")
    text = read_text(path)
    for row_number, row in enumerate(rows, 2):
        for column in LAYOUT_START_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Status"].strip() not in {"Closed", "Open", "Ready"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Status")
        if "Do not" not in row["Blocked action"]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocked action must be explicit")
    for token in (
        "empty Footprint properties",
        f"{board}-footprint-binding-inventory.csv",
        f"{board}-mechanical-envelope-inventory.csv",
        "production/board-order/three_board_layout_rules.md",
        "Gerbers",
        "drills",
        "pick-place",
        "BOM/CPL",
        "manufacturing ZIP",
        "PCBA order",
    ):
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")
    board_tokens = {
        "PB-100": ("high-current", "JPB1", "power copper", "fuse"),
        "LB-100": ("STM32H563", "JPB1", "CAN1_TX_ROUTE", "DNP/open"),
        "FB-100": ("USB-C", "no-back-power", "JFB1", "VBUS"),
    }
    for token in board_tokens[board]:
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include board-specific token {token}")


def validate_footprint_binding_inventory(board: str, path: Path) -> int:
    rows = validate_csv(path)
    if not rows:
        fail(f"empty footprint inventory: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in FOOTPRINT_BINDING_INVENTORY_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    text = read_text(path)
    board_tokens = {
        "PB-100": ("TPS48110AQDGXRQ1", "JPB1", "CAN1", "high-current"),
        "LB-100": ("STM32H563VIT6", "JPB1", "CAN1_TX_ROUTE", "DNP/open"),
        "FB-100": ("USB4105-GF-A", "JFB1", "USB-C", "VBUS"),
    }
    for token in board_tokens[board]:
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include board-specific footprint token {token}")
    seen_items = set()
    open_items = 0
    for row_number, row in enumerate(rows, 2):
        item = row["Footprint item"].strip()
        if item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Footprint item {item}")
        seen_items.add(item)
        for column in FOOTPRINT_BINDING_INVENTORY_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Assembly owner"].strip() not in {"Factory", "Garage", "Factory or DNP"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Assembly owner")
        binding_state = row["KiCad footprint binding state"].strip()
        drawing_state = row["Drawing review state"].strip()
        if binding_state not in {"Open", "Not required"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid KiCad footprint binding state")
        if drawing_state not in {"Open", "Not required"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Drawing review state")
        impact = row["Board-import impact"].strip()
        if binding_state == "Open":
            open_items += 1
            if drawing_state != "Open":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: open binding requires open drawing review")
            if "BOARD_IMPORT_BLOCKED" not in impact:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: board import must remain blocked")
        else:
            if drawing_state != "Not required":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Not required binding needs Not required drawing review")
            if impact != "NO_FOOTPRINT_REQUIRED":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Not required item must not block board import by footprint")
        next_action = row["Next action"].lower()
        if not any(verb in next_action for verb in ("review", "verify", "select", "keep", "close", "bind")):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Next action must be actionable")
    return open_items


def validate_footprint_binding_status() -> None:
    rows = validate_csv(FOOTPRINT_BINDING_STATUS)
    missing_columns = [column for column in FOOTPRINT_BINDING_STATUS_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{FOOTPRINT_BINDING_STATUS.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    seen_boards = set()
    inventory_counts = {
        board: validate_footprint_binding_inventory(board, path)
        for board, path in FOOTPRINT_BINDING_INVENTORIES.items()
    }
    for row_number, row in enumerate(rows, 2):
        board = row["Board"].strip()
        seen_boards.add(board)
        if board not in REQUIRED_ORDER_BOARDS:
            fail(f"{FOOTPRINT_BINDING_STATUS.relative_to(REPO_ROOT)}:{row_number}: unknown board {board}")
        inventory = row["Inventory"].strip()
        if inventory != str(FOOTPRINT_BINDING_INVENTORIES[board].relative_to(REPO_ROOT)):
            fail(f"{FOOTPRINT_BINDING_STATUS.relative_to(REPO_ROOT)}:{row_number}: wrong inventory path")
        try:
            open_items = int(row["Open footprint items"].strip())
        except ValueError:
            fail(f"{FOOTPRINT_BINDING_STATUS.relative_to(REPO_ROOT)}:{row_number}: Open footprint items must be an integer")
        if open_items != inventory_counts[board]:
            fail(
                f"{FOOTPRINT_BINDING_STATUS.relative_to(REPO_ROOT)}:{row_number}: "
                f"open item count {open_items} does not match inventory count {inventory_counts[board]}"
            )
        if row["Board import state"].strip() != "BLOCKED":
            fail(f"{FOOTPRINT_BINDING_STATUS.relative_to(REPO_ROOT)}:{row_number}: board import must be BLOCKED")
        row_text = " ".join(row.values())
        for token in (f"{board}.kicad_pcb", "empty Footprint", "Do not create", "package drawing review"):
            if token not in row_text:
                fail(f"{FOOTPRINT_BINDING_STATUS.relative_to(REPO_ROOT)}:{row_number}: must include {token}")
    missing_boards = sorted(REQUIRED_ORDER_BOARDS - seen_boards)
    if missing_boards:
        fail(f"{FOOTPRINT_BINDING_STATUS.relative_to(REPO_ROOT)} is missing boards: {', '.join(missing_boards)}")


def validate_mechanical_envelope_inventory(board: str, path: Path) -> int:
    rows = validate_csv(path)
    if not rows:
        fail(f"empty mechanical envelope inventory: {path.relative_to(REPO_ROOT)}")
    missing_columns = [column for column in MECHANICAL_ENVELOPE_INVENTORY_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    text = read_text(path)
    board_tokens = {
        "PB-100": ("JPB1", "fuse", "high-current", "CAN1"),
        "LB-100": ("JPB1", "STM32H563VITx", "BLE antenna", "CAN1_TX_ROUTE"),
        "FB-100": ("USB-C", "JFB1", "CH_LED_1..CH_LED_10", "OLED"),
    }
    for token in board_tokens[board]:
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include board-specific mechanical token {token}")
    seen_items = set()
    for row_number, row in enumerate(rows, 2):
        item = row["Mechanical item"].strip()
        if item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Mechanical item {item}")
        seen_items.add(item)
        for column in MECHANICAL_ENVELOPE_INVENTORY_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Review state"].strip() != "Open":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Review state must be Open")
        if "BOARD_IMPORT_BLOCKED" not in row["Board-import impact"]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: board import must remain blocked")
        next_action = row["Next action"].lower()
        if not any(verb in next_action for verb in ("create", "select", "review", "define", "close", "apply")):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Next action must be actionable")
    return len(rows)


def validate_mechanical_envelope_status() -> None:
    rows = validate_csv(MECHANICAL_ENVELOPE_STATUS)
    missing_columns = [column for column in MECHANICAL_ENVELOPE_STATUS_COLUMNS if column not in rows[0]]
    if missing_columns:
        fail(f"{MECHANICAL_ENVELOPE_STATUS.relative_to(REPO_ROOT)} is missing columns: {', '.join(missing_columns)}")
    seen_boards = set()
    inventory_counts = {
        board: validate_mechanical_envelope_inventory(board, path)
        for board, path in MECHANICAL_ENVELOPE_INVENTORIES.items()
    }
    for row_number, row in enumerate(rows, 2):
        board = row["Board"].strip()
        seen_boards.add(board)
        if board not in REQUIRED_ORDER_BOARDS:
            fail(f"{MECHANICAL_ENVELOPE_STATUS.relative_to(REPO_ROOT)}:{row_number}: unknown board {board}")
        inventory = row["Inventory"].strip()
        if inventory != str(MECHANICAL_ENVELOPE_INVENTORIES[board].relative_to(REPO_ROOT)):
            fail(f"{MECHANICAL_ENVELOPE_STATUS.relative_to(REPO_ROOT)}:{row_number}: wrong inventory path")
        try:
            open_items = int(row["Open mechanical items"].strip())
        except ValueError:
            fail(f"{MECHANICAL_ENVELOPE_STATUS.relative_to(REPO_ROOT)}:{row_number}: Open mechanical items must be an integer")
        if open_items != inventory_counts[board]:
            fail(
                f"{MECHANICAL_ENVELOPE_STATUS.relative_to(REPO_ROOT)}:{row_number}: "
                f"open item count {open_items} does not match inventory count {inventory_counts[board]}"
            )
        if row["Board import state"].strip() != "BLOCKED":
            fail(f"{MECHANICAL_ENVELOPE_STATUS.relative_to(REPO_ROOT)}:{row_number}: board import must be BLOCKED")
        row_text = " ".join(row.values())
        for token in (f"{board}.kicad_pcb", "Do not create", "mechanical", "evidence closes"):
            if token not in row_text:
                fail(f"{MECHANICAL_ENVELOPE_STATUS.relative_to(REPO_ROOT)}:{row_number}: must include {token}")
    missing_boards = sorted(REQUIRED_ORDER_BOARDS - seen_boards)
    if missing_boards:
        fail(f"{MECHANICAL_ENVELOPE_STATUS.relative_to(REPO_ROOT)} is missing boards: {', '.join(missing_boards)}")


def validate_kicad_scaffold(board: str, board_dir: Path, status: str) -> None:
    kicad_dir = board_dir / "kicad"
    project_path = kicad_dir / f"{board}.kicad_pro"
    schematic_path = kicad_dir / f"{board}.kicad_sch"
    try:
        project = json.loads(project_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing KiCad project: {project_path.relative_to(REPO_ROOT)}")
    except json.JSONDecodeError as error:
        fail(f"invalid KiCad project JSON in {project_path.relative_to(REPO_ROOT)}: {error}")
    if project.get("project", {}).get("name") != board:
        fail(f"{project_path.relative_to(REPO_ROOT)} must use project name {board}")
    for path in (
        schematic_path,
        kicad_dir / "sym-lib-table",
        kicad_dir / "fp-lib-table",
        kicad_dir / "lib" / f"{board.replace('-', '')}.kicad_sym",
    ):
        validate_s_expression_balance(path)
    readme = read_text(kicad_dir / "README.md")
    if f"no `{board}.kicad_pcb`" not in readme:
        fail(f"{(kicad_dir / 'README.md').relative_to(REPO_ROOT)} must explicitly block {board}.kicad_pcb")
    schematic_text = read_text(schematic_path)
    if status == "Closed":
        closeout_path = SCHEMATIC_REVIEW_CLOSEOUTS[board]
        read_text(closeout_path)
        for token in ("Reviewed", "value-bearing", "schematic", "PCB layout and manufacturing outputs remain separate"):
            if token not in schematic_text and token not in read_text(closeout_path):
                fail(f"{schematic_path.relative_to(REPO_ROOT)} or closeout must include {token}")
        for token in (
            f"{board}-pcb-layout-start-checklist.csv",
            f"{board}-footprint-binding-inventory.csv",
            f"{board}-mechanical-envelope-inventory.csv",
            f"{board}.kicad_pcb",
            "footprint binding",
            "mechanical envelope",
        ):
            if token not in schematic_text:
                fail(f"{schematic_path.relative_to(REPO_ROOT)} must include layout-start token {token}")
        if board == "LB-100":
            for token in ("STM32H563VITx", "PB_5V_OUT", "219.2 mA", "415.2 mA", "CAN1", "DNP/open"):
                if token not in schematic_text:
                    fail(f"{schematic_path.relative_to(REPO_ROOT)} must include reviewed LB-100 token {token}")
        else:
            for token in ("JFB1", "USB_D_P", "USB_D_N", "CH_LED_1..CH_LED_10", "no back-power", "role-free"):
                if token not in schematic_text:
                    fail(f"{schematic_path.relative_to(REPO_ROOT)} must include reviewed FB-100 token {token}")
    validate_no_layout_before_freeze(board, board_dir, status)


def main() -> int:
    validate_adr_0014()
    for board, path in FREEZE_CHECKLISTS.items():
        validate_checklist(board, path)
        board_dir = LB100_DIR if board == "LB-100" else FB100_DIR
        status = checklist_status(path)
        validate_no_layout_before_freeze(board, board_dir, status)
        validate_kicad_scaffold(board, board_dir, status)
    for board, path in BLOCKER_REGISTERS.items():
        validate_blocker_register(board, path)
    for path in MANIFESTS.values():
        validate_manifest(path)
    validate_contract_csv(
        LB100_CONTRACTS[0],
        LB100_RESOURCE_COLUMNS,
        ("OUT1_CTL..OUT10_CTL", "OUT1_IMON..OUT10_IMON", "CAN1_TX_ROUTE", "SPARE_01..SPARE_16"),
    )
    validate_contract_csv(
        LB100_CONTRACTS[1],
        LB100_RAIL_COLUMNS,
        ("PB_5V_OUT", "LB_3V3_IO", "USB", "ADR-0012"),
    )
    validate_contract_csv(
        FB100_CONTRACTS[0],
        FB100_SIGNAL_COLUMNS,
        ("USB_D_P", "USB_D_N", "CH_LED_1..CH_LED_10", "no-back-power"),
    )
    validate_contract_csv(
        FB100_CONTRACTS[1],
        FB100_MECHANICAL_COLUMNS,
        ("FB-MECH-001", "USB-C", "No FB-100 PCB layout", "JLCPCB/PCBWay"),
    )
    validate_lb100_pin_binding()
    validate_sourcing_precheck(
        LB100_COMPONENT_SOURCING,
        (
            "LB_3V3_MAIN_REG",
            "LB_CAN1_TRANSCEIVER",
            "LB_CAN2_TRANSCEIVER",
            "LB_LIN_TRANSCEIVER_DNP",
            "LB_RS485_TRANSCEIVER_DNP",
            "LB_BLE_MODULE",
            "LB_FRAM",
            "LB_RTC",
            "LB_IMU",
            "LB_LUX",
            "LB_MICROSD_SOCKET",
            "LB_SERVICE_USB_BOUNDARY",
        ),
    )
    validate_lb100_rail_budget_closeout()
    for closeout_path in LB100_CLOSEOUTS:
        validate_generic_closeout_csv(closeout_path, ("Closed", "Do not"))
    validate_sourcing_precheck(
        LB100_SOURCING,
        ("STM32H563VIT6", "C6937834", "STM32H573VIT6", "C7545121", "STM32H563RGT6", "C22470894"),
    )
    validate_fb100_interface_pinout()
    for closeout_path in FB100_CLOSEOUTS:
        validate_generic_closeout_csv(closeout_path, ("Closed", "Do not"))
    validate_sourcing_precheck(
        FB100_SOURCING,
        (
            "USB4105-GF-A",
            "C3020560",
            "TYPE-C-31-M-12",
            "C165948",
            "USBLC6-2SC6",
            "C7519",
            "TPD2EUSB30ADRTR",
            "C94934",
            "FB_STATUS_RGB",
            "FB_CHANNEL_LED",
            "FB_FPC_CONNECTOR",
            "FB_FFC_CABLE",
            "FB_SERVICE_BUTTON",
            "FB_RESET_BUTTON",
            "FB_OLED_DNP",
            "FB_BUTTON_LED_PASSIVES",
            "FB_OLED_ALT_091_DNP",
        ),
    )
    validate_layout_rules()
    validate_footprint_binding_status()
    validate_mechanical_envelope_status()
    validate_layout_start_readiness()
    for board, path in LAYOUT_START_CHECKLISTS.items():
        validate_layout_start_checklist(board, path)
    validate_order_readiness()
    validate_no_layout_before_freeze("PB-100", PB100_DIR, checklist_status(PB100_FREEZE))
    print("Three-board order validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
