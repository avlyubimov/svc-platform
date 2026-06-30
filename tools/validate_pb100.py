#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PB100_DIR = REPO_ROOT / "hardware" / "power-board" / "PB-100"
KICAD_DIR = PB100_DIR / "kicad"
PRODUCTION_DIR = REPO_ROOT / "production"
DISALLOWED_LAYOUT_SUFFIXES = {
    ".kicad_pcb",
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
    ".zip",
}
DISALLOWED_LAYOUT_NAME_FRAGMENTS = (
    "gerber",
    "drill",
    "pick-place",
    "pick_and_place",
    "pickplace",
    "placement",
)
MANUFACTURING_HINT_SUFFIXES = {".csv", ".rpt", ".txt", ".xlsx", ".zip"}
FORBIDDEN_ROLE_TOKENS = (
    "FOG",
    "SEAT",
    "USB",
    "CHIGEE",
    "DVR",
    "BRAKE",
    "CIGARETTE",
)
SYMBOL_MPN_COLUMNS = (
    "Symbol key",
    "Schematic block",
    "Function",
    "Critical",
    "Preferred MPN or class",
    "Preferred package",
    "Alternate 1",
    "Alternate 2",
    "KiCad symbol status",
    "Footprint status",
    "Assembly/sourcing status",
    "Freeze condition",
    "Primary source",
)
REQUIRED_SYMBOL_KEYS = {
    "HS_CTRL",
    "OUT_FET",
    "OUT2_ESCAPE_FET",
    "INPUT_IDEAL_DIODE",
    "INPUT_CONNECTOR",
    "INPUT_REVERSE_FET",
    "INPUT_TVS",
    "LOGIC_BUCK",
    "LOGIC_BUCK_INDUCTOR",
    "TOTAL_CURRENT_MONITOR",
    "TOTAL_CURRENT_SHUNT",
    "THERMAL_NTC",
    "B2B_CONNECTOR",
    "OUTPUT_CONNECTOR",
    "OUTPUT_FUSE_HOLDER",
    "MAIN_FUSE_HOLDER",
    "CAN1_TX_DISABLE",
}
SYMBOL_WORKLIST_COLUMNS = (
    "Symbol key",
    "Concrete symbol name",
    "Library",
    "Symbol source",
    "Pin evidence status",
    "Footprint dependency",
    "Instance refs",
    "Allowed action",
    "Blocked action",
    "Freeze close evidence",
)
SYMBOL_PIN_EVIDENCE_COLUMNS = (
    "Symbol name",
    "Pin number",
    "Pin name",
    "Source",
    "Source revision",
    "Package",
    "Notes",
)
PIN_MAP_EVIDENCE_SYMBOLS = {"PB100_JPB1_100PIN_PRELIM"}
INSTANCE_SYMBOL_MAP_COLUMNS = (
    "Ref",
    "Instance block",
    "Symbol key",
    "Concrete symbol name",
    "Symbol state",
    "Notes",
)
SHEET_REFERENCE_MAP_COLUMNS = (
    "Sheet file",
    "Ref",
    "Symbol key",
    "Capture status",
    "Notes",
)
KICAD_SHEET_MANIFEST_COLUMNS = (
    "Sheet file",
    "Sheet kind",
    "Purpose",
    "Primary artifacts",
    "Status",
    "Capture gate",
)
NET_DOMAIN_PLAN_COLUMNS = (
    "Net pattern",
    "Domain",
    "Primary sheet",
    "Direction",
    "Default state",
    "Safety rule",
)
BOM_SYMBOL_MAP_COLUMNS = (
    "Symbol key",
    "BOM file",
    "BOM item",
    "Qty basis",
    "Population",
    "Assembly owner",
    "Status",
    "Notes",
)
SCHEMATIC_READINESS_DASHBOARD_COLUMNS = (
    "Area",
    "Status",
    "Evidence",
    "Machine check",
    "Remaining close work",
)
SCHEMATIC_FREEZE_GAP_REGISTER_COLUMNS = (
    "Gate",
    "Status",
    "Close evidence required",
    "Primary gap artifact",
    "Validator coverage",
    "Next close action",
)
OUTPUT_CHANNEL_PIN_CONTRACT_COLUMNS = (
    "Output",
    "Controller ref",
    "Switch ref",
    "Fuse ref",
    "Connector ref",
    "Control net",
    "Fault net",
    "Current net",
    "Load net",
    "Fused net",
    "Default state",
    "Safety rule",
)
OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS = (
    "Pin number",
    "Pin name",
    "Signal role",
    "Net pattern",
    "Direction",
    "Default state",
    "Freeze dependency",
)
INPUT_PROTECTION_PIN_CONTRACT_COLUMNS = (
    "Ref",
    "Symbol key",
    "Concrete symbol name",
    "Interface point",
    "Planned net",
    "Direction",
    "Default state",
    "Freeze dependency",
)
LOGIC_POWER_DESIGN_COLUMNS = (
    "Item",
    "Ref or net",
    "Design state",
    "Value status",
    "Freeze dependency",
    "Notes",
)
OUTPUT_STAGE_DESIGN_VALUE_COLUMNS = (
    "Output class",
    "Applies to",
    "Design item",
    "Related net pattern",
    "Value status",
    "Candidate direction",
    "Freeze dependency",
    "Notes",
)
OUTPUT_NET_EXPANSION_COLUMNS = (
    "Output",
    "Net pattern",
    "Expanded net",
    "Primary sheet",
    "Source artifact",
    "Default state",
    "Safety rule",
)
INPUT_POWER_DESIGN_VALUE_COLUMNS = (
    "Block",
    "Design item",
    "Related net",
    "Value status",
    "Candidate direction",
    "Freeze dependency",
    "Notes",
)
LOGIC_POWER_DESIGN_VALUE_COLUMNS = (
    "Design item",
    "Related net",
    "Value status",
    "Candidate direction",
    "Freeze dependency",
    "Notes",
)
CAN1_SAFETY_VERIFICATION_COLUMNS = (
    "Requirement",
    "Signal or artifact",
    "Rev.1 default",
    "Verification method",
    "Pass condition",
    "Blocked change",
)
ASSEMBLY_SOURCING_RECHECK_COLUMNS = (
    "Symbol key",
    "Assembly owner",
    "Preferred MPN or class",
    "Recheck status",
    "Recheck source",
    "Alternate coverage",
    "Factory action",
    "Garage action",
    "Freeze dependency",
)
VALIDATION_TRACEABILITY_COLUMNS = (
    "Test ID",
    "Freeze gate",
    "Validation phase",
    "Primary artifact",
    "Method",
    "Pass condition",
    "Safety constraint",
)
TEST_POINT_PLAN_COLUMNS = (
    "Test point ref",
    "Net",
    "Sheet",
    "Signal class",
    "Requirement",
    "Population",
    "Access intent",
    "Validation target",
    "Placement status",
)
FAULT_RESPONSE_MATRIX_COLUMNS = (
    "Fault ID",
    "Area",
    "Fault condition",
    "Detection source",
    "Hardware default",
    "Firmware response",
    "User-visible state",
    "Validation artifact",
    "Safety constraint",
)
SCHEMATIC_CAPTURE_WORK_QUEUE_COLUMNS = (
    "Work item",
    "Sheet file",
    "Capture scope",
    "Required refs",
    "Primary source artifacts",
    "Capture status",
    "Blocker",
    "Freeze close evidence",
    "Layout boundary",
)
REVIEW_RELEASE_MANIFEST_COLUMNS = (
    "Artifact",
    "Category",
    "Freeze role",
    "Required for freeze",
    "Validation hook",
    "Status",
)
REQUIRED_NET_PATTERNS = {
    "VBAT_RAW",
    "VBAT_PROT",
    "PB_5V_OUT",
    "LB_3V3_IO",
    "OUTn_CTL",
    "OUTn_FLT",
    "OUTn_IMON",
    "OUTn_LOAD",
    "OUTn_FUSED",
    "CAN1_TX_DISABLE_CMD",
    "CAN1_TX_DISABLED_STATUS",
    "CAN1_RX_ROUTE",
    "CAN1_TX_ROUTE",
}
ALLOWED_BOM_FILES = {"factory_bom_draft.csv", "garage_bom_draft.csv"}
OUTPUT_CONTROLLER_SYMBOL = "PB100_TPS48110AQDGXRQ1_PRELIM"
REQUIRED_READINESS_AREAS = {
    "Architecture baseline",
    "PB-100 requirements",
    "Symbol readiness",
    "KiCad scaffold",
    "Capture work queue",
    "Review release manifest",
    "Freeze gap register",
    "Validation traceability",
    "Instance map",
    "Sheet map",
    "Net domains",
    "Output pin contract",
    "Output controller template",
    "Output net expansion",
    "Output stage design values",
    "Input controller template",
    "Current monitor template",
    "Logic buck template",
    "Input power design values",
    "Logic power design values",
    "Input protection contract",
    "Test point plan",
    "Fault response matrix",
    "Hardware capability manifest",
    "Logic power values",
    "BOM synchronization",
    "Assembly sourcing recheck",
    "CAN1 safety",
    "CAN1 safety verification",
    "Layout authorization",
}
ALLOWED_DASHBOARD_STATUSES = {"Closed", "Conditional", "Open", "Blocked"}
REQUIRED_LOGIC_POWER_ITEMS = {
    "Buck regulator",
    "Buck input rail",
    "Buck output rail",
    "Inductor",
    "Input capacitors",
    "Output capacitors",
    "Feedback divider",
    "UVLO network",
    "Power-good",
    "EMI input filter",
}
REQUIRED_OUTPUT_STAGE_CLASSES = {"High current", "Medium current", "Low current"}
REQUIRED_OUTPUT_STAGE_ITEMS = {
    "OV threshold divider",
    "Current warning threshold",
    "Short-circuit threshold",
    "Fault timer",
    "Bootstrap capacitor",
    "Gate drive resistors",
    "Current sense topology",
    "Inductive clamp strategy",
}
REQUIRED_INPUT_POWER_ITEMS = {
    "Battery positive derating",
    "TVS clamp selection",
    "Charge-pump capacitor",
    "Enable network",
    "Gate clamp and discharge",
    "Q1 package and copper path",
    "Shunt value and power rating",
    "I2C address straps",
    "I2C pull-up domain",
    "Alert mapping",
    "Bus voltage sense",
    "Protected battery distribution",
}
REQUIRED_LOGIC_POWER_VALUE_ITEMS = {
    "Input filter",
    "UVLO divider",
    "RON programming",
    "Feedback divider",
    "Bootstrap capacitor",
    "Switch node damping",
    "Inductor",
    "Output capacitors",
    "Power-good pull-up",
    "Higher-current fallback",
}
REQUIRED_CAN1_SAFETY_REQUIREMENTS = {
    "Vehicle CAN read-only default",
    "TX physical path",
    "Disable command",
    "Disabled status",
    "RX independence",
    "DNP BOM ownership",
    "Firmware safety",
    "Future TX change process",
}
REQUIRED_FAULT_IDS = {
    "PBFLT-INPUT-REV",
    "PBFLT-LOAD-DUMP",
    "PBFLT-LOGIC-RAIL",
    "PBFLT-LB-ABSENT",
    "PBFLT-OUT-OC",
    "PBFLT-OUT-SHORT",
    "PBFLT-OUT2-INRUSH",
    "PBFLT-FUSE-OPEN",
    "PBFLT-THERM-HIGH",
    "PBFLT-THERM-STALE",
    "PBFLT-CUR-STALE",
    "PBFLT-BUDGET",
    "PBFLT-CAN1-TX",
    "PBFLT-B2B-MISMATCH",
}
REQUIRED_CAPTURE_WORK_ITEMS = {
    "CAP-TOP",
    "CAP-INP",
    "CAP-LOGIC",
    "CAP-OUT-TEMPLATE",
    "CAP-OUT-INST",
    "CAP-TEL",
    "CAP-B2B",
    "CAP-CAN1",
    "CAP-TP",
}
ALLOWED_CAPTURE_STATUSES = {
    "Scaffold ready",
    "Planned capture",
    "Blocked pending symbol",
    "Review-defined",
}
REQUIRED_RELEASE_MANIFEST_ARTIFACTS = {
    "hardware/power-board/PB-100/PB-100-schematic-package.md",
    "hardware/power-board/PB-100/PB-100-schematic-readiness-dashboard.csv",
    "hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md",
    "hardware/power-board/PB-100/PB-100-schematic-freeze-gap-register.csv",
    "hardware/power-board/PB-100/PB-100-validation-traceability.csv",
    "hardware/power-board/PB-100/PB-100-schematic-capture-work-queue.csv",
    "hardware/power-board/PB-100/PB-100-review-release-manifest.csv",
    "hardware/power-board/PB-100/PB-100-output-net-expansion.csv",
    "hardware/power-board/PB-100/PB-100-test-point-plan.csv",
    "hardware/power-board/PB-100/PB-100-fault-response-matrix.csv",
    "hardware/power-board/PB-100/PB-100-can1-safety-verification.csv",
    "hardware/power-board/PB-100/kicad/PB-100.kicad_sch",
    "hardware/power-board/PB-100/kicad/lib/PB100.kicad_sym",
    "firmware/configs/hardware/pb-100-capabilities.json",
    "production/bom/pb100_symbol_bom_map.csv",
    "production/bom/pb100_assembly_sourcing_recheck.csv",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(REPO_ROOT)}")


