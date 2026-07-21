from __future__ import annotations

from .common import (
    ASSEMBLY_READINESS_TRACE_COLUMNS,
    ASSEMBLY_SOURCING_RECHECK_COLUMNS,
    FACTORY_ASSEMBLY_CLOSEOUT_PRECHECK_COLUMNS,
    FACTORY_ASSEMBLY_FREEZE_CHECKLIST_COLUMNS,
    FACTORY_ASSEMBLY_SOURCING_PRECHECK_COLUMNS,
    PB100_DIR,
    Path,
    REPO_ROOT,
    REQUIRED_FACTORY_ASSEMBLY_CLOSEOUT_PRECHECKS,
    REQUIRED_FACTORY_ASSEMBLY_FREEZE_CHECKS,
    REQUIRED_FACTORY_ASSEMBLY_SOURCING_PRECHECKS,
    SOURCING_EVIDENCE_COLUMNS,
    csv,
    fail,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


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
        dependency = row["Freeze dependency"].lower()
        if not any(token in dependency for token in ("schematic freeze", "later gate", "release", "post-prototype")):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: lifecycle dependency must remain explicit")
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
            if not all(token in row_text for token in ("80v", "toll", "40a")):
                fail("INPUT_REVERSE_FET sourcing row must keep selected 80 V TOLL and 40 A review explicit")

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


def trace_symbol_keys(value: str) -> set[str]:
    return {part.strip() for part in value.split(";") if part.strip()}


def validate_assembly_readiness_trace() -> None:
    path = PB100_DIR / "PB-100-assembly-readiness-trace.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty assembly readiness trace: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in ASSEMBLY_READINESS_TRACE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_owner: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        owner = row["Assembly owner"].strip()
        if owner in rows_by_owner:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate assembly owner row {owner}")
        if owner not in {"Factory", "Garage", "Safety DNP"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown assembly owner row {owner}")
        rows_by_owner[owner] = row
        for column in ASSEMBLY_READINESS_TRACE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "schematic freeze" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze action must reference schematic freeze")
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    for owner in ("Factory", "Garage", "Safety DNP"):
        if owner not in rows_by_owner:
            fail(f"{path.relative_to(REPO_ROOT)} must include {owner} assembly trace row")

    sourcing_rows = list(
        csv.DictReader((REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv").open(newline="", encoding="utf-8"))
    )
    expected_keys_by_owner = {
        "Factory": {
            row["Symbol key"].strip()
            for row in sourcing_rows
            if row["Assembly owner"].strip() == "Factory"
        },
        "Garage": {
            row["Symbol key"].strip()
            for row in sourcing_rows
            if row["Assembly owner"].strip() == "Garage"
        },
    }

    for owner in ("Factory", "Garage"):
        trace_keys = trace_symbol_keys(rows_by_owner[owner]["Required symbol keys"])
        expected_keys = expected_keys_by_owner[owner]
        if trace_keys != expected_keys:
            missing = sorted(expected_keys - trace_keys)
            extra = sorted(trace_keys - expected_keys)
            fail(
                f"{path.relative_to(REPO_ROOT)} {owner} keys mismatch; "
                f"missing={','.join(missing)} extra={','.join(extra)}"
            )

    factory_text = " ".join(rows_by_owner["Factory"].values()).lower()
    for token in ("jlcpcb", "pcbway", "alternates", "assembly class", "do not lock"):
        if token not in factory_text:
            fail(f"factory assembly trace must preserve {token}")

    garage_text = " ".join(rows_by_owner["Garage"].values()).lower()
    for token in ("user-installed", "connector", "fuse", "wire gauge", "crimp", "do not move"):
        if token not in garage_text:
            fail(f"garage assembly trace must preserve {token}")

    safety_text = " ".join(rows_by_owner["Safety DNP"].values()).lower()
    for token in ("can1_tx_disable", "dnp/open", "no default-populated", "future adr"):
        if token not in safety_text:
            fail(f"safety DNP assembly trace must preserve {token}")


def validate_factory_assembly_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-factory-assembly-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty factory assembly freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in FACTORY_ASSEMBLY_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_FACTORY_ASSEMBLY_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown factory assembly check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate factory assembly check {check_id}")
        rows_by_check[check_id] = row
        for column in FACTORY_ASSEMBLY_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_FACTORY_ASSEMBLY_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing factory assembly checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "HS_CTRL",
        "OUT_FET",
        "OUT2_ESCAPE_FET",
        "INPUT_IDEAL_DIODE",
        "INPUT_REVERSE_FET",
        "INPUT_TVS",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "TOTAL_CURRENT_MONITOR",
        "TOTAL_CURRENT_SHUNT",
        "THERMAL_NTC",
        "B2B_CONNECTOR",
        "CAN1_TX_DISABLE",
        "Alternate 1",
        "Alternate 2",
        "JLCPCB PCBWay",
        "assembly class",
        "reel",
        "tray",
        "cut tape",
        "authorized distributor",
        "2026-07-21",
        "date-stamped",
        "TPS48110AQDGXRQ1",
        "IAUT300N08S5N012ATMA2",
        "IAUT300N08S5N014ATMA1",
        "BUK7J2R4-80MX",
        "TOLL",
        "PG-HSOF-8-1",
        "LFPAK56E",
        "19-VSSOP",
        "SM8S33AHM3/I",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "DO-218AC",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "CSS4J-4026R-L500F",
        "1.0mΩ",
        "NTCGS103JF103FT8",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV10",
        "20 mm",
        "DNP/open",
        "no default-populated TX",
        "future ADR",
        "factory_bom_draft.csv",
        "pb100_symbol_bom_map.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "pb100_sourcing_evidence_snapshot.csv",
        "PB-100-review-release-manifest.csv",
        "PB-100-schematic-freeze-checklist.md",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
    ):
        if token not in checklist_text:
            fail(f"factory assembly freeze checklist must include {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("JLCPCB/PCBWay", "Alternates", "Verify", "schematic freeze"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support factory checklist token {token}")
    for token in ("2026-07-21", "live-stock claim", "DNP/open"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support factory checklist token {token}")


def validate_factory_assembly_sourcing_precheck() -> None:
    path = PB100_DIR / "PB-100-factory-assembly-sourcing-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty factory assembly sourcing precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in FACTORY_ASSEMBLY_SOURCING_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_FACTORY_ASSEMBLY_SOURCING_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown factory sourcing precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate factory sourcing precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in FACTORY_ASSEMBLY_SOURCING_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_FACTORY_ASSEMBLY_SOURCING_PRECHECKS - rows_by_id.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing factory assembly sourcing prechecks: "
            f"{', '.join(missing_checks)}"
        )

    precheck_text = read_text(path)
    for token in (
        "HS_CTRL",
        "OUT_FET",
        "OUT2_ESCAPE_FET",
        "INPUT_IDEAL_DIODE",
        "INPUT_REVERSE_FET",
        "INPUT_TVS",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "TOTAL_CURRENT_MONITOR",
        "TOTAL_CURRENT_SHUNT",
        "THERMAL_NTC",
        "B2B_CONNECTOR",
        "CAN1_TX_DISABLE",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-factory-assembly-freeze-checklist.csv",
        "PB-100-symbol-mpn-readiness.csv",
        "production/bom/factory_bom_draft.csv",
        "production/bom/pb100_symbol_bom_map.csv",
        "production/bom/pb100_assembly_sourcing_recheck.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "JLCPCB PCBWay",
        "assembly class",
        "reel",
        "tray",
        "cut tape",
        "extended part",
        "orderable suffix",
        "Alternate 1",
        "Alternate 2",
        "TPS48110AQDGXRQ1",
        "IAUT300N08S5N012ATMA2",
        "IAUT300N08S5N014ATMA1",
        "BUK7J2R4-80MX",
        "LM74930Q1RGERQ1",
        "IAUTN15S6N025ATMA1",
        "19-VSSOP",
        "TOLL",
        "PG-HSOF-8-1",
        "LFPAK56E",
        "VQFN-24 RGE",
        "SM8S33AHM3/I",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "DO-218AC",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "CSS4J-4026R-L500F",
        "1.0mΩ",
        "NTCGS103JF103FT8",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV10",
        "20 mm",
        "DNP/open",
        "no default-populated TX",
        "future ADR",
        "2026-07-21",
        "order-date",
        "authorized distributor",
        "manufacturer evidence",
        "no live-stock claim",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "centroid",
        "PCBA order package",
        "manufacturing ZIP",
    ):
        if token not in precheck_text:
            fail(f"factory assembly sourcing precheck must include {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("JLCPCB/PCBWay", "authorized distributor", "schematic freeze"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support factory sourcing precheck token {token}")
    for token in ("2026-07-21", "live-stock claim", "DNP/open"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support factory sourcing precheck token {token}")


def validate_factory_assembly_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-factory-assembly-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty factory assembly closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in FACTORY_ASSEMBLY_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_FACTORY_ASSEMBLY_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown factory closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate factory closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in FACTORY_ASSEMBLY_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        row_text = " ".join(row.values()).lower()
        if precheck_id == "FACT-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("factory assembly closeout no-layout row must block PCB layout explicitly")

    missing_checks = sorted(REQUIRED_FACTORY_ASSEMBLY_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing factory assembly closeout prechecks: "
            f"{', '.join(missing_checks)}"
        )

    closeout_text = read_text(path)
    for token in (
        "HS_CTRL",
        "OUT_FET",
        "OUT2_ESCAPE_FET",
        "INPUT_IDEAL_DIODE",
        "INPUT_REVERSE_FET",
        "INPUT_TVS",
        "LOGIC_BUCK",
        "LOGIC_BUCK_INDUCTOR",
        "TOTAL_CURRENT_MONITOR",
        "TOTAL_CURRENT_SHUNT",
        "THERMAL_NTC",
        "B2B_CONNECTOR",
        "CAN1_TX_DISABLE",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-factory-assembly-freeze-checklist.csv",
        "PB-100-factory-assembly-sourcing-precheck.csv",
        "PB-100-symbol-mpn-readiness.csv",
        "production/bom/factory_bom_draft.csv",
        "production/bom/pb100_symbol_bom_map.csv",
        "production/bom/pb100_assembly_sourcing_recheck.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "PB-100-board-release-blocker-register.csv",
        "JLCPCB PCBWay",
        "JLCPCB/PCBWay",
        "assembly class",
        "reel",
        "tray",
        "cut tape",
        "extended part",
        "orderable suffix",
        "Alternate 1",
        "Alternate 2",
        "TPS48110AQDGXRQ1",
        "IAUT300N08S5N012ATMA2",
        "IAUT300N08S5N014ATMA1",
        "BUK7J2R4-80MX",
        "LM74930Q1RGERQ1",
        "IAUTN15S6N025ATMA1",
        "19-VSSOP",
        "TOLL",
        "PG-HSOF-8-1",
        "LFPAK56E",
        "VQFN-24 RGE",
        "SM8S33AHM3/I",
        "SLD8S33A",
        "DM8W33AQ-13",
        "SM8S33A-Q",
        "MCC SM8S33A EOL",
        "Vishay HE3 NFD",
        "DO-218AC",
        "LM5164QDDATQ1",
        "LM5013-Q1",
        "TPS54360B-Q1",
        "INA228-Q1",
        "INA229-Q1",
        "INA226",
        "CSS4J-4026R-L500F",
        "1.0mΩ",
        "NTCGS103JF103FT8",
        "Vishay NTCS0402E3",
        "Murata NCU18",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV10",
        "20 mm",
        "DNP/open",
        "no default-populated TX",
        "future ADR",
        "2026-07-21",
        "order-date",
        "authorized distributor",
        "manufacturer evidence",
        "no live-stock claim",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "centroid",
        "fabrication package",
        "manufacturing ZIP",
        "assembly output",
        "PCBA order package",
    ):
        if token not in closeout_text:
            fail(f"factory assembly closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-factory-assembly-freeze-checklist.csv": ("FACT-FRZ-001", "FACT-FRZ-010"),
        "PB-100-factory-assembly-sourcing-precheck.csv": ("FACT-SRC-001", "FACT-SRC-010"),
        "PB-100-assembly-readiness-trace.csv": ("Factory", "CAN1_TX_DISABLE"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"factory assembly closeout precheck requires {supporting_artifact} token {token}")

    sourcing_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_assembly_sourcing_recheck.csv")
    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("JLCPCB/PCBWay", "authorized distributor", "schematic freeze"):
        if token not in sourcing_text:
            fail(f"assembly sourcing recheck must support factory closeout precheck token {token}")
    for token in ("2026-07-21", "live-stock claim", "DNP/open"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support factory closeout precheck token {token}")


def evidence_link_is_valid(value: str) -> bool:
    return value.startswith(("https://", "http://", "docs/", "hardware/", "production/"))


def validate_sourcing_evidence_date(path: Path, row_number: int, value: str) -> None:
    parts = value.split("-")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid evidence date {value}")
    year, month, day = (int(part) for part in parts)
    if year < 2026 or not (1 <= month <= 12) or not (1 <= day <= 31):
        fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: evidence date must be a current snapshot date")


def validate_sourcing_evidence_snapshot() -> None:
    path = REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty sourcing evidence snapshot: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SOURCING_EVIDENCE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    readiness_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-mpn-readiness.csv").open(newline="", encoding="utf-8"))
    )
    critical_keys = {
        row["Symbol key"].strip()
        for row in readiness_rows
        if row["Critical"].strip().lower() == "yes"
    }

    seen_keys = set()
    for row_number, row in enumerate(rows, 2):
        symbol_key = row["Symbol key"].strip()
        if symbol_key in seen_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate symbol key {symbol_key}")
        seen_keys.add(symbol_key)
        if symbol_key not in critical_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: symbol key {symbol_key} is not critical")
        for column in SOURCING_EVIDENCE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_sourcing_evidence_date(path, row_number, row["Evidence date"].strip())
        for column in ("Primary evidence URL", "Secondary evidence URL"):
            if not evidence_link_is_valid(row[column].strip()):
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid {column}")
        row_text = " ".join(row.values()).lower()
        blocker_text = row["Open sourcing blocker"].lower()
        if "open:" not in blocker_text and not (
            "none for pbrel pre-layout" in blocker_text
            and any(token in blocker_text for token in ("remain", "recheck"))
        ):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: later blocker/gate must remain explicit")
        if symbol_key == "INPUT_TVS":
            for token in ("obsolete", "eol", "do not lock", "active"):
                if token not in row_text:
                    fail(f"INPUT_TVS sourcing evidence must explicitly track {token}")
        if symbol_key == "CAN1_TX_DISABLE":
            for token in ("dnp/open", "no default-populated tx", "future adr"):
                if token not in row_text:
                    fail(f"CAN1_TX_DISABLE evidence must preserve {token}")

    missing_keys = sorted(critical_keys - seen_keys)
    extra_keys = sorted(seen_keys - critical_keys)
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing critical sourcing evidence keys: "
            f"{', '.join(missing_keys)}"
        )
    if extra_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} has non-critical sourcing evidence keys: "
            f"{', '.join(extra_keys)}"
        )
