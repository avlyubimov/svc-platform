from __future__ import annotations

from .common import (
    FORBIDDEN_ROLE_TOKENS,
    INPUT_PROTECTION_PIN_CONTRACT_COLUMNS,
    LOGIC_POWER_DESIGN_COLUMNS,
    OUTPUT_CHANNEL_PIN_CONTRACT_COLUMNS,
    OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS,
    OUTPUT_CONTROLLER_SYMBOL,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_LOGIC_POWER_ITEMS,
    csv,
    fail,
    validate_csv,
)


def validate_output_channel_pin_contract() -> None:
    path = PB100_DIR / "PB-100-output-channel-pin-contract.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output channel pin contract: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_CHANNEL_PIN_CONTRACT_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    output_matrix_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-output-channel-matrix.csv").open(newline="", encoding="utf-8"))
    )
    expected_outputs = {row["Output"].strip() for row in output_matrix_rows}
    instance_map_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-instance-symbol-map.csv").open(newline="", encoding="utf-8"))
    )
    symbol_key_by_ref = {row["Ref"].strip(): row["Symbol key"].strip() for row in instance_map_rows}
    b2b_rows = list(csv.DictReader((PB100_DIR / "PB-100-b2b-pin-map.csv").open(newline="", encoding="utf-8")))
    b2b_nets = {row["Net"].strip() for row in b2b_rows}

    seen_outputs = set()
    for row_number, row in enumerate(rows, 2):
        output = row["Output"].strip()
        if output in seen_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate output {output}")
        seen_outputs.add(output)
        if output not in expected_outputs:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown output {output}")
        try:
            output_number = int(output.removeprefix("OUT"))
        except ValueError:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid output name {output}")

        expected_refs = {
            "Controller ref": (f"U{100 + output_number}", "HS_CTRL"),
            "Switch ref": (f"Q{100 + output_number}", "OUT_FET"),
            "Fuse ref": (f"F{100 + output_number}", "OUTPUT_FUSE_HOLDER"),
            "Connector ref": (f"J{100 + output_number}", "OUTPUT_CONNECTOR"),
        }
        for column, (expected_ref, expected_key) in expected_refs.items():
            actual_ref = row[column].strip()
            if actual_ref != expected_ref:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {column} must be "
                    f"{expected_ref}, got {actual_ref}"
                )
            actual_key = symbol_key_by_ref.get(actual_ref)
            if actual_key != expected_key:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {actual_ref} must map to "
                    f"{expected_key}, got {actual_key}"
                )

        expected_nets = {
            "Control net": f"{output}_CTL",
            "Fault net": f"{output}_FLT",
            "Current net": f"{output}_IMON",
            "Load net": f"{output}_LOAD",
            "Fused net": f"{output}_FUSED",
        }
        for column, expected_net in expected_nets.items():
            actual_net = row[column].strip()
            if actual_net != expected_net:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {column} must be "
                    f"{expected_net}, got {actual_net}"
                )
            for forbidden_token in FORBIDDEN_ROLE_TOKENS:
                if forbidden_token in actual_net:
                    fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net {actual_net}")

        for connector_net in (row["Control net"].strip(), row["Fault net"].strip(), row["Current net"].strip()):
            if connector_net not in b2b_nets:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: {connector_net} "
                    "is missing from PB-100-b2b-pin-map.csv"
                )

        default_state = row["Default state"].strip().lower()
        safety_rule = row["Safety rule"].strip().lower()
        if "off" not in default_state:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: default state must be off")
        if "configuration" not in safety_rule:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: safety rule must preserve configuration mapping")
        if output == "OUT2" and "soa" not in safety_rule:
            fail("OUT2 output pin contract must keep SOA close work explicit")

    missing_outputs = sorted(expected_outputs - seen_outputs)
    extra_outputs = sorted(seen_outputs - expected_outputs)
    if missing_outputs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing outputs: "
            f"{', '.join(missing_outputs)}"
        )
    if extra_outputs:
        fail(
            f"{path.relative_to(REPO_ROOT)} has outputs not in output matrix: "
            f"{', '.join(extra_outputs)}"
        )