def validate_csv(path: Path) -> None:
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


def validate_kicad_scaffold() -> None:
    json.loads(read_text(KICAD_DIR / "PB-100.kicad_pro"))
    for schematic_path in sorted(KICAD_DIR.rglob("*.kicad_sch")):
        validate_s_expression_balance(schematic_path)
    for table_name in ("sym-lib-table", "fp-lib-table"):
        validate_s_expression_balance(KICAD_DIR / table_name)
    validate_s_expression_balance(KICAD_DIR / "lib" / "PB100.kicad_sym")
    validate_no_layout_artifacts()


def validate_kicad_cli_checks() -> None:
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli is None:
        print("PB-100 KiCad CLI checks skipped: kicad-cli not found")
        return

    with tempfile.TemporaryDirectory(prefix="svc-pb100-kicad-") as temp_dir:
        report_path = Path(temp_dir) / "PB-100-erc.json"
        command = [
            kicad_cli,
            "sch",
            "erc",
            "--format",
            "json",
            "--output",
            str(report_path),
            "--exit-code-violations",
            str(KICAD_DIR / "PB-100.kicad_sch"),
        ]
        result = subprocess.run(command, check=False, text=True, capture_output=True)
        if result.returncode != 0:
            details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
            fail(f"KiCad ERC failed for PB-100 schematic: {details}")

        try:
            report = json.loads(read_text(report_path))
        except json.JSONDecodeError as error:
            fail(f"invalid KiCad ERC JSON report: {error}")

        violations = []
        for sheet in report.get("sheets", []):
            violations.extend(sheet.get("violations", []))
        if violations:
            fail(f"KiCad ERC reported {len(violations)} PB-100 schematic violations")

        version = report.get("kicad_version", "unknown")
        print(f"PB-100 KiCad ERC passed with kicad-cli {version}")
        validate_kicad_cli_netlist_export(kicad_cli, Path(temp_dir))


def validate_kicad_cli_netlist_export(kicad_cli: str, temp_dir: Path) -> None:
    netlist_path = temp_dir / "PB-100.net"
    command = [
        kicad_cli,
        "sch",
        "export",
        "netlist",
        "--format",
        "kicadsexpr",
        "--output",
        str(netlist_path),
        str(KICAD_DIR / "PB-100.kicad_sch"),
    ]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        fail(f"KiCad netlist export failed for PB-100 schematic: {details}")

    netlist_text = read_text(netlist_path)
    if "(export" not in netlist_text or "(design" not in netlist_text:
        fail("KiCad netlist export did not produce a valid PB-100 netlist")
    validate_s_expression_balance(netlist_path)
    print("PB-100 KiCad netlist export passed")


def validate_no_layout_artifacts() -> None:
    search_roots = (PB100_DIR, PRODUCTION_DIR)
    for search_root in search_roots:
        for path in search_root.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.lower()
            suffix = path.suffix.lower()
            if name.endswith(".kicad_pcb-bak") or suffix in DISALLOWED_LAYOUT_SUFFIXES:
                fail(f"layout/manufacturing artifact is blocked before schematic freeze: {path.relative_to(REPO_ROOT)}")
            if suffix in MANUFACTURING_HINT_SUFFIXES and any(fragment in name for fragment in DISALLOWED_LAYOUT_NAME_FRAGMENTS):
                fail(f"layout/manufacturing artifact name is blocked before schematic freeze: {path.relative_to(REPO_ROOT)}")


