from __future__ import annotations

from .common import (
    BOARD_PRINT_CLOSURE_MATRIX_COLUMNS,
    BOARD_RELEASE_BLOCKER_REGISTER_COLUMNS,
    ENGINEERING_BLOCKER_CLOSEOUT,
    PB100_DIR,
    REPO_ROOT,
    SCHEMATIC_FREEZE_GAP_REGISTER_COLUMNS,
    SCHEMATIC_REVIEW_CLOSEOUT,
    csv,
    fail,
    re,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def freeze_checklist_rows_by_gate() -> dict[str, dict[str, str]]:
    text = read_text(PB100_DIR / "PB-100-schematic-freeze-checklist.md")
    rows_by_gate: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] in {"Gate", "---"}:
            continue
        gate, status, evidence, close_condition = cells[0], cells[1], cells[2], cells[3]
        if status in {"Closed", "Conditional", "Open", "Blocked"}:
            rows_by_gate[gate] = {
                "Status": status,
                "Evidence": evidence,
                "Close condition": close_condition,
            }
    return rows_by_gate


def freeze_checklist_status() -> str:
    text = read_text(PB100_DIR / "PB-100-schematic-freeze-checklist.md")
    match = re.search(r"^Status:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    if match is None:
        fail("PB-100 schematic freeze checklist must include top-level Status")
    return match.group(1).strip()


def freeze_checklist_gates_by_status() -> dict[str, str]:
    rows_by_gate = freeze_checklist_rows_by_gate()
    gates_by_status = {gate: row["Status"] for gate, row in rows_by_gate.items()}
    return gates_by_status


def validate_schematic_freeze_gap_register() -> None:
    path = PB100_DIR / "PB-100-schematic-freeze-gap-register.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty schematic freeze gap register: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in SCHEMATIC_FREEZE_GAP_REGISTER_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    checklist_rows_by_gate = freeze_checklist_rows_by_gate()
    gates_by_status = {gate: row["Status"] for gate, row in checklist_rows_by_gate.items()}
    tracked_gates = set(pbrel_id_by_gate())
    seen_gates = set()
    rows_by_gate: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        gate = row["Gate"].strip()
        status = row["Status"].strip()
        if gate in seen_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Gate {gate}")
        seen_gates.add(gate)
        rows_by_gate[gate] = row
        if gate not in gates_by_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown freeze checklist gate {gate}")
        if gate not in tracked_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: gate {gate} is not a tracked PB freeze gate")
        if status not in {"Closed", "Conditional", "Open", "Blocked"}:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid gap status {status}")
        if status != gates_by_status[gate]:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: gap status must match checklist status {gates_by_status[gate]}")
        for column in (
            "Close evidence required",
            "Primary gap artifact",
            "Validator coverage",
            "Next close action",
        ):
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")

    missing_gates = sorted(tracked_gates - seen_gates)
    extra_gates = sorted(seen_gates - tracked_gates)
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing tracked PB freeze gates: "
            f"{', '.join(missing_gates)}"
        )
    if extra_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} has non-tracked PB freeze gates: "
            f"{', '.join(extra_gates)}"
        )

    required_checklist_evidence = {
        "CAN1 safety policy": (
            "PB-100-can1-tx-disable-trace.csv",
            "PB-100-can1-safety-verification.csv",
            "PB-100-can1-production-dnp-review.csv",
            "PB-100-can1-default-disable-freeze-checklist.csv",
            "PB-100-can1-default-disable-derivation-precheck.csv",
            "PB-100-can1-default-disable-closeout-precheck.csv",
        ),
        "Board current budget": (
            "PB-100-board-current-budget-trace.csv",
            "PB-100-board-current-budget-freeze-review.csv",
            "PB-100-board-current-budget-design-calculation.md",
            "PB-100-board-current-budget-value-freeze-checklist.csv",
            "PB-100-board-current-budget-value-derivation-precheck.csv",
            "PB-100-board-current-budget-closeout-precheck.csv",
            "PB-100-input-power-design-values.csv",
        ),
        "Board-to-board interface": (
            "PB-100-b2b-interface-trace.csv",
            "PB-100-b2b-lb100-resource-binding.csv",
            "PB-100-b2b-lb100-pin-audit-checklist.csv",
            "PB-100-b2b-interface-freeze-checklist.csv",
            "PB-100-b2b-interface-closeout-precheck.csv",
            "PB-100-b2b-pin-map.csv",
        ),
        "High/medium output stage": (
            "PB-100-high-medium-output-baseline-trace.csv",
            "PB-100-high-medium-output-freeze-review.csv",
            "PB-100-output-stage-value-freeze-checklist.csv",
            "PB-100-output-stage-value-derivation-precheck.csv",
            "PB-100-output-stage-closeout-precheck.csv",
            "PB-100-out2-soa.md",
        ),
        "Low-current output stage": (
            "PB-100-low-current-output-baseline-trace.csv",
            "PB-100-low-current-output-freeze-review.csv",
            "PB-100-output-stage-value-freeze-checklist.csv",
            "PB-100-output-stage-value-derivation-precheck.csv",
            "PB-100-output-stage-closeout-precheck.csv",
            "ADR-0011",
        ),
        "Input reverse protection": (
            "PB-100-input-reverse-package-trace.csv",
            "PB-100-input-reverse-freeze-review.csv",
            "PB-100-input-reverse-q1-freeze-checklist.csv",
            "PB-100-input-reverse-q1-derivation-precheck.csv",
            "PB-100-input-reverse-q1-closeout-precheck.csv",
            "PB-100-input-reverse-protection.md",
        ),
        "TVS/load-dump protection": (
            "PB-100-tvs-load-dump-margin-trace.csv",
            "PB-100-tvs-load-dump-freeze-review.csv",
            "PB-100-tvs-overshoot-escape-checklist.csv",
            "PB-100-tvs-overshoot-validation-precheck.csv",
            "PB-100-protection-validation.csv",
        ),
        "Logic power rails": (
            "PB-100-logic-power-rail-trace.csv",
            "PB-100-logic-power-freeze-review.csv",
            "PB-100-logic-power-value-freeze-checklist.csv",
            "PB-100-logic-power-value-derivation-precheck.csv",
            "PB-100-logic-power-closeout-precheck.csv",
            "PB-100-logic-power-budget.csv",
        ),
        "Current telemetry": (
            "PB-100-current-telemetry-trace.csv",
            "PB-100-current-telemetry-freeze-review.csv",
            "PB-100-current-telemetry-value-freeze-checklist.csv",
            "PB-100-current-telemetry-value-derivation-precheck.csv",
            "PB-100-current-telemetry-closeout-precheck.csv",
            "PB-100-current-telemetry-map.csv",
        ),
        "Thermal telemetry": (
            "PB-100-thermal-telemetry-trace.csv",
            "PB-100-thermal-telemetry-freeze-review.csv",
            "PB-100-thermal-telemetry-value-freeze-checklist.csv",
            "PB-100-thermal-telemetry-value-derivation-precheck.csv",
            "PB-100-thermal-telemetry-closeout-precheck.csv",
            "PB-100-thermal-telemetry-map.csv",
        ),
        "Factory assembly readiness": (
            "PB-100-assembly-readiness-trace.csv",
            "PB-100-factory-assembly-freeze-checklist.csv",
            "PB-100-factory-assembly-sourcing-precheck.csv",
            "PB-100-factory-assembly-closeout-precheck.csv",
            "pb100_sourcing_evidence_snapshot.csv",
        ),
        "Garage assembly readiness": (
            "PB-100-assembly-readiness-trace.csv",
            "PB-100-garage-connector-fuse-plan.md",
            "PB-100-garage-install-freeze-checklist.csv",
            "PB-100-garage-install-sourcing-precheck.csv",
            "PB-100-garage-install-closeout-precheck.csv",
        ),
    }
    for gate, tokens in required_checklist_evidence.items():
        evidence = checklist_rows_by_gate[gate]["Evidence"]
        for token in tokens:
            if token not in evidence:
                fail(f"freeze checklist evidence for {gate} must include {token}")

    can_gap_text = " ".join(rows_by_gate["CAN1 safety policy"].values())
    can_text = can_gap_text.lower()
    if "dnp/open" not in can_text or "default" not in can_text:
        fail("CAN1 safety policy gap must keep DNP/open default explicit")
    for token in (
        "PB-100-can1-tx-disable-trace.csv",
        "PB-100-can1-production-dnp-review.csv",
        "PB-100-can1-reset-bench-checklist.csv",
        "PB-100-can1-default-disable-freeze-checklist.csv",
        "PB-100-can1-default-disable-derivation-precheck.csv",
        "PB-100-can1-default-disable-closeout-precheck.csv",
        "JP_CAN1",
        "U_CAN1",
        "future ADR",
        "explicit hardware action",
    ):
        if token not in can_gap_text:
            fail(f"CAN1 safety policy gap must keep {token} explicit")
    input_text = " ".join(rows_by_gate["Input reverse protection"].values())
    for token in (
        "PB-100-input-reverse-package-trace.csv",
        "PB-100-input-reverse-freeze-review.csv",
        "PB-100-input-reverse-q1-freeze-checklist.csv",
        "PB-100-input-reverse-q1-derivation-precheck.csv",
        "PB-100-input-reverse-q1-closeout-precheck.csv",
        "Q1",
        "40 A",
        "BUK7S1R2-80M",
        "80 V",
        "LFPAK88",
        "SOA",
    ):
        if token not in input_text:
            fail(f"Input reverse protection gap must keep {token} explicit")
    high_medium_text = " ".join(rows_by_gate["High/medium output stage"].values())
    for token in (
        "PB-100-high-medium-output-baseline-trace.csv",
        "PB-100-high-medium-output-freeze-review.csv",
        "PB-100-output-stage-value-freeze-checklist.csv",
        "PB-100-output-stage-value-derivation-precheck.csv",
        "PB-100-output-stage-closeout-precheck.csv",
        "OUT2",
        "SOA",
        "gate drive",
        "sense",
    ):
        if token not in high_medium_text:
            fail(f"High/medium output stage gap must keep {token} explicit")
    low_current_text = " ".join(rows_by_gate["Low-current output stage"].values())
    for token in (
        "PB-100-low-current-output-baseline-trace.csv",
        "PB-100-low-current-output-freeze-review.csv",
        "PB-100-output-stage-value-freeze-checklist.csv",
        "PB-100-output-stage-value-derivation-precheck.csv",
        "PB-100-output-stage-closeout-precheck.csv",
        "OUT5",
        "OUT8",
        "OUT9",
        "no direct 40 V",
    ):
        if token not in low_current_text:
            fail(f"Low-current output stage gap must keep {token} explicit")
    current_budget_text = " ".join(rows_by_gate["Board current budget"].values())
    for token in (
        "PB-100-board-current-budget-trace.csv",
        "PB-100-board-current-budget-freeze-review.csv",
        "PB-100-board-current-budget-design-calculation.md",
        "PB-100-board-current-budget-value-freeze-checklist.csv",
        "PB-100-board-current-budget-value-derivation-precheck.csv",
        "PB-100-board-current-budget-closeout-precheck.csv",
        "40 A",
        "firmware config",
        "shunt",
    ):
        if token not in current_budget_text:
            fail(f"Board current budget gap must keep {token} explicit")
    tvs_text = " ".join(rows_by_gate["TVS/load-dump protection"].values())
    for token in (
        "PB-100-tvs-load-dump-margin-trace.csv",
        "PB-100-tvs-load-dump-freeze-review.csv",
        "PB-100-tvs-overshoot-escape-checklist.csv",
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "PB-100-tvs-overshoot-closeout-precheck.csv",
        "80 V",
        "DO-218AC",
        "overshoot",
        "peak stress",
    ):
        if token not in tvs_text:
            fail(f"TVS/load-dump gap must keep {token} explicit")
    current_telemetry_text = " ".join(rows_by_gate["Current telemetry"].values())
    for token in (
        "PB-100-current-telemetry-trace.csv",
        "PB-100-current-telemetry-freeze-review.csv",
        "PB-100-current-telemetry-value-freeze-checklist.csv",
        "PB-100-current-telemetry-value-derivation-precheck.csv",
        "PB-100-current-telemetry-closeout-precheck.csv",
        "0.5mΩ",
        "ADC or I2C",
        "firmware safety",
    ):
        if token not in current_telemetry_text:
            fail(f"Current telemetry gap must keep {token} explicit")
    thermal_telemetry_text = " ".join(rows_by_gate["Thermal telemetry"].values())
    for token in (
        "PB-100-thermal-telemetry-trace.csv",
        "PB-100-thermal-telemetry-freeze-review.csv",
        "PB-100-thermal-telemetry-value-freeze-checklist.csv",
        "PB-100-thermal-telemetry-value-derivation-precheck.csv",
        "PB-100-thermal-telemetry-closeout-precheck.csv",
        "NTCGS103JF103FT8",
        "self-heating",
        "firmware thresholds",
    ):
        if token not in thermal_telemetry_text:
            fail(f"Thermal telemetry gap must keep {token} explicit")
    logic_power_text = " ".join(rows_by_gate["Logic power rails"].values())
    for token in (
        "PB-100-logic-power-rail-trace.csv",
        "PB-100-logic-power-freeze-review.csv",
        "PB-100-logic-power-value-freeze-checklist.csv",
        "PB-100-logic-power-value-derivation-precheck.csv",
        "PB-100-logic-power-closeout-precheck.csv",
        "1 A",
        "power-good",
        "UVLO",
    ):
        if token not in logic_power_text:
            fail(f"Logic power rails gap must keep {token} explicit")
    b2b_text = " ".join(rows_by_gate["Board-to-board interface"].values())
    for token in (
        "PB-100-b2b-interface-trace.csv",
        "PB-100-b2b-lb100-resource-binding.csv",
        "PB-100-b2b-lb100-pin-audit-checklist.csv",
        "PB-100-b2b-interface-freeze-checklist.csv",
        "PB-100-b2b-interface-closeout-precheck.csv",
        "FX18-100P-0.8SV10",
        "FX18-100S-0.8SV20",
        "exact LB-100 MCU pin binding",
    ):
        if token not in b2b_text:
            fail(f"Board-to-board interface gap must keep {token} explicit")
    factory_text = " ".join(rows_by_gate["Factory assembly readiness"].values()).lower()
    if (
        "pb-100-assembly-readiness-trace.csv" not in factory_text
        or "pb-100-factory-assembly-freeze-checklist.csv" not in factory_text
        or "pb-100-factory-assembly-sourcing-precheck.csv" not in factory_text
        or "pb-100-factory-assembly-closeout-precheck.csv" not in factory_text
        or "assembly" not in factory_text
        or "alternat" not in factory_text
    ):
        fail("Factory assembly readiness gap must keep assembly and alternatives explicit")
    garage_text = " ".join(rows_by_gate["Garage assembly readiness"].values()).lower()
    if (
        "pb-100-assembly-readiness-trace.csv" not in garage_text
        or "pb-100-garage-install-freeze-checklist.csv" not in garage_text
        or "pb-100-garage-install-sourcing-precheck.csv" not in garage_text
        or "pb-100-garage-install-closeout-precheck.csv" not in garage_text
        or "garage" not in garage_text
        or "user" not in garage_text
    ):
        fail("Garage assembly readiness gap must keep garage/user scope explicit")


