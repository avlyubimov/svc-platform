#!/usr/bin/env python3
"""Generate or verify deterministic LB-100/FB-100 powered-off evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from board_schematic_validation.powered_off_calculations import render_powered_off_evidence


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    REPO_ROOT
    / "hardware/logic-board/LB-100/LB-100-fb-powered-off-calculation-evidence.csv"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if checked-in evidence differs from the calculations",
    )
    args = parser.parse_args()
    expected = render_powered_off_evidence()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            print(
                "stale LB-100/FB-100 powered-off evidence; run "
                "tools/generate_lb_fb_release_evidence.py",
                file=sys.stderr,
            )
            return 1
        print("LB-100/FB-100 powered-off evidence is current")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