def validate_symbol_library() -> None:
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    required_symbols = [
        "PB100_INPUT_PROTECTION_PRELIM",
        "PB100_LOGIC_POWER_PRELIM",
        "PB100_OUTPUT_CHANNEL_PRELIM",
        "PB100_B2B_JPB1_ABSTRACT",
        "PB100_CAN1_TX_DISABLE_PRELIM",
    ]
    for symbol_name in required_symbols:
        if f'(symbol "{symbol_name}"' not in symbol_text:
            fail(f"missing preliminary KiCad symbol: {symbol_name}")
    if symbol_text.count("(in_bom no)") < len(required_symbols):
        fail("preliminary symbols must be excluded from BOM")
    if symbol_text.count("(on_board no)") < len(required_symbols):
        fail("preliminary symbols must be excluded from board")


def validate_kicad_no_role_tokens() -> None:
    checked_paths = sorted(KICAD_DIR.rglob("*.kicad_sch")) + sorted((KICAD_DIR / "lib").rglob("*.kicad_sym"))
    for path in checked_paths:
        text = read_text(path)
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in text:
                fail(
                    f"accessory role token `{forbidden_token}` appears in KiCad artifact: "
                    f"{path.relative_to(REPO_ROOT)}"
                )


def validate_instance_plan() -> None:
    path = PB100_DIR / "PB-100-schematic-instance-plan.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    references = {row["Ref"] for row in rows}
    for output_number in range(1, 11):
        suffix = f"{100 + output_number}"
        for prefix in ("U", "Q", "F", "J"):
            expected_ref = f"{prefix}{suffix}"
            if expected_ref not in references:
                fail(f"missing output instance reference: {expected_ref}")


def validate_symbol_mpn_readiness() -> None:
    path = PB100_DIR / "PB-100-symbol-mpn-readiness.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty symbol/MPN readiness table: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SYMBOL_MPN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    seen_keys = set()
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        if not symbol_key:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing symbol key")
        if symbol_key in seen_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        seen_keys.add(symbol_key)

        critical = row["Critical"].strip().lower()
        if critical not in {"yes", "no"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Critical must be yes or no")

        primary_source = row["Primary source"].strip()
        if not primary_source:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing primary source")
        if not (
            primary_source.startswith("https://")
            or primary_source.startswith("docs/")
            or primary_source.startswith("hardware/")
        ):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: primary source must be "
                "an https URL or an internal docs/ or hardware/ path"
            )

        for column in (
            "Schematic block",
            "Function",
            "Preferred MPN or class",
            "Preferred package",
            "KiCad symbol status",
            "Footprint status",
            "Assembly/sourcing status",
            "Freeze condition",
        ):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

        if critical == "yes":
            for column in ("Alternate 1", "Alternate 2"):
                if not row[column].strip():
                    fail(
                        f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                        f"critical symbol {symbol_key} is missing {column}"
                    )
            assembly_status = row["Assembly/sourcing status"].lower()
            if "recheck" not in assembly_status and "garage-installed" not in assembly_status:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: critical symbol "
                    f"{symbol_key} must keep assembly/sourcing recheck explicit"
                )

        if row["KiCad symbol status"].strip().lower() in {"final", "locked"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol status must not be final/locked")

    missing_keys = sorted(REQUIRED_SYMBOL_KEYS - seen_keys)
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required symbol keys: "
            f"{', '.join(missing_keys)}"
        )


def validate_symbol_capture_worklist() -> None:
    path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty symbol capture worklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SYMBOL_WORKLIST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    readiness_path = PB100_DIR / "PB-100-symbol-mpn-readiness.csv"
    readiness_rows = list(csv.DictReader(readiness_path.open(newline="", encoding="utf-8")))
    readiness_keys = {row["Symbol key"].strip() for row in readiness_rows}
    critical_keys = {
        row["Symbol key"].strip()
        for row in readiness_rows
        if row["Critical"].strip().lower() == "yes"
    }

    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    open_items_text = read_text(PB100_DIR / "PB-100-symbol-open-items.md")
    worklist_keys = set()
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        if symbol_key not in readiness_keys:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                f"unknown readiness symbol key {symbol_key}"
            )
        if symbol_key in worklist_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        worklist_keys.add(symbol_key)

        concrete_symbol_name = row["Concrete symbol name"].strip()
        if not concrete_symbol_name.startswith("PB100_") or not concrete_symbol_name.endswith("_PRELIM"):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: concrete symbol name "
                "must use PB100_*_PRELIM"
            )
        if row["Library"].strip() != "PB100":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: library must be PB100")

        symbol_source = row["Symbol source"].strip()
        if not (
            symbol_source.startswith("https://")
            or symbol_source.startswith("docs/")
            or symbol_source.startswith("hardware/")
        ):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol source must be "
                "an https URL or an internal docs/ or hardware/ path"
            )

        for column in (
            "Pin evidence status",
            "Footprint dependency",
            "Instance refs",
            "Allowed action",
            "Blocked action",
            "Freeze close evidence",
        ):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

        created = "preliminary symbol created" in row["Pin evidence status"].strip().lower()
        symbol_present = f'(symbol "{concrete_symbol_name}"' in symbol_text
        if not created:
            if not row["Pin evidence status"].strip().lower().startswith("pending"):
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pending symbol status must be explicit")
            if symbol_present:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: pending symbol "
                    f"{concrete_symbol_name} is already present in PB100.kicad_sym"
                )
            if symbol_key not in open_items_text or concrete_symbol_name not in open_items_text:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: pending symbol "
                    f"{symbol_key}/{concrete_symbol_name} must be tracked in PB-100-symbol-open-items.md"
                )

    missing_worklist_keys = sorted(critical_keys - worklist_keys)
    if missing_worklist_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing critical symbol worklist keys: "
            f"{', '.join(missing_worklist_keys)}"
        )


def validate_symbol_capture_progress() -> None:
    path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    for row_number, row in enumerate(rows, 2):
        pin_status = row["Pin evidence status"].strip().lower()
        if "preliminary symbol created" not in pin_status:
            continue

        symbol_name = row["Concrete symbol name"].strip()
        marker = f'(symbol "{symbol_name}"'
        start = symbol_text.find(marker)
        if start < 0:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: worklist marks "
                f"{symbol_name} created, but symbol is missing from PB100.kicad_sym"
            )

        next_symbol = symbol_text.find('\n  (symbol "', start + 1)
        if next_symbol < 0:
            next_symbol = symbol_text.rfind("\n)")
        symbol_block = symbol_text[start:next_symbol]
        if "(in_bom no)" not in symbol_block:
            fail(f"preliminary symbol {symbol_name} must be excluded from BOM")
        if "(on_board no)" not in symbol_block:
            fail(f"preliminary symbol {symbol_name} must be excluded from board")
        if '(property "Footprint" ""' not in symbol_block:
            fail(f"preliminary symbol {symbol_name} must not lock a footprint")


def symbol_block(symbol_text: str, symbol_name: str) -> str:
    marker = f'(symbol "{symbol_name}"'
    start = symbol_text.find(marker)
    if start < 0:
        return ""
    next_symbol = symbol_text.find('\n  (symbol "', start + 1)
    if next_symbol < 0:
        next_symbol = symbol_text.rfind("\n)")
    return symbol_text[start:next_symbol]