def required_closeout_artifact_by_gate() -> dict[str, str]:
    return {
        "CAN1 safety policy": "pb-100-can1-default-disable-closeout-precheck.csv",
        "Board current budget": "pb-100-board-current-budget-closeout-precheck.csv",
        "Board-to-board interface": "pb-100-b2b-interface-closeout-precheck.csv",
        "High/medium output stage": "pb-100-output-stage-closeout-precheck.csv",
        "Low-current output stage": "pb-100-output-stage-closeout-precheck.csv",
        "Input reverse protection": "pb-100-input-reverse-q1-closeout-precheck.csv",
        "TVS/load-dump protection": "pb-100-tvs-overshoot-closeout-precheck.csv",
        "Logic power rails": "pb-100-logic-power-closeout-precheck.csv",
        "Current telemetry": "pb-100-current-telemetry-closeout-precheck.csv",
        "Thermal telemetry": "pb-100-thermal-telemetry-closeout-precheck.csv",
        "Factory assembly readiness": "pb-100-factory-assembly-closeout-precheck.csv",
        "Garage assembly readiness": "pb-100-garage-install-closeout-precheck.csv",
    }


def pbrel_id_by_gate() -> dict[str, str]:
    return {
        "CAN1 safety policy": "PBREL-001",
        "Board current budget": "PBREL-002",
        "Board-to-board interface": "PBREL-003",
        "High/medium output stage": "PBREL-004",
        "Low-current output stage": "PBREL-005",
        "Input reverse protection": "PBREL-006",
        "TVS/load-dump protection": "PBREL-007",
        "Logic power rails": "PBREL-008",
        "Current telemetry": "PBREL-009",
        "Thermal telemetry": "PBREL-010",
        "Factory assembly readiness": "PBREL-011",
        "Garage assembly readiness": "PBREL-012",
    }