def validate_output_controller_pin_template() -> None:
    path = PB100_DIR / "PB-100-output-controller-pin-template.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty output controller pin template: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    evidence_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-pin-evidence.csv").open(newline="", encoding="utf-8"))
    )
    evidence_pins = {
        row["Pin number"].strip(): row["Pin name"].strip()
        for row in evidence_rows
        if row["Symbol name"].strip() == OUTPUT_CONTROLLER_SYMBOL
    }
    if not evidence_pins:
        fail(f"missing pin evidence for {OUTPUT_CONTROLLER_SYMBOL}")

    seen_pins = set()
    net_patterns = set()
    for row_number, row in enumerate(rows, 2):
        pin_number = row["Pin number"].strip()
        pin_name = row["Pin name"].strip()
        net_pattern = row["Net pattern"].strip()
        for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if pin_number in seen_pins:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate pin {pin_number}")
        seen_pins.add(pin_number)
        expected_pin_name = evidence_pins.get(pin_number)
        if expected_pin_name is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} is not in pin evidence")
        if pin_name != expected_pin_name:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} must be "
                f"{expected_pin_name}, got {pin_name}"
            )
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in net_pattern:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net pattern {net_pattern}")
        if not (
            net_pattern.startswith("OUTn_")
            or net_pattern in {"GND", "NC", "VBAT_PROT"}
        ):
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: unsupported output-controller "
                f"net pattern {net_pattern}"
            )
        if pin_name == "N.C." and net_pattern != "NC":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: N.C. pin must use NC net pattern")
        if pin_name == "GND" and net_pattern != "GND":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: GND pin must use GND net pattern")
        if pin_name == "VS" and net_pattern != "VBAT_PROT":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: VS pin must use VBAT_PROT")
        if "final" in row["Default state"].lower() and "not final" not in row["Default state"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: default state must not lock final values")
        if "schematic review" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic review")
        net_patterns.add(net_pattern)

    missing_pins = sorted(evidence_pins.keys() - seen_pins, key=lambda value: int(value))
    extra_pins = sorted(seen_pins - evidence_pins.keys(), key=lambda value: int(value))
    if missing_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing controller pins: "
            f"{', '.join(missing_pins)}"
        )
    if extra_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} has pins not in evidence: "
            f"{', '.join(extra_pins)}"
        )
    for required_pattern in ("OUTn_CTL", "OUTn_FLT", "OUTn_IMON", "OUTn_SRC", "OUTn_PU", "OUTn_PD", "VBAT_PROT"):
        if required_pattern not in net_patterns:
            fail(
                f"{path.relative_to(REPO_ROOT)} is missing required output-controller "
                f"net pattern {required_pattern}"
            )


def sort_pin_number(pin_number: str) -> tuple[int, str]:
    return (0, f"{int(pin_number):04d}") if pin_number.isdigit() else (1, pin_number)


