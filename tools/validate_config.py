#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "firmware" / "configs" / "config-example.json"
CONFIG_SCHEMA_PATH = REPO_ROOT / "firmware" / "configs" / "svc-config.schema.json"
PB100_CAPABILITIES_PATH = REPO_ROOT / "firmware" / "configs" / "hardware" / "pb-100-capabilities.json"
CONFIG_ACCEPTANCE_HEADER_PATH = REPO_ROOT / "firmware" / "services" / "config_acceptance.h"
CONFIG_ACCEPTANCE_IMPL_PATH = REPO_ROOT / "firmware" / "services" / "config_acceptance.c"
CONFIG_STORE_HEADER_PATH = REPO_ROOT / "firmware" / "services" / "config_store.h"
CONFIG_STORE_IMPL_PATH = REPO_ROOT / "firmware" / "services" / "config_store.c"
HARDWARE_CAPABILITY_HEADER_PATH = REPO_ROOT / "firmware" / "services" / "hardware_capability.h"
HARDWARE_CAPABILITY_IMPL_PATH = REPO_ROOT / "firmware" / "services" / "hardware_capability.c"
PB100_CAPABILITY_HEADER_PATH = REPO_ROOT / "firmware" / "services" / "pb100_capability.h"
PB100_CAPABILITY_IMPL_PATH = REPO_ROOT / "firmware" / "services" / "pb100_capability.c"
CONFIG_ACCEPTANCE_TEST_PATH = REPO_ROOT / "firmware" / "tests" / "test_config_acceptance.c"
CONFIG_STORE_TEST_PATH = REPO_ROOT / "firmware" / "tests" / "test_config_store.c"
HARDWARE_CAPABILITY_TEST_PATH = REPO_ROOT / "firmware" / "tests" / "test_hardware_capability.c"
RUNTIME_BOOT_HEADER_PATH = REPO_ROOT / "firmware" / "services" / "runtime_boot.h"
RUNTIME_BOOT_IMPL_PATH = REPO_ROOT / "firmware" / "services" / "runtime_boot.c"
RUNTIME_BOOT_TEST_PATH = REPO_ROOT / "firmware" / "tests" / "test_runtime_boot.c"
CONFIGURATION_DOC_PATH = REPO_ROOT / "firmware" / "services" / "configuration.md"
CONFIG_STORE_DOC_PATH = REPO_ROOT / "firmware" / "services" / "config-store.md"
RUNTIME_BOOT_DOC_PATH = REPO_ROOT / "firmware" / "services" / "runtime-boot.md"
SYSTEM_SAFETY_DOC_PATH = REPO_ROOT / "firmware" / "services" / "system-safety.md"
SVC_TYPES_PATH = REPO_ROOT / "firmware" / "core" / "svc_types.h"
SVC_CONFIG_PATH = REPO_ROOT / "firmware" / "core" / "svc_config.h"
SVC_DEFAULTS_PATH = REPO_ROOT / "firmware" / "core" / "svc_config_defaults.c"
POWER_BUDGET_PATH = REPO_ROOT / "firmware" / "services" / "power_budget.h"
PB100_OUTPUT_MATRIX_PATH = REPO_ROOT / "hardware" / "power-board" / "PB-100" / "PB-100-output-channel-matrix.csv"
PB100_CURRENT_TELEMETRY_PATH = REPO_ROOT / "hardware" / "power-board" / "PB-100" / "PB-100-current-telemetry-map.csv"
PB100_THERMAL_TELEMETRY_PATH = REPO_ROOT / "hardware" / "power-board" / "PB-100" / "PB-100-thermal-telemetry-map.csv"
FORBIDDEN_HARDWARE_CAPABILITY_ROLE_TOKENS = (
    "USB",
    "FOG",
    "SEAT",
    "CHIGEE",
    "DVR",
    "BRAKE",
    "CIGARETTE",
)
REQUIRED_HARDWARE_CAPABILITY_TOKENS = (
    "svc_config_accept_for_hardware",
    "svc_config_store_load_latest",
    "SVC_CONFIG_STORE_LOAD_FALLBACK_DEFAULT",
    "SVC_CONFIG_STORE_SOURCE_FALLBACK_DEFAULT",
    "SVC_CONFIG_ACCEPTANCE_CONFIG_EXCEEDS_HARDWARE",
    "SVC_CONFIG_ACCEPTANCE_INVALID_HARDWARE_CAPABILITY",
    "svc_runtime_boot",
    "SVC_RUNTIME_BOOT_REJECTED_CONFIG",
    "SVC_RUNTIME_BOOT_INVALID_ARGUMENT",
    "svc_hardware_capability_validate_config",
    "svc_pb100_hardware_capability",
    "SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_OUTPUT_CAPABILITY",
    "SVC_HARDWARE_CAPABILITY_CONFIG_REQUIRES_PWM",
    "SVC_HARDWARE_CAPABILITY_CONFIG_EXCEEDS_POWER_BUDGET",
    "can1_read_only_default",
    "can1_tx_route_dnp_open",
    "configuration_required_for_roles",
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(REPO_ROOT)}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    except FileNotFoundError:
        fail(f"missing required config: {path.relative_to(REPO_ROOT)}")
    except json.JSONDecodeError as error:
        fail(f"invalid JSON in {path.relative_to(REPO_ROOT)}: {error}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(REPO_ROOT)} must contain a JSON object")
    return data


