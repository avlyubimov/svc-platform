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
RULES = KICAD / "Q2-C100.kicad_dru"
REQUIRED_KICAD_VERSION = "10.0.4"
EXPECTED_UNCONNECTED_ITEMS = 0


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
    for generator in (
        "tools/generate_q2_qualification_coupon.py",
        "tools/generate_q2_coupon_prefab_screening.py",
    ):
        result = run([sys.executable, generator, "--check"])
        if result.returncode:
            fail(result.stdout.strip() or result.stderr.strip() or f"generated files are stale: {generator}")


def validate_documents() -> None:
    require_tokens(
        COUPON / "README.md",
        (
            "ELECTRICAL ROUTING COMPLETE / FABRICATION BLOCKED",
            "zero unconnected items",
            "CORRELATION-A",
            "FORCED-B",
            "436500228",
            "436500328",
            "436500428",
            "S1751-46R",
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
            "CGA3E2X7R1H104K080AE",
            "CRCW120610K0FKEAHP",
            "CRCW120642K2FKEAHP",
            "at least 1.0 uF",
            "S1751-46R",
            "distinct two-, three- and four-position Molex Micro-Fit",
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
            "unconnected items: 0",
            "`FAB-REVIEW` remains open",
            "Required before `FAB-REVIEW`",
            "3.0453 W",
            "two five-via",
        ),
    )
    require_tokens(
        COUPON / "Q2-C100-pre-fab-screening.md",
        (
            "CALCULATION SCREEN COMPLETE / THERMAL, EXTRACTION AND FAB-REVIEW OPEN",
            "1.9033 mOhm",
            "3.0453 W",
            "seven TOLL source pads",
            "194.75 nH",
            "not an IPC-2152 ampacity claim",
        ),
    )
    require_tokens(
        COUPON / "Q2-C100-pre-fab-screening.csv",
        (
            "RAW_QDUT_NECK_FCU",
            "SOURCE_LEADS_AGGREGATE",
            "POWER_VIA_ROW_MIN_PLATING",
            "CONDITIONAL",
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
            "CRCW120610K0FKEAHP",
            "CRS1206QFX-1002ELF",
            "CGA3E2X7R1H104K080AE",
            "GCJ188R71H104KA12D",
            "436500228",
            "436500328",
            "436500428",
            "S1751-46R",
        ),
    )
    require_tokens(
        COUPON / "Q2-C100-bom.csv",
        (
            "QDUT",
            "UCTRL",
            "QREV",
            "786202073",
            "BZT52H-B56-Q",
            "CRCW120610K0FKEAHP",
            "CRCW120642K2FKEAHP",
            "CRCW06031K00FKEAHP",
            "CGA3E2X7R1H104K080AE",
            "436450208",
            "436450308",
            "436450408",
            "430300002",
            "430300039",
            "S1751-46R",
            "FAB-REVIEW",
        ),
    )
    require_tokens(
        COUPON / "Q2-C100-fixture-interface-selection.md",
        (
            "EXACT BOARD INTERFACE PARTS SELECTED / FIT, PROBES, SAFETY AND FAB-REVIEW OPEN",
            "SD-43650-010",
            "1.57 mm PCB",
            "2.0 mm",
            "3.18 mm terminal tails",
            "30 mating cycles",
            "manufacturer key coding",
            "S1751-46R",
            "does not specify a working-voltage or measurement-bandwidth rating",
            "does not authorize fabrication or energized use",
        ),
    )
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
        "ROV1": ("CRCW120642K2FKEAHP 42.2k 1%", "Q2C100:R_1206_3216Metric"),
        "ROV2": ("CRCW120642K2FKEAHP 42.2k 1%", "Q2C100:R_1206_3216Metric"),
        "ROV3": ("CRCW06031K00FKEAHP 1.00k 1%", "Q2C100:R_C_0603_1608Metric"),
        "RVS": ("CRCW120610K0FKEAHP 10.0k 1%", "Q2C100:R_1206_3216Metric"),
        "CCAP": ("CGA3E2X7R1H104K080AE 100nF 50V X7R", "Q2C100:R_C_0603_1608Metric"),
        "JDRIVE": ("436500428 MICRO-FIT 4POS DRIVER", "Q2C100:MicroFit_43650_0428_Vertical_R90"),
        "JHEAT": ("436500228 MICRO-FIT 2POS HEATER", "Q2C100:MicroFit_43650_0228_Vertical"),
        "JTEMP": ("436500328 MICRO-FIT 3POS TEMP", "Q2C100:MicroFit_43650_0328_Vertical"),
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
    for ref in ("TPD", "TPG", "TPS", "TPHG", "TPOUT", "TPOV", "TPVS", "TPFLT", "TPGND"):
        value, footprint = components.get(ref, ("", ""))
        if not value.startswith("S1751-46R ") or footprint != "Q2C100:Harwin_S1751-46R":
            fail(f"Q2-C100 {ref} test-point selection mismatch: {components.get(ref)}")
    for name, endpoint in {
        "EXT_TRIGGER": ("JDRIVE", "3"),
        "EXT_INTERLOCK": ("JDRIVE", "4"),
        "HEATER_POS": ("JHEAT", "1"),
        "HEATER_NEG": ("JHEAT", "2"),
        "TSEP_POS": ("JTEMP", "1"),
        "TSEP_NEG": ("JTEMP", "2"),
    }.items():
        require_net(nets, name, {endpoint})
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
    if len(drc.get("unconnected_items", [])) != EXPECTED_UNCONNECTED_ITEMS:
        fail(f"Q2-C100 must have zero unconnected items; found {len(drc.get('unconnected_items', []))}")
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
            'PAD-TO-PAD ROUTING COMPLETE; FAB REVIEW OPEN',
            '(segment ',
            '(via ',
            'Q2C100:MicroFit_43650_0228_Vertical',
            'Q2C100:MicroFit_43650_0328_Vertical',
            'Q2C100:MicroFit_43650_0428_Vertical_R90',
            'Q2C100:Harwin_S1751-46R',
            '(size 1.80 1.80) (drill 1.05)',
            '(size 1.30 1.30) (drill 1.30)',
            '(size 3.45 1.85)',
        ),
    )
    board_text = BOARD.read_text(encoding="utf-8")
    for placeholder in ("PinHeader_1x", "TestPoint_Loop_1.0mm"):
        if placeholder in board_text or placeholder in SCHEMATIC.read_text(encoding="utf-8"):
            fail(f"Q2-C100 obsolete fixture placeholder remains: {placeholder}")
    if "\n\t(zone " in board_text:
        fail("Q2-C100 pre-FAB-REVIEW milestone must not introduce unreviewed copper zones")

    require_tokens(
        RULES,
        (
            'rule "Q2-C100 default clearance"',
            "clearance (min 0.20mm)",
            'rule "Q2-C100 RAW 101V clearance"',
            "clearance (min 2.00mm)",
            "A.Reference == 'QDUT'",
            "A.Reference == 'ROV1'",
            "A.Reference == 'RVS'",
        ),
    )

    net_by_code = {
        int(code): name
        for code, name in re.findall(r'^\t\(net (\d+) "([^"]*)"\)$', board_text, re.MULTILINE)
    }
    expected_nets = {
        0: "",
        1: "COMMON_SOURCE",
        2: "CTRL_CAP",
        3: "CTRL_FLT_N",
        4: "CTRL_OV",
        5: "CTRL_VS",
        6: "EXT_INTERLOCK",
        7: "EXT_TRIGGER",
        8: "GND",
        9: "HEATER_NEG",
        10: "HEATER_POS",
        11: "OV_MID",
        12: "Q2_HGATE",
        13: "QREV_DGATE",
        14: "RAW_101V",
        15: "SYSTEM_OUT",
        16: "TSEP_NEG",
        17: "TSEP_POS",
    }
    if net_by_code != expected_nets:
        fail(f"Q2-C100 board net table changed: {net_by_code}")

    segment_pattern = re.compile(
        r'^\t\(segment \(start [-0-9.]+ [-0-9.]+\) \(end [-0-9.]+ [-0-9.]+\) '
        r'\(width ([0-9.]+)\) \(layer "([^"]+)"\) \(net (\d+)\)',
        re.MULTILINE,
    )
    segments = [
        (float(width), layer, net_by_code[int(code)])
        for width, layer, code in segment_pattern.findall(board_text)
    ]
    if not segments:
        fail("Q2-C100 board has no parsed routing segments")
    if any(width < 0.20 for width, _, _ in segments):
        fail("Q2-C100 contains a track below the reviewed 0.20 mm routing floor")
    if any(layer not in {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"} for _, layer, _ in segments):
        fail("Q2-C100 contains routing outside the reviewed four copper layers")

    routed_nets = {net for _, _, net in segments}
    expected_routed_nets = {
        "COMMON_SOURCE",
        "CTRL_CAP",
        "CTRL_FLT_N",
        "CTRL_OV",
        "CTRL_VS",
        "GND",
        "OV_MID",
        "Q2_HGATE",
        "QREV_DGATE",
        "RAW_101V",
        "SYSTEM_OUT",
    }
    if routed_nets != expected_routed_nets:
        fail(f"Q2-C100 routed-net set changed: {sorted(routed_nets)}")

    geometry_pattern = re.compile(
        r'^\t\(segment \(start ([-0-9.]+) ([-0-9.]+)\) \(end ([-0-9.]+) ([-0-9.]+)\) '
        r'\(width ([0-9.]+)\) \(layer "([^"]+)"\) \(net (\d+)\)',
        re.MULTILINE,
    )
    geometry = {
        (
            float(x1),
            float(y1),
            float(x2),
            float(y2),
            float(width),
            layer,
            net_by_code[int(code)],
        )
        for x1, y1, x2, y2, width, layer, code in geometry_pattern.findall(board_text)
    }
    required_power_geometry = {
        (40.0, 12.0, 40.0, 28.0, 7.0, layer, "RAW_101V")
        for layer in ("F.Cu", "B.Cu")
    } | {
        (40.0, 43.0, 40.0, 57.0, 6.0, layer, "COMMON_SOURCE")
        for layer in ("F.Cu", "B.Cu")
    } | {
        (40.0, 50.0, 70.0, 50.0, 6.0, layer, "COMMON_SOURCE")
        for layer in ("F.Cu", "B.Cu")
    } | {
        (40.0, 72.0, 40.0, 90.0, 7.0, layer, "SYSTEM_OUT")
        for layer in ("F.Cu", "B.Cu")
    } | {
        (40.0, 28.0, 40.0, 33.45, 6.5, "F.Cu", "RAW_101V"),
        (40.0, 66.55, 40.0, 72.0, 8.0, "F.Cu", "SYSTEM_OUT"),
        (37.0, 42.75, 44.2, 42.75, 4.0, "F.Cu", "COMMON_SOURCE"),
        (35.8, 57.25, 43.0, 57.25, 4.0, "F.Cu", "COMMON_SOURCE"),
    }
    qdut_spokes = {
        (x, 39.1, x, 42.75, 0.8, "F.Cu", "COMMON_SOURCE")
        for x in (37.0, 38.2, 39.4, 40.6, 41.8, 43.0, 44.2)
    }
    qrev_spokes = {
        (x, 60.9, x, 57.25, 0.8, "F.Cu", "COMMON_SOURCE")
        for x in (35.8, 37.0, 38.2, 39.4, 40.6, 41.8, 43.0)
    }
    missing_geometry = (required_power_geometry | qdut_spokes | qrev_spokes) - geometry
    if missing_geometry:
        fail(f"Q2-C100 reviewed high-current geometry changed: {sorted(missing_geometry)}")

    segment_layers: dict[str, set[str]] = {}
    for width, layer, net in segments:
        segment_layers.setdefault(net, set()).add(layer)
    if segment_layers["Q2_HGATE"] != {"F.Cu"}:
        fail("Q2_HGATE must remain a direct F.Cu-only correlation path")
    if "In1.Cu" not in segment_layers["QREV_DGATE"]:
        fail("QREV_DGATE must retain its reviewed In1.Cu crossing")
    if "In2.Cu" not in segment_layers["COMMON_SOURCE"]:
        fail("COMMON_SOURCE must retain separate In2.Cu Kelvin routing")
    if "In1.Cu" not in segment_layers["SYSTEM_OUT"]:
        fail("SYSTEM_OUT must retain separate In1.Cu controller-sense routing")

    for net, minimum_width in (("RAW_101V", 7.0), ("COMMON_SOURCE", 6.0), ("SYSTEM_OUT", 7.0)):
        for layer in ("F.Cu", "B.Cu"):
            if not any(
                routed_net == net and routed_layer == layer and width >= minimum_width
                for width, routed_layer, routed_net in segments
            ):
                fail(f"Q2-C100 {net} lacks the reviewed {minimum_width:.1f} mm {layer} power spine")

    via_pattern = re.compile(
        r'^\t\(via \(at [-0-9.]+ [-0-9.]+\) \(size ([0-9.]+)\) \(drill ([0-9.]+)\) '
        r'\(layers "F.Cu" "B.Cu"\) \(net (\d+)\)',
        re.MULTILINE,
    )
    vias = [
        (float(size), float(drill), net_by_code[int(code)])
        for size, drill, code in via_pattern.findall(board_text)
    ]
    if any(size < 0.8 or drill < 0.4 for size, drill, _ in vias):
        fail("Q2-C100 contains a via below the reviewed 0.8/0.4 mm minimum")
    for net, minimum_count in (("RAW_101V", 7), ("COMMON_SOURCE", 29), ("SYSTEM_OUT", 7)):
        power_vias = [(size, drill) for size, drill, via_net in vias if via_net == net]
        reviewed_power_vias = [
            (size, drill) for size, drill in power_vias if size >= 1.2 and drill >= 0.6
        ]
        if len(reviewed_power_vias) < minimum_count:
            fail(f"Q2-C100 {net} power-via stitching changed")

    via_geometry_pattern = re.compile(
        r'^\t\(via \(at ([-0-9.]+) ([-0-9.]+)\) \(size ([0-9.]+)\) \(drill ([0-9.]+)\) '
        r'\(layers "F.Cu" "B.Cu"\) \(net (\d+)\)',
        re.MULTILINE,
    )
    via_geometry = {
        (float(x), float(y), float(size), float(drill), net_by_code[int(code)])
        for x, y, size, drill, code in via_geometry_pattern.findall(board_text)
    }
    required_vias = {
        (x, y, 1.2, 0.6, "RAW_101V")
        for x, y in ((37.0, 20.0), (43.0, 20.0), (37.0, 28.0), (38.5, 28.0), (40.0, 28.0), (41.5, 28.0), (43.0, 28.0))
    } | {
        (x, y, 1.2, 0.6, "COMMON_SOURCE")
        for y in (42.0, 43.5, 56.5, 58.0)
        for x in (37.0, 38.5, 40.0, 41.5, 43.0)
    } | {
        (x, 50.0, 1.2, 0.6, "COMMON_SOURCE")
        for x in (37.0, 43.0, 50.0, 60.0)
    } | {
        (x, y, 1.2, 0.6, "SYSTEM_OUT")
        for x, y in ((37.0, 72.0), (38.5, 72.0), (40.0, 72.0), (41.5, 72.0), (43.0, 72.0), (37.0, 80.0), (43.0, 80.0))
    }
    missing_vias = required_vias - via_geometry
    if missing_vias:
        fail(f"Q2-C100 reviewed power-via field changed: {sorted(missing_vias)}")


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
    print("Q2-C100 validation passed (ERC 0, DRC 0, unconnected 0, parity 4 board holes; FAB-REVIEW remains open).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
