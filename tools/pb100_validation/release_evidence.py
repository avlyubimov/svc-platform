from __future__ import annotations

import csv
import subprocess
import sys

from .common import PB100_DIR, REPO_ROOT, fail, read_text


SELECTED_MOSFET = "IAUT300N08S5N012ATMA2"
SELECTED_SURGE_FET = "IAUTN15S6N025ATMA1"
SELECTED_CONTROLLER = "LM74930QRGERQ1"
SELECTED_FOOTPRINT = "PB100:PG-HSOF-8-1_TOLL_Infineon"
SELECTED_CONTROLLER_FOOTPRINT = "PB100:VQFN-24_RGE_4x4mm_P0.5mm_EP2.4mm"
FIVE_BLOCKERS = {"PBREL-001", "PBREL-004", "PBREL-006", "PBREL-007", "PBREL-011"}


def _rows(name: str) -> list[dict[str, str]]:
    with (PB100_DIR / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def validate_five_blocker_release_evidence() -> None:
    generator = REPO_ROOT / "tools" / "generate_pb100_release_evidence.py"
    result = subprocess.run(
        [sys.executable, str(generator), "--check"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        fail(result.stderr.strip() or result.stdout.strip())

    blocker_rows = _rows("PB-100-board-release-blocker-register.csv")
    status_by_id = {row["Blocker ID"]: row["Status"] for row in blocker_rows}
    if set(status_by_id) != {f"PBREL-{number:03d}" for number in range(1, 13)}:
        fail("PB-100 blocker register must contain PBREL-001 through PBREL-012 exactly")
    expected_active = {"PBREL-007": "Conditional"}
    actual_active = {
        blocker_id: status
        for blocker_id, status in status_by_id.items()
        if status != "Closed"
    }
    if actual_active != expected_active:
        fail(f"PB-100 active blocker state must be {expected_active}, got {actual_active}")

    for blocker_id in FIVE_BLOCKERS:
        row = next(row for row in blocker_rows if row["Blocker ID"] == blocker_id)
        row_text = " ".join(row.values())
        required_tokens = (
            ("EVT-LAYOUT-AUTHORIZED", "EVT", "production")
            if blocker_id in {"PBREL-006", "PBREL-007"}
            else ("pre-layout", "later")
        )
        for token in required_tokens:
            if token not in row_text:
                fail(f"{blocker_id} must distinguish current evidence from later physical gates using {token}")

    output_rows = _rows("PB-100-output-soa-evidence.csv")
    if len(output_rows) != 6 or any(row["Result"] != "PASS" for row in output_rows):
        fail("generated output SOA evidence must contain four classes plus two common PASS rows")
    high = next(row for row in output_rows if row["Channels"] == "OUT2")
    expected_high = {
        "IOC actual A": "34.96",
        "ISC actual A": "95.91",
        "tOC ms": "9.95",
        "Fast transient case": "80 A / 4 ms",
        "10us 60V SOA current margin A": "104.1",
    }
    for field, value in expected_high.items():
        if high[field] != value:
            fail(f"OUT2 generated evidence {field} must be {value}, got {high[field]}")

    transient_rows = _rows("PB-100-transient-margin-evidence.csv")
    expected_corners = {
        (us, ri, duration, initial)
        for us in {"79", "101"}
        for ri in {"0.5", "4"}
        for duration in {"40", "400"}
        for initial in {"25", "125"}
    }
    actual_corners = {
        (row["Us V"], row["Ri ohm"], row["td ms"], row["Initial Tj C"])
        for row in transient_rows
    }
    if actual_corners != expected_corners:
        fail("generated load-dump evidence must cover every ISO 16750-2 design corner")
    if not any(row["Result"] == "FAIL" for row in transient_rows):
        fail("historical single-TVS evidence must retain its load-dump screening failure")
    for row in transient_rows:
        for field in (
            "Peak TVS current A", "Peak clamp V", "Peak TVS power W", "TVS energy J",
            "Typical ZthJM C/W", "Predicted peak Tj C", "Margin to LM74700 60 V",
        ):
            float(row[field])

    surge_rows = _rows("PB-100-surge-stopper-evidence.csv")
    expected_surge_corners = {
        (us, ri, duration, rise_time, thermal_state, ambient, preload, initial)
        for us in {"79", "101"}
        for ri in {"0.5", "4"}
        for duration in {"40", "400"}
        for rise_time in {"5", "10"}
        for thermal_state, ambient, preload, initial in {
            ("Cold start", "25", "0", "25"),
            ("Hot soak", "125", "0", "125"),
            ("Hot steady 40 A", "125", "40", "150"),
        }
    }
    actual_surge_corners = {
        (
            row["Us V"], row["Ri ohm"], row["td ms"], row["Rise time ms"],
            row["Thermal state"],
            row["Ambient C"], row["Preload current A"], row["Initial Tj C"],
        )
        for row in surge_rows
    }
    if actual_surge_corners != expected_surge_corners:
        fail("active surge-stopper evidence must cover every ISO and Q2 thermal-state corner")
    for row in surge_rows:
        if row["SOA screen"] != "PASS" or row["Result"] != "CONDITIONAL PRODUCTION":
            fail("active surge-stopper corners must remain conditional despite the provisional SOA screen")
        if row["Load response"] != "DISCONNECT":
            fail("active surge-stopper corners must disconnect the load")
        if float(row["OV cutoff max V"]) > 55.0:
            fail("active surge-stopper maximum cutoff must not exceed 55 V")
        if float(row["Q2 linear-mode ID A"]) != 40.0:
            fail("active surge-stopper SOA screen must use the full 40 A load current")
        if float(row["OV deglitch us"]) != 7.0:
            fail("active surge-stopper evidence must retain the maximum OV deglitch interval")
        if float(row["Input rise during OV delay V"]) > 0.123:
            fail("active surge-stopper OV-delay input rise exceeds the 5 ms rise-time bound")
        if float(row["Pre-layout commutation overshoot allowance V"]) != 4.5:
            fail("active surge-stopper must reserve the 4.5 V pre-layout commutation allowance")
        if row["Protected-node screen"] != "PASS":
            fail("active surge-stopper protected-node peak budget must remain below 80 V")
        if float(row["Protected-node peak budget V"]) > 59.52:
            fail("active surge-stopper protected-node peak budget exceeds 59.52 V")
        if float(row["Protected MOSFET rating V"]) != 80.0:
            fail("active surge-stopper protected-node screen must use the selected 80 V Q1")
        if float(row["Protected-node margin V"]) < 20.48:
            fail("active surge-stopper protected-node budget must retain at least 20.48 V")
        if float(row["Fully-enhanced Q2 VDS V"]) > 0.2:
            fail("OV deglitch must model Q2 fully enhanced rather than in linear mode")
        if float(row["Qgd max nC"]) != 40.0:
            fail("active surge-stopper transition must use maximum Qgd rather than total gate charge")
        if float(row["Miller transition bound us"]) > float(row["SOA reference pulse us"]):
            fail("active surge-stopper Miller transition must fit within the SOA pulse curve")
        if float(row["Qgs max nC"]) != 52.0:
            fail("active surge-stopper post-Miller envelope must use complete maximum Qgs")
        if float(row["Post-Miller ID-fall bound us"]) != 0.41:
            fail("active surge-stopper evidence must include the post-Miller current fall")
        if float(row["Complete linear-transition bound us"]) != 0.72:
            fail("active surge-stopper evidence must retain the complete transition bound")
        if float(row["Complete linear-transition bound us"]) > float(row["SOA reference pulse us"]):
            fail("active surge-stopper complete transition must fit within the SOA pulse curve")
        if float(row["SOA reference VDS V"]) < 101.0:
            fail("active surge-stopper SOA screen must use at least the 101 V design corner")
        if float(row["SOA current margin x"]) < 1.5:
            fail("temperature-derated Q2 linear-mode SOA margin must remain at least 1.5x")
        if row["Pulse count"] != "10" or row["Pulse spacing s"] != "60":
            fail("active surge-stopper evidence must preserve ten pulses at 60 s spacing")
    if "Q2 avalanche-energy margin x" in surge_rows[0]:
        fail("Q2 linear-mode SOA must not be accepted from avalanche-energy margin")
    if "Turn-off bound us" in surge_rows[0]:
        fail("OV deglitch must not be added to the Q2 linear-mode interval")

    q2_by_item = {row["Evidence item"]: row for row in _rows("PB-100-input-q2-evidence.csv")}
    if q2_by_item["Exact orderable MPN"]["Value"] != SELECTED_SURGE_FET:
        fail("generated Q2 evidence must use the selected orderable surge MOSFET")
    if q2_by_item["Q2 conduction loss at 25 C maximum"]["Value"] != "4.000":
        fail("generated Q2 evidence must retain the 4.000 W minimum conduction loss")
    if q2_by_item["Q2 hot conduction loss"]["Value"] != "7.200":
        fail("generated Q2 evidence must retain the conservative 7.200 W hot loss")
    if q2_by_item["Maximum full thermal path"]["Value"] != "3.47":
        fail("generated Q2 evidence must retain the 3.47 K/W post-layout limit")
    if q2_by_item["Hot steady initial junction"]["Value"] != "150.0":
        fail("generated Q2 evidence must start the hot SOA corner at 150 C")
    if q2_by_item["Maximum gate-drain charge"]["Value"] != "40":
        fail("generated Q2 evidence must use the maximum gate-drain charge")
    if q2_by_item["Maximum gate-source charge"]["Value"] != "52":
        fail("generated Q2 evidence must use maximum Qgs for the post-Miller bound")
    if q2_by_item["Miller transition bound"]["Value"] != "0.31":
        fail("generated Q2 evidence must separate the 0.31 us Miller transition")
    if q2_by_item["Post-Miller current-fall bound"]["Value"] != "0.41":
        fail("generated Q2 evidence must include the 0.41 us post-Miller current fall")
    if q2_by_item["Complete linear-transition bound"]["Value"] != "0.72":
        fail("generated Q2 evidence must retain the 0.72 us complete transition")
    if q2_by_item["ISO load-dump rise-time range"]["Value"] != "5-10":
        fail("generated Q2 evidence must retain the ISO 5-10 ms rise-time range")
    if q2_by_item["Pre-layout commutation overshoot allowance"]["Value"] != "4.50":
        fail("generated Q2 evidence must reserve the 4.5 V pre-layout overshoot allowance")
    if q2_by_item["Worst protected-node peak budget"]["Value"] != "59.52":
        fail("generated Q2 evidence must retain the 59.52 V protected-node peak budget")
    if q2_by_item["Protected-node margin to 80 V Q1"]["Value"] != "20.48":
        fail("generated Q2 evidence must retain the 20.48 V protected-node margin")
    if q2_by_item["Hot-corner SOA margin"]["Value"] != "2.08":
        fail("generated Q2 evidence must retain the provisional 2.08x hot SOA screen")
    if q2_by_item["Production qualification status"]["Value"] != "Conditional":
        fail("generated Q2 evidence must keep PBREL-007 production qualification conditional")
    if q2_by_item["Production qualification status"]["Result"] != "EVT-LAYOUT-AUTHORIZED / PRODUCTION BLOCKED":
        fail("generated Q2 evidence must authorize EVT layout without opening production")

    q1_by_item = {row["Evidence item"]: row for row in _rows("PB-100-input-q1-evidence.csv")}
    if q1_by_item["Exact orderable MPN"]["Value"] != SELECTED_MOSFET:
        fail("generated Q1 evidence must use the selected orderable MOSFET")
    if q1_by_item["Q1 conduction loss"]["Value"] != "4.032":
        fail("generated Q1 evidence must retain the 4.032 W hot loss")
    if q1_by_item["Cooling architecture"]["Value"] != "Passive PCB copper plus thermal pad to metal enclosure":
        fail("generated Q1 evidence must select passive PCB/enclosure cooling")
    if q1_by_item["Target junction ceiling"]["Value"] != "150.0":
        fail("generated Q1 evidence must use the 150 C design target")
    if q1_by_item["Maximum full thermal path"]["Value"] != "6.20":
        fail("generated Q1 evidence must retain the 6.20 K/W post-layout limit")

    factory_rows = _rows("PB-100-factory-production-evidence.csv")
    if not factory_rows or any("PASS" not in row["Pre-layout result"] for row in factory_rows):
        fail("factory production evidence must pass every pre-layout source/process row")

    output_sheet = read_text(PB100_DIR / "kicad" / "sheets" / "outputs-1-10.kicad_sch")
    input_sheet = read_text(PB100_DIR / "kicad" / "sheets" / "input-protection.kicad_sch")
    if output_sheet.count(f'(property "Value" "{SELECTED_MOSFET}"') != 20:
        # The deterministic PB generator emits one local lib symbol and one
        # placed instance for each of Q101-Q110.
        fail("outputs sheet must contain exact selected TOLL value in its local symbol and Q101-Q110")
    if input_sheet.count(f'(property "Value" "{SELECTED_MOSFET}"') != 2:
        fail("input sheet must contain exact selected TOLL value in its local symbol and Q1")
    if input_sheet.count(f'(property "Value" "{SELECTED_SURGE_FET}"') != 2:
        fail("input sheet must contain exact selected 150 V TOLL value in its local symbol and Q2")
    if input_sheet.count(f'(property "Value" "{SELECTED_CONTROLLER}"') != 2:
        fail("input sheet must contain exact selected LM74930-Q1 value in its local symbol and U1")
    if f'(property "Footprint" "{SELECTED_CONTROLLER_FOOTPRINT}"' not in input_sheet:
        fail("input sheet must bind the selected LM74930-Q1 RGE footprint")
    if '(property "Value" "CGA6N3X7R2A225M230AE 2.2uF 100V X7R; Ceff>=1uF@56V"' not in input_sheet:
        fail("input sheet must retain the selected >=1 uF effective LM74930 VS storage capacitor")
    for sheet_name, sheet_text in (("outputs", output_sheet), ("input", input_sheet)):
        if f'(property "Footprint" "{SELECTED_FOOTPRINT}"' not in sheet_text:
            fail(f"{sheet_name} sheet must bind the selected TOLL footprint")
        for pin in ("5", "6", "7", "8", "Tab"):
            if f'(pin "{pin}"' not in sheet_text:
                fail(f"{sheet_name} sheet selected TOLL instances must include pin {pin}")
    for token in (
        '(property "Value" "SM8S33AHM3/I"',
        '(property "Footprint" "PB100:DO-218AC_Vishay_SM8S"',
        '(dnp yes)',
    ):
        if token not in input_sheet:
            fail("D1 must be exact, footprint-bound, and DNP in the input sheet")

    historical_allowlist = {
        PB100_DIR / "PB-100-five-blocker-closeout-2026-07-21.md",
        PB100_DIR / "PB-100-input-reverse-package-trace.csv",
        PB100_DIR / "PB-100-mosfet-voltage-margin-review.md",
        PB100_DIR / "kicad" / "lib" / "PB100.pretty" / "LFPAK88_SOT1235_Nexperia.kicad_mod",
    }
    selected_preliminary = []
    for path in PB100_DIR.rglob("*"):
        if not path.is_file() or path in historical_allowlist:
            continue
        try:
            if "BUK7S1R2-80M" in path.read_text(encoding="utf-8"):
                selected_preliminary.append(str(path.relative_to(REPO_ROOT)))
        except UnicodeDecodeError:
            continue
    if selected_preliminary:
        fail("rejected preliminary BUK7S1R2-80M leaked into active PB evidence: " + ", ".join(selected_preliminary))

    closeout = read_text(PB100_DIR / "PB-100-five-blocker-closeout-2026-07-21.md")
    for token in FIVE_BLOCKERS | {
        "59.45",
        "IAUT300N08S5N014ATMA1",
        "BUK7J2R4-80MX",
        "does not",
        ".kicad_pcb",
    }:
        if token not in closeout:
            fail(f"five-blocker closeout is missing {token}")
