#!/usr/bin/env python3
"""Attach selected PB-100 surface pads to an existing internal plane.

This helper is intentionally narrow: it finds a DRC-clear conventional
through-via escape for explicit pad centres supplied by the engineer.  It
does not infer nets or alter placement, zones, stack-up, or net classes.
KiCad refill and DRC remain the acceptance authority for every result.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pcbnew

from route_pb100_residual import (
    a_star_between,
    add_track,
    add_via,
    build_occupancy,
    cell_point,
    compress_path,
    free_via_site,
    grid_cell,
    in_bounds,
)


Point = tuple[float, float]


def parse_point(value: str) -> Point:
    try:
        x_text, y_text = value.split(",", 1)
        return float(x_text), float(y_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"expected X,Y coordinates, received {value!r}"
        ) from error


def candidate_sites(
    endpoint: Point,
    via_occupancy: dict[str, dict[tuple[int, int], set[int]]],
    net_code: int,
    maximum_radius_cells: int,
) -> list[tuple[int, int]]:
    centre = grid_cell(endpoint)
    candidates: list[tuple[float, tuple[int, int]]] = []
    for dx in range(-maximum_radius_cells, maximum_radius_cells + 1):
        for dy in range(-maximum_radius_cells, maximum_radius_cells + 1):
            cell = (centre[0] + dx, centre[1] + dy)
            if not in_bounds(cell) or not free_via_site(
                via_occupancy, cell, net_code
            ):
                continue
            candidates.append((math.hypot(dx, dy), cell))
    return [cell for _, cell in sorted(candidates)]


def attach_one(
    board: pcbnew.BOARD,
    endpoint: Point,
    escape: Point | None,
    layer_name: str,
    net_code: int,
    maximum_radius_cells: int,
) -> tuple[Point, int]:
    route_occupancy, via_occupancy = build_occupancy(board)
    route_start = escape or endpoint
    start = grid_cell(route_start)
    for candidate in candidate_sites(
        endpoint, via_occupancy, net_code, maximum_radius_cells
    ):
        path = a_star_between(
            route_occupancy[layer_name],
            [start],
            [candidate],
            net_code,
        )
        if path is None:
            continue
        points = [cell_point(cell) for cell in compress_path(path)]
        add_track(board, endpoint, route_start, layer_name, net_code)
        add_track(board, route_start, points[0], layer_name, net_code)
        for first, second in zip(points, points[1:]):
            add_track(board, first, second, layer_name, net_code)
        add_via(board, cell_point(candidate), net_code)
        return cell_point(candidate), len(points)
    raise RuntimeError(
        f"no conventional through-via escape found from {endpoint} "
        f"within {maximum_radius_cells / 10:.1f} mm"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--net", required=True)
    parser.add_argument("--layer", default="F.Cu")
    parser.add_argument("--endpoint", action="append", type=parse_point, required=True)
    parser.add_argument(
        "--escape",
        action="append",
        type=parse_point,
        help=(
            "optional forced surface fan-out point paired with --endpoint; "
            "use the pad's long axis in a fine-pitch row"
        ),
    )
    parser.add_argument("--maximum-radius-mm", type=float, default=8.0)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    net = board.FindNet(args.net)
    if net is None:
        raise RuntimeError(f"net {args.net!r} not found")
    net_code = net.GetNetCode()
    maximum_radius_cells = round(args.maximum_radius_mm / 0.10)
    escapes = args.escape or []
    if escapes and len(escapes) != len(args.endpoint):
        parser.error("--escape count must match --endpoint count")
    if not escapes:
        escapes = [None] * len(args.endpoint)

    for endpoint, escape in zip(args.endpoint, escapes):
        via, point_count = attach_one(
            board,
            endpoint,
            escape,
            args.layer,
            net_code,
            maximum_radius_cells,
        )
        print(f"attached {args.net} {endpoint} to plane via {via} ({point_count} points)")

    pcbnew.SaveBoard(str(args.output), board)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