def validate_symbol_pin_evidence() -> None:
    path = PB100_DIR / "PB-100-symbol-pin-evidence.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty symbol pin evidence table: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SYMBOL_PIN_EVIDENCE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    worklist_path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    worklist_rows = list(csv.DictReader(worklist_path.open(newline="", encoding="utf-8")))
    created_symbols = {
        row["Concrete symbol name"].strip()
        for row in worklist_rows
        if "preliminary symbol created" in row["Pin evidence status"].strip().lower()
    }

    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    evidence_by_symbol: dict[str, set[tuple[str, str]]] = {}
    for row_number, row in enumerate(rows, 2):
        symbol_name = row["Symbol name"].strip()
        pin_number = row["Pin number"].strip()
        pin_name = row["Pin name"].strip()
        source = row["Source"].strip()
        if not symbol_name or not pin_number or not pin_name:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing symbol or pin identity")
        if not (source.startswith("https://") or source.startswith("hardware/") or source.startswith("docs/")):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: source must be "
                "an https URL or an internal docs/ or hardware/ path"
            )
        for column in ("Source revision", "Package", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

        block = symbol_block(symbol_text, symbol_name)
        if not block:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol {symbol_name} is missing")

        expected_name = f'(name "{pin_name}"'
        expected_number = f'(number "{pin_number}"'
        pin_matches = [
            line
            for line in block.splitlines()
            if expected_name in line and expected_number in line
        ]
        if not pin_matches:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} "
                f"{pin_name} is not present in {symbol_name}"
            )

        evidence_by_symbol.setdefault(symbol_name, set()).add((pin_number, pin_name))

    missing_evidence = sorted(created_symbols - evidence_by_symbol.keys() - PIN_MAP_EVIDENCE_SYMBOLS)
    if missing_evidence:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing pin evidence for created symbols: "
            f"{', '.join(missing_evidence)}"
        )


def validate_jpb1_symbol_from_pin_map() -> None:
    worklist_path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    worklist_rows = list(csv.DictReader(worklist_path.open(newline="", encoding="utf-8")))
    created = any(
        row["Concrete symbol name"].strip() == "PB100_JPB1_100PIN_PRELIM"
        and "preliminary symbol created" in row["Pin evidence status"].strip().lower()
        for row in worklist_rows
    )
    if not created:
        return

    pin_map_path = PB100_DIR / "PB-100-b2b-pin-map.csv"
    validate_csv(pin_map_path)
    pin_map_rows = list(csv.DictReader(pin_map_path.open(newline="", encoding="utf-8")))
    if len(pin_map_rows) != 100:
        fail(f"{pin_map_path.relative_to(REPO_ROOT)} must contain exactly 100 JPB1 pins")

    symbol_name = "PB100_JPB1_100PIN_PRELIM"
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    block = symbol_block(symbol_text, symbol_name)
    if not block:
        fail(f"created B2B symbol is missing from PB100.kicad_sym: {symbol_name}")

    for row in pin_map_rows:
        pin_number = row["Pin"].strip()
        pin_name = row["Net"].strip()
        expected_name = f'(name "{pin_name}"'
        expected_number = f'(number "{pin_number}"'
        if not any(expected_name in line and expected_number in line for line in block.splitlines()):
            fail(f"{symbol_name} is missing JPB1 pin {pin_number} {pin_name}")


def validate_instance_symbol_map() -> None:
    path = PB100_DIR / "PB-100-schematic-instance-symbol-map.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty instance-symbol map: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INSTANCE_SYMBOL_MAP_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    instance_path = PB100_DIR / "PB-100-schematic-instance-plan.csv"
    instance_rows = list(csv.DictReader(instance_path.open(newline="", encoding="utf-8")))
    instance_refs = {row["Ref"].strip() for row in instance_rows}
    map_refs = {row["Ref"].strip() for row in rows}
    missing_refs = sorted(instance_refs - map_refs)
    extra_refs = sorted(map_refs - instance_refs)
    if missing_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing instance refs: "
            f"{', '.join(missing_refs)}"
        )
    if extra_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} has refs not in instance plan: "
            f"{', '.join(extra_refs)}"
        )

    readiness_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-mpn-readiness.csv").open(newline="", encoding="utf-8"))
    )
    readiness_keys = {row["Symbol key"].strip() for row in readiness_rows}
    worklist_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-capture-worklist.csv").open(newline="", encoding="utf-8"))
    )
    worklist_by_key = {row["Symbol key"].strip(): row for row in worklist_rows}
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")

    for row_number, row in enumerate(rows, 2):
        ref = row["Ref"].strip()
        symbol_key = row["Symbol key"].strip()
        symbol_name = row["Concrete symbol name"].strip()
        symbol_state = row["Symbol state"].strip()
        if symbol_key not in readiness_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown symbol key {symbol_key}")
        worklist_row = worklist_by_key.get(symbol_key)
        if worklist_row is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol key {symbol_key} is missing worklist row")
        if symbol_name != worklist_row["Concrete symbol name"].strip():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} maps to {symbol_name}, "
                f"but worklist uses {worklist_row['Concrete symbol name'].strip()}"
            )
        if symbol_state not in {"Created", "Pending"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Symbol state must be Created or Pending")
        symbol_present = f'(symbol "{symbol_name}"' in symbol_text
        if symbol_state == "Created" and not symbol_present and symbol_name not in PIN_MAP_EVIDENCE_SYMBOLS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: created symbol is missing: {symbol_name}")
        if symbol_state == "Pending" and symbol_present:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pending symbol is already present: {symbol_name}")
        if ref == "Q102" and "OUT2_ESCAPE_FET" not in row["Notes"]:
            fail("Q102 instance-symbol map must preserve the OUT2 escape-FET note")


def validate_sheet_reference_map() -> None:
    path = PB100_DIR / "PB-100-schematic-sheet-reference-map.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty sheet-reference map: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SHEET_REFERENCE_MAP_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    instance_map_path = PB100_DIR / "PB-100-schematic-instance-symbol-map.csv"
    instance_rows = list(csv.DictReader(instance_map_path.open(newline="", encoding="utf-8")))
    symbol_by_ref = {row["Ref"].strip(): row["Symbol key"].strip() for row in instance_rows}
    expected_refs = set(symbol_by_ref)
    seen_refs = set()
    allowed_virtual_sheets = {"cross-sheet-review"}
    allowed_statuses = {"Planned", "Pending symbol", "Review-defined"}

    for row_number, row in enumerate(rows, 2):
        sheet_file = row["Sheet file"].strip()
        ref = row["Ref"].strip()
        symbol_key = row["Symbol key"].strip()
        capture_status = row["Capture status"].strip()
        if ref in seen_refs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate ref {ref}")
        seen_refs.add(ref)
        if ref not in symbol_by_ref:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown instance ref {ref}")
        if symbol_key != symbol_by_ref[ref]:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} uses {symbol_key}, "
                f"but instance-symbol map uses {symbol_by_ref[ref]}"
            )
        if capture_status not in allowed_statuses:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid capture status {capture_status}")
        if not row["Notes"].strip():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty Notes")
        if sheet_file not in allowed_virtual_sheets:
            sheet_path = KICAD_DIR / "sheets" / sheet_file
            if not sheet_path.exists():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing sheet file {sheet_file}")
        if ref == "Q1" and capture_status != "Pending symbol":
            fail("Q1 must remain marked Pending symbol while INPUT_REVERSE_FET is open")
        if ref == "TP1..TPn" and sheet_file != "cross-sheet-review":
            fail("TP1..TPn must remain cross-sheet-review until exact test point locations close")

    missing_refs = sorted(expected_refs - seen_refs)
    extra_refs = sorted(seen_refs - expected_refs)
    if missing_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing refs from instance-symbol map: "
            f"{', '.join(missing_refs)}"
        )
    if extra_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} has refs not in instance-symbol map: "
            f"{', '.join(extra_refs)}"
        )


