from __future__ import annotations

from .common import (
    DISALLOWED_LAYOUT_NAME_FRAGMENTS,
    DISALLOWED_LAYOUT_SUFFIXES,
    ET,
    FORBIDDEN_ROLE_TOKENS,
    KICAD_DIR,
    MANUFACTURING_HINT_SUFFIXES,
    MIN_KICAD_COMPONENTS,
    MIN_KICAD_NETS,
    PB100_DIR,
    PRODUCTION_DIR,
    QUALIFICATION_COUPON_LAYOUT_ALLOWLIST,
    Path,
    REPO_ROOT,
    REQUIRED_KICAD_CLI_VERSION,
    csv,
    fail,
    json,
    re,
    read_text,
    shutil,
    subprocess,
    tempfile,
    validate_s_expression_balance,
)


def validate_kicad_scaffold() -> None:
    json.loads(read_text(KICAD_DIR / "PB-100.kicad_pro"))
    for schematic_path in sorted(KICAD_DIR.rglob("*.kicad_sch")):
        validate_s_expression_balance(schematic_path)
    for table_name in ("sym-lib-table", "fp-lib-table"):
        validate_s_expression_balance(KICAD_DIR / table_name)
    validate_s_expression_balance(KICAD_DIR / "lib" / "PB100.kicad_sym")
    validate_no_layout_artifacts()
    validate_kicad_top_sheet_links()
    validate_kicad_no_sheet_placeholders()


def validate_kicad_top_sheet_links() -> None:
    top_path = KICAD_DIR / "PB-100.kicad_sch"
    top_text = read_text(top_path)
    manifest_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-kicad-sheet-manifest.csv").open(newline="", encoding="utf-8"))
    )
    child_sheets = [row["Sheet file"].strip() for row in manifest_rows if row["Sheet kind"].strip() == "child"]
    for sheet_file in child_sheets:
        sheet_path = KICAD_DIR / "sheets" / sheet_file
        if not sheet_path.exists():
            fail(f"missing child sheet linked by manifest: {sheet_path.relative_to(REPO_ROOT)}")
        sheet_name = sheet_file.removesuffix(".kicad_sch")
        sheetfile_token = f'(property "Sheetfile" "sheets/{sheet_file}"'
        sheetname_token = f'(property "Sheetname" "{sheet_name}"'
        if sheetfile_token not in top_text:
            fail(f"{top_path.relative_to(REPO_ROOT)} must link sheets/{sheet_file}")
        if sheetname_token not in top_text:
            fail(f"{top_path.relative_to(REPO_ROOT)} must name child sheet {sheet_name}")


def validate_kicad_no_sheet_placeholders() -> None:
    for schematic_path in sorted(KICAD_DIR.rglob("*.kicad_sch")):
        text = read_text(schematic_path).lower()
        for token in ("sheet-placeholder", "placeholder sheet"):
            if token in text:
                fail(
                    f"{schematic_path.relative_to(REPO_ROOT)} still contains `{token}`; "
                    "PB-100 child sheets must contain captured schematic content before ERC/netlist validation"
                )


def validate_kicad_cli_checks() -> None:
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli is None:
        fail("kicad-cli is required for PB-100 validation; install KiCad CLI before running make check")

    version_result = subprocess.run(
        [kicad_cli, "--version"],
        check=False,
        text=True,
        capture_output=True)
    if version_result.returncode != 0:
        details = "\n".join(part for part in (version_result.stdout.strip(), version_result.stderr.strip()) if part)
        fail(f"unable to read kicad-cli version: {details}")
    actual_version = version_result.stdout.strip()
    if actual_version != REQUIRED_KICAD_CLI_VERSION:
        fail(f"kicad-cli version {actual_version} is not the required {REQUIRED_KICAD_CLI_VERSION}")

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
    component_count = len(re.findall(r"(?m)^\s*\(comp\b", netlist_text))
    net_count = len(re.findall(r"(?m)^\s*\(net\b", netlist_text))
    if component_count < MIN_KICAD_COMPONENTS:
        fail(
            f"KiCad netlist has {component_count} components; "
            f"expected at least {MIN_KICAD_COMPONENTS}"
        )
    if net_count < MIN_KICAD_NETS:
        fail(
            f"KiCad netlist has {net_count} electrical nets; "
            f"expected at least {MIN_KICAD_NETS}"
        )
    validate_can1_netlist_topology(kicad_cli, temp_dir)
    print("PB-100 KiCad netlist export passed")


