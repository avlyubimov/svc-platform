from __future__ import annotations

from .common import (
    ALLOWED_BOM_FILES,
    ALLOWED_DASHBOARD_STATUSES,
    BOM_SYMBOL_MAP_COLUMNS,
    CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM,
    FORBIDDEN_ROLE_TOKENS,
    INSTANCE_SYMBOL_MAP_COLUMNS,
    INTERNAL_SYMBOL_TRACE_SOURCE_BY_KEY,
    KICAD_DIR,
    KICAD_SHEET_MANIFEST_COLUMNS,
    NET_DOMAIN_PLAN_COLUMNS,
    PB100_DIR,
    PIN_MAP_EVIDENCE_SYMBOLS,
    Path,
    REPO_ROOT,
    REQUIRED_NET_PATTERNS,
    REQUIRED_READINESS_AREAS,
    REQUIRED_SYMBOL_KEYS,
    SCHEMATIC_READINESS_DASHBOARD_COLUMNS,
    SHEET_REFERENCE_MAP_COLUMNS,
    SYMBOL_MPN_COLUMNS,
    SYMBOL_PIN_EVIDENCE_COLUMNS,
    SYMBOL_WORKLIST_COLUMNS,
    csv,
    fail,
    re,
    read_text,
    validate_csv,
)
from .release import (
    freeze_checklist_status,
)


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
    worklist_path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    worklist_rows = list(csv.DictReader(worklist_path.open(newline="", encoding="utf-8")))
    created_worklist_keys = {
        row["Symbol key"].strip()
        for row in worklist_rows
        if "preliminary symbol created" in row["Pin evidence status"].strip().lower()
    }
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
        if symbol_key in created_worklist_keys and "created" not in row["KiCad symbol status"].lower():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol {symbol_key} "
                "is created in worklist but readiness status does not say created"
            )

    missing_keys = sorted(REQUIRED_SYMBOL_KEYS - seen_keys)
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required symbol keys: "
            f"{', '.join(missing_keys)}"
        )


def validate_symbol_trace_provenance() -> None:
    readiness_path = PB100_DIR / "PB-100-symbol-mpn-readiness.csv"
    readiness_rows = list(csv.DictReader(readiness_path.open(newline="", encoding="utf-8")))
    readiness_by_key = {row["Symbol key"].strip(): row for row in readiness_rows}
    worklist_path = PB100_DIR / "PB-100-symbol-capture-worklist.csv"
    worklist_rows = list(csv.DictReader(worklist_path.open(newline="", encoding="utf-8")))
    worklist_by_key = {row["Symbol key"].strip(): row for row in worklist_rows}
    for symbol_key, expected_source in INTERNAL_SYMBOL_TRACE_SOURCE_BY_KEY.items():
        source_path = REPO_ROOT / expected_source
        if not source_path.exists():
            fail(f"missing internal symbol trace source: {expected_source}")
        if symbol_key not in readiness_by_key:
            fail(f"{readiness_path.relative_to(REPO_ROOT)} is missing {symbol_key}")
        if symbol_key not in worklist_by_key:
            fail(f"{worklist_path.relative_to(REPO_ROOT)} is missing {symbol_key}")
        readiness_source = readiness_by_key[symbol_key]["Primary source"].strip()
        if readiness_source != expected_source:
            fail(f"{symbol_key} readiness primary source must be {expected_source}")
        worklist_source = worklist_by_key[symbol_key]["Symbol source"].strip()
        if worklist_source != expected_source:
            fail(f"{symbol_key} worklist symbol source must be {expected_source}")


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
        exact_selected_symbols = {
            "PB100_LM74930QRGERQ1",
            "PB100_POWER_NMOS_TOLL_80V",
            "PB100_POWER_NMOS_TOLL_150V",
            "PB100_SM8S33AHM3I",
        }
        if not concrete_symbol_name.startswith("PB100_") or (
            not concrete_symbol_name.endswith("_PRELIM")
            and concrete_symbol_name not in exact_selected_symbols
        ):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: concrete symbol name "
                "must use PB100_*_PRELIM or an explicitly selected exact symbol"
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

        created = "symbol created" in row["Pin evidence status"].strip().lower()
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
        if "symbol created" not in pin_status:
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
        selected_physical_symbols = {
            "PB100_TJA1051TK3_CAN_PHY_PRELIM": "PB100:HVSON-8_L3.0-W3.0-P0.65-BL-EP",
            "PB100_ESD2CANFD24_Q1_PRELIM": "PB100:SOT-23-3_DBZ_TI",
        }
        if symbol_name in selected_physical_symbols:
            if "(in_bom yes)" not in symbol_block or "(on_board yes)" not in symbol_block:
                fail(f"selected physical symbol {symbol_name} must be included in BOM and board")
            expected_footprint = selected_physical_symbols[symbol_name]
            if f'(property "Footprint" "{expected_footprint}"' not in symbol_block:
                fail(f"selected physical symbol {symbol_name} must bind {expected_footprint}")
            continue
        if "(in_bom no)" not in symbol_block:
            fail(f"preliminary symbol {symbol_name} must be excluded from BOM")
        if "(on_board no)" not in symbol_block:
            fail(f"preliminary symbol {symbol_name} must be excluded from board")
        if symbol_name == "PB100_JPB1_100PIN_PRELIM":
            if '(property "Footprint" "PB100:FX18-100P-0.8SV10_Hirose"' not in symbol_block:
                fail("JPB1 preliminary symbol must bind the Product Owner-approved FX18 footprint")
        elif symbol_name == "PB100_POWER_NMOS_TOLL_80V":
            if '(property "Footprint" "PB100:PG-HSOF-8-1_TOLL_Infineon"' not in symbol_block:
                fail("selected 80 V power MOSFET symbol must bind the reviewed TOLL footprint")
        elif symbol_name == "PB100_POWER_NMOS_TOLL_150V":
            if '(property "Footprint" "PB100:PG-HSOF-8-1_TOLL_Infineon"' not in symbol_block:
                fail("selected 150 V surge MOSFET symbol must bind the reviewed TOLL footprint")
        elif symbol_name == "PB100_LM74930QRGERQ1":
            expected_footprint = 'PB100:VQFN-24_RGE_4x4mm_P0.5mm_EP2.4mm'
            if f'(property "Footprint" "{expected_footprint}"' not in symbol_block:
                fail("selected LM74930-Q1 symbol must bind the reviewed RGE footprint")
        elif symbol_name == "PB100_SM8S33AHM3I":
            if '(property "Footprint" "PB100:DO-218AC_Vishay_SM8S"' not in symbol_block:
                fail("selected SM8S33AHM3/I symbol must bind the reviewed DO-218AC footprint")
        elif '(property "Footprint" ""' not in symbol_block:
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
        if "symbol created" in row["Pin evidence status"].strip().lower()
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


