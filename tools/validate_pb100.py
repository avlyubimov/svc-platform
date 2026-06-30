#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PB100_DIR = REPO_ROOT / "hardware" / "power-board" / "PB-100"
KICAD_DIR = PB100_DIR / "kicad"


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
    if list(KICAD_DIR.rglob("*.kicad_pcb")):
        fail("PB-100 KiCad scaffold must not contain .kicad_pcb before schematic freeze")


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
    validate_symbol_library()
    validate_instance_plan()
    validate_net_naming_contract()
    print("PB-100 validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