def validate_can1_netlist_topology(kicad_cli: str, temp_dir: Path) -> None:
    """Validate the captured CAN1 safety circuit from connectivity, not labels in prose."""
    netlist_path = temp_dir / "PB-100.xml"
    command = [
        kicad_cli,
        "sch",
        "export",
        "netlist",
        "--format",
        "kicadxml",
        "--output",
        str(netlist_path),
        str(KICAD_DIR / "PB-100.kicad_sch"),
    ]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        fail(f"KiCad XML netlist export failed for CAN1 topology validation: {details}")

    try:
        root = ET.parse(netlist_path).getroot()
    except (ET.ParseError, OSError) as error:
        fail(f"invalid KiCad XML netlist for CAN1 topology validation: {error}")

    components = {
        component.get("ref", ""): component
        for component in root.findall("./components/comp")
    }
    expected_components = {
        "JP_CAN1": ("CAN1_TX_DNP_LINK_PRELIM", "PB100:R0603_DNP_LINK_1608Metric"),
        "U_CAN1": ("SN74LVC1G125_Q1_DBV_PRELIM", "PB100:SOT-23-5_DBV_TI"),
        "R_CAN1_OE": ("47k 1%", "PB100:R0402"),
        "R_CAN1_TX_BIAS": ("47k 1%", "PB100:R0402"),
        "R_CAN1_STATUS_SER": ("1k 1%", "PB100:R0402"),
        "R_CAN1_STATUS_PULL": ("100k 1%", "PB100:R0402"),
        "U_CAN1_PHY": ("TJA1051TK/3/1J", "PB100:HVSON-8_L3.0-W3.0-P0.65-BL-EP"),
        "R_CAN1_SILENT": ("47k 1%", "PB100:R0402"),
        "JP_CAN1_NORMAL": ("CAN1_NORMAL_MODE_DNP", "PB100:R0603_DNP_LINK_1608Metric"),
        "D_CAN1": ("ESD2CANFD24QDBZRQ1", "PB100:SOT-23-3_DBZ_TI"),
        "R_CAN1_TERM": ("120R 1% DNP", "PB100:R0603_DNP_LINK_1608Metric"),
        "C_CAN1_VCC": ("100nF 50V X7R", "PB100:C0402"),
        "C_CAN1_VIO": ("100nF 50V X7R", "PB100:C0402"),
    }
    for reference, (expected_value, expected_footprint) in expected_components.items():
        component = components.get(reference)
        if component is None:
            fail(f"CAN1 topology is missing physical component {reference}")
        value = component.findtext("value", default="").strip()
        footprint = component.findtext("footprint", default="").strip()
        if value != expected_value:
            fail(f"CAN1 component {reference} value is {value!r}; expected {expected_value!r}")
        if footprint != expected_footprint:
            fail(
                f"CAN1 component {reference} footprint is {footprint!r}; "
                f"expected {expected_footprint!r}"
            )

    if components["JP_CAN1"].find("./property[@name='dnp']") is None:
        fail("JP_CAN1 must be physically marked DNP in the exported KiCad netlist")
    for reference in ("JP_CAN1_NORMAL", "R_CAN1_TERM"):
        if components[reference].find("./property[@name='dnp']") is None:
            fail(f"{reference} must be physically marked DNP in the exported KiCad netlist")

    nets = {}
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        nets[name] = {(node.get("ref", ""), node.get("pin", "")) for node in net.findall("node")}

    validate_input_power_netlist_topology(components, nets)

    exact_nets = {
        "CAN1_TX_ROUTE": {("JPB1", "70"), ("U_CAN1", "2")},
        "CAN1_TX_GATE_OUT": {("U_CAN1", "4"), ("JP_CAN1", "1")},
        "CAN1_TXD_SAFE": {
            ("JP_CAN1", "2"),
            ("R_CAN1_TX_BIAS", "2"),
            ("U_CAN1_PHY", "1"),
        },
        "CAN1_RX_ROUTE": {("JPB1", "69"), ("U_CAN1_PHY", "4")},
        "CAN1_PHY_SILENT": {
            ("JP_CAN1_NORMAL", "1"),
            ("R_CAN1_SILENT", "2"),
            ("U_CAN1_PHY", "8"),
        },
        "CAN1_HARNESS_H": {
            ("D_CAN1", "1"),
            ("R_CAN1_TERM", "1"),
            ("U_CAN1_PHY", "7"),
        },
        "CAN1_HARNESS_L": {
            ("D_CAN1", "2"),
            ("R_CAN1_TERM", "2"),
            ("U_CAN1_PHY", "6"),
        },
        "CAN1_TX_DISABLED_STATUS": {
            ("JPB1", "68"),
            ("R_CAN1_STATUS_SER", "2"),
            ("R_CAN1_STATUS_PULL", "2"),
        },
        "CAN1_TX_DISABLE_CMD": {
            ("JPB1", "67"),
            ("U_CAN1", "1"),
            ("R_CAN1_OE", "2"),
            ("R_CAN1_STATUS_SER", "1"),
        },
    }
    for net_name, expected_nodes in exact_nets.items():
        actual_nodes = nets.get(net_name)
        if actual_nodes != expected_nodes:
            fail(
                f"CAN1 net {net_name} has nodes {sorted(actual_nodes or set())}; "
                f"expected {sorted(expected_nodes)}"
            )

    rail_nodes = nets.get("LB_3V3_IO", set())
    required_rail_nodes = {
        ("U_CAN1", "5"),
        ("R_CAN1_OE", "1"),
        ("R_CAN1_TX_BIAS", "1"),
        ("R_CAN1_STATUS_PULL", "1"),
        ("U_CAN1_PHY", "5"),
        ("R_CAN1_SILENT", "1"),
        ("C_CAN1_VIO", "1"),
    }
    missing_rail_nodes = required_rail_nodes - rail_nodes
    if missing_rail_nodes:
        fail(f"CAN1 safety pull-ups are not tied to LB_3V3_IO: {sorted(missing_rail_nodes)}")

    required_pb5v_nodes = {("U_CAN1_PHY", "3"), ("C_CAN1_VCC", "1")}
    missing_pb5v_nodes = required_pb5v_nodes - nets.get("PB_5V_OUT", set())
    if missing_pb5v_nodes:
        fail(f"CAN1 transceiver VCC is not tied to PB_5V_OUT: {sorted(missing_pb5v_nodes)}")
    required_ground_nodes = {
        ("U_CAN1_PHY", "2"),
        ("U_CAN1_PHY", "9"),
        ("D_CAN1", "3"),
        ("JP_CAN1_NORMAL", "2"),
        ("C_CAN1_VCC", "2"),
        ("C_CAN1_VIO", "2"),
    }
    missing_ground_nodes = required_ground_nodes - nets.get("GND", set())
    if missing_ground_nodes:
        fail(f"CAN1 physical-layer ground is incomplete: {sorted(missing_ground_nodes)}")

    jpb1 = components.get("JPB1")
    if jpb1 is None:
        fail("PB-100 topology is missing JPB1")
    if jpb1.findtext("footprint", default="").strip() != "PB100:FX18-100P-0.8SV10_Hirose":
        fail("JPB1 must bind the reviewed Hirose FX18-100P footprint")
    mf_nodes = {
        ("JPB1", "MF_A_PIN1_51_END"),
        ("JPB1", "MF_B_PIN1_51_END"),
        ("JPB1", "MF_A_PIN50_100_END"),
        ("JPB1", "MF_B_PIN50_100_END"),
    }
    missing_mf_nodes = mf_nodes - nets.get("GND", set())
    if missing_mf_nodes:
        fail(f"JPB1 MF contacts are not tied only to GND: {sorted(missing_mf_nodes)}")
    forbidden_mf_nets = {
        net_name: sorted(mf_nodes & nodes)
        for net_name, nodes in nets.items()
        if net_name in {"AGND", "PB_5V_OUT", "LB_3V3_IO", "VBAT", "VBAT_RAW", "VBAT_PROT"}
        and mf_nodes & nodes
    }
    if forbidden_mf_nets:
        fail(f"JPB1 MF contacts are tied to forbidden nets: {forbidden_mf_nets}")

    print("PB-100 CAN1 and JPB1 MF physical net topology passed")


