"""PB-100 bounded clamp-loop voltage model."""

from __future__ import annotations

from dataclasses import dataclass

from .model import TRANSIENT


@dataclass(frozen=True)
class Margin:
    item: str
    limit_v: float
    margin_v: float
    result: str


def margins() -> tuple[Margin, ...]:
    limits = (
        ("LM74700-Q1 recommended operating ceiling", TRANSIENT.lm74700_recommended_max_v),
        ("LM74700-Q1 ANODE absolute maximum", TRANSIENT.lm74700_absolute_max_v),
        ("IAUT300N08S5N012 VDS", TRANSIENT.mosfet_limit_v),
        ("TPS48110-Q1 and 100 V buck family", TRANSIENT.controller_limit_v),
    )
    return tuple(
        Margin(
            item=item,
            limit_v=limit_v,
            margin_v=limit_v - TRANSIENT.bounded_stress_v,
            result="PASS" if limit_v > TRANSIENT.bounded_stress_v else "FAIL",
        )
        for item, limit_v in limits
    )
