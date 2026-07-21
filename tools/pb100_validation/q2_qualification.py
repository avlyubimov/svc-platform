from __future__ import annotations

import csv

from .common import PB100_DIR, fail, read_text


Q2_QUALIFICATION_INPUTS = {
    "Q2Q-001": "IAUTN15S6N025ATMA1",
    "Q2Q-002": "LM74930QRGERQ1 hard overvoltage cutoff",
    "Q2Q-003": "101 V maximum during qualification trajectory",
    "Q2Q-004": "40 A before cutoff",
    "Q2Q-005": "150 degC before cutoff",
    "Q2Q-006": "10.0-14.5 V VGS",
    "Q2Q-007": "128 mA minimum sink current",
    "Q2Q-008": "7 us maximum with Q2 fully enhanced",
    "Q2Q-009": "10 pulses with 60 s spacing",
}
Q2_QUALIFICATION_PENDING = {f"Q2Q-{number:03d}" for number in range(10, 16)}
Q2_EMPIRICAL_PLAN_PASSED = {"Q2E-001", "Q2E-002"}
Q2_EMPIRICAL_IN_PROGRESS = {"Q2E-003"}
Q2_EMPIRICAL_NOT_STARTED = {f"Q2E-{number:03d}" for number in range(4, 14)}


def _rows(name: str) -> list[dict[str, str]]:
    with (PB100_DIR / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _require_tokens(document: str, tokens: tuple[str, ...], label: str) -> None:
    for token in tokens:
        if token not in document:
            fail(f"{label} is missing {token}")


def validate_q2_maximum_bound_qualification() -> None:
    rows = _rows("PB-100-q2-maximum-bound-qualification.csv")
    rows_by_id = {row["Qualification ID"]: row for row in rows}
    expected_ids = set(Q2_QUALIFICATION_INPUTS) | Q2_QUALIFICATION_PENDING | {
        "Q2Q-016",
        "Q2Q-017",
        "Q2Q-018",
    }
    if len(rows_by_id) != len(rows) or set(rows_by_id) != expected_ids:
        fail("Q2 maximum-bound qualification ledger must contain Q2Q-001 through Q2Q-018 exactly")

    for qualification_id, required_bound in Q2_QUALIFICATION_INPUTS.items():
        row = rows_by_id[qualification_id]
        if row["Required bound"] != required_bound or row["Status"] != "PASS INPUT":
            fail(f"{qualification_id} must preserve the reviewed qualification input")

    for qualification_id in Q2_QUALIFICATION_PENDING:
        row = rows_by_id[qualification_id]
        if row["Status"] != "PENDING EMPIRICAL":
            fail(f"{qualification_id} must remain PENDING EMPIRICAL until accepted test evidence exists")
        accepted_source = row["Accepted source"]
        if "Infineon" not in accepted_source or "empirical" not in accepted_source.lower():
            fail(f"{qualification_id} must retain both vendor and empirical acceptance routes")

    q2q016 = rows_by_id["Q2Q-016"]
    for token in ("IFX-260721-2228076", "CRM0032570008656", "no trajectory model or FAE statement"):
        if token not in q2q016["Current evidence"]:
            fail(f"Q2Q-016 must retain the non-qualifying Infineon response token {token}")
    if q2q016["Status"] != "RECEIVED NON-QUALIFYING":
        fail("Q2Q-016 must distinguish a redirect response from qualification evidence")
    if rows_by_id["Q2Q-017"]["Status"] != "PARALLEL REROUTE REQUIRED":
        fail("Q2 vendor request must remain a parallel Infineon MyCases route")
    expected_decision = "BLOCKED until Q2Q-010 through Q2Q-015 are PASS VENDOR or PASS EMPIRICAL"
    if rows_by_id["Q2Q-018"]["Required bound"] != expected_decision:
        fail("Q2 qualification decision must accept only completed vendor or empirical trajectory evidence")
    if rows_by_id["Q2Q-018"]["Status"] != "BLOCKED":
        fail("Q2 pre-layout qualification must remain BLOCKED while empirical evidence is pending")

    request = read_text(PB100_DIR / "PB-100-q2-vendor-support-request.md")
    _require_tokens(
        request,
        (
            "IAUTN15S6N025ATMA1",
            "LM74930QRGERQ1",
            "101 V",
            "40 A",
            "150 degC",
            "10.0-14.5 V",
            "128 mA",
            "7 us",
            "ten load-dump events with 60 s spacing",
            "VDS(t)",
            "ID(t)",
            "process, temperature, and lot coverage",
            "typical SPICE",
            "support@infineon.com",
            "Status: `EMAIL RESPONSE RECEIVED — NON-QUALIFYING`",
            "MyCases reroute required",
            "IFX-260721-2228076",
            "CRM0032570008656",
            "PB-100-q2-vendor-response-2026-07-21.md",
            "PB-100-q2-empirical-qualification-plan.md",
            "no `PB-100.kicad_pcb`",
        ),
        "Q2 vendor qualification request",
    )

    response = read_text(PB100_DIR / "PB-100-q2-vendor-response-2026-07-21.md")
    _require_tokens(
        response,
        (
            "RECEIVED / NON-QUALIFYING",
            "IFX-260721-2228076",
            "CRM0032570008656",
            "MyCases",
            "PENDING EMPIRICAL",
            "Q2Q-010",
            "Q2Q-015",
            "PBREL-007",
            "PB-100 board import remains prohibited",
            "Controlled FB-100 layout may continue",
        ),
        "Q2 vendor response record",
    )

    audit = read_text(PB100_DIR / "PB-100-q2-replacement-evidence-audit.md")
    _require_tokens(
        audit,
        (
            "RETAIN IAUTN15S6N025ATMA1 / EMPIRICAL QUALIFICATION SELECTED",
            "IAUTN15S6N038ATMA1",
            "SQJQ570E",
            "SQJ590EP",
            "IPB048N15N5LF",
            "Nexperia automotive Enhanced-SOA ASFET family",
            "no reviewed replacement supplies the missing public qualification artifact",
            "QUALIFICATION-COUPON-ONLY",
            "PB-100 board import",
        ),
        "Q2 replacement evidence audit",
    )

    plan = read_text(PB100_DIR / "PB-100-q2-empirical-qualification-plan.md")
    _require_tokens(
        plan,
        (
            "APPROVED ROUTE FOR ENGINEERING EXECUTION / RESULTS PENDING",
            "QUALIFICATION-COUPON-ONLY",
            "101 V",
            "40 A",
            "150 degC",
            "10.0 V",
            "14.5 V",
            "128 mA",
            "7 us",
            "Five Q2 devices",
            "Thirty new Q2 devices",
            "three independent",
            "200 MHz",
            "1 GS/s",
            "50 MHz",
            "ten events at 60 s spacing",
            "<= 0.80 us",
            "1.25x",
            "<= 120 V",
            "1.5x",
            "no more than 5%",
            "0.10 V",
            "PASS EMPIRICAL",
            "controlled Q2-C100 schematic",
            "zero unconnected items",
        ),
        "Q2 empirical qualification plan",
    )

    empirical_rows = _rows("PB-100-q2-empirical-qualification-readiness.csv")
    empirical_by_id = {row["Evidence ID"]: row for row in empirical_rows}
    expected_empirical_ids = Q2_EMPIRICAL_PLAN_PASSED | Q2_EMPIRICAL_IN_PROGRESS | Q2_EMPIRICAL_NOT_STARTED | {"Q2E-014"}
    if len(empirical_by_id) != len(empirical_rows) or set(empirical_by_id) != expected_empirical_ids:
        fail("Q2 empirical readiness ledger must contain Q2E-001 through Q2E-014 exactly")
    for evidence_id in Q2_EMPIRICAL_PLAN_PASSED:
        if empirical_by_id[evidence_id]["Status"] != "PASS PLAN":
            fail(f"{evidence_id} must record the approved plan input")
    for evidence_id in Q2_EMPIRICAL_IN_PROGRESS:
        row = empirical_by_id[evidence_id]
        if row["Status"] != "IN PROGRESS":
            fail(f"{evidence_id} must distinguish controlled routing from completed coupon evidence")
        for token in ("Q2-C100", "zero unconnected items", "FAB-REVIEW"):
            if token not in " ".join(row.values()):
                fail(f"{evidence_id} must retain the controlled coupon milestone token {token}")
    for evidence_id in Q2_EMPIRICAL_NOT_STARTED:
        if empirical_by_id[evidence_id]["Status"] != "NOT STARTED":
            fail(f"{evidence_id} cannot pass before coupon or bench evidence exists")
    q2e014 = empirical_by_id["Q2E-014"]
    if q2e014["Status"] != "BLOCKED" or "No PB-100 board import" not in q2e014["Authorization effect"]:
        fail("Q2E-014 must retain the blocked PB-100 board-import boundary")

    blocker = next(
        row
        for row in _rows("PB-100-board-release-blocker-register.csv")
        if row["Blocker ID"] == "PBREL-007"
    )
    blocker_text = " ".join(blocker.values())
    if blocker["Status"] != "Conditional" or "PB-100-q2-maximum-bound-qualification.csv" not in blocker_text:
        fail("PBREL-007 must remain Conditional and reference the Q2 qualification ledger")
    for token in ("PB-100-q2-empirical-qualification-plan.md", "QUALIFICATION-COUPON-ONLY"):
        if token not in blocker_text:
            fail(f"PBREL-007 blocker register must include the empirical route token {token}")

    pre_layout = next(
        row
        for row in _rows("PB-100-staged-release-readiness.csv")
        if row["Blocker ID"] == "PBREL-007" and row["Stage"] == "Pre-layout design"
    )
    if pre_layout["Stage status"] != "Conditional" or pre_layout["Current blocker authorization"] != "BLOCKED":
        fail("PBREL-007 pre-layout must remain Conditional with BLOCKED authorization")
    if "QUALIFICATION-COUPON-ONLY" not in " ".join(pre_layout.values()):
        fail("PBREL-007 staged readiness must distinguish coupon work from PB-100 layout")
