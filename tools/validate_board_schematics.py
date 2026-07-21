#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from board_schematic_validation.runner import validate


def main() -> int:
    failures = validate(Path(__file__).resolve().parents[1])
    if failures:
        print("LB-100/FB-100 schematic validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("LB-100/FB-100 schematic validation passed (calculations, netlist topology, footprints, ERC).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