def require_dict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        fail(f"expected object at `{key}`")
    return value


def require_list(parent: dict[str, Any], key: str) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list):
        fail(f"expected array at `{key}`")
    return value


def decimal_value(value: Any, path: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        fail(f"expected numeric value at `{path}`")
    return Decimal(str(value))


def decimal_to_int(value: Any, path: str) -> int:
    number = decimal_value(value, path)
    if number != number.to_integral_value():
        fail(f"expected integer value at `{path}`")
    return int(number)


def decimal_amps_to_ma(value: Any, path: str) -> int:
    milliamps = decimal_value(value, path) * Decimal(1000)
    if milliamps != milliamps.to_integral_value():
        fail(f"expected `{path}` to convert to integer milliamps")
    return int(milliamps)


def parse_defines() -> dict[str, int]:
    defines: dict[str, int] = {}
    for text in (read_text(SVC_CONFIG_PATH), read_text(POWER_BUDGET_PATH)):
        for name, value in re.findall(r"#define\s+([A-Z0-9_]+)\s+(-?\d+)U?", text):
            defines[name] = int(value)
    return defines


def parse_allowed_roles() -> set[str]:
    roles = set()
    for role_name in re.findall(r"\bOUT_ROLE_([A-Z0-9_]+)\b", read_text(SVC_TYPES_PATH)):
        if role_name != "COUNT":
            roles.add(role_name)
    if not roles:
        fail("no output roles found in firmware/core/svc_types.h")
    return roles


def parse_c_default_outputs() -> list[dict[str, Any]]:
    pattern = re.compile(
        r"\{SVC_OUTPUT_OUT(\d+),\s+OUT_ROLE_([A-Z0-9_]+),\s+"
        r"(\d+)U,\s+(\d+)U,\s+(true|false),\s+SVC_PRIORITY_([ABC])\}"
    )
    outputs = []
    for output_number, role, fuse_a, current_ma, pwm, priority in pattern.findall(read_text(SVC_DEFAULTS_PATH)):
        outputs.append(
            {
                "id": f"OUT{output_number}",
                "role": role,
                "fuse_a": int(fuse_a),
                "current_limit_ma": int(current_ma),
                "pwm": pwm == "true",
                "priority": priority,
            }
        )
    if len(outputs) != 10:
        fail(f"expected 10 C default outputs, found {len(outputs)}")
    return outputs


def parse_c_shed_order() -> list[str]:
    text = read_text(SVC_DEFAULTS_PATH)
    match = re.search(r"\.shed_order\s*=\s*\{(?P<body>.*?)\}", text, re.S)
    if match is None:
        fail("missing C default shed_order")
    priorities = re.findall(r"SVC_PRIORITY_([ABC])", match.group("body"))
    if len(priorities) != 3:
        fail(f"expected 3 C shed priorities, found {len(priorities)}")
    return priorities


def require_schema_enum(schema: dict[str, Any], definition_name: str) -> list[str]:
    try:
        values = schema["$defs"][definition_name]["enum"]
    except KeyError:
        fail(f"missing schema enum $defs.{definition_name}.enum")
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        fail(f"schema enum $defs.{definition_name}.enum must be a string array")
    return values


def validate_schema(schema: dict[str, Any], allowed_roles: set[str]) -> None:
    schema_roles = require_schema_enum(schema, "outputRole")
    if set(schema_roles) != allowed_roles:
        fail("schema outputRole enum does not match firmware output_role_t")

    schema_outputs = require_schema_enum(schema, "outputId")
    if schema_outputs != [f"OUT{output_number}" for output_number in range(1, 11)]:
        fail("schema outputId enum must be OUT1..OUT10")

    schema_priorities = require_schema_enum(schema, "loadPriority")
    if schema_priorities != ["A", "B", "C"]:
        fail("schema loadPriority enum must be A, B, C")

    outputs_schema = schema.get("properties", {}).get("outputs", {})
    if outputs_schema.get("minItems") != 10 or outputs_schema.get("maxItems") != 10:
        fail("schema outputs array must require exactly 10 items")


def validate_battery(config: dict[str, Any], defines: dict[str, int]) -> None:
    battery = require_dict(config, "battery")
    warn_mv = decimal_amps_to_ma(battery.get("warn_v"), "battery.warn_v")
    cutoff_mv = decimal_amps_to_ma(battery.get("cutoff_v"), "battery.cutoff_v")
    recovery_mv = decimal_amps_to_ma(battery.get("recovery_v"), "battery.recovery_v")
    shutdown_delay_s = decimal_to_int(battery.get("shutdown_delay_s"), "battery.shutdown_delay_s")

    if not cutoff_mv < warn_mv <= recovery_mv:
        fail("battery thresholds must satisfy cutoff_v < warn_v <= recovery_v")
    if shutdown_delay_s <= 0:
        fail("battery.shutdown_delay_s must be positive")

    expected = {
        "battery.warn_v": defines["SVC_DEFAULT_BATTERY_WARN_MV"],
        "battery.cutoff_v": defines["SVC_DEFAULT_BATTERY_CUTOFF_MV"],
        "battery.recovery_v": defines["SVC_DEFAULT_BATTERY_RECOVERY_MV"],
        "battery.shutdown_delay_s": defines["SVC_DEFAULT_BATTERY_SHUTDOWN_DELAY_S"],
    }
    actual = {
        "battery.warn_v": warn_mv,
        "battery.cutoff_v": cutoff_mv,
        "battery.recovery_v": recovery_mv,
        "battery.shutdown_delay_s": shutdown_delay_s,
    }
    for key, expected_value in expected.items():
        if actual[key] != expected_value:
            fail(f"{key}={actual[key]} does not match C default {expected_value}")


def validate_thermal(config: dict[str, Any], defines: dict[str, int]) -> None:
    thermal = require_dict(config, "thermal")
    expected = {
        "warn_c": defines["SVC_DEFAULT_THERMAL_WARN_C"],
        "cutoff_c": defines["SVC_DEFAULT_THERMAL_CUTOFF_C"],
        "recovery_c": defines["SVC_DEFAULT_THERMAL_RECOVERY_C"],
    }

    for zone_key in ("pcb", "power_zone_a", "power_zone_b"):
        zone = require_dict(thermal, zone_key)
        actual = {
            "warn_c": decimal_to_int(zone.get("warn_c"), f"thermal.{zone_key}.warn_c"),
            "cutoff_c": decimal_to_int(zone.get("cutoff_c"), f"thermal.{zone_key}.cutoff_c"),
            "recovery_c": decimal_to_int(zone.get("recovery_c"), f"thermal.{zone_key}.recovery_c"),
        }
        if not actual["recovery_c"] < actual["warn_c"] < actual["cutoff_c"]:
            fail(f"thermal.{zone_key} thresholds must satisfy recovery_c < warn_c < cutoff_c")
        if actual != expected:
            fail(f"thermal.{zone_key} does not match C defaults: {actual} != {expected}")


def validate_power_budget(config: dict[str, Any], defines: dict[str, int]) -> None:
    power_budget = require_dict(config, "power_budget")
    total_current_limit_ma = decimal_amps_to_ma(
        power_budget.get("total_current_limit_a"),
        "power_budget.total_current_limit_a",
    )
    if total_current_limit_ma == 0:
        fail("power_budget.total_current_limit_a must be positive")
    if total_current_limit_ma > defines["SVC_MAIN_FUSE_LIMIT_MA"]:
        fail("power_budget.total_current_limit_a exceeds main fuse limit")
    if total_current_limit_ma != defines["SVC_DEFAULT_TOTAL_CURRENT_LIMIT_MA"]:
        fail("power_budget.total_current_limit_a does not match C default")

    shed_order = require_list(power_budget, "shed_priority_order")
    if shed_order != parse_c_shed_order():
        fail("power_budget.shed_priority_order does not match C default")
    if sorted(shed_order) != ["A", "B", "C"]:
        fail("power_budget.shed_priority_order must contain A, B, and C once")


def validate_outputs(config: dict[str, Any], allowed_roles: set[str]) -> None:
    outputs = require_list(config, "outputs")
    if len(outputs) != 10:
        fail(f"expected 10 outputs in config-example.json, found {len(outputs)}")

    c_outputs = parse_c_default_outputs()
    for index, output in enumerate(outputs):
        if not isinstance(output, dict):
            fail(f"outputs[{index}] must be an object")
        expected_id = f"OUT{index + 1}"
        if output.get("id") != expected_id:
            fail(f"outputs[{index}].id must be {expected_id}")

        role = output.get("role")
        if role not in allowed_roles:
            fail(f"outputs[{index}].role is not a known firmware role: {role}")
        priority = output.get("priority")
        if priority not in {"A", "B", "C"}:
            fail(f"outputs[{index}].priority must be A, B, or C")
        if not isinstance(output.get("pwm"), bool):
            fail(f"outputs[{index}].pwm must be boolean")

        fuse_a = decimal_to_int(output.get("fuse_a"), f"outputs[{index}].fuse_a")
        current_limit_ma = decimal_amps_to_ma(output.get("current_limit_a"), f"outputs[{index}].current_limit_a")
        if fuse_a <= 0 or current_limit_ma <= 0:
            fail(f"outputs[{index}] fuse/current limits must be positive")
        if current_limit_ma > fuse_a * 1000:
            fail(f"outputs[{index}].current_limit_a exceeds fuse_a")

        expected_output = c_outputs[index]
        actual_output = {
            "id": output["id"],
            "role": role,
            "fuse_a": fuse_a,
            "current_limit_ma": current_limit_ma,
            "pwm": output["pwm"],
            "priority": priority,
        }
        if actual_output != expected_output:
            fail(f"outputs[{index}] does not match C default: {actual_output} != {expected_output}")


def load_csv_dicts(path: Path) -> list[dict[str, str]]:
    try:
        return list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    except FileNotFoundError:
        fail(f"missing required CSV: {path.relative_to(REPO_ROOT)}")


def validate_no_role_tokens_in_capabilities(capabilities: dict[str, Any]) -> None:
    text = json.dumps(capabilities, sort_keys=True)
    for token in FORBIDDEN_HARDWARE_CAPABILITY_ROLE_TOKENS:
        if token in text:
            fail(f"hardware capabilities must not contain accessory role token: {token}")


def parse_c_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    fail(f"invalid C boolean literal: {value}")


def parse_c_uint_field(text: str, field_name: str) -> int:
    match = re.search(rf"\.{field_name}\s*=\s*(\d+)U", text)
    if match is None:
        fail(f"PB-100 C capability missing integer field: {field_name}")
    return int(match.group(1))


def parse_c_bool_field(text: str, field_name: str) -> bool:
    match = re.search(rf"\.{field_name}\s*=\s*(true|false)", text)
    if match is None:
        fail(f"PB-100 C capability missing boolean field: {field_name}")
    return parse_c_bool(match.group(1))


def parse_pb100_c_capability(text: str) -> dict[str, Any]:
    if ".output_count = SVC_OUTPUT_COUNT" not in text:
        fail("PB-100 C capability output_count must use SVC_OUTPUT_COUNT")

    output_pattern = re.compile(
        r"\{SVC_OUTPUT_OUT(\d+),\s*(\d+)U,\s*(\d+)U,\s*"
        r"(true|false),\s*(true|false)\}"
    )
    outputs = []
    for output_number, fuse_a, current_ma, pwm_supported, safe_default_off in output_pattern.findall(text):
        outputs.append(
            {
                "id": f"OUT{output_number}",
                "max_fuse_a": int(fuse_a),
                "max_current_ma": int(current_ma),
                "pwm_supported": parse_c_bool(pwm_supported),
                "safe_default_off": parse_c_bool(safe_default_off),
            }
        )
    if len(outputs) != 10:
        fail(f"expected 10 PB-100 C capability outputs, found {len(outputs)}")

    return {
        "main_fuse_limit_ma": parse_c_uint_field(text, "main_fuse_limit_ma"),
        "board_continuous_limit_ma": parse_c_uint_field(text, "board_continuous_limit_ma"),
        "default_total_current_limit_ma": parse_c_uint_field(text, "default_total_current_limit_ma"),
        "outputs_default_off": parse_c_bool_field(text, "outputs_default_off"),
        "configuration_required_for_roles": parse_c_bool_field(text, "configuration_required_for_roles"),
        "can1_read_only_default": parse_c_bool_field(text, "can1_read_only_default"),
        "can1_tx_route_dnp_open": parse_c_bool_field(text, "can1_tx_route_dnp_open"),
        "can1_tx_requires_future_adr": parse_c_bool_field(text, "can1_tx_requires_future_adr"),
        "can1_hardware_action_required_for_tx": parse_c_bool_field(
            text,
            "can1_hardware_action_required_for_tx",
        ),
        "outputs": outputs,
    }


def expected_pb100_c_capability(capabilities: dict[str, Any]) -> dict[str, Any]:
    power_budget = require_capability_dict(capabilities, "power_budget")
    safety = require_capability_dict(capabilities, "safety")
    can1 = require_capability_dict(safety, "can1")
    outputs = require_list(capabilities, "outputs")
    return {
        "main_fuse_limit_ma": int(power_budget["main_fuse_target_a"]) * 1000,
        "board_continuous_limit_ma": int(power_budget["board_continuous_target_a"]) * 1000,
        "default_total_current_limit_ma": int(power_budget["default_total_current_limit_a"]) * 1000,
        "outputs_default_off": safety.get("outputs_default_state") == "off",
        "configuration_required_for_roles": safety.get("configuration_required_for_roles") is True,
        "can1_read_only_default": can1.get("vehicle_can_read_only_default") is True,
        "can1_tx_route_dnp_open": can1.get("tx_route_population") == "DNP/open",
        "can1_tx_requires_future_adr": can1.get("tx_requires_future_adr") is True,
        "can1_hardware_action_required_for_tx": can1.get("hardware_action_required_for_tx") is True,
        "outputs": [
            {
                "id": output["id"],
                "max_fuse_a": int(output["target_fuse_a"]),
                "max_current_ma": int(output["target_current_limit_a"]) * 1000,
                "pwm_supported": output["pwm_capability"] == "yes",
                "safe_default_off": output["safe_default"] == "off",
            }
            for output in outputs
        ],
    }


def validate_pb100_c_capability(capabilities: dict[str, Any], pb100_implementation_text: str) -> None:
    actual = parse_pb100_c_capability(pb100_implementation_text)
    expected = expected_pb100_c_capability(capabilities)
    if actual != expected:
        fail(f"PB-100 C hardware capability does not match JSON manifest: {actual} != {expected}")


def validate_hardware_capability_service(capabilities: dict[str, Any]) -> None:
    config_acceptance_header_text = read_text(CONFIG_ACCEPTANCE_HEADER_PATH)
    config_acceptance_implementation_text = read_text(CONFIG_ACCEPTANCE_IMPL_PATH)
    config_store_header_text = read_text(CONFIG_STORE_HEADER_PATH)
    config_store_implementation_text = read_text(CONFIG_STORE_IMPL_PATH)
    runtime_boot_header_text = read_text(RUNTIME_BOOT_HEADER_PATH)
    runtime_boot_implementation_text = read_text(RUNTIME_BOOT_IMPL_PATH)
    header_text = read_text(HARDWARE_CAPABILITY_HEADER_PATH)
    implementation_text = read_text(HARDWARE_CAPABILITY_IMPL_PATH)
    pb100_header_text = read_text(PB100_CAPABILITY_HEADER_PATH)
    pb100_implementation_text = read_text(PB100_CAPABILITY_IMPL_PATH)
    config_acceptance_test_text = read_text(CONFIG_ACCEPTANCE_TEST_PATH)
    config_store_test_text = read_text(CONFIG_STORE_TEST_PATH)
    runtime_boot_test_text = read_text(RUNTIME_BOOT_TEST_PATH)
    test_text = read_text(HARDWARE_CAPABILITY_TEST_PATH)
    configuration_doc_text = read_text(CONFIGURATION_DOC_PATH)
    config_store_doc_text = read_text(CONFIG_STORE_DOC_PATH)
    runtime_boot_doc_text = read_text(RUNTIME_BOOT_DOC_PATH)
    system_safety_doc_text = read_text(SYSTEM_SAFETY_DOC_PATH)
    service_text = "\n".join((
        config_acceptance_header_text,
        config_acceptance_implementation_text,
        config_store_header_text,
        config_store_implementation_text,
        runtime_boot_header_text,
        runtime_boot_implementation_text,
        header_text,
        implementation_text,
        pb100_header_text,
        pb100_implementation_text,
        config_acceptance_test_text,
        config_store_test_text,
        runtime_boot_test_text,
        test_text,
    ))

    for token in REQUIRED_HARDWARE_CAPABILITY_TOKENS:
        if token not in service_text:
            fail(f"hardware capability service is missing required token: {token}")

    role_free_source_text = "\n".join((
        config_acceptance_header_text,
        config_acceptance_implementation_text,
        config_store_header_text,
        config_store_implementation_text,
        runtime_boot_header_text,
        runtime_boot_implementation_text,
        header_text,
        implementation_text,
        pb100_header_text,
        pb100_implementation_text,
    ))
    for token in FORBIDDEN_HARDWARE_CAPABILITY_ROLE_TOKENS:
        if token in role_free_source_text:
            fail(f"hardware capability service must not contain accessory role token: {token}")

    docs_text = "\n".join((configuration_doc_text, config_store_doc_text, runtime_boot_doc_text, system_safety_doc_text))
    for path in (
        "firmware/services/config_acceptance.h",
        "firmware/services/config_acceptance.c",
        "firmware/services/config_store.h",
        "firmware/services/config_store.c",
        "firmware/services/hardware_capability.h",
        "firmware/services/hardware_capability.c",
        "firmware/services/pb100_capability.h",
        "firmware/services/pb100_capability.c",
        "firmware/services/runtime_boot.h",
        "firmware/services/runtime_boot.c",
        "firmware/tests/test_config_acceptance.c",
        "firmware/tests/test_config_store.c",
        "firmware/tests/test_hardware_capability.c",
        "firmware/tests/test_runtime_boot.c",
    ):
        if path not in docs_text:
            fail(f"configuration/runtime docs must reference {path}")

    validate_pb100_c_capability(capabilities, pb100_implementation_text)


def require_capability_dict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        fail(f"expected object in PB-100 capabilities at `{key}`")
    return value


def validate_pb100_capabilities(config: dict[str, Any]) -> dict[str, Any]:
    capabilities = load_json(PB100_CAPABILITIES_PATH)
    validate_no_role_tokens_in_capabilities(capabilities)

    device = require_dict(config, "device")
    hardware = require_dict(device, "hardware")
    board = require_capability_dict(capabilities, "board")
    if board.get("id") != "PB-100":
        fail("PB-100 capabilities board.id must be PB-100")
    if hardware.get("power_board") != board.get("id"):
        fail("config device.hardware.power_board must match PB-100 capabilities board.id")
    if not isinstance(board.get("capability_source"), str) or not board["capability_source"].startswith("hardware/"):
        fail("PB-100 capabilities board.capability_source must reference hardware source")

    power_budget = require_capability_dict(capabilities, "power_budget")
    config_power_budget = require_dict(config, "power_budget")
    if power_budget.get("main_fuse_target_a") != 50:
        fail("PB-100 capabilities main_fuse_target_a must remain 50")
    if power_budget.get("board_continuous_target_a") != 40:
        fail("PB-100 capabilities board_continuous_target_a must remain 40")
    if power_budget.get("default_total_current_limit_a") != decimal_to_int(
        config_power_budget.get("total_current_limit_a"),
        "power_budget.total_current_limit_a",
    ):
        fail("PB-100 capabilities total current limit must match config example")

    safety = require_capability_dict(capabilities, "safety")
    if safety.get("outputs_default_state") != "off":
        fail("PB-100 capabilities outputs_default_state must be off")
    if safety.get("configuration_required_for_roles") is not True:
        fail("PB-100 capabilities must require configuration for roles")
    can1 = require_capability_dict(safety, "can1")
    if can1.get("vehicle_can_read_only_default") is not True:
        fail("PB-100 capabilities CAN1 must be read-only by default")
    if can1.get("tx_route_population") != "DNP/open":
        fail("PB-100 capabilities CAN1 TX route must remain DNP/open")
    if can1.get("tx_requires_future_adr") is not True:
        fail("PB-100 capabilities CAN1 TX must require future ADR")
    if can1.get("hardware_action_required_for_tx") is not True:
        fail("PB-100 capabilities CAN1 TX must require explicit hardware action")
    if can1.get("disabled_status_signal") != "CAN1_TX_DISABLED_STATUS":
        fail("PB-100 capabilities CAN1 disabled status signal mismatch")

    matrix_rows = load_csv_dicts(PB100_OUTPUT_MATRIX_PATH)
    matrix_by_output = {row["Output"].strip(): row for row in matrix_rows}
    outputs = capabilities.get("outputs")
    if not isinstance(outputs, list) or len(outputs) != 10:
        fail("PB-100 capabilities must contain exactly 10 outputs")
    seen_outputs = set()
    for index, output in enumerate(outputs):
        if not isinstance(output, dict):
            fail(f"PB-100 capabilities outputs[{index}] must be an object")
        output_id = output.get("id")
        expected_id = f"OUT{index + 1}"
        if output_id != expected_id:
            fail(f"PB-100 capabilities outputs[{index}].id must be {expected_id}")
        if output_id in seen_outputs:
            fail(f"duplicate PB-100 capability output {output_id}")
        seen_outputs.add(output_id)
        if "role" in output or "reference_default_role" in output:
            fail("PB-100 hardware capabilities must not contain output roles")
        matrix_row = matrix_by_output.get(output_id)
        if matrix_row is None:
            fail(f"PB-100 capabilities output {output_id} missing from output matrix")
        expected = {
            "class": matrix_row["Class"].strip(),
            "target_fuse_a": int(matrix_row["Target fuse A"]),
            "target_current_limit_a": int(matrix_row["Target current limit A"]),
            "pwm_capability": matrix_row["PWM"].strip(),
            "control_signal": f"{output_id}_CTL",
            "fault_signal": f"{output_id}_FLT",
            "current_signal": f"{output_id}_IMON",
            "load_signal": f"{output_id}_LOAD",
            "fused_signal": f"{output_id}_FUSED",
            "safe_default": "off",
        }
        actual = {key: output.get(key) for key in expected}
        if actual != expected:
            fail(f"PB-100 capabilities output {output_id} mismatch: {actual} != {expected}")

    telemetry = require_capability_dict(capabilities, "telemetry")
    current_signals = telemetry.get("current_signals")
    thermal_signals = telemetry.get("thermal_signals")
    board_signals = telemetry.get("board_signals")
    if current_signals != [row["Signal"].strip() for row in load_csv_dicts(PB100_CURRENT_TELEMETRY_PATH)]:
        fail("PB-100 capabilities current_signals must match current telemetry map")
    if thermal_signals != [row["Signal"].strip() for row in load_csv_dicts(PB100_THERMAL_TELEMETRY_PATH)]:
        fail("PB-100 capabilities thermal_signals must match thermal telemetry map")
    if board_signals != ["VBAT_SENSE", "PB_PWR_GOOD", "PB_FAULT", "PB_ID_ADC"]:
        fail("PB-100 capabilities board_signals mismatch")
    return capabilities


def validate_rules(config: dict[str, Any], allowed_roles: set[str]) -> None:
    rules = config.get("rules", [])
    if not isinstance(rules, list):
        fail("rules must be an array")

    condition_pattern = re.compile(r"^(engine_running|high_beam|left_indicator) == (true|false)$")
    action_pattern = re.compile(r"^([A-Z0-9_]+)\.pwm = ([0-9]+)$")
    for rule_index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            fail(f"rules[{rule_index}] must be an object")
        conditions = rule.get("if", [])
        actions = rule.get("then", [])
        if not isinstance(conditions, list) or not all(isinstance(condition, str) for condition in conditions):
            fail(f"rules[{rule_index}].if must be an array of strings")
        if not isinstance(actions, list) or not all(isinstance(action, str) for action in actions):
            fail(f"rules[{rule_index}].then must be an array of strings")

        for condition_index, condition in enumerate(conditions):
            if condition_pattern.match(condition) is None:
                fail(f"rules[{rule_index}].if[{condition_index}] is not supported by firmware rule parser")

        for action_index, action in enumerate(actions):
            match = action_pattern.match(action)
            if match is None:
                fail(f"rules[{rule_index}].then[{action_index}] is not supported by firmware rule parser")
            role, pwm_value_text = match.groups()
            if role not in allowed_roles or role == "NONE":
                fail(f"rules[{rule_index}].then[{action_index}] uses unknown or non-actionable role: {role}")
            pwm_value = int(pwm_value_text)
            if pwm_value > 100:
                fail(f"rules[{rule_index}].then[{action_index}] PWM value must be 0..100")


def main() -> int:
    config = load_json(CONFIG_PATH)
    schema = load_json(CONFIG_SCHEMA_PATH)
    defines = parse_defines()
    allowed_roles = parse_allowed_roles()
    validate_schema(schema, allowed_roles)
    require_dict(config, "device")
    validate_battery(config, defines)
    validate_thermal(config, defines)
    validate_power_budget(config, defines)
    validate_outputs(config, allowed_roles)
    capabilities = validate_pb100_capabilities(config)
    validate_hardware_capability_service(capabilities)
    validate_rules(config, allowed_roles)
    print("Config validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
