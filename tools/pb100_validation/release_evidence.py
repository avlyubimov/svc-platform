from __future__ import annotations

import csv
import subprocess
import sys

from .common import PB100_DIR, REPO_ROOT, fail, read_text


SELECTED_MOSFET = "IAUT300N08S5N012ATMA2"
SELECTED_FOOTPRINT = "PB100:PG-HSOF-8-1_TOLL_Infineon"
FIVE_BLOCKERS = {"PBREL-001", "PBREL-004", "PBREL-006", "PBREL-007", "PBREL-011"}


def _rows(name: str) -> list[dict[str, str]]:
    with (PB100_DIR / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def validate_five_blocker_release_evidence() -> None:
    generator = REPO_ROOT / "tools" / "generate_pb100_release_evidence.py"
    result = subprocess.run(
        [sys.executable, str(generator), "--check"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        fail(result.stderr.strip() or result.stdout.strip())

    blocker_rows = _rows("PB-100-board-release-blocker-register.csv")
    status_by_id = {row["Blocker ID"]: row["Status"] for row in blocker_rows}
    if set(status_by_id) != {f"PBREL-{number:03d}" for number in range(1, 13)}:
        fail("PB-100 blocker register must contain PBREL-001 through PBREL-012 exactly")
    if any(status != "Closed" for status in status_by_id.values()):
        open_ids = sorted(blocker_id for blocker_id, status in status_by_id.items() if status != "Closed")
        fail(f"PB-100 PBREL pre-layout blockers are not all closed: {', '.join(open_ids)}")

    for blocker_id in FIVE_BLOCKERS:
        row = next(row for row in blocker_rows if row["Blocker ID"] == blocker_id)
        row_text = " ".join(row.values())
        if "pre-layout" not in row_text or "later" not in row_text:
            fail(f"{blocker_id} must distinguish closed pre-layout evidence from later physical gates")

    output_rows = _rows("PB-100-output-soa-evidence.csv")
    if len(output_rows) != 6 or any(row["Result"] != "PASS" for row in output_rows):
        fail("generated output SOA evidence must contain four classes plus two common PASS rows")
    high = next(row for row in output_rows if row["Channels"] == "OUT2")
    expected_high = {
        "IOC actual A": "34.96",
        "ISC actual A": "95.91",
        "tOC ms": "9.95",
        "Fast transient case": "80 A / 4 ms",
        "10us 60V SOA current margin A": "104.1",
    }
    for field, value in expected_high.items():
        if high[field] != value:
            fail(f"OUT2 generated evidence {field} must be {value}, got {high[field]}")

    transient_rows = _rows("PB-100-transient-margin-evidence.csv")
    transient_by_item = {row["Evidence item"]: row for row in transient_rows}
    if transient_by_item["Bounded downstream stress"]["Value"] != "59.45":
        fail("generated transient evidence must preserve the reviewed 59.45 V bound")
    for item in (
        "LM74700-Q1 recommended operating ceiling",
        "LM74700-Q1 ANODE absolute maximum",
        "IAUT300N08S5N012 VDS",
        "TPS48110-Q1 and 100 V buck family",
    ):
        if transient_by_item[item]["Result"] != "PASS":
            fail(f"generated transient margin must pass for {item}")

    q1_by_item = {row["Evidence item"]: row for row in _rows("PB-100-input-q1-evidence.csv")}
    for item, value in (
        ("Exact orderable MPN", SELECTED_MOSFET),
        ("Q1 conduction loss", "4.032"),
        ("Junction at acceptance ceiling", "126.61"),
        ("Junction margin", "48.39"),
    ):
        if q1_by_item[item]["Value"] != value or q1_by_item[item]["Result"] != "PASS":
            fail(f"generated Q1 evidence must keep {item}={value} PASS")

    factory_rows = _rows("PB-100-factory-production-evidence.csv")
    if not factory_rows or any("PASS" not in row["Pre-layout result"] for row in factory_rows):
        fail("factory production evidence must pass every pre-layout source/process row")

    output_sheet = read_text(PB100_DIR / "kicad" / "sheets" / "outputs-1-10.kicad_sch")
    input_sheet = read_text(PB100_DIR / "kicad" / "sheets" / "input-protection.kicad_sch")
    if output_sheet.count(f'(property "Value" "{SELECTED_MOSFET}"') != 11:
        # One local lib-symbol property plus ten instances.
        fail("outputs sheet must contain exact selected TOLL value in its local symbol and Q101-Q110")
    if input_sheet.count(f'(property "Value" "{SELECTED_MOSFET}"') != 2:
        fail("input sheet must contain exact selected TOLL value in its local symbol and Q1")
    for sheet_name, sheet_text in (("outputs", output_sheet), ("input", input_sheet)):
        if f'(property "Footprint" "{SELECTED_FOOTPRINT}"' not in sheet_text:
            fail(f"{sheet_name} sheet must bind the selected TOLL footprint")
        for pin in ("5", "6", "7", "8", "Tab"):
            if f'(pin "{pin}"' not in sheet_text:
                fail(f"{sheet_name} sheet selected TOLL instances must include pin {pin}")
    for token in (
        '(property "Value" "SM8S33AHM3/I"',
        '(property "Footprint" "PB100:DO-218AC_Vishay_SM8S"',
    ):
        if token not in input_sheet:
            fail("D1 must be exact and footprint-bound in the input sheet")

    historical_allowlist = {
        PB100_DIR / "PB-100-five-blocker-closeout-2026-07-21.md",
        PB100_DIR / "PB-100-input-reverse-package-trace.csv",
        PB100_DIR / "PB-100-mosfet-voltage-margin-review.md",
        PB100_DIR / "kicad" / "lib" / "PB100.pretty" / "LFPAK88_SOT1235_Nexperia.kicad_mod",
    }
    selected_preliminary = []
    for path in PB100_DIR.rglob("*"):
        if not path.is_file() or path in historical_allowlist:
            continue
        try:
            if "BUK7S1R2-80M" in path.read_text(encoding="utf-8"):
                selected_preliminary.append(str(path.relative_to(REPO_ROOT)))
        except UnicodeDecodeError:
            continue
    if selected_preliminary:
        fail("rejected preliminary BUK7S1R2-80M leaked into active PB evidence: " + ", ".join(selected_preliminary))

    closeout = read_text(PB100_DIR / "PB-100-five-blocker-closeout-2026-07-21.md")
    for token in FIVE_BLOCKERS | {
        "59.45",
        "IAUT300N08S5N014ATMA1",
        "BUK7J2R4-80MX",
        "does not",
        ".kicad_pcb",
    }:
        if token not in closeout:
            fail(f"five-blocker closeout is missing {token}")
