#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COUPON = ROOT / "hardware" / "power-board" / "PB-100" / "qualification" / "Q2-C100"
KICAD = COUPON / "kicad"
SCHEMATIC = KICAD / "Q2-C100.kicad_sch"
BOARD = KICAD / "Q2-C100.kicad_pcb"
REQUIRED_KICAD_VERSION = "10.0.4"
EXPECTED_OPEN_LOW_ENERGY_ITEMS = 36


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def require_tokens(path: Path, tokens: tuple[str, ...]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing Q2-C100 evidence file: {path.relative_to(ROOT)}")
    for token in tokens:
        if token not in text:
            fail(f"{path.relative_to(ROOT)} is missing {token}")


def validate_generated_files() -> None:
    result = run([sys.executable, "tools/generate_q2_qualification_coupon.py", "--check"])
    if result.returncode:
        fail(result.stdout.strip() or result.stderr.strip() or "Q2-C100 generated files are stale")


def validate_documents() -> None:
    require_tokens(
        COUPON / "README.md",
        (
            "CONTROLLED ROUTING IN PROGRESS / NOT FOR FABRICATION",
            "exactly 36 unconnected",
            "CORRELATION-A",
            "FORCED-B",
            "Gerber, drill, pick-and-place and manufacturing ZIP files are prohibited",
        ),
    )
    require_tokens(
        COUPON / "Q2-C100-electrical-contract.md",
        (
            "IAUTN15S6N025ATMA1",
            "LM74930-Q1 RGE",
            "RTN exposed pad 25 is electrically isolated",
            "65 V",
            "BZT52H-B56-Q",
            "CGA6N3X7R2A225M230AE",
            "at least 1.0 uF",
            "No grounded oscilloscope input",
        ),
    )
    require_tokens(
        COUPON / "Q2-C100-layout-fabrication-gate.md",
        (
            "four copper layers",
            "2.0 mm finished thickness",
            "1.475 +/-0.05 mm finished hole",
            "board DRC rule violations: 0",
            "exactly 36",
            "Required before `FAB-REVIEW`",
        ),
    )
    require_tokens(
        COUPON / "Q2-C100-component-decision-record.md",
        (
            "why the",
            "IAUTN15S6N025ATMA1",
            "IAUTN15S6N038ATMA1",
            "SQJQ570E",
            "IAUT300N08S5N012ATMA2",
            "786202073",
            "greater-than-10-year",
            "JLCPCB/PCBWay",
            "500 USD",
        ),
    )
    require_tokens(COUPON / "Q2-C100-bom.csv", ("QDUT", "UCTRL", "QREV", "786202073", "BZT52H-B56-Q", "FAB-REVIEW"))
    require_tokens(COUPON / "Q2-C100-assembly-variants.csv", ("CORRELATION-A", "FORCED-B", "No simultaneous external drive"))

    forbidden_suffixes = {".gbr", ".ger", ".drl", ".xln", ".pos", ".zip"}
    forbidden = [path for path in COUPON.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes]
    if forbidden:
        fail(f"Q2-C100 manufacturing output exists before FAB-REVIEW: {[str(path.relative_to(ROOT)) for path in forbidden]}")


def validate_kicad_version(kicad_cli: str) -> None:
    result = run([kicad_cli, "--version"])
    actual = result.stdout.strip()
    if result.returncode or actual != REQUIRED_KICAD_VERSION:
        fail(f"kicad-cli {REQUIRED_KICAD_VERSION} is required; found {actual or 'unavailable'}")


def parse_netlist(path: Path) -> tuple[dict[str, tuple[str, str]], dict[str, set[tuple[str, str]]]]:
    root = ET.parse(path).getroot()
    components = {
        comp.attrib["ref"]: (
            comp.findtext("value", default=""),
            comp.findtext("footprint", default=""),
        )
        for comp in root.findall("./components/comp")
    }
    nets = {
        net.attrib["name"]: {
            (node.attrib["ref"], node.attrib["pin"])
            for node in net.findall("node")
            if not node.attrib["ref"].startswith(("XEXT", "XPWR"))
        }
        for net in root.findall("./nets/net")
    }
    return components, nets


def require_net(nets: dict[str, set[tuple[str, str]]], name: str, expected: set[tuple[str, str]]) -> None:
    actual = nets.get(name, set())
    if actual != expected:
        fail(f"Q2-C100 net {name} mismatch: expected={sorted(expected)}, actual={sorted(actual)}")


def validate_netlist(kicad_cli: str, temp: Path) -> None:
    path = temp / "Q2-C100.xml"
    result = run([kicad_cli, "sch", "export", "netlist", "--format", "kicadxml", "--output", str(path), str(SCHEMATIC)])
    if result.returncode:
        fail(f"Q2-C100 netlist export failed: {result.stdout}{result.stderr}")
    components, nets = parse_netlist(path)
    expected_components = {
        "QDUT": ("IAUTN15S6N025ATMA1", "PB100:PG-HSOF-8-1_TOLL_Infineon"),
        "QREV": ("IAUT300N08S5N012ATMA2", "PB100:PG-HSOF-8-1_TOLL_Infineon"),
        "UCTRL": ("LM74930QRGERQ1", "PB100:VQFN-24_RGE_4x4mm_P0.5mm_EP2.4mm"),
        "DZVS": ("BZT52H-B56-Q 56V", "Q2C100:SOD123F"),
    }
    for ref, expected in expected_components.items():
        if components.get(ref) != expected:
            fail(f"Q2-C100 {ref} component mismatch: {components.get(ref)}")

    require_net(nets, "RAW_101V", {("JRAW", "1"), ("QDUT", "Tab"), ("ROV1", "1"), ("RVS", "1"), ("TPD", "1")})
    require_net(
        nets,
        "COMMON_SOURCE",
        {("JCOMMON", "1"), ("JDRIVE", "2"), ("TPS", "1"), ("UCTRL", "2"), ("UCTRL", "15")}
        | {("QDUT", str(pin)) for pin in range(2, 9)}
        | {("QREV", str(pin)) for pin in range(2, 9)},
    )
    require_net(nets, "Q2_HGATE", {("JDRIVE", "1"), ("QDUT", "1"), ("TPG", "1"), ("TPHG", "1"), ("UCTRL", "14")})
    require_net(nets, "QREV_DGATE", {("QREV", "1"), ("UCTRL", "1")})
    require_net(nets, "SYSTEM_OUT", {("JOUT", "1"), ("QREV", "Tab"), ("TPOUT", "1")} | {("UCTRL", pin) for pin in ("18", "19", "20", "24")})
    require_net(nets, "CTRL_VS", {("CCAP", "2"), ("CVS1", "1"), ("CVS2", "1"), ("DZVS", "1"), ("RVS", "2"), ("TPVS", "1")} | {("UCTRL", pin) for pin in ("4", "6", "7", "22")})
    for forbidden in (("UCTRL", "25"), ("UCTRL", "3")):
        if any(forbidden in endpoints and not name.startswith("unconnected-") for name, endpoints in nets.items()):
            fail(f"Q2-C100 forbidden controller connection exists: {forbidden}")


def validate_erc_and_drc(kicad_cli: str, temp: Path) -> None:
    erc_path = temp / "Q2-C100-erc.json"
    result = run([kicad_cli, "sch", "erc", "--format", "json", "--severity-all", "--output", str(erc_path), str(SCHEMATIC)])
    if result.returncode:
        fail(f"Q2-C100 ERC invocation failed: {result.stdout}{result.stderr}")
    erc = json.loads(erc_path.read_text(encoding="utf-8"))
    findings = [finding for sheet in erc.get("sheets", []) for finding in sheet.get("violations", [])]
    if findings:
        fail(f"Q2-C100 ERC findings changed: {Counter(finding.get('type') for finding in findings)}")

    drc_path = temp / "Q2-C100-drc.json"
    result = run([kicad_cli, "pcb", "drc", "--format", "json", "--schematic-parity", "--severity-all", "--output", str(drc_path), str(BOARD)])
    if result.returncode:
        fail(f"Q2-C100 DRC invocation failed: {result.stdout}{result.stderr}")
    drc = json.loads(drc_path.read_text(encoding="utf-8"))
    if drc.get("violations"):
        fail(f"Q2-C100 DRC findings changed: {Counter(finding.get('type') for finding in drc['violations'])}")
    if len(drc.get("unconnected_items", [])) != EXPECTED_OPEN_LOW_ENERGY_ITEMS:
        fail(f"Q2-C100 open low-energy milestone changed: expected {EXPECTED_OPEN_LOW_ENERGY_ITEMS}, found {len(drc.get('unconnected_items', []))}")
    parity = drc.get("schematic_parity", [])
    if Counter(finding.get("type") for finding in parity) != Counter({"extra_footprint": 4}):
        fail(f"Q2-C100 schematic parity changed: {Counter(finding.get('type') for finding in parity)}")
    board_only = set()
    for finding in parity:
        for item in finding.get("items", []):
            match = re.search(r"\bH[1-4]\b", str(item.get("description", "")))
            if match:
                board_only.add(match.group(0))
    if board_only != {"H1", "H2", "H3", "H4"}:
        fail(f"Q2-C100 unexpected board-only footprints: {sorted(board_only)}")


def validate_board_contract() -> None:
    require_tokens(
        BOARD,
        (
            '(general (thickness 2.0)',
            '(2 "In1.Cu" power)',
            '(4 "In2.Cu" power)',
            'Q2-C100 Rev.1  QUALIFICATION COUPON ONLY',
            'DANGER - NOT FOR VEHICLE / NOT FOR FAB',
            '(segment ',
            '(via ',
        ),
    )
    board_text = BOARD.read_text(encoding="utf-8")
    if "\n\t(zone " in board_text:
        fail("Q2-C100 controlled-routing milestone must not introduce unreviewed copper zones")


def main() -> int:
    validate_generated_files()
    validate_documents()
    validate_board_contract()
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli is None:
        fail("kicad-cli is required for Q2-C100 validation")
    validate_kicad_version(kicad_cli)
    with tempfile.TemporaryDirectory(prefix="svc-q2-c100-") as temp_dir:
        temp = Path(temp_dir)
        validate_netlist(kicad_cli, temp)
        validate_erc_and_drc(kicad_cli, temp)
    print("Q2-C100 validation passed (ERC 0, DRC 0, parity 4 board holes, 36 controlled low-energy opens).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