def validate_kicad_sheet_manifest() -> None:
    path = PB100_DIR / "PB-100-kicad-sheet-manifest.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty KiCad sheet manifest: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in KICAD_SHEET_MANIFEST_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    expected_sheet_files = {"PB-100.kicad_sch"} | {
        sheet_path.name for sheet_path in sorted((KICAD_DIR / "sheets").glob("*.kicad_sch"))
    }
    manifest_sheet_files = {row["Sheet file"].strip() for row in rows}
    missing_sheets = sorted(expected_sheet_files - manifest_sheet_files)
    extra_sheets = sorted(manifest_sheet_files - expected_sheet_files)
    if missing_sheets:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing KiCad sheets: "
            f"{', '.join(missing_sheets)}"
        )
    if extra_sheets:
        fail(
            f"{path.relative_to(REPO_ROOT)} lists unknown KiCad sheets: "
            f"{', '.join(extra_sheets)}"
        )

    allowed_kinds = {"top", "child"}
    allowed_statuses = {"Scaffold", "Template scaffold"}
    for row_number, row in enumerate(rows, 2):
        sheet_file = row["Sheet file"].strip()
        sheet_kind = row["Sheet kind"].strip()
        if sheet_kind not in allowed_kinds:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid sheet kind {sheet_kind}")
        if row["Status"].strip() not in allowed_statuses:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid sheet status {row['Status'].strip()}")
        for column in ("Purpose", "Primary artifacts", "Capture gate"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if sheet_kind == "top" and sheet_file != "PB-100.kicad_sch":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: only PB-100.kicad_sch may be top")
        if sheet_kind == "child" and not (KICAD_DIR / "sheets" / sheet_file).exists():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: child sheet file is missing: {sheet_file}")

    sheet_reference_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-sheet-reference-map.csv").open(newline="", encoding="utf-8"))
    )
    referenced_sheets = {
        row["Sheet file"].strip()
        for row in sheet_reference_rows
        if row["Sheet file"].strip() != "cross-sheet-review"
    }
    missing_referenced = sorted(referenced_sheets - manifest_sheet_files)
    if missing_referenced:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing sheets used by sheet-reference map: "
            f"{', '.join(missing_referenced)}"
        )


def validate_net_domain_plan() -> None:
    path = PB100_DIR / "PB-100-schematic-net-domain-plan.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty schematic net-domain plan: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in NET_DOMAIN_PLAN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    sheet_manifest_path = PB100_DIR / "PB-100-kicad-sheet-manifest.csv"
    sheet_manifest_rows = list(csv.DictReader(sheet_manifest_path.open(newline="", encoding="utf-8")))
    manifest_sheets = {row["Sheet file"].strip() for row in sheet_manifest_rows}
    seen_patterns = set()
    for row_number, row in enumerate(rows, 2):
        net_pattern = row["Net pattern"].strip()
        if not net_pattern:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty Net pattern")
        if net_pattern in seen_patterns:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Net pattern {net_pattern}")
        seen_patterns.add(net_pattern)
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in net_pattern:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net pattern {net_pattern}")
        for column in ("Domain", "Direction", "Default state", "Safety rule"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        primary_sheet = row["Primary sheet"].strip()
        if primary_sheet not in manifest_sheets:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown Primary sheet {primary_sheet}")

    missing_patterns = sorted(REQUIRED_NET_PATTERNS - seen_patterns)
    if missing_patterns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required net patterns: "
            f"{', '.join(missing_patterns)}"
        )

    can_tx_rows = [row for row in rows if row["Net pattern"].strip() == "CAN1_TX_ROUTE"]
    if len(can_tx_rows) != 1:
        fail("CAN1_TX_ROUTE must appear exactly once in schematic net-domain plan")
    can_tx_row = can_tx_rows[0]
    default_state = can_tx_row["Default state"].lower()
    safety_rule = can_tx_row["Safety rule"].lower()
    if "dnp/open" not in default_state:
        fail("CAN1_TX_ROUTE default state must remain DNP/open")
    if "future adr" not in safety_rule:
        fail("CAN1_TX_ROUTE safety rule must require a future ADR")


def validate_bom_symbol_map() -> None:
    path = REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty PB-100 symbol BOM map: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOM_SYMBOL_MAP_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    readiness_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-mpn-readiness.csv").open(newline="", encoding="utf-8"))
    )
    readiness_keys = {row["Symbol key"].strip() for row in readiness_rows}
    critical_keys = {
        row["Symbol key"].strip()
        for row in readiness_rows
        if row["Critical"].strip().lower() == "yes"
    }

    bom_items_by_file: dict[str, set[str]] = {}
    for bom_file in ALLOWED_BOM_FILES:
        bom_path = REPO_ROOT / "production" / "bom" / bom_file
        validate_csv(bom_path)
        bom_rows = list(csv.DictReader(bom_path.open(newline="", encoding="utf-8")))
        bom_items_by_file[bom_file] = {row["Item"].strip() for row in bom_rows}

    seen_keys = set()
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        bom_file = row["BOM file"].strip()
        bom_item = row["BOM item"].strip()
        if symbol_key not in readiness_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown symbol key {symbol_key}")
        if symbol_key in seen_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        seen_keys.add(symbol_key)
        if bom_file not in ALLOWED_BOM_FILES:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unsupported BOM file {bom_file}")
        if bom_item not in bom_items_by_file[bom_file]:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: BOM item {bom_item} "
                f"is missing from production/bom/{bom_file}"
            )
        for column in ("Qty basis", "Population", "Assembly owner", "Status", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if bom_file == "factory_bom_draft.csv" and row["Assembly owner"].strip() != "Factory":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: factory BOM row must use Factory owner")
        if bom_file == "garage_bom_draft.csv" and row["Assembly owner"].strip() != "Garage":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: garage BOM row must use Garage owner")

    missing_keys = sorted(readiness_keys - seen_keys)
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing symbol keys: "
            f"{', '.join(missing_keys)}"
        )

    missing_critical = sorted(critical_keys - seen_keys)
    if missing_critical:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing critical symbol keys: "
            f"{', '.join(missing_critical)}"
        )

    can1_rows = [row for row in rows if row["Symbol key"].strip() == "CAN1_TX_DISABLE"]
    if len(can1_rows) != 1:
        fail("CAN1_TX_DISABLE must appear exactly once in PB-100 symbol BOM map")
    can1_row = can1_rows[0]
    if "dnp/open" not in can1_row["Population"].lower() and "dnp/open" not in can1_row["Notes"].lower():
        fail("CAN1_TX_DISABLE BOM mapping must keep DNP/open explicit")


def validate_schematic_readiness_dashboard() -> None:
    path = PB100_DIR / "PB-100-schematic-readiness-dashboard.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty schematic readiness dashboard: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SCHEMATIC_READINESS_DASHBOARD_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    seen_areas = set()
    rows_by_area: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        area = row["Area"].strip()
        status = row["Status"].strip()
        if not area:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing Area")
        if area in seen_areas:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Area {area}")
        seen_areas.add(area)
        rows_by_area[area] = row
        if status not in ALLOWED_DASHBOARD_STATUSES:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Status {status}")
        for column in ("Evidence", "Machine check", "Remaining close work"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

    missing_areas = sorted(REQUIRED_READINESS_AREAS - seen_areas)
    if missing_areas:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing readiness areas: "
            f"{', '.join(missing_areas)}"
        )

    if rows_by_area["Architecture baseline"]["Status"].strip() != "Closed":
        fail("Architecture baseline must remain Closed in schematic readiness dashboard")
    if rows_by_area["PB-100 requirements"]["Status"].strip() != "Closed":
        fail("PB-100 requirements must remain Closed in schematic readiness dashboard")
    if rows_by_area["Layout authorization"]["Status"].strip() != "Blocked":
        fail("Layout authorization must remain Blocked before schematic freeze")
    if "schematic freeze" not in rows_by_area["Layout authorization"]["Remaining close work"].lower():
        fail("Layout authorization close work must reference schematic freeze")

    symbol_row = rows_by_area["Symbol readiness"]
    if symbol_row["Status"].strip() != "Conditional":
        fail("Symbol readiness must remain Conditional while pending symbols exist")
    if "INPUT_REVERSE_FET" not in symbol_row["Remaining close work"]:
        fail("Symbol readiness must mention pending INPUT_REVERSE_FET close work")

    can_row = rows_by_area["CAN1 safety"]
    can_text = " ".join(can_row[column] for column in SCHEMATIC_READINESS_DASHBOARD_COLUMNS).lower()
    if "dnp/open" not in can_text or "future adr" not in can_text:
        fail("CAN1 safety dashboard row must keep DNP/open and future ADR explicit")


def freeze_checklist_gates_by_status() -> dict[str, str]:
    text = read_text(PB100_DIR / "PB-100-schematic-freeze-checklist.md")
    gates_by_status: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] in {"Gate", "---"}:
            continue
        gate, status = cells[0], cells[1]
        if status in {"Closed", "Conditional", "Open", "Blocked"}:
            gates_by_status[gate] = status
    return gates_by_status