def engineering_blocker_closeout_statuses() -> dict[str, str]:
    path = REPO_ROOT / ENGINEERING_BLOCKER_CLOSEOUT
    if not path.exists():
        return {}
    text = read_text(path)
    statuses: dict[str, str] = {}
    for blocker_id in pbrel_id_by_gate().values():
        marker = f"## {blocker_id} "
        marker_index = text.find(marker)
        if marker_index < 0:
            continue
        next_marker_index = text.find("\n## PBREL-", marker_index + len(marker))
        section = text[marker_index:] if next_marker_index < 0 else text[marker_index:next_marker_index]
        status_match = re.search(r"Closeout status:\s*([A-Za-z -]+)\.", section)
        if status_match:
            statuses[blocker_id] = status_match.group(1).strip()
    return statuses


def validate_engineering_blocker_closeout() -> None:
    path = REPO_ROOT / ENGINEERING_BLOCKER_CLOSEOUT
    text = read_text(path)
    normalized_text = re.sub(r"\s+", " ", text)
    lower_text = text.lower()
    if "does not authorize pcb layout" not in lower_text:
        fail(f"{path.relative_to(REPO_ROOT)} must explicitly avoid PCB layout authorization")
    for token in (
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "BOM/CPL",
        "manufacturing ZIP",
        "PCBA order",
    ):
        if token not in text and token not in normalized_text:
            fail(f"{path.relative_to(REPO_ROOT)} must keep no-layout token {token}")

    common_section_tokens = (
        "Closeout status:",
        "Why blocker existed",
        "Candidate comparison",
        "Recommended solution",
        "Risks",
        "Alternatives",
        "Cost impact",
        "Thermal impact",
        "Production impact",
        "Field reliability impact",
        "Why this component/solution",
        "Why not alternative A",
        "Why not alternative B",
        "Expected lifetime",
        "Operating margin",
        "Maximum junction temperature",
        "Availability",
        "Automotive qualification",
        "LCSC availability",
        "PCBWay/JLCPCB compatibility",
        "Known risks",
        "Evidence and calculations",
        "Datasheet and sourcing evidence",
        "Post-prototype validation",
        "No-layout boundary",
    )
    specific_tokens_by_id = {
        "PBREL-001": (
            "CAN1_TX_ROUTE",
            "DNP/open",
            "future ADR",
            "SN74LVC1G125-Q1",
            "PB-BENCH-012",
        ),
        "PBREL-002": (
            "40 A",
            "50 A",
            "0.5mΩ",
            "CSS4J-4026R-L500F",
            "PB-BENCH-006",
            "PB-BENCH-010",
        ),
        "PBREL-003": (
            "FX18-100P-0.8SV10",
            "FX18-100S-0.8SV20",
            "STM32H563VITx",
            "JPB1",
        ),
        "PBREL-004": (
            "TPS48110AQDGXRQ1",
            "BUK7S1R2-80M",
            "OUT2",
            "SOA",
        ),
        "PBREL-005": (
            "OUT5",
            "OUT8",
            "OUT9",
            "ADR-0011",
            "no direct 40 V",
        ),
        "PBREL-006": (
            "LM74700QDBVRQ1",
            "BUK7S1R2-80M",
            "40 A",
            "Q1",
        ),
        "PBREL-007": (
            "SM8S33AHM3/I",
            "53.3 V",
            "80 V",
            "overshoot",
        ),
        "PBREL-008": (
            "LM5164QDDATQ1",
            "PB_5V_OUT",
            "100 V",
            "1 A",
            "LM5013-Q1",
        ),
        "PBREL-009": (
            "INA228-Q1",
            "0.5mΩ",
            "±40.96 mV",
            "PB-BENCH-005",
        ),
        "PBREL-010": (
            "NTCGS103JF103FT8",
            "TEMP_PCB",
            "TEMP_PWR_A",
            "TEMP_PWR_B",
            "PB-BENCH-009",
        ),
        "PBREL-011": (
            "JLCPCB",
            "PCBWay",
            "DNP/open",
            "PowerPAK",
            "TOLL",
            "LFPAK88",
            "DO-218AC",
            "FX18",
        ),
        "PBREL-012": (
            "TE DEUTSCH",
            "DTP",
            "DT",
            "Littelfuse",
            "MAXI",
            "garage-installed",
        ),
    }
    blocker_rows = list(
        csv.DictReader(
            (PB100_DIR / "PB-100-board-release-blocker-register.csv").open(
                newline="", encoding="utf-8"
            )
        )
    )
    expected_status_by_id = {
        row["Blocker ID"].strip(): row["Status"].strip() for row in blocker_rows
    }
    for gate, blocker_id in pbrel_id_by_gate().items():
        marker = f"## {blocker_id} — {gate}"
        marker_index = text.find(marker)
        if marker_index < 0:
            fail(f"{path.relative_to(REPO_ROOT)} is missing closeout section {marker}")
        next_marker_index = text.find("\n## PBREL-", marker_index + len(marker))
        section = text[marker_index:] if next_marker_index < 0 else text[marker_index:next_marker_index]
        normalized_section = re.sub(r"\s+", " ", section)
        status_match = re.search(r"Closeout status:\s*([A-Za-z -]+)\.", section)
        if status_match is None:
            fail(f"{path.relative_to(REPO_ROOT)} {blocker_id} section must include a closeout status")
        actual_status = status_match.group(1).strip()
        expected_status = expected_status_by_id.get(blocker_id)
        if actual_status != expected_status:
            fail(
                f"{path.relative_to(REPO_ROOT)} {blocker_id} status {actual_status} "
                f"does not match blocker register status {expected_status}"
            )
        for token in common_section_tokens + specific_tokens_by_id[blocker_id]:
            if token not in section and token not in normalized_section:
                fail(f"{path.relative_to(REPO_ROOT)} {blocker_id} section must include {token}")


