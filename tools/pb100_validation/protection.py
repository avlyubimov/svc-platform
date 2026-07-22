from __future__ import annotations

from collections.abc import Iterable

from .common import (
    OUTPUT_FREEZE_REVIEW_COLUMNS,
    PB100_DIR,
    REPO_ROOT,
    REQUIRED_TVS_LOAD_DUMP_FREEZE_REVIEW_ITEMS,
    REQUIRED_TVS_OVERSHOOT_CLOSEOUT_PRECHECKS,
    REQUIRED_TVS_OVERSHOOT_ESCAPE_CHECKS,
    REQUIRED_TVS_OVERSHOOT_VALIDATION_CHECKS,
    TVS_LOAD_DUMP_MARGIN_TRACE_COLUMNS,
    TVS_OVERSHOOT_CLOSEOUT_PRECHECK_COLUMNS,
    TVS_OVERSHOOT_ESCAPE_CHECKLIST_COLUMNS,
    TVS_OVERSHOOT_VALIDATION_PRECHECK_COLUMNS,
    csv,
    fail,
    read_text,
    validate_csv,
    validate_no_role_tokens_in_row,
)


def _load_rows(name: str) -> tuple[object, list[dict[str, str]]]:
    path = PB100_DIR / name
    validate_csv(path)
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        fail(f"empty protection artifact: {path.relative_to(REPO_ROOT)}")
    return path, rows


def _validate_keyed_rows(
    name: str,
    key_column: str,
    required_keys: set[str],
    required_columns: Iterable[str],
) -> tuple[object, dict[str, dict[str, str]]]:
    path, rows = _load_rows(name)
    missing_columns = [column for column in required_columns if column not in rows[0]]
    if missing_columns:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    rows_by_key: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        key = row[key_column].strip()
        if key not in required_keys:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: unknown {key_column} {key}")
        if key in rows_by_key:
            fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: duplicate {key_column} {key}")
        for column in required_columns:
            if not row[column].strip():
                fail(f"{path.relative_to(REPO_ROOT)}:{row_number}: empty {column}")
        validate_no_role_tokens_in_row(path, row_number, row)
        rows_by_key[key] = row

    missing_keys = sorted(required_keys - rows_by_key.keys())
    if missing_keys:
        fail(
            f"{path.relative_to(REPO_ROOT)} is missing required rows: "
            f"{', '.join(missing_keys)}"
        )
    return path, rows_by_key


def _require_tokens(name: str, tokens: Iterable[str]) -> None:
    path = PB100_DIR / name
    text = read_text(path)
    for token in tokens:
        if token not in text:
            fail(f"{path.relative_to(REPO_ROOT)} must include {token}")


def validate_tvs_candidate_consistency() -> None:
    stale_tvs_source = "https://www.mccsemi.com/products/esd-protection-and-power-tvs/tvs/SM8S33A"
    active_tvs_paths = (
        "PB-100-symbol-capture-worklist.csv",
        "PB-100-power-path-candidates.csv",
        "PB-100-symbol-mpn-readiness.csv",
    )
    for name in active_tvs_paths:
        text = read_text(PB100_DIR / name)
        if stale_tvs_source in text:
            fail(f"{name} must not use MCC SM8S33A as the active TVS source")
        if "SM8S33AHM3" not in text:
            fail(f"{name} must preserve the rejected SM8S33AHM3/DNP trace")


def validate_tvs_load_dump_margin_trace() -> None:
    required_items = {
        "TPS48110 high-side controller",
        "IAUT300N08S5N012ATMA2 output MOSFET",
        "SIDR626LDP and IAUTN06S5N008 historical paths",
        "IAUT300N08S5N012ATMA2 input reverse MOSFET",
        "LM74700QDBVRQ1 ideal-diode controller",
        "LM5164QDDATQ1 buck",
        "LM5013-Q1 buck alternate",
        "TPS54360B-Q1 buck alternate",
        "TPS2HB35 direct smart switch",
    }
    _, rows = _validate_keyed_rows(
        "PB-100-tvs-load-dump-margin-trace.csv",
        "Protected item",
        required_items,
        TVS_LOAD_DUMP_MARGIN_TRACE_COLUMNS,
    )
    lm74700 = " ".join(rows["LM74700QDBVRQ1 ideal-diode controller"].values())
    for token in ("FAIL", "2.40 V", "at least 5 V"):
        if token not in lm74700:
            fail(f"LM74700 load-dump row must include {token}")
    _require_tokens(
        "PB-100-protection-validation.csv",
        (
            "48.99-54.89V",
            "2.08x provisional hot SOA margin",
            "150 C initial Tj",
            "59.52V protected-node peak budget",
            "CONDITIONAL PRODUCTION",
            "EVT-LAYOUT-AUTHORIZED",
            "PBREL-006 design gate Closed",
            "SM8S33AHM3/I legacy D1",
            "NOT APPROVED",
        ),
    )