def validate_schematic_freeze_gap_register() -> None:
    path = PB100_DIR / "PB-100-schematic-freeze-gap-register.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty schematic freeze gap register: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SCHEMATIC_FREEZE_GAP_REGISTER_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    gates_by_status = freeze_checklist_gates_by_status()
    conditional_gates = {gate for gate, status in gates_by_status.items() if status == "Conditional"}
    seen_gates = set()
    rows_by_gate: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        gate = row["Gate"].strip()
        status = row["Status"].strip()
        if gate in seen_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Gate {gate}")
        seen_gates.add(gate)
        rows_by_gate[gate] = row
        if gate not in gates_by_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown freeze checklist gate {gate}")
        if status != "Conditional":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: gap register rows must remain Conditional")
        if gates_by_status[gate] != "Conditional":
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: gate {gate} is "
                f"{gates_by_status[gate]} in freeze checklist but present in gap register"
            )
        for column in (
            "Close evidence required",
            "Primary gap artifact",
            "Validator coverage",
            "Next close action",
        ):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

    missing_gates = sorted(conditional_gates - seen_gates)
    extra_gates = sorted(seen_gates - conditional_gates)
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing conditional gates: "
            f"{', '.join(missing_gates)}"
        )
    if extra_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} has non-conditional gates: "
            f"{', '.join(extra_gates)}"
        )

    can_text = " ".join(rows_by_gate["CAN1 safety policy"].values()).lower()
    if "dnp/open" not in can_text or "default" not in can_text:
        fail("CAN1 safety policy gap must keep DNP/open default explicit")
    input_text = " ".join(rows_by_gate["Input reverse protection"].values())
    if "Q1" not in input_text or "40 A" not in input_text or "TOLL" not in input_text:
        fail("Input reverse protection gap must keep Q1 TOLL and 40 A review explicit")
    factory_text = " ".join(rows_by_gate["Factory assembly readiness"].values()).lower()
    if "assembly" not in factory_text or "alternat" not in factory_text:
        fail("Factory assembly readiness gap must keep assembly and alternatives explicit")
    garage_text = " ".join(rows_by_gate["Garage assembly readiness"].values()).lower()
    if "garage" not in garage_text or "user" not in garage_text:
        fail("Garage assembly readiness gap must keep garage/user scope explicit")


def validate_output_channel_pin_contract() -> None:
    path = PB100_DIR / "PB-100-output-channel-pin-contract.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output channel pin contract: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_CHANNEL_PIN_CONTRACT_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    output_matrix_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8"))
    )
    expected_outputs = {row["Output"].strip() for row in output_matrix_rows}
    instance_map_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-instance-symbol-map.csv").open(newline="", encoding="utf-8"))
    )
    symbol_key_by_ref = {row["Ref"].strip(): row["Symbol key"].strip() for row in instance_map_rows}
    b2b_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    b2b_nets = {row["Net"].strip() for row in b2b_rows}

    seen_outputs = set()
    for row_number, row in enumerate(rows, 2):
        output = row["Output"].strip()
        if output in seen_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output {output}")
        seen_outputs.add(output)
        if output not in expected_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output {output}")
        try:
            output_number = int(output.removeprefix("OUT"))
        except ValueError:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid output name {output}")

        expected_refs = {
            "Controller ref": (f"U{100 + output_number}", "HS_CTRL"),
            "Switch ref": (f"Q{100 + output_number}", "OUT_FET"),
            "Fuse ref": (f"F{100 + output_number}", "OUTPUT_FUSE_HOLDER"),
            "Connector ref": (f"J{100 + output_number}", "OUTPUT_CONNECTOR"),
        }
        for column, (expected_ref, expected_key) in expected_refs.items():
            actual_ref = row[column].strip()
            if actual_ref != expected_ref:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {column} must be "
                    f"{expected_ref}, got {actual_ref}"
                )
            actual_key = symbol_key_by_ref.get(actual_ref)
            if actual_key != expected_key:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {actual_ref} must map to "
                    f"{expected_key}, got {actual_key}"
                )

        expected_nets = {
            "Control net": f"{output}_CTL",
            "Fault net": f"{output}_FLT",
            "Current net": f"{output}_IMON",
            "Load net": f"{output}_LOAD",
            "Fused net": f"{output}_FUSED",
        }
        for column, expected_net in expected_nets.items():
            actual_net = row[column].strip()
            if actual_net != expected_net:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {column} must be "
                    f"{expected_net}, got {actual_net}"
                )
            for forbidden_token in FORBIDDEN_ROLE_TOKENS:
                if forbidden_token in actual_net:
                    fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net {actual_net}")

        for connector_net in (row["Control net"].strip(), row["Fault net"].strip(), row["Current net"].strip()):
            if connector_net not in b2b_nets:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {connector_net} "
                    "is missing from PB-100-b2b-pin-map.csv"
                )

        default_state = row["Default state"].strip().lower()
        safety_rule = row["Safety rule"].strip().lower()
        if "off" not in default_state:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: default state must be off")
        if "configuration" not in safety_rule:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: safety rule must preserve configuration mapping")
        if output == "OUT2" and "soa" not in safety_rule:
            fail("OUT2 output pin contract must keep SOA close work explicit")

    missing_outputs = sorted(expected_outputs - seen_outputs)
    extra_outputs = sorted(seen_outputs - expected_outputs)
    if missing_outputs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing outputs: "
            f"{', '.join(missing_outputs)}"
        )
    if extra_outputs:
        fail(
            f"{path.relative_to(REPO_ROOT)} has outputs not in output matrix: "
            f"{', '.join(extra_outputs)}"
        )


def validate_output_controller_pin_template() -> None:
    path = PB100_DIR / "PB-100-output-controller-pin-template.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output controller pin template: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    evidence_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-pin-evidence.csv").open(newline="", encoding="utf-8"))
    )
    evidence_pins = {
        row["Pin number"].strip(): row["Pin name"].strip()
        for row in evidence_rows
        if row["Symbol name"].strip() == OUTPUT_CONTROLLER_SYMBOL
    }
    if not evidence_pins:
        fail(f"missing pin evidence for {OUTPUT_CONTROLLER_SYMBOL}")

    seen_pins = set()
    net_patterns = set()
    for row_number, row in enumerate(rows, 2):
        pin_number = row["Pin number"].strip()
        pin_name = row["Pin name"].strip()
        net_pattern = row["Net pattern"].strip()
        for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if pin_number in seen_pins:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate pin {pin_number}")
        seen_pins.add(pin_number)
        expected_pin_name = evidence_pins.get(pin_number)
        if expected_pin_name is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} is not in pin evidence")
        if pin_name != expected_pin_name:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} must be "
                f"{expected_pin_name}, got {pin_name}"
            )
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in net_pattern:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net pattern {net_pattern}")
        if not (
            net_pattern.startswith("OUTn_")
            or net_pattern in {"GND", "NC", "VBAT_PROT"}
        ):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: unsupported output-controller "
                f"net pattern {net_pattern}"
            )
        if pin_name == "N.C." and net_pattern != "NC":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: N.C. pin must use NC net pattern")
        if pin_name == "GND" and net_pattern != "GND":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: GND pin must use GND net pattern")
        if pin_name == "VS" and net_pattern != "VBAT_PROT":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: VS pin must use VBAT_PROT")
        if "final" in row["Default state"].lower() and "not final" not in row["Default state"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: default state must not lock final values")
        if "schematic review" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic review")
        net_patterns.add(net_pattern)

    missing_pins = sorted(evidence_pins.keys() - seen_pins, key=lambda value: int(value))
    extra_pins = sorted(seen_pins - evidence_pins.keys(), key=lambda value: int(value))
    if missing_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing controller pins: "
            f"{', '.join(missing_pins)}"
        )
    if extra_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} has pins not in evidence: "
            f"{', '.join(extra_pins)}"
        )
    for required_pattern in ("OUTn_CTL", "OUTn_FLT", "OUTn_IMON", "OUTn_SRC", "OUTn_PU", "OUTn_PD", "VBAT_PROT"):
        if required_pattern not in net_patterns:
            fail(
                f"{path.relative_to(REPO_ROOT)} is missing required output-controller "
                f"net pattern {required_pattern}"
            )


def sort_pin_number(pin_number: str) -> tuple[int, str]:
    return (0, f"{int(pin_number):04d}") if pin_number.isdigit() else (1, pin_number)


