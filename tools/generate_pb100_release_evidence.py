#!/usr/bin/env python3
"""Generate or verify the deterministic PB-100 five-blocker evidence files."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from pb100_evidence.render import (
    render_factory,
    render_output_soa,
    render_q1,
    render_q2,
    render_surge_stopper,
    render_transient,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PB100_DIR = REPO_ROOT / "hardware" / "power-board" / "PB-100"
OUTPUTS = {
    PB100_DIR / "PB-100-transient-margin-evidence.csv": render_transient,
    PB100_DIR / "PB-100-surge-stopper-evidence.csv": render_surge_stopper,
    PB100_DIR / "PB-100-output-soa-evidence.csv": render_output_soa,
    PB100_DIR / "PB-100-input-q1-evidence.csv": render_q1,
    PB100_DIR / "PB-100-input-q2-evidence.csv": render_q2,
    PB100_DIR / "PB-100-factory-production-evidence.csv": render_factory,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if checked-in evidence differs from the calculations",
    )
    args = parser.parse_args()

    stale: list[str] = []
    for path, renderer in OUTPUTS.items():
        expected = renderer()
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                stale.append(str(path.relative_to(REPO_ROOT)))
        else:
            path.write_text(expected, encoding="utf-8")
            print(f"wrote {path.relative_to(REPO_ROOT)}")

    if stale:
        print("stale PB-100 release evidence:", file=sys.stderr)
        for path in stale:
            print(f"  {path}", file=sys.stderr)
        print("run tools/generate_pb100_release_evidence.py", file=sys.stderr)
        return 1
    if args.check:
        print("PB-100 release evidence is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