def validate_tvs_load_dump_freeze_review() -> None:
    _validate_keyed_rows(
        "PB-100-tvs-load-dump-freeze-review.csv",
        "Review item",
        REQUIRED_TVS_LOAD_DUMP_FREEZE_REVIEW_ITEMS,
        OUTPUT_FREEZE_REVIEW_COLUMNS,
    )
    _require_tokens(
        "PB-100-tvs-load-dump-freeze-review.csv",
        (
            "LM74930QRGERQ1",
            "IAUTN15S6N025ATMA1",
            "48.99-54.89 V",
            "59.52 V peak budget",
            "PBREL-007 production qualification remains Conditional",
            "EVT-LAYOUT-AUTHORIZED",
            "EVT-FAB-AUTHORIZED",
        ),
    )


def validate_tvs_overshoot_escape_checklist() -> None:
    _validate_keyed_rows(
        "PB-100-tvs-overshoot-escape-checklist.csv",
        "Check ID",
        REQUIRED_TVS_OVERSHOOT_ESCAPE_CHECKS,
        TVS_OVERSHOOT_ESCAPE_CHECKLIST_COLUMNS,
    )
    _require_tokens(
        "PB-100-tvs-overshoot-escape-checklist.csv",
        (
            "79-101 V",
            "0.5-4 ohm",
            "40-400 ms",
            "Q2 linear-mode SOA",
            "dynamic SOA",
            "7.200 W",
            "150 C initial Tj",
            "5-10 ms",
            "ten pulses separated by 60 s",
            "PB-100.kicad_pcb",
        ),
    )


def validate_tvs_overshoot_validation_precheck() -> None:
    _, rows = _validate_keyed_rows(
        "PB-100-tvs-overshoot-validation-precheck.csv",
        "Validation ID",
        REQUIRED_TVS_OVERSHOOT_VALIDATION_CHECKS,
        TVS_OVERSHOOT_VALIDATION_PRECHECK_COLUMNS,
    )
    instrumentation = " ".join(rows["TVS-VAL-006"].values()).lower()
    if "probe" not in instrumentation or "bandwidth" not in instrumentation:
        fail("TVS validation must record probe bandwidth")
    parasitics = " ".join(rows["TVS-VAL-007"].values()).lower()
    if "parasitic" not in parasitics or "inductance" not in parasitics:
        fail("TVS validation must require extracted parasitic inductance")
    _require_tokens(
        "PB-100-tvs-overshoot-validation-precheck.csv",
        ("48 boundary rows", "Cutoff tolerance", "dynamic SOA", "ten pulses", "PB-100.kicad_pcb"),
    )


def validate_tvs_overshoot_closeout_precheck() -> None:
    _, rows = _validate_keyed_rows(
        "PB-100-tvs-overshoot-closeout-precheck.csv",
        "Precheck ID",
        REQUIRED_TVS_OVERSHOOT_CLOSEOUT_PRECHECKS,
        TVS_OVERSHOOT_CLOSEOUT_PRECHECK_COLUMNS,
    )
    for precheck_id, row in rows.items():
        if "do not" not in row["Blocked action"].lower():
            fail(f"{precheck_id} must explicitly block premature acceptance")
    _require_tokens(
        "PB-100-tvs-overshoot-closeout-precheck.csv",
        (
            "ADR-0016",
            "ADR-0018",
            "no higher than 55 V",
            "Hot derated SOA limit is provisionally 83.33 A",
            "protected-node peak budget is 59.52 V",
            "dynamic SOA",
            "Ten pulses at 60 s",
            "PBREL-007 production qualification remains Conditional",
            "EVT-LAYOUT-AUTHORIZED",
            "EVT-FAB-AUTHORIZED",
        ),
    )