def validate_component_pin_template(
    file_name: str,
    symbol_name: str,
    allowed_net_patterns: set[str],
    required_net_patterns: set[str],
) -> None:
    path = PB100_DIR / file_name
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty component pin template: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    evidence_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-pin-evidence.csv").open(newline="", encoding="utf-8"))
    )
    evidence_pins = {
        row["Pin number"].strip(): row["Pin name"].strip()
        for row in evidence_rows
        if row["Symbol name"].strip() == symbol_name
    }
    if not evidence_pins:
        fail(f"missing pin evidence for {symbol_name}")

    seen_pins = set()
    net_patterns = set()
    for row_number, row in enumerate(rows, 2):
        pin_number = row["Pin number"].strip()
        pin_name = row["Pin name"].strip()
        net_pattern = row["Net pattern"].strip()
        for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if pin_number in seen_pins:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate pin {pin_number}")
        seen_pins.add(pin_number)
        expected_pin_name = evidence_pins.get(pin_number)
        if expected_pin_name is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} is not in pin evidence")
        if pin_name != expected_pin_name:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} must be "
                f"{expected_pin_name}, got {pin_name}"
            )
        if net_pattern not in allowed_net_patterns:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: unsupported net pattern "
                f"{net_pattern}"
            )
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in net_pattern:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net pattern {net_pattern}")
        if "final" in row["Default state"].lower() and "not final" not in row["Default state"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: default state must not lock final values")
        if "schematic review" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic review")
        net_patterns.add(net_pattern)

    missing_pins = sorted(evidence_pins.keys() - seen_pins, key=sort_pin_number)
    extra_pins = sorted(seen_pins - evidence_pins.keys(), key=sort_pin_number)
    if missing_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing pins for {symbol_name}: "
            f"{', '.join(missing_pins)}"
        )
    if extra_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} has pins not in evidence for {symbol_name}: "
            f"{', '.join(extra_pins)}"
        )

    missing_patterns = sorted(required_net_patterns - net_patterns)
    if missing_patterns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required net patterns: "
            f"{', '.join(missing_patterns)}"
        )


def validate_input_and_power_pin_templates() -> None:
    validate_component_pin_template(
        "PB-100-input-controller-pin-template.csv",
        "PB100_LM74700QDBVRQ1_PRELIM",
        {
            "LM74700_VCAP",
            "GND",
            "INPUT_PROT_EN",
            "VBAT_REV_PROT",
            "INPUT_FET_GATE",
            "VBAT_RAW",
        },
        {"VBAT_RAW", "VBAT_REV_PROT", "INPUT_FET_GATE", "INPUT_PROT_EN"},
    )
    validate_component_pin_template(
        "PB-100-current-monitor-pin-template.csv",
        "PB100_INA228_Q1_PRELIM",
        {
            "IIN_MON_A1",
            "IIN_MON_A0",
            "PB_I2C_INT",
            "PB_I2C_SDA",
            "PB_I2C_SCL",
            "LB_3V3_IO",
            "GND",
            "VBAT_PROT",
            "IIN_SHUNT_LO",
            "IIN_SHUNT_HI",
        },
        {"IIN_SHUNT_HI", "IIN_SHUNT_LO", "PB_I2C_SDA", "PB_I2C_SCL", "VBAT_PROT"},
    )
    validate_component_pin_template(
        "PB-100-logic-buck-pin-template.csv",
        "PB100_LM5164QDDATQ1_PRELIM",
        {
            "GND",
            "VBAT_PROT",
            "BUCK_EN_UVLO",
            "BUCK_RON_SET",
            "BUCK_FB",
            "PB_PWR_GOOD",
            "BUCK_BST",
            "BUCK_SW",
        },
        {"VBAT_PROT", "BUCK_EN_UVLO", "BUCK_FB", "PB_PWR_GOOD", "BUCK_SW"},
    )


def validate_input_protection_pin_contract() -> None:
    path = PB100_DIR / "PB-100-input-protection-pin-contract.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input protection pin contract: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_PROTECTION_PIN_CONTRACT_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    instance_map_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-instance-symbol-map.csv").open(newline="", encoding="utf-8"))
    )
    instance_by_ref = {row["Ref"].strip(): row for row in instance_map_rows}
    required_refs = {"J1", "D1", "U1", "Q1", "RSH1", "U2"}
    required_nets = {
        "VBAT_RAW",
        "GND",
        "VBAT_PROT",
        "INPUT_FET_GATE",
        "VBAT_REV_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "IIN_SENSE",
        "VBAT_SENSE",
    }
    seen_refs = set()
    seen_nets = set()
    q1_rows = []
    for row_number, row in enumerate(rows, 2):
        ref = row["Ref"].strip()
        symbol_key = row["Symbol key"].strip()
        concrete_symbol_name = row["Concrete symbol name"].strip()
        planned_net = row["Planned net"].strip()
        for column in ("Ref", "Symbol key", "Concrete symbol name", "Interface point", "Planned net", "Direction", "Default state", "Freeze dependency"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        instance_row = instance_by_ref.get(ref)
        if instance_row is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown instance ref {ref}")
        if symbol_key != instance_row["Symbol key"].strip():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} uses {symbol_key}, "
                f"but instance-symbol map uses {instance_row['Symbol key'].strip()}"
            )
        if concrete_symbol_name != instance_row["Concrete symbol name"].strip():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} uses {concrete_symbol_name}, "
                f"but instance-symbol map uses {instance_row['Concrete symbol name'].strip()}"
            )
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in planned_net:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in planned net {planned_net}")
        seen_refs.add(ref)
        seen_nets.add(planned_net)
        if ref == "Q1":
            q1_rows.append(row)

    missing_refs = sorted(required_refs - seen_refs)
    if missing_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input refs: "
            f"{', '.join(missing_refs)}"
        )
    missing_nets = sorted(required_nets - seen_nets)
    if missing_nets:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input planned nets: "
            f"{', '.join(missing_nets)}"
        )
    if not q1_rows:
        fail("input protection pin contract must include Q1 pending reverse FET rows")
    q1_state = instance_by_ref["Q1"]["Symbol state"].strip()
    if q1_state != "Pending":
        fail("Q1 must remain Pending until INPUT_REVERSE_FET symbol evidence closes")
    for row in q1_rows:
        close_text = " ".join(row[column] for column in ("Default state", "Freeze dependency"))
        if "Pending" not in close_text or "TOLL" not in close_text or "40 A" not in close_text:
            fail("Q1 input protection rows must keep pending TOLL and 40 A review explicit")


def validate_logic_power_design_placeholders() -> None:
    path = PB100_DIR / "PB-100-logic-power-design-placeholders.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic power design placeholders: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_DESIGN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    seen_items = set()
    refs_or_nets = set()
    for row_number, row in enumerate(rows, 2):
        item = row["Item"].strip()
        if not item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing Item")
        if item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Item {item}")
        seen_items.add(item)
        refs_or_nets.add(row["Ref or net"].strip())
        for column in ("Ref or net", "Design state", "Value status", "Freeze dependency", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

        value_status = row["Value status"].strip().lower()
        if "final" in value_status and "not final" not in value_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: logic power value must not be final before review")
        for blocked_word in ("locked", "released"):
            if blocked_word in value_status:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: logic power value "
                    f"must not be {blocked_word} before review"
                )
        if "tbd" not in value_status and "not final" not in value_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Value status must remain TBD/not final")

    missing_items = sorted(REQUIRED_LOGIC_POWER_ITEMS - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic power items: "
            f"{', '.join(missing_items)}"
        )
    for required_ref_or_net in ("U3", "L1", "VBAT_PROT", "PB_5V_OUT", "PB_PWR_GOOD"):
        if required_ref_or_net not in refs_or_nets:
            fail(
                f"{path.relative_to(REPO_ROOT)} is missing required logic power "
                f"ref/net {required_ref_or_net}"
            )


def validate_not_final_value_status(path: Path, row_number: int, value_status: str) -> None:
    normalized = value_status.strip().lower()
    if "tbd" not in normalized and "not final" not in normalized:
        fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Value status must remain TBD/not final")
    if "final" in normalized and "not final" not in normalized:
        fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: value must not be final before schematic review")
    for blocked_word in ("locked", "released", "approved"):
        if blocked_word in normalized:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: value must not be "
                f"{blocked_word} before schematic review"
            )