def validate_input_power_netlist_topology(components, nets) -> None:
    """Keep the active cutoff and total-current shunt in the only load path."""
    for reference in ("D1", "U1", "Q1", "Q2", "RSH1", "U2", "U3"):
        if reference not in components:
            fail(f"input power topology is missing physical component {reference}")
    if components["D1"].find("./property[@name='dnp']") is None:
        fail("legacy input TVS D1 must remain physically marked DNP")

    required_nodes = {
        "VBAT_RAW": {("Q2", "Tab")},
        "INPUT_COMMON_SOURCE": {
            *(("Q1", str(pin)) for pin in range(2, 9)),
            *(("Q2", str(pin)) for pin in range(2, 9)),
            ("U1", "2"),
            ("U1", "15"),
        },
        "VBAT_REV_PROT": {
            ("Q1", "Tab"),
            ("RSH1", "1"),
            ("U1", "18"),
            ("U1", "19"),
            ("U1", "20"),
            ("U1", "24"),
        },
        "VBAT_PROT": {
            ("RSH1", "2"),
            ("U2", "8"),
            ("U3", "2"),
            ("U101", "20"),
        },
        "IIN_SHUNT_IN": {("RSH1", "3"), ("U2", "10")},
        "IIN_SHUNT_OUT": {("RSH1", "4"), ("U2", "9")},
    }
    for net_name, expected_subset in required_nodes.items():
        missing_nodes = expected_subset - nets.get(net_name, set())
        if missing_nodes:
            fail(f"input power net {net_name} is missing {sorted(missing_nodes)}")

    forbidden_nodes = {
        "VBAT_RAW": {("Q1", "Tab"), ("RSH1", "1"), ("RSH1", "2")},
        "VBAT_REV_PROT": {("RSH1", "2"), ("U2", "8"), ("U3", "2"), ("U101", "20")},
        "VBAT_PROT": {("Q1", "Tab"), ("RSH1", "1")},
    }
    for net_name, forbidden_subset in forbidden_nodes.items():
        unexpected_nodes = forbidden_subset & nets.get(net_name, set())
        if unexpected_nodes:
            fail(f"input power net {net_name} contains forbidden nodes {sorted(unexpected_nodes)}")

    print("PB-100 active-cutoff and shunt topology passed")


def validate_no_layout_artifacts() -> None:
    search_roots = (PB100_DIR, PRODUCTION_DIR)
    for search_root in search_roots:
        for path in search_root.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.lower()
            suffix = path.suffix.lower()
            if path in QUALIFICATION_COUPON_LAYOUT_ALLOWLIST:
                continue
            if name.endswith(".kicad_pcb-bak") or suffix in DISALLOWED_LAYOUT_SUFFIXES:
                fail(f"layout/manufacturing artifact is blocked before schematic freeze: {path.relative_to(REPO_ROOT)}")
            if suffix in MANUFACTURING_HINT_SUFFIXES and any(fragment in name for fragment in DISALLOWED_LAYOUT_NAME_FRAGMENTS):
                fail(f"layout/manufacturing artifact name is blocked before schematic freeze: {path.relative_to(REPO_ROOT)}")


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
