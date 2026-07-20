from __future__ import annotations

from .common import (
    GARAGE_CONNECTOR_FUSE_PLAN_COLUMNS,
    GARAGE_INSTALL_CLOSEOUT_PRECHECK_COLUMNS,
    GARAGE_INSTALL_FREEZE_CHECKLIST_COLUMNS,
    GARAGE_INSTALL_SOURCING_PRECHECK_COLUMNS,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_GARAGE_INSTALL_CLOSEOUT_PRECHECKS,
    REQUIRED_GARAGE_INSTALL_FREEZE_CHECKS,
    REQUIRED_GARAGE_INSTALL_SOURCING_PRECHECKS,
    csv,
    fail,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def validate_garage_connector_fuse_plan() -> None:
    csv_path = PB100_DIR / "PB-100-garage-connector-fuse-plan.csv"
    validate_csv(csv_path)
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty garage connector/fuse plan: {csv_path.relative_to(REPO_ROOT)}")
    fieldnames = rows[0].keys()
    missing_columns = [column for column in GARAGE_CONNECTOR_FUSE_PLAN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{csv_path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    required_interfaces = {
        "Battery input",
        "Main harness fuse",
        "OUT1",
        "OUT2",
        "OUT3",
        "OUT4",
        "OUT5",
        "OUT6",
        "OUT7",
        "OUT8",
        "OUT9",
        "OUT10",
        "CAN/service",
        "External inputs",
        "Per-channel fuses",
    }
    rows_by_interface: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        interface = row["Interface"].strip()
        if interface in rows_by_interface:
            fail(f"{csv_path.relative_to(REPO_ROOT)}:{row_number}: duplicate interface {interface}")
        rows_by_interface[interface] = row
        for column in GARAGE_CONNECTOR_FUSE_PLAN_COLUMNS:
            if not row[column].strip():
                fail(f"{csv_path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if row["Status"].strip() not in {"Candidate", "Conditional"}:
            fail(f"{csv_path.relative_to(REPO_ROOT)}:{row_number}: invalid Status {row['Status'].strip()}")

    missing_interfaces = sorted(required_interfaces - rows_by_interface.keys())
    if missing_interfaces:
        fail(
            f"{csv_path.relative_to(REPO_ROOT)} is missing interfaces: "
            f"{', '.join(missing_interfaces)}"
        )
    for output in ("OUT1", "OUT2"):
        row_text = " ".join(rows_by_interface[output].values())
        if "DTP" not in row_text or "DT 13A class is too close" not in row_text and output == "OUT1":
            fail(f"{output} garage connector plan must keep DTP class and DT margin note")
    for output in ("OUT3", "OUT4", "OUT5", "OUT6", "OUT7", "OUT8", "OUT9", "OUT10"):
        row_text = " ".join(rows_by_interface[output].values())
        if "DT" not in row_text:
            fail(f"{output} garage connector plan must use DT class")
    if "DTM" not in " ".join(rows_by_interface["CAN/service"].values()):
        fail("CAN/service garage connector plan must use DTM signal class")
    if "MINI/ATO" not in " ".join(rows_by_interface["Per-channel fuses"].values()):
        fail("per-channel fuses must stay on MINI/ATO blade family")
    if rows_by_interface["Battery input"]["Status"].strip() != "Conditional":
        fail("battery input connector must remain conditional until derating review closes")

    doc_path = PB100_DIR / "PB-100-garage-connector-fuse-plan.md"
    doc_text = read_text(doc_path).lower()
    for token in ("wire gauge", "crimp", "service", "enclosure", "does not freeze exact connector mpns"):
        if token not in doc_text:
            fail(f"{doc_path.relative_to(REPO_ROOT)} must preserve garage boundary token {token}")

    garage_bom_text = read_text(REPO_ROOT / "production" / "bom" / "garage_bom_draft.csv")
    for token in ("Deutsch DTP", "Deutsch DT", "Deutsch DTM", "Mini/ATO", "Automotive wire", "Enclosure"):
        if token not in garage_bom_text:
            fail(f"garage BOM must preserve {token}")


def validate_garage_install_freeze_checklist() -> None:
    path = PB100_DIR / "PB-100-garage-install-freeze-checklist.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty garage install freeze checklist: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in GARAGE_INSTALL_FREEZE_CHECKLIST_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_check: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        check_id = row["Check ID"].strip()
        if check_id not in REQUIRED_GARAGE_INSTALL_FREEZE_CHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown garage install check {check_id}")
        if check_id in rows_by_check:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate garage install check {check_id}")
        rows_by_check[check_id] = row
        for column in GARAGE_INSTALL_FREEZE_CHECKLIST_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_GARAGE_INSTALL_FREEZE_CHECKS - rows_by_check.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing garage install checks: "
            f"{', '.join(missing_checks)}"
        )

    checklist_text = read_text(path)
    for token in (
        "INPUT_CONNECTOR",
        "OUTPUT_CONNECTOR",
        "OUTPUT_FUSE_HOLDER",
        "MAIN_FUSE_HOLDER",
        "user-installed",
        "MAXI 50A",
        "DT and DTP",
        "50A input path",
        "6mm2 / 10AWG",
        "DEUTSCH DTP",
        "size 12",
        "25A",
        "DT 13A class is too close",
        "DEUTSCH DT",
        "size 16",
        "OUT3 through OUT10",
        "DEUTSCH DTM",
        "DTM 4-pin",
        "DTM 8-pin",
        "size 20",
        "7.5A",
        "MINI/ATO",
        "5A 10A 15A and 20A",
        "service cover",
        "plug/receptacle",
        "contacts",
        "seals",
        "wedgelocks",
        "boots",
        "backshells",
        "crimp tool",
        "insertion/removal tool",
        "spare contacts",
        "2026-07-17",
        "2.5-4 mm2 / 14-12 AWG",
        "0.5-1.0 mm2 / 20-18 AWG",
        "ASA/PETG",
        "2 mm silicone gasket",
        "M3 hardware",
        "PB-BENCH-015",
        "garage_bom_draft.csv",
        "pb100_symbol_bom_map.csv",
        "pb100_assembly_sourcing_recheck.csv",
        "pb100_sourcing_evidence_snapshot.csv",
        "PB-100-garage-connector-fuse-plan.md",
        "PB-100-garage-connector-fuse-plan.csv",
        "PB-100-assembly-readiness-trace.csv",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "connector footprints",
        "fuse-holder footprints",
    ):
        if token not in checklist_text:
            fail(f"garage install freeze checklist must include {token}")

    plan_text = read_text(PB100_DIR / "PB-100-garage-connector-fuse-plan.md")
    for token in ("does not freeze exact connector MPNs", "DTP 2-pin", "DT 2-pin", "DTM", "MAXI", "MINI/ATO"):
        if token not in plan_text:
            fail(f"garage connector/fuse plan must support checklist token {token}")

    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("2026-07-17", "OUTPUT_CONNECTOR", "OUTPUT_FUSE_HOLDER", "MAIN_FUSE_HOLDER", "Open:"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support garage checklist token {token}")


def validate_garage_install_sourcing_precheck() -> None:
    path = PB100_DIR / "PB-100-garage-install-sourcing-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty garage install sourcing precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in GARAGE_INSTALL_SOURCING_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_GARAGE_INSTALL_SOURCING_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown garage sourcing precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate garage sourcing precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in GARAGE_INSTALL_SOURCING_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")

    missing_checks = sorted(REQUIRED_GARAGE_INSTALL_SOURCING_PRECHECKS - rows_by_id.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing garage install sourcing prechecks: "
            f"{', '.join(missing_checks)}"
        )

    precheck_text = read_text(path)
    for token in (
        "INPUT_CONNECTOR",
        "OUTPUT_CONNECTOR",
        "OUTPUT_FUSE_HOLDER",
        "MAIN_FUSE_HOLDER",
        "user-installed",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-garage-install-freeze-checklist.csv",
        "PB-100-garage-connector-fuse-plan.md",
        "PB-100-garage-connector-fuse-plan.csv",
        "production/bom/garage_bom_draft.csv",
        "production/bom/pb100_symbol_bom_map.csv",
        "production/bom/pb100_assembly_sourcing_recheck.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "ring-lug battery lead",
        "near-battery MAXI 50A",
        "high-current sealed harness entry",
        "serviceable gland",
        "DT and DTP",
        "50A input path",
        "6mm2 / 10AWG",
        "6 mm2 / 10 AWG",
        "DEUTSCH DTP",
        "DTP 2-pin",
        "size 12",
        "25A",
        "DEUTSCH DT",
        "DT 2-pin",
        "size 16",
        "DT 13A class is too close",
        "OUT3 through OUT10",
        "DEUTSCH DTM",
        "DTM 4-pin",
        "DTM 8-pin",
        "size 20",
        "7.5A",
        "MINI/ATO",
        "5A 10A 15A and 20A",
        "service cover",
        "plug/receptacle",
        "contacts",
        "seals",
        "wedgelocks",
        "boots",
        "backshells",
        "crimp tool",
        "insertion/removal tool",
        "spare contacts",
        "2026-07-17",
        "2.5-4 mm2 / 14-12 AWG",
        "0.5-1.0 mm2 / 20-18 AWG",
        "ASA/PETG",
        "2 mm silicone gasket",
        "M3 hardware",
        "PB-BENCH-015",
        "does not freeze exact connector MPNs",
        "Open:",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "connector footprints",
        "fuse-holder footprints",
        "enclosure CAD release",
        "manufacturing output",
    ):
        if token not in precheck_text:
            fail(f"garage install sourcing precheck must include {token}")

    plan_text = read_text(PB100_DIR / "PB-100-garage-connector-fuse-plan.md")
    for token in ("does not freeze exact connector MPNs", "DTP 2-pin", "DT 2-pin", "DTM", "MAXI", "MINI/ATO"):
        if token not in plan_text:
            fail(f"garage connector/fuse plan must support sourcing precheck token {token}")

    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("2026-07-17", "INPUT_CONNECTOR", "OUTPUT_CONNECTOR", "OUTPUT_FUSE_HOLDER", "MAIN_FUSE_HOLDER", "Open:"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support garage sourcing precheck token {token}")


def validate_garage_install_closeout_precheck() -> None:
    path = PB100_DIR / "PB-100-garage-install-closeout-precheck.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty garage install closeout precheck: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [
        column for column in GARAGE_INSTALL_CLOSEOUT_PRECHECK_COLUMNS if column not in fieldnames
    ]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_id: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        precheck_id = row["Precheck ID"].strip()
        if precheck_id not in REQUIRED_GARAGE_INSTALL_CLOSEOUT_PRECHECKS:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown garage closeout precheck {precheck_id}")
        if precheck_id in rows_by_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate garage closeout precheck {precheck_id}")
        rows_by_id[precheck_id] = row
        for column in GARAGE_INSTALL_CLOSEOUT_PRECHECK_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        if "do not" not in row["Blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blocked action must be explicit")
        row_text = " ".join(row.values()).lower()
        if precheck_id == "GAR-CLS-010" and ("no pcb layout" not in row_text or "pb-100.kicad_pcb" not in row_text):
            fail("garage install closeout no-layout row must block PCB layout explicitly")

    missing_checks = sorted(REQUIRED_GARAGE_INSTALL_CLOSEOUT_PRECHECKS - rows_by_id.keys())
    if missing_checks:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing garage install closeout prechecks: "
            f"{', '.join(missing_checks)}"
        )

    closeout_text = read_text(path)
    for token in (
        "INPUT_CONNECTOR",
        "OUTPUT_CONNECTOR",
        "OUTPUT_FUSE_HOLDER",
        "MAIN_FUSE_HOLDER",
        "user-installed",
        "PB-100-assembly-readiness-trace.csv",
        "PB-100-garage-install-freeze-checklist.csv",
        "PB-100-garage-install-sourcing-precheck.csv",
        "PB-100-garage-connector-fuse-plan.md",
        "PB-100-garage-connector-fuse-plan.csv",
        "PB-100-board-current-budget-closeout-precheck.csv",
        "production/bom/garage_bom_draft.csv",
        "production/bom/pb100_symbol_bom_map.csv",
        "production/bom/pb100_assembly_sourcing_recheck.csv",
        "production/bom/pb100_sourcing_evidence_snapshot.csv",
        "PB-100-board-release-blocker-register.csv",
        "ring-lug battery lead",
        "near-battery MAXI 50A",
        "high-current sealed harness entry",
        "serviceable gland",
        "DT and DTP",
        "50A input path",
        "6mm2 / 10AWG",
        "6 mm2 / 10 AWG",
        "DEUTSCH DTP",
        "DTP 2-pin",
        "size 12",
        "25A",
        "DEUTSCH DT",
        "DT 2-pin",
        "size 16",
        "DT 13A class is too close",
        "OUT3 through OUT10",
        "DEUTSCH DTM",
        "DTM 4-pin",
        "DTM 8-pin",
        "size 20",
        "7.5A",
        "MINI/ATO",
        "5A 10A 15A and 20A",
        "service cover",
        "plug/receptacle",
        "contacts",
        "seals",
        "wedgelocks",
        "boots",
        "backshells",
        "crimp tool",
        "insertion/removal tool",
        "spare contacts",
        "2026-07-17",
        "2.5-4 mm2 / 14-12 AWG",
        "0.5-1.0 mm2 / 20-18 AWG",
        "ASA/PETG",
        "2 mm silicone gasket",
        "M3 hardware",
        "PB-BENCH-015",
        "does not freeze exact connector MPNs",
        "Open:",
        "No PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "connector footprints",
        "fuse-holder footprints",
        "enclosure CAD release",
        "fabrication package",
        "manufacturing output",
        "manufacturing ZIP",
        "PCBA order package",
    ):
        if token not in closeout_text:
            fail(f"garage install closeout precheck must include {token}")

    for supporting_artifact, tokens in {
        "PB-100-garage-install-freeze-checklist.csv": ("GAR-FRZ-001", "GAR-FRZ-010"),
        "PB-100-garage-install-sourcing-precheck.csv": ("GAR-SRC-001", "GAR-SRC-010"),
        "PB-100-assembly-readiness-trace.csv": ("Garage", "MAIN_FUSE_HOLDER"),
    }.items():
        supporting_text = read_text(PB100_DIR / supporting_artifact)
        for token in tokens:
            if token not in supporting_text:
                fail(f"garage install closeout precheck requires {supporting_artifact} token {token}")

    plan_text = read_text(PB100_DIR / "PB-100-garage-connector-fuse-plan.md")
    for token in ("does not freeze exact connector MPNs", "DTP 2-pin", "DT 2-pin", "DTM", "MAXI", "MINI/ATO"):
        if token not in plan_text:
            fail(f"garage connector/fuse plan must support closeout precheck token {token}")

    evidence_text = read_text(REPO_ROOT / "production" / "bom" / "pb100_sourcing_evidence_snapshot.csv")
    for token in ("2026-07-17", "INPUT_CONNECTOR", "OUTPUT_CONNECTOR", "OUTPUT_FUSE_HOLDER", "MAIN_FUSE_HOLDER", "Open:"):
        if token not in evidence_text:
            fail(f"sourcing evidence snapshot must support garage closeout precheck token {token}")
