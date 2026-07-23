#!/usr/bin/env python3
"""Generate or validate the segregated LB-100 Rev.1 bare-PCB EVT package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware/logic-board/LB-100/kicad/LB-100.kicad_pcb"
OUTPUT = ROOT / "hardware/logic-board/LB-100/manufacturing/evt-rev1"
ARCHIVE_NAME = "LB-100-rev1-evt-gerber-drill.zip"
MANIFEST_NAME = "LB-100-rev1-evt-manifest.json"
NOTES_NAME = "LB-100-rev1-evt-NOT-FOR-PRODUCTION.txt"
REQUIRED_KICAD_VERSION = "10.0.4"
GERBER_LAYERS = (
    "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,"
    "F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
)
FAB_FILES = (
    "LB-100-F_Cu.gtl",
    "LB-100-In1_Cu.g1",
    "LB-100-In2_Cu.g2",
    "LB-100-In3_Cu.g3",
    "LB-100-In4_Cu.g4",
    "LB-100-B_Cu.gbl",
    "LB-100-F_Mask.gts",
    "LB-100-B_Mask.gbs",
    "LB-100-f_silkscreen.gto",
    "LB-100-b_silkscreen.gbo",
    "LB-100-Edge_Cuts.gm1",
    "LB-100-PTH.drl",
    "LB-100-NPTH.drl",
    "LB-100-job.gbrjob",
    NOTES_NAME,
)
REVIEW_FILES = (
    "LB-100-PTH-drl_map.gbr",
    "LB-100-NPTH-drl_map.gbr",
    "LB-100-drl-report.txt",
)
PUBLISHED_FILES = (
    ARCHIVE_NAME,
    NOTES_NAME,
    "LB-100-drl-report.txt",
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str]) -> None:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        details = "\n".join(
            part for part in (result.stdout.strip(), result.stderr.strip()) if part
        )
        fail(details or f"command failed: {' '.join(command)}")


def validate_source(kicad_cli: str) -> None:
    version = subprocess.run(
        [kicad_cli, "--version"], text=True, capture_output=True, check=False
    )
    if version.returncode or version.stdout.strip() != REQUIRED_KICAD_VERSION:
        fail(
            f"kicad-cli {REQUIRED_KICAD_VERSION} is required; "
            f"found {version.stdout.strip() or 'unavailable'}"
        )
    run([sys.executable, "tools/generate_lb100_layout.py", "--check"])
    run([sys.executable, "tools/validate_lb100_layout.py"])


def notes() -> str:
    return """LB-100 REV.1 EVT - NOT FOR PRODUCTION

Release scope: five bare PCBs for bench bring-up and measurements only.
Stack: JLCPCB JLC06161H-3313, 6 layers, 1.6 mm, ENIG.
Copper: 1 oz outer, 0.5 oz inner per the selected stack construction.
Drill: separate plated and non-plated Excellon files, millimetres.
USB: request 90 ohm differential control; do not alter routing without review.

