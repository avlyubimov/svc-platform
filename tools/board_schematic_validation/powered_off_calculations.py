from __future__ import annotations

import csv
import io
import math


def render_powered_off_evidence() -> str:
    e73_ioff_a = 10e-6
    e73_pull_max_ohm = 22_000 * 1.01
    e73_uart_off_v = e73_ioff_a * e73_pull_max_ohm

    r13_max_ohm = 3_900 * 1.01
    r13_min_ohm = 3_900 * 0.99
    r14_min_ohm = 15_000 * 0.99
    r14_max_ohm = 15_000 * 1.01
    input_leakage_a = 10e-6
    parallel_min_ohm = r13_max_ohm * r14_min_ohm / (r13_max_ohm + r14_min_ohm)
    parallel_max_ohm = r13_min_ohm * r14_max_ohm / (r13_min_ohm + r14_max_ohm)
    usb_present_min_v = (
        4.75 * r14_min_ohm / (r13_max_ohm + r14_min_ohm)
        - input_leakage_a * parallel_min_ohm
    )
    usb_present_max_v = (
        5.50 * r14_max_ohm / (r13_min_ohm + r14_max_ohm)
        + input_leakage_a * parallel_max_ohm
    )
    usb_absent_max_v = input_leakage_a * r14_max_ohm
    discharge_tau_s = r14_max_ohm * 130e-9
    usb_removal_ms = 1_000 * discharge_tau_s * math.log(usb_present_max_v / 0.77)

    rows = (
        ("E73 UART powered-off clamp", e73_uart_off_v, "V", 0.300, "MAX", 0.300 - e73_uart_off_v),
        ("USB VBUS minimum present", usb_present_min_v, "V", 3.430, "MIN", usb_present_min_v - 3.430),
        ("USB VBUS maximum absent", usb_absent_max_v, "V", 0.770, "MAX", 0.770 - usb_absent_max_v),
        ("USB VBUS removal time", usb_removal_ms, "ms", 3.810, "MAX", 3.810 - usb_removal_ms),
    )
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("Calculation", "Calculated value", "Unit", "Acceptance limit", "Limit type", "Margin", "Result"))
    for name, value, unit, limit, limit_type, margin in rows:
        passed = value <= limit if limit_type == "MAX" else value >= limit
        writer.writerow(
            (
                name,
                f"{value:.4f}",
                unit,
                f"{limit:.4f}",
                limit_type,
                f"{margin:.4f}",
                "PASS" if passed else "FAIL",
            )
        )
    return output.getvalue()
