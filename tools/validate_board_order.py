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
LB100_CONTRACTS = (
    LB100_DIR / "LB-100-jpb1-resource-budget.csv",
    LB100_DIR / "LB-100-rail-tree-precheck.csv",
)
FB100_CONTRACTS = (
    FB100_DIR / "FB-100-interface-signal-plan.csv",
    FB100_DIR / "FB-100-ui-mechanical-precheck.csv",
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


def validate_no_layout_before_freeze(board: str, board_dir: Path, status: str) -> None:
    pcbs = sorted(board_dir.rglob("*.kicad_pcb"))
    manufacturing = manufacturing_files(board_dir)
    if status != "Closed" and pcbs:
        fail(f"{board} has PCB layout before schematic freeze: {pcbs[0].relative_to(REPO_ROOT)}")
    if status != "Closed" and manufacturing:
        fail(f"{board} has manufacturing output before schematic freeze: {manufacturing[0].relative_to(REPO_ROOT)}")


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
    if "does not" not in lower_text or "pcb layout" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must block PCB layout")
    if "board-release-blocker-register.csv" not in text:
        fail(f"{path.relative_to(REPO_ROOT)} must reference blocker register")
    status = checklist_status(path)
    if status != "Open":
        fail(f"{path.relative_to(REPO_ROOT)} must remain Open until all gates close")
    gates = checklist_gates(path)
    if not any(row["Status"] == "Closed" for row in gates):
        fail(f"{path.relative_to(REPO_ROOT)} must have closed baseline gates")
    if not any(row["Status"] == "Conditional" for row in gates):
        fail(f"{path.relative_to(REPO_ROOT)} must have conditional close gates")
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
        if row["Status"].strip() not in {"Open", "Conditional"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: blockers must remain Open or Conditional")
        for column in BLOCKER_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        impact = row["Layout impact"].lower()
        if "block" not in impact or "layout" not in impact:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Layout impact must block layout")


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
    missing_boards = sorted(REQUIRED_ORDER_BOARDS - seen_boards)
    if missing_boards:
        fail(f"{ORDER_READINESS.relative_to(REPO_ROOT)} is missing boards: {', '.join(missing_boards)}")


def validate_kicad_scaffold(board: str, board_dir: Path) -> None:
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
    validate_no_layout_before_freeze(board, board_dir, "Open")


def main() -> int:
    validate_adr_0014()
    for board, path in FREEZE_CHECKLISTS.items():
        validate_checklist(board, path)
        board_dir = LB100_DIR if board == "LB-100" else FB100_DIR
        validate_no_layout_before_freeze(board, board_dir, checklist_status(path))
        validate_kicad_scaffold(board, board_dir)
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
    validate_order_readiness()
    validate_no_layout_before_freeze("PB-100", PB100_DIR, "Open")
    print("Three-board order validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