Before payment, run supplier DFM and confirm the exact stack, 100 x 70 mm
outline, all six copper layers, PTH/NPTH split and USB impedance request.
Reject automatic layer reduction, drill substitution, rerouting or geometry
changes. This archive is not a BOM/CPL, stencil, PCBA, PB-100, motorcycle or
production release.
"""


def validate_job(job: dict[str, object]) -> None:
    attributes = job.get("FilesAttributes", [])
    if not isinstance(attributes, list):
        fail("invalid LB-100 Gerber job attributes")
    file_functions = {
        str(entry.get("FileFunction", ""))
        for entry in attributes
        if isinstance(entry, dict)
    }
    for token in (
        "Copper,L1,Top",
        "Copper,L2,Inr",
        "Copper,L3,Inr",
        "Copper,L4,Inr",
        "Copper,L5,Inr",
        "Copper,L6,Bot",
        "SolderMask,Top",
        "SolderMask,Bot",
        "Legend,Top",
        "Legend,Bot",
        "Profile",
    ):
        if not any(value.startswith(token) for value in file_functions):
            fail(f"Gerber job is missing {token}")


def validate_drill_report(drill_report: str) -> None:
    for token in (
        "0.300mm",
        "(409 holes)",
        "Total plated holes count 423",
        "Total unplated holes count 10",
    ):
        if token not in drill_report:
            fail(f"LB-100 drill report is missing {token}")


def validate_generated_files(directory: Path) -> None:
    for name in (*FAB_FILES, *REVIEW_FILES):
        path = directory / name
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"missing or empty EVT artifact: {path.relative_to(ROOT)}")
    if "LB-100 REV.1 EVT - NOT FOR PRODUCTION" not in (
        directory / NOTES_NAME
    ).read_text(encoding="utf-8"):
        fail("LB-100 EVT package lost its non-production marking")
    validate_job(
        json.loads(
            (directory / "LB-100-job.gbrjob").read_text(encoding="utf-8")
        )
    )
    validate_drill_report(
        (directory / "LB-100-drl-report.txt").read_text(encoding="utf-8")
    )


def write_archive(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in FAB_FILES:
            data = (source / name).read_bytes()
            info = zipfile.ZipInfo(name, date_time=(2026, 7, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def generate(kicad_cli: str) -> None:
    validate_source(kicad_cli)
    with tempfile.TemporaryDirectory(prefix="svc-lb100-evt-") as temp_dir:
        temp = Path(temp_dir)
        run(
            [
                kicad_cli,
                "pcb",
                "export",
                "gerbers",
                "--output",
                f"{temp}/",
                "--layers",
                GERBER_LAYERS,
                "--subtract-soldermask",
                "--check-zones",
                str(BOARD),
            ]
        )
        run(
            [
                kicad_cli,
                "pcb",
                "export",
                "drill",
                "--output",
                f"{temp}/",
                "--format",
                "excellon",
                "--excellon-units",
                "mm",
                "--excellon-separate-th",
                "--generate-map",
                "--map-format",
                "gerberx2",
                "--generate-report",
                "--report-path",
                str(temp / "LB-100-drl-report.txt"),
                str(BOARD),
            ]
        )
        (temp / NOTES_NAME).write_text(notes(), encoding="utf-8")
        validate_generated_files(temp)
        write_archive(temp, temp / ARCHIVE_NAME)

        OUTPUT.mkdir(parents=True, exist_ok=True)
        generated_names = (*FAB_FILES, *REVIEW_FILES, ARCHIVE_NAME, MANIFEST_NAME)
        for name in generated_names:
            destination = OUTPUT / name
            if destination.exists():
                destination.unlink()
        for name in PUBLISHED_FILES:
            shutil.copy2(temp / name, OUTPUT / name)
        manifest = {
            "board": "LB-100",
            "revision": "REV.1 EVT",
            "scope": "five bare PCBs; not for production",
            "kicad_cli": REQUIRED_KICAD_VERSION,
            "stackup": "JLC06161H-3313",
            "published_files": {
                name: sha256(OUTPUT / name) for name in PUBLISHED_FILES
            },
            "archive_files": {
                name: sha256(temp / name) for name in FAB_FILES
            },
        }
        (OUTPUT / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    validate_existing()
    print(f"LB-100 EVT package generated: {OUTPUT.relative_to(ROOT)}")


def validate_existing() -> None:
    manifest_path = OUTPUT / MANIFEST_NAME
    if not manifest_path.is_file():
        fail(f"missing {manifest_path.relative_to(ROOT)}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("stackup") != "JLC06161H-3313":
        fail("LB-100 EVT package stackup changed")
    published_hashes = manifest.get("published_files", {})
    if not isinstance(published_hashes, dict) or set(published_hashes) != set(
        PUBLISHED_FILES
    ):
        fail("LB-100 EVT published file set changed")
    for name, expected in published_hashes.items():
        if sha256(OUTPUT / name) != expected:
            fail(f"LB-100 EVT artifact hash mismatch: {name}")
    if "LB-100 REV.1 EVT - NOT FOR PRODUCTION" not in (
        OUTPUT / NOTES_NAME
    ).read_text(encoding="utf-8"):
        fail("LB-100 EVT package lost its non-production marking")
    validate_drill_report(
        (OUTPUT / "LB-100-drl-report.txt").read_text(encoding="utf-8")
    )
    archive_hashes = manifest.get("archive_files", {})
    if not isinstance(archive_hashes, dict) or set(archive_hashes) != set(FAB_FILES):
        fail("LB-100 EVT archive manifest file set changed")
    with zipfile.ZipFile(OUTPUT / ARCHIVE_NAME) as archive:
        if set(archive.namelist()) != set(FAB_FILES):
            fail("LB-100 EVT archive contains an unexpected file set")
        if any(info.file_size == 0 for info in archive.infolist()):
            fail("LB-100 EVT archive contains an empty file")
        for name in FAB_FILES:
            member = archive.read(name)
            if hashlib.sha256(member).hexdigest() != archive_hashes[name]:
                fail(f"LB-100 EVT archive hash mismatch: {name}")
        validate_job(json.loads(archive.read("LB-100-job.gbrjob")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        validate_existing()
        print("LB-100 EVT package validation passed")
        return 0
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli is None:
        fail("kicad-cli is required to generate the LB-100 EVT package")
    generate(kicad_cli)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
