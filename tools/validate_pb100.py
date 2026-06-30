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
    validate_net_naming_contract()
    print("PB-100 validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
