# Readiness Consistency Validation

This package owns cross-document release-readiness consistency only. It does
not validate electrical topology, KiCad geometry, firmware, or manufacturing
rules already covered by the engineering validators.

Sources of truth:

- `docs/adr/ADR-0015-can1-physical-layer-board-ownership.md` for CAN1 ownership.
- The PB-100, LB-100, and FB-100 board-release blocker registers for active
  blocker IDs and counts.
- The reviewed FX18 footprint and inventory checks in `validate_board_order.py`
  for physical land implementation.

`consistency.py` verifies that the two three-board readiness CSV files and
`docs/product/final-readiness.md` report the same active blockers. It also
rejects stale active-document claims about ADR-0015, CAN1 ownership, FX18 lands,
or the selected 80 V MOSFET baseline.

Run it directly with:

```sh
make validate-readiness-consistency
```

It is also part of `make check`.
