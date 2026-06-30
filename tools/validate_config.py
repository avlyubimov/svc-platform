#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "firmware" / "configs" / "config-example.json"
SVC_TYPES_PATH = REPO_ROOT / "firmware" / "core" / "svc_types.h"
SVC_CONFIG_PATH = REPO_ROOT / "firmware" / "core" / "svc_config.h"
SVC_DEFAULTS_PATH = REPO_ROOT / "firmware" / "core" / "svc_config_defaults.c"
POWER_BUDGET_PATH = REPO_ROOT / "firmware" / "services" / "power_budget.h"


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
        for name, value in re.findall(r"#define\s+([A-Z0-9_]+)\s+(\d+)U", text):
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


def main() -> int:
    config = load_json(CONFIG_PATH)
    defines = parse_defines()
    allowed_roles = parse_allowed_roles()
    require_dict(config, "device")
    validate_battery(config, defines)
    validate_power_budget(config, defines)
    validate_outputs(config, allowed_roles)
    print("Config validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