def validate_component_pin_template(
    file_name: str,
    symbol_name: str,
    allowed_net_patterns: set[str],
    required_net_patterns: set[str],
) -> None:
    path = PB100_DIR / file_name
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty component pin template: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    evidence_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-symbol-pin-evidence.csv").open(newline="", encoding="utf-8"))
    )
    evidence_pins = {
        row["Pin number"].strip(): row["Pin name"].strip()
        for row in evidence_rows
        if row["Symbol name"].strip() == symbol_name
    }
    if not evidence_pins:
        fail(f"missing pin evidence for {symbol_name}")

    seen_pins = set()
    net_patterns = set()
    for row_number, row in enumerate(rows, 2):
        pin_number = row["Pin number"].strip()
        pin_name = row["Pin name"].strip()
        net_pattern = row["Net pattern"].strip()
        for column in OUTPUT_CONTROLLER_PIN_TEMPLATE_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        if pin_number in seen_pins:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate pin {pin_number}")
        seen_pins.add(pin_number)
        expected_pin_name = evidence_pins.get(pin_number)
        if expected_pin_name is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} is not in pin evidence")
        if pin_name != expected_pin_name:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: pin {pin_number} must be "
                f"{expected_pin_name}, got {pin_name}"
            )
        if net_pattern not in allowed_net_patterns:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: unsupported net pattern "
                f"{net_pattern}"
            )
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in net_pattern:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in net pattern {net_pattern}")
        if "final" in row["Default state"].lower() and "not final" not in row["Default state"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: default state must not lock final values")
        if "schematic review" not in row["Freeze dependency"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: freeze dependency must reference schematic review")
        net_patterns.add(net_pattern)

    missing_pins = sorted(evidence_pins.keys() - seen_pins, key=sort_pin_number)
    extra_pins = sorted(seen_pins - evidence_pins.keys(), key=sort_pin_number)
    if missing_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing pins for {symbol_name}: "
            f"{', '.join(missing_pins)}"
        )
    if extra_pins:
        fail(
            f"{path.relative_to(REPO_ROOT)} has pins not in evidence for {symbol_name}: "
            f"{', '.join(extra_pins)}"
        )

    missing_patterns = sorted(required_net_patterns - net_patterns)
    if missing_patterns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required net patterns: "
            f"{', '.join(missing_patterns)}"
        )


def validate_input_and_power_pin_templates() -> None:
    validate_component_pin_template(
        "PB-100-input-controller-pin-template.csv",
        "PB100_LM74700QDBVRQ1_PRELIM",
        {
            "LM74700_VCAP",
            "GND",
            "INPUT_PROT_EN",
            "VBAT_REV_PROT",
            "INPUT_FET_GATE",
            "VBAT_RAW",
        },
        {"VBAT_RAW", "VBAT_REV_PROT", "INPUT_FET_GATE", "INPUT_PROT_EN"},
    )
    validate_component_pin_template(
        "PB-100-current-monitor-pin-template.csv",
        "PB100_INA228_Q1_PRELIM",
        {
            "IIN_MON_A1",
            "IIN_MON_A0",
            "PB_I2C_INT",
            "PB_I2C_SDA",
            "PB_I2C_SCL",
            "LB_3V3_IO",
            "GND",
            "VBAT_PROT",
            "IIN_SHUNT_LO",
            "IIN_SHUNT_HI",
        },
        {"IIN_SHUNT_HI", "IIN_SHUNT_LO", "PB_I2C_SDA", "PB_I2C_SCL", "VBAT_PROT"},
    )
    validate_component_pin_template(
        "PB-100-logic-buck-pin-template.csv",
        "PB100_LM5164QDDATQ1_PRELIM",
        {
            "GND",
            "VBAT_PROT",
            "BUCK_EN_UVLO",
            "BUCK_RON_SET",
            "BUCK_FB",
            "PB_PWR_GOOD",
            "BUCK_BST",
            "BUCK_SW",
        },
        {"VBAT_PROT", "BUCK_EN_UVLO", "BUCK_FB", "PB_PWR_GOOD", "BUCK_SW"},
    )