def validate_schematic_review_closeout() -> None:
    path = REPO_ROOT / SCHEMATIC_REVIEW_CLOSEOUT
    text = read_text(path)
    normalized_text = " ".join(text.split())
    for token in (
        "Status: Retracted; schematic freeze is Open",
        "Review date: 2026-07-20",
        "does not create KiCad PCB layout",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "BOM/CPL",
        "manufacturing ZIP",
        "PCBA orders",
        "closure was retracted",
        "80 V MOSFET baseline",
        "actual overshoot",
        "FX18 MF/TH mechanics",
        "post-prototype",
        "board-print remains NO-GO",
        "CAN1_TX_ROUTE",
        "DNP/open",
        "40 A default total current budget",
        "JPB1",
        "TPS48110AQDGXRQ1",
        "ADR-0011",
        "SM8S33AHM3/I",
        "80 V MOSFET",
        "LM74700QDBVRQ1",
        "LM5164QDDATQ1",
        "INA228-Q1",
        "TEMP_PCB",
        "TEMP_PWR_A",
        "TEMP_PWR_B",
        "JLCPCB/PCBWay",
        "garage",
        "PB-100-engineering-blocker-closeout.md",
        "PB-100-post-prototype-validation-gate.csv",
    ):
        if token not in text and token not in normalized_text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")


