from __future__ import annotations

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Component:
    value: str
    footprint: str
    pins: frozenset[str]
    dnp: bool


@dataclass(frozen=True)
class Netlist:
    components: dict[str, Component]
    nets: dict[str, frozenset[tuple[str, str]]]


def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def export_netlist(schematic: Path, output: Path, *, repo_root: Path) -> Netlist:
    result = run(
        ["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(output), str(schematic)],
        cwd=repo_root,
    )
    if result.returncode:
        raise RuntimeError(f"KiCad netlist export failed for {schematic}:\n{result.stdout}{result.stderr}")
    root = ET.parse(output).getroot()
    components: dict[str, Component] = {}
    for node in root.findall("./components/comp"):
        ref = node.attrib["ref"]
        components[ref] = Component(
            value=node.findtext("value", default=""),
            footprint=node.findtext("footprint", default=""),
            pins=frozenset(pin.attrib["num"] for pin in node.findall("./units/unit/pins/pin")),
            dnp=any(prop.attrib.get("name") == "dnp" for prop in node.findall("property")),
        )
    nets = {
        node.attrib["name"]: frozenset((endpoint.attrib["ref"], endpoint.attrib["pin"]) for endpoint in node.findall("node"))
        for node in root.findall("./nets/net")
    }
    return Netlist(components=components, nets=nets)


def erc_violations(schematic: Path, output: Path, *, repo_root: Path) -> list[dict[str, object]]:
    result = run(
        ["kicad-cli", "sch", "erc", "--format", "json", "--severity-all", "-o", str(output), str(schematic)],
        cwd=repo_root,
    )
    if result.returncode:
        raise RuntimeError(f"KiCad ERC execution failed for {schematic}:\n{result.stdout}{result.stderr}")
    report = json.loads(output.read_text(encoding="utf-8"))
    return [violation for sheet in report.get("sheets", []) for violation in sheet.get("violations", [])]


def footprint_pads(path: Path) -> frozenset[str]:
    return frozenset(re.findall(r'\(pad\s+"([^"]+)"', path.read_text(encoding="utf-8")))