def parse_symbol_pin_numbers(symbol_name: str) -> set[str]:
    block = symbol_block(read_text(KICAD_DIR / "lib" / "PB100.kicad_sym"), symbol_name)
    if not block:
        fail(f"symbol pad-map target is missing from PB100.kicad_sym: {symbol_name}")
    return set(re.findall(r'\(number "([^"]+)"', block))


def parse_footprint_pad_numbers(path: Path) -> set[str]:
    if not path.exists():
        fail(f"symbol-footprint pad-map references missing footprint: {path.relative_to(REPO_ROOT)}")
    return set(re.findall(r'\(pad "([^"]+)"', read_text(path)))


def footprint_pad_blocks(path: Path, pad_number: str) -> list[str]:
    text = read_text(path)
    pattern = re.compile(rf'\n\t\(pad "{re.escape(pad_number)}" .*?\n\t\)', re.DOTALL)
    return pattern.findall(text)


def validate_large_mosfet_paste_segmentation() -> None:
    checks = (
        (
            PB100_DIR / "kicad" / "lib" / "PB100.pretty" / "PG-HSOF-8-1_TOLL_Infineon.kicad_mod",
            "Tab",
            42,
        ),
        (
            PB100_DIR / "kicad" / "lib" / "PB100.pretty" / "LFPAK88_SOT1235_Nexperia.kicad_mod",
            "mb",
            12,
        ),
    )
    for path, pad_number, minimum_paste_apertures in checks:
        blocks = footprint_pad_blocks(path, pad_number)
        if not blocks:
            fail(f"{path.relative_to(REPO_ROOT)} is missing large MOSFET drain pad {pad_number}")
        copper_blocks = [block for block in blocks if '"F.Cu"' in block]
        paste_only_blocks = [
            block
            for block in blocks
            if '"F.Paste"' in block and '"F.Cu"' not in block and '"F.Mask"' not in block
        ]
        if len(copper_blocks) != 1:
            fail(
                f"{path.relative_to(REPO_ROOT)} must have exactly one copper/mask drain pad "
                f"{pad_number}, got {len(copper_blocks)}"
            )
        if '"F.Paste"' in copper_blocks[0]:
            fail(f"{path.relative_to(REPO_ROOT)} drain copper pad {pad_number} must not use solid F.Paste")
        if len(paste_only_blocks) < minimum_paste_apertures:
            fail(
                f"{path.relative_to(REPO_ROOT)} drain pad {pad_number} needs at least "
                f"{minimum_paste_apertures} segmented paste apertures, got {len(paste_only_blocks)}"
            )