def validate_no_role_tokens_in_row(path: Path, row_number: int, row: dict[str, str]) -> None:
    row_text = " ".join(row.values())
    for forbidden_token in FORBIDDEN_ROLE_TOKENS:
        if forbidden_token in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token {forbidden_token} is not allowed")


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
        validate_not_final_value_status(path, row_number, row["Value status"])
        if "schematic freeze" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")
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
        validate_not_final_value_status(path, row_number, row["Value status"])
        if "schematic freeze" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")
        for net_name in [part.strip() for part in row["Related net"].split(";")]:
            if net_name not in allowed_nets:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown input-power net {net_name}")
        if design_item == "Q1 package and copper path":
            row_text = " ".join(row.values())
            if "TOLL" not in row_text or "40 A" not in row_text:
                fail("Q1 package and copper path must keep TOLL and 40 A review explicit")
        if design_item == "Shunt value and power rating" and "four-terminal" not in " ".join(row.values()).lower():
            fail("input shunt design row must preserve four-terminal requirement")

    missing_items = sorted(REQUIRED_INPUT_POWER_ITEMS - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input-power design items: "
            f"{', '.join(missing_items)}"
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
        if "enabled by default" in row_text or "default-populated tx" in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: CAN1 TX must not be enabled/populated by default")
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


def validate_assembly_sourcing_recheck() -> None:
    path = REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty assembly sourcing recheck register: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in ASSEMBLY_SOURCING_RECHECK_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    readiness_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-mpn-readiness.csv").open(newline="", encoding="utf-8"))
    )
    critical_readiness = {
        row["Symbol key"].strip(): row
        for row in readiness_rows
        if row["Critical"].strip().lower() == "yes"
    }
    bom_rows = list(
        csv.DictReader((REPO_ROOT / "production" / "bom" / "pb100_symbol_bom_map.csv").open(newline="", encoding="utf-8"))
    )
    bom_owner_by_key = {row["Symbol key"].strip(): row["Assembly owner"].strip() for row in bom_rows}

    seen_keys = set()
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        if symbol_key in seen_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        seen_keys.add(symbol_key)
        if symbol_key not in critical_readiness:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol key {symbol_key} is not critical readiness key")
        expected_owner = bom_owner_by_key.get(symbol_key)
        if row["Assembly owner"].strip() != expected_owner:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: assembly owner must be "
                f"{expected_owner}, got {row['Assembly owner'].strip()}"
            )
        for column in ASSEMBLY_SOURCING_RECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if "schematic freeze" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic freeze")
        row_text = " ".join(row.values()).lower()
        if symbol_key == "CAN1_TX_DISABLE":
            if "dnp/open" not in row_text or "no default-populated tx" not in row_text:
                fail("CAN1_TX_DISABLE sourcing row must keep DNP/open and no default-populated TX explicit")
        else:
            if "recheck" not in row_text:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: sourcing row must keep recheck explicit")
        if row["Assembly owner"].strip() == "Factory":
            if row["Factory action"].strip() == "N/A":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: factory row needs Factory action")
            if row["Garage action"].strip() != "N/A":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: factory row must use N/A Garage action")
        elif row["Assembly owner"].strip() == "Garage":
            if row["Garage action"].strip() == "N/A":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: garage row needs Garage action")
            if row["Factory action"].strip() != "N/A":
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: garage row must use N/A Factory action")
        else:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid assembly owner {row['Assembly owner'].strip()}")
        if "alternat" not in row["Alternate coverage"].lower() and symbol_key != "CAN1_TX_DISABLE":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: alternate coverage must remain explicit")
        if symbol_key == "INPUT_REVERSE_FET":
            if "toll" not in row_text or "40 a" not in row_text:
                fail("INPUT_REVERSE_FET sourcing row must keep TOLL and 40 A review explicit")

    missing_keys = sorted(critical_readiness.keys() - seen_keys)
    extra_keys = sorted(seen_keys - critical_readiness.keys())
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing critical sourcing keys: "
            f"{', '.join(missing_keys)}"
        )
    if extra_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} has non-critical sourcing keys: "
            f"{', '.join(extra_keys)}"
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

    conditional_gates = {
        gate for gate, status in freeze_checklist_gates_by_status().items() if status == "Conditional"
    }
    seen_test_ids = set()
    gates_with_tests: dict[str, list[dict[str, str]]] = {gate: [] for gate in conditional_gates}
    allowed_phases = {"Schematic review", "Schematic plus bench", "Production review"}
    for row_number, row in enumerate(rows, 2):
        test_id = row["Test ID"].strip()
        freeze_gate = row["Freeze gate"].strip()
        if test_id in seen_test_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Test ID {test_id}")
        seen_test_ids.add(test_id)
        if not test_id.startswith("PBVAL-"):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Test ID must start with PBVAL-")
        if freeze_gate not in conditional_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown or non-conditional freeze gate {freeze_gate}")
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
        if freeze_gate == "Input reverse protection":
            if "q1" not in row_text or "40 a" not in row_text:
                fail("Input reverse validation trace must keep Q1 and 40 A explicit")
        if freeze_gate == "Factory assembly readiness" and "sourcing recheck" not in row_text:
            fail("Factory assembly validation trace must require sourcing recheck")
        if freeze_gate == "Garage assembly readiness" and "garage" not in row_text:
            fail("Garage assembly validation trace must keep garage scope explicit")
        gates_with_tests[freeze_gate].append(row)

    missing_gates = sorted(gate for gate, gate_rows in gates_with_tests.items() if not gate_rows)
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing validation rows for gates: "
            f"{', '.join(missing_gates)}"
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
            if row["Capture status"].strip() != "Blocked pending symbol":
                fail("Q1 capture work must remain Blocked pending symbol")
            if "INPUT_REVERSE_FET" not in row_text or "TOLL" not in row_text:
                fail("Q1 capture work must keep INPUT_REVERSE_FET and TOLL evidence blocker explicit")
        if work_item == "CAP-CAN1":
            row_text = " ".join(row.values()).lower()
            if "dnp/open" not in row_text or "future adr" not in row_text:
                fail("CAN1 capture work must keep DNP/open and future ADR explicit")
        if work_item == "CAP-TP" and "footprint" not in row["Blocker"].lower():
            fail("test point capture work must keep footprint/placement blocker explicit")

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

    allowed_statuses = {"Frozen", "Ready", "Conditional", "Open"}
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
        if hook.startswith("validate_") and hook not in globals():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown validation hook {hook}")

    missing_artifacts = sorted(REQUIRED_RELEASE_MANIFEST_ARTIFACTS - seen_artifacts)
    if missing_artifacts:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing release artifacts: "
            f"{', '.join(missing_artifacts)}"
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


def main() -> int:
    csv_paths = sorted(PB100_DIR.glob("*.csv")) + sorted((REPO_ROOT / "production" / "bom").glob("*.csv"))
    for csv_path in csv_paths:
        validate_csv(csv_path)
    validate_kicad_scaffold()
    validate_kicad_cli_checks()
    validate_symbol_library()
    validate_kicad_no_role_tokens()
    validate_instance_plan()
    validate_symbol_mpn_readiness()
    validate_symbol_capture_worklist()
    validate_symbol_capture_progress()
    validate_symbol_pin_evidence()
    validate_jpb1_symbol_from_pin_map()
    validate_instance_symbol_map()
    validate_sheet_reference_map()
    validate_kicad_sheet_manifest()
    validate_net_domain_plan()
    validate_bom_symbol_map()
    validate_schematic_readiness_dashboard()
    validate_schematic_freeze_gap_register()
    validate_schematic_capture_work_queue()
    validate_review_release_manifest()
    validate_output_channel_pin_contract()
    validate_output_controller_pin_template()
    validate_output_net_expansion()
    validate_input_and_power_pin_templates()
    validate_input_protection_pin_contract()
    validate_logic_power_design_placeholders()
    validate_output_stage_design_values()
    validate_input_power_design_values()
    validate_logic_power_design_values()
    validate_can1_safety_verification()
    validate_assembly_sourcing_recheck()
    validate_validation_traceability()
    validate_test_point_plan()
    validate_fault_response_matrix()
    validate_net_naming_contract()
    print("PB-100 validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
