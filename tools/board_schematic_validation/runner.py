from __future__ import annotations

import re
import tempfile
from pathlib import Path

from .model import erc_violations, export_netlist, run
from .rules import validate_fb, validate_lb


def validate(repo_root: Path) -> list[str]:
    boards = {
        "LB-100": repo_root / "hardware/logic-board/LB-100/kicad/LB-100.kicad_sch",
        "FB-100": repo_root / "hardware/front-board/FB-100/kicad/FB-100.kicad_sch",
    }
    failures: list[str] = []
    generated = run(["python3", "tools/generate_lb_fb_schematics.py", "--check"], cwd=repo_root)
    if generated.returncode:
        failures.append(f"generated schematics are stale: {generated.stdout}{generated.stderr}".strip())

    with tempfile.TemporaryDirectory(prefix="svc-board-schematic-") as directory:
        temp = Path(directory)
        netlists = {
            board: export_netlist(path, temp / f"{board}.xml", repo_root=repo_root)
            for board, path in boards.items()
        }
        failures.extend(validate_lb(netlists["LB-100"], boards["LB-100"].parent / "lib/LB100.pretty"))
        failures.extend(validate_fb(netlists["FB-100"], boards["FB-100"].parent / "lib/FB100.pretty"))

        reports = {
            board: erc_violations(path, temp / f"{board}-erc.json", repo_root=repo_root)
            for board, path in boards.items()
        }
        for board, violations in reports.items():
            errors = [item for item in violations if item.get("severity") == "error"]
            if errors:
                failures.append(f"{board}: ERC contains {len(errors)} error(s)")
        lb_warnings = reports["LB-100"]
        warning_signature: list[str] = []
        for item in lb_warnings:
            if item.get("severity") != "warning" or item.get("type") != "isolated_pin_label":
                warning_signature.append(f"unexpected:{item.get('type')}")
                continue
            description = str(item.get("items", [{}])[0].get("description", ""))
            match = re.search(r"'([^']+)'", description)
            warning_signature.append(match.group(1) if match else description)
        warning_signature.sort()
        expected_warnings = ["USB_CC1", "USB_CC2"]
        if warning_signature != expected_warnings:
            failures.append(f"LB-100: unreviewed ERC warning set: {warning_signature}")
        if reports["FB-100"]:
            failures.append(f"FB-100: expected zero ERC findings, got {len(reports['FB-100'])}")
    return failures