def validate_board_release_blocker_register() -> None:
    path = PB100_DIR / "PB-100-board-release-blocker-register.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board release blocker register: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_RELEASE_BLOCKER_REGISTER_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    gates_by_status = freeze_checklist_gates_by_status()
    required_closeout_by_gate = required_closeout_artifact_by_gate()
    expected_blocker_id_by_gate = pbrel_id_by_gate()
    closeout_statuses = engineering_blocker_closeout_statuses()
    allowed_statuses = {"Closed", "Conditional", "Open", "Blocked"}
    seen_gates = set()
    seen_blockers = set()
    for row_number, row in enumerate(rows, 2):
        gate = row["Gate"].strip()
        blocker_id = row["Blocker ID"].strip()
        status = row["Status"].strip()
        if gate in seen_gates:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Gate {gate}")
        seen_gates.add(gate)
        if blocker_id in seen_blockers:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Blocker ID {blocker_id}")
        seen_blockers.add(blocker_id)
        if gate not in gates_by_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown freeze checklist gate {gate}")
        if gate not in expected_blocker_id_by_gate:
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: gate {gate} is not a tracked PBREL gate"
            )
        expected_blocker_id = expected_blocker_id_by_gate[gate]
        if blocker_id != expected_blocker_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocker ID must be {expected_blocker_id}")
        if not blocker_id.startswith("PBREL-"):
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocker ID must start with PBREL-")
        if status not in allowed_statuses:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid release blocker status {status}")
        if status == "Closed" and closeout_statuses.get(blocker_id) != "Closed":
            fail(
                f"{path.relative_to(REPO_ROOT)}:{row_number}: Closed blocker {blocker_id} "
                f"must have Closed closeout in {ENGINEERING_BLOCKER_CLOSEOUT}"
            )
        if gates_by_status[gate] == "Closed" and status != "Closed":
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: closed freeze gate {gate} cannot keep an active blocker")
        for column in BOARD_RELEASE_BLOCKER_REGISTER_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        row_text = " ".join(row.values()).lower()
        if "block" not in row["Layout impact"].lower() or "layout" not in row["Layout impact"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Layout impact must explicitly block layout")
        if "final" not in row["Required close evidence"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Required close evidence must require final evidence")
        if "review" not in row_text and "test" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: release blocker must require review or test")
        required_closeout = required_closeout_by_gate.get(gate)
        if required_closeout is None:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: no closeout artifact rule for gate {gate}")
        if required_closeout not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: release blocker must reference {required_closeout}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_gates = sorted(set(expected_blocker_id_by_gate) - seen_gates)
    extra_gates = sorted(seen_gates - set(expected_blocker_id_by_gate))
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing PBREL blocker rows for gates: "
            f"{', '.join(missing_gates)}"
        )
    if extra_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} has blockers for non-PBREL gates: "
            f"{', '.join(extra_gates)}"
        )