def validate_input_protection_pin_contract() -> None:
    path = PB100_DIR / "PB-100-input-protection-pin-contract.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty input protection pin contract: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in INPUT_PROTECTION_PIN_CONTRACT_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    instance_map_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-schematic-instance-symbol-map.csv").open(newline="", encoding="utf-8"))
    )
    instance_by_ref = {row["Ref"].strip(): row for row in instance_map_rows}
    required_refs = {"J1", "D1", "U1", "Q1", "RSH1", "U2"}
    required_nets = {
        "VBAT_RAW",
        "GND",
        "VBAT_PROT",
        "INPUT_FET_GATE",
        "VBAT_REV_PROT",
        "IIN_SHUNT_HI",
        "IIN_SHUNT_LO",
        "IIN_SENSE",
        "VBAT_SENSE",
    }
    seen_refs = set()
    seen_nets = set()
    q1_rows = []
    for row_number, row in enumerate(rows, 2):
        ref = row["Ref"].strip()
        symbol_key = row["Symbol key"].strip()
        concrete_symbol_name = row["Concrete symbol name"].strip()
        planned_net = row["Planned net"].strip()
        for column in ("Ref", "Symbol key", "Concrete symbol name", "Interface point", "Planned net", "Direction", "Default state", "Freeze dependency"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        instance_row = instance_by_ref.get(ref)
        if instance_row is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown instance ref {ref}")
        if symbol_key != instance_row["Symbol key"].strip():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} uses {symbol_key}, "
                f"but instance-symbol map uses {instance_row['Symbol key'].strip()}"
            )
        if concrete_symbol_name != instance_row["Concrete symbol name"].strip():
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: {ref} uses {concrete_symbol_name}, "
                f"but instance-symbol map uses {instance_row['Concrete symbol name'].strip()}"
            )
        for forbidden_token in FORBIDDEN_ROLE_TOKENS:
            if forbidden_token in planned_net:
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: role token in planned net {planned_net}")
        seen_refs.add(ref)
        seen_nets.add(planned_net)
        if ref == "Q1":
            q1_rows.append(row)

    missing_refs = sorted(required_refs - seen_refs)
    if missing_refs:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input refs: "
            f"{', '.join(missing_refs)}"
        )
    missing_nets = sorted(required_nets - seen_nets)
    if missing_nets:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing input planned nets: "
            f"{', '.join(missing_nets)}"
        )
    if not q1_rows:
        fail("input protection pin contract must include Q1 reverse FET rows")
    q1_state = instance_by_ref["Q1"]["Symbol state"].strip()
    if q1_state != "Created":
        fail("Q1 must be Created after INPUT_REVERSE_FET symbol evidence closes")
    q1_close_text = " ".join(
        row[column]
        for row in q1_rows
        for column in ("Interface point", "Default state", "Freeze dependency")
    )
    if not all(token in q1_close_text for token in ("BUK7S1R2-80M", "LFPAK88", "40 A")):
        fail("Q1 input protection rows must keep selected 80 V LFPAK88 and 40 A review explicit")


def validate_logic_power_design_placeholders() -> None:
    path = PB100_DIR / "PB-100-logic-power-design-placeholders.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty logic power design placeholders: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in LOGIC_POWER_DESIGN_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    seen_items = set()
    refs_or_nets = set()
    for row_number, row in enumerate(rows, 2):
        item = row["Item"].strip()
        if not item:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: missing Item")
        if item in seen_items:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Item {item}")
        seen_items.add(item)
        refs_or_nets.add(row["Ref or net"].strip())
        for column in ("Ref or net", "Design state", "Value status", "Freeze dependency", "Notes"):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

        value_status = row["Value status"].strip().lower()
        if "final" in value_status and "not final" not in value_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: logic power value must not be final before review")
        for blocked_word in ("locked", "released"):
            if blocked_word in value_status:
                fail(
                    f"{path.relative_to(REPO_ROOT)}:{row_number}: logic power value "
                    f"must not be {blocked_word} before review"
                )
        if "tbd" not in value_status and "not final" not in value_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Value status must remain TBD/not final")

    missing_items = sorted(REQUIRED_LOGIC_POWER_ITEMS - seen_items)
    if missing_items:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing logic power items: "
            f"{', '.join(missing_items)}"
        )
    for required_ref_or_net in ("U3", "L1", "VBAT_PROT", "PB_5V_OUT", "PB_PWR_GOOD"):
        if required_ref_or_net not in refs_or_nets:
            fail(
                f"{path.relative_to(REPO_ROOT)} is missing required logic power "
                f"ref/net {required_ref_or_net}"
            )