def validate_symbol_footprint_pad_map() -> None:
    path = PB100_DIR / "PB-100-symbol-footprint-pad-map.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty symbol-footprint pad-map: {path.relative_to(REPO_ROOT)}")
    required_columns = {
        "Map ID",
        "Symbol name",
        "Symbol pin numbers",
        "Footprint path",
        "Footprint pad numbers",
        "Compatibility state",
        "Evidence",
        "Blocked action",
    }
    missing_columns = required_columns - set(rows[0])
    if missing_columns:
        fail(f"{path.relative_to(REPO_ROOT)} is missing columns: {', '.join(sorted(missing_columns))}")
    seen_ids = set()
    for row_number, row in enumerate(rows, 2):
        map_id = row["Map ID"].strip()
        if map_id in seen_ids:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Map ID {map_id}")
        seen_ids.add(map_id)
        if row["Compatibility state"].strip() != "Compatible":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Compatibility state must be Compatible")
        if "Do not" not in row["Blocked action"]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocked action must be explicit")
        symbol_name = row["Symbol name"].strip()
        symbol_expected = set(row["Symbol pin numbers"].split())
        footprint_path = REPO_ROOT / row["Footprint path"].strip()
        footprint_expected = set(row["Footprint pad numbers"].split())
        symbol_actual = parse_symbol_pin_numbers(symbol_name)
        footprint_actual = parse_footprint_pad_numbers(footprint_path)
        missing_symbol_pins = sorted(symbol_expected - symbol_actual)
        missing_footprint_pads = sorted(footprint_expected - footprint_actual)
        if missing_symbol_pins:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {symbol_name} missing symbol pins "
                f"{', '.join(missing_symbol_pins)}"
            )
        if missing_footprint_pads:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                f"{row['Footprint path'].strip()} missing footprint pads {', '.join(missing_footprint_pads)}"
            )
        if symbol_expected != footprint_expected:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol pin set and footprint pad set must match"
            )