def validate_board_print_closure_matrix() -> None:
    path = PB100_DIR / "PB-100-board-print-closure-matrix.csv"
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty board-print closure matrix: {path.relative_to(REPO_ROOT)}")

    fieldnames = rows[0].keys()
    missing_columns = [column for column in BOARD_PRINT_CLOSURE_MATRIX_COLUMNS if column not in fieldnames]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    blocker_rows = list(
        csv.DictReader((PB100_DIR / "PB-100-board-release-blocker-register.csv").open(newline="", encoding="utf-8"))
    )
    blockers_by_gate = {
        row["Gate"].strip(): row
        for row in blocker_rows
    }
    required_closeout_by_gate = required_closeout_artifact_by_gate()
    allowed_states = {"Closed", "Conditional", "Open", "Blocked"}

    rows_by_gate: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        gate = row["Gate"].strip()
        if gate in rows_by_gate:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate Gate {gate}")
        rows_by_gate[gate] = row
        if gate not in blockers_by_gate:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: gate {gate} has no release blocker row")
        for column in BOARD_PRINT_CLOSURE_MATRIX_COLUMNS:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        proof_state = row["Current proof state"].strip()
        if proof_state not in allowed_states:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: invalid Current proof state {proof_state}")
        blocker_row = blockers_by_gate[gate]
        blocker_status = blocker_row["Status"].strip()
        if proof_state != blocker_status:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Current proof state must match blocker status {blocker_status}")
        blocker_id = blocker_row["Blocker ID"].strip()
        if row["Blocker ID"].strip() != blocker_id:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Blocker ID must match {blocker_id}")
        required_closeout = required_closeout_by_gate[gate]
        if row["Closeout artifact"].strip().lower() != required_closeout:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Closeout artifact must be {required_closeout}")
        row_text = " ".join(row.values()).lower()
        if "dated" not in row_text:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: close evidence must require dated evidence")
        if "do not" not in row["Board-print blocked action"].lower():
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Board-print blocked action must be explicit")
        for token in ("pb-100.kicad_pcb", "gerbers", "drills", "pick-place", "manufacturing zip"):
            if token not in row["Board-print blocked action"].lower():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: Board-print blocked action must block {token}")
        validate_no_role_tokens_in_row(path, row_number, row)

    missing_gates = sorted(blockers_by_gate.keys() - rows_by_gate.keys())
    extra_gates = sorted(rows_by_gate.keys() - blockers_by_gate.keys())
    if missing_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing release blocker closure rows: "
            f"{', '.join(missing_gates)}"
        )
    if extra_gates:
        fail(
            f"{path.relative_to(REPO_ROOT)} has closure rows without blocker rows: "
            f"{', '.join(extra_gates)}"
        )

    matrix_text = read_text(path)
    for token in (
        "PBREL-001",
        "PBREL-002",
        "PBREL-003",
        "PBREL-004",
        "PBREL-005",
        "PBREL-006",
        "PBREL-007",
        "PBREL-008",
        "PBREL-009",
        "PBREL-010",
        "PBREL-011",
        "PBREL-012",
        "PB-100.kicad_pcb",
        "Gerbers",
        "drills",
        "pick-place",
        "manufacturing ZIP",
        "fabrication package",
        "PCBA order package",
    ):
        if token not in matrix_text:
            fail(f"board-print closure matrix must include {token}")