def validate_input_reverse_fet_symbol_evidence() -> None:
    symbol_name = "PB100_POWER_NMOS_TOLL_80V"
    symbol_text = read_text(KICAD_DIR / "lib" / "PB100.kicad_sym")
    block = symbol_block(symbol_text, symbol_name)
    if not block:
        fail(f"{symbol_name} must exist after Q1 pin evidence is captured")

    expected_pins = (("1", "G"),) + tuple(
        (str(pin_number), "S") for pin_number in range(2, 9)
    ) + (("Tab", "D"),)
    for pin_number, pin_name in expected_pins:
        expected_name = f'(name "{pin_name}"'
        expected_number = f'(number "{pin_number}"'
        if not any(expected_name in line and expected_number in line for line in block.splitlines()):
            fail(f"{symbol_name} is missing Q1 pin {pin_number} {pin_name}")

    if "(in_bom no)" not in block:
        fail(f"{symbol_name} must remain excluded from BOM")
    if "(on_board no)" not in block:
        fail(f"{symbol_name} must remain excluded from board")
    if '(property "Value" "IAUT300N08S5N012ATMA2"' not in block:
        fail(f"{symbol_name} must lock the Product Owner-approved IAUT300N08S5N012ATMA2 value")
    if '(property "Footprint" "PB100:PG-HSOF-8-1_TOLL_Infineon"' not in block:
        fail(f"{symbol_name} must bind the reviewed TOLL footprint")

    open_items_text = read_text(PB100_DIR / "PB-100-symbol-open-items.md")
    if "Evidence captured" not in open_items_text:
        fail("Q1 symbol-open-items row must mark evidence captured")
    if "final plane/polygon/bus review remains a layout gate" not in open_items_text.lower():
        fail("Q1 symbol-open-items row must preserve the later physical thermal gate")


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

    for mf_identifier in (
        "MF_A_PIN1_51_END",
        "MF_B_PIN1_51_END",
        "MF_A_PIN50_100_END",
        "MF_B_PIN50_100_END",
    ):
        if f'(number "{mf_identifier}"' not in block:
            fail(f"{symbol_name} is missing approved GND MF pin {mf_identifier}")
    if '(property "Footprint" "PB100:FX18-100P-0.8SV10_Hirose"' not in block:
        fail(f"{symbol_name} must bind the reviewed Hirose FX18-100P footprint")


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
        can1_concrete_symbols = {
            "PB100_CAN1_TX_DISABLE_PRELIM",
            "PB100_CAN1_SAFETY_RESISTOR_PRELIM",
            "PB100_CAN1_TX_DNP_LINK_PRELIM",
            "PB100_SN74LVC1G125_Q1_DBV_PRELIM",
        }
        if symbol_key == "CAN1_TX_DISABLE" and symbol_name in can1_concrete_symbols:
            pass
        elif symbol_name != worklist_row["Concrete symbol name"].strip():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} maps to {symbol_name}, "
                f"but worklist uses {worklist_row['Concrete symbol name'].strip()}"
            )
        if symbol_state not in {"Created", "Selected", "Pending"}:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: "
                "Symbol state must be Created, Selected, or Pending"
            )
        symbol_present = f'(symbol "{symbol_name}"' in symbol_text
        if symbol_state in {"Created", "Selected"} and not symbol_present and symbol_name not in PIN_MAP_EVIDENCE_SYMBOLS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: created symbol is missing: {symbol_name}")
        if symbol_state == "Pending" and symbol_present:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pending symbol is already present: {symbol_name}")
        if ref == "Q102" and not all(
            token in row["Notes"] for token in ("IAUT300N08S5N012ATMA2", "SOA", "thermal")
        ):
            fail("Q102 instance-symbol map must preserve selected 80 V SOA/thermal evidence")


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

    manifest_rows_by_sheet = {row["Sheet file"].strip(): row for row in rows}
    capture_queue_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-capture-work-queue.csv").open(newline="", encoding="utf-8"))
    )
    capture_rows_by_work_item = {row["Work item"].strip(): row for row in capture_queue_rows}
    for work_item, tokens in CAPTURE_TRACE_ARTIFACTS_BY_WORK_ITEM.items():
        if work_item not in capture_rows_by_work_item:
            fail(f"KiCad sheet manifest trace check is missing capture work item {work_item}")
        sheet_file = capture_rows_by_work_item[work_item]["Sheet file"].strip()
        if sheet_file not in manifest_rows_by_sheet:
            fail(f"{path.relative_to(REPO_ROOT)} must include manifest row for {sheet_file}")
        primary_artifacts = manifest_rows_by_sheet[sheet_file]["Primary artifacts"]
        for token in tokens:
            if token not in primary_artifacts:
                fail(f"{path.relative_to(REPO_ROOT)} {sheet_file} row must include {token}")

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
    freeze_closed = freeze_checklist_status() == "Closed"
    expected_layout_status = "Ready" if freeze_closed else "Blocked"
    if rows_by_area["Layout authorization"]["Status"].strip() != expected_layout_status:
        fail(f"Layout authorization must be {expected_layout_status} for current schematic freeze state")
    if "schematic freeze" not in rows_by_area["Layout authorization"]["Remaining close work"].lower():
        fail("Layout authorization close work must reference schematic freeze")

    symbol_row = rows_by_area["Symbol readiness"]
    expected_symbol_status = "Closed" if freeze_closed else "Conditional"
    if symbol_row["Status"].strip() != expected_symbol_status:
        fail(f"Symbol readiness must be {expected_symbol_status} for current schematic freeze state")
    symbol_text = " ".join(symbol_row.values())
    for token in ("LM74930QRGERQ1", "IAUTN15S6N025ATMA1", "IAUT300N08S5N012ATMA2 80 V TOLL"):
        if token not in symbol_text:
            fail(f"Symbol readiness must include selected input-power token {token}")

    can_row = rows_by_area["CAN1 safety"]
    can_text = " ".join(can_row[column] for column in SCHEMATIC_READINESS_DASHBOARD_COLUMNS).lower()
    if "dnp/open" not in can_text or "future adr" not in can_text:
        fail("CAN1 safety dashboard row must keep DNP/open and future ADR explicit")

    required_dashboard_evidence = {
        "Symbol readiness": (
            "PB-100-input-reverse-package-trace.csv",
            "PB-100-input-reverse-q1-freeze-checklist.csv",
            "PB-100-input-reverse-q1-derivation-precheck.csv",
            "PB-100-input-reverse-q1-closeout-precheck.csv",
        ),
        "Output pin contract": ("PB-100-high-medium-output-baseline-trace.csv", "PB-100-low-current-output-baseline-trace.csv"),
        "Output stage design values": (
            "PB-100-high-medium-output-baseline-trace.csv",
            "PB-100-low-current-output-baseline-trace.csv",
            "PB-100-output-stage-value-freeze-checklist.csv",
            "PB-100-output-stage-value-derivation-precheck.csv",
            "PB-100-output-stage-closeout-precheck.csv",
        ),
        "Input power design values": (
            "PB-100-board-current-budget-trace.csv",
            "PB-100-input-q1-evidence.csv",
            "PB-100-surge-stopper-evidence.csv",
            "PB-100-protection-validation.csv",
            "PB-100-staged-release-readiness.csv",
        ),
        "Logic power design values": (
            "PB-100-logic-power-rail-trace.csv",
            "PB-100-logic-power-freeze-review.csv",
            "PB-100-logic-power-value-freeze-checklist.csv",
            "PB-100-logic-power-value-derivation-precheck.csv",
            "PB-100-logic-power-closeout-precheck.csv",
        ),
        "Input protection contract": (
            "PB-100-input-controller-pin-template.csv",
            "PB-100-input-reverse-package-trace.csv",
            "PB-100-surge-stopper-evidence.csv",
        ),
        "Current monitor template": (
            "PB-100-current-monitor-pin-template.csv",
            "PB-100-current-telemetry-value-freeze-checklist.csv",
            "PB-100-current-telemetry-value-derivation-precheck.csv",
            "PB-100-current-telemetry-closeout-precheck.csv",
        ),
        "Hardware capability manifest": (
            "PB-100-current-telemetry-trace.csv",
            "PB-100-thermal-telemetry-trace.csv",
            "PB-100-can1-tx-disable-trace.csv",
        ),
        "Logic power values": (
            "PB-100-logic-power-rail-trace.csv",
            "PB-100-logic-power-freeze-review.csv",
            "PB-100-logic-power-value-freeze-checklist.csv",
            "PB-100-logic-power-value-derivation-precheck.csv",
            "PB-100-logic-power-closeout-precheck.csv",
        ),
        "B2B LB-100 pin precheck": (
            "PB-100-b2b-lb100-pin-binding-precheck.md",
            "PB-100-b2b-lb100-pin-audit-checklist.csv",
            "PB-100-b2b-interface-freeze-checklist.csv",
            "PB-100-b2b-interface-closeout-precheck.csv",
        ),
        "BOM synchronization": (
            "PB-100-assembly-readiness-trace.csv",
            "PB-100-factory-assembly-freeze-checklist.csv",
            "PB-100-factory-assembly-sourcing-precheck.csv",
            "PB-100-factory-assembly-closeout-precheck.csv",
            "PB-100-garage-install-freeze-checklist.csv",
            "PB-100-garage-install-closeout-precheck.csv",
        ),
        "Assembly sourcing recheck": (
            "PB-100-assembly-readiness-trace.csv",
            "PB-100-factory-assembly-freeze-checklist.csv",
            "PB-100-factory-assembly-sourcing-precheck.csv",
            "PB-100-factory-assembly-closeout-precheck.csv",
            "PB-100-garage-install-freeze-checklist.csv",
            "PB-100-garage-install-closeout-precheck.csv",
        ),
        "CAN1 safety": (
            "PB-100-can1-tx-disable-trace.csv",
            "PB-100-can1-production-dnp-review.csv",
            "PB-100-can1-default-disable-freeze-checklist.csv",
            "PB-100-can1-default-disable-derivation-precheck.csv",
            "PB-100-can1-default-disable-closeout-precheck.csv",
        ),
        "CAN1 safety verification": (
            "PB-100-can1-tx-disable-trace.csv",
            "PB-100-can1-reset-bench-checklist.csv",
            "PB-100-can1-default-disable-freeze-checklist.csv",
            "PB-100-can1-default-disable-derivation-precheck.csv",
            "PB-100-can1-default-disable-closeout-precheck.csv",
        ),
    }
    for area, tokens in required_dashboard_evidence.items():
        evidence = rows_by_area[area]["Evidence"]
        for token in tokens:
            if token not in evidence:
                fail(f"readiness dashboard evidence for {area} must include {token}")
