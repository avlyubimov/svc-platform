#!/usr/bin/env python3
"""Route one explicitly reviewed PB-100 connectivity pair.

The caller supplies real copper anchors and, when needed, forced dogbone
escape points along the long axis of fine-pitch pads.  The shared conservative
multilayer router then finds the remaining path.  A refilled KiCad DRC is
required before any result is promoted to the routing manifest.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

import route_pb100_residual as residual
from route_pb100_residual import (
    add_multi_layer_route,
    add_track,
    build_occupancy,
    grid_cell,
    multi_layer_a_star,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--net", required=True)
    parser.add_argument("--first", type=parse_point, required=True)
    parser.add_argument("--first-layer", required=True)
    parser.add_argument("--first-escape", type=parse_point)
    parser.add_argument("--second", type=parse_point, required=True)
    parser.add_argument("--second-layer", required=True)
    parser.add_argument("--second-escape", type=parse_point)
    parser.add_argument("--max-expanded-states", type=int, default=1_500_000)
    parser.add_argument("--via-cost", type=float, default=residual.VIA_COST)
    parser.add_argument("--grid-mm", type=float, default=residual.GRID_MM)
    parser.add_argument(
        "--clearance-margin-mm",
        type=float,
        default=residual.CLEARANCE_MARGIN_MM,
    )
    args = parser.parse_args()

    if args.grid_mm <= 0:
        parser.error("--grid-mm must be positive")
    residual.MAX_EXPANDED_STATES = args.max_expanded_states
    residual.VIA_COST = args.via_cost
    residual.GRID_MM = args.grid_mm
    residual.CLEARANCE_MARGIN_MM = args.clearance_margin_mm
    board = pcbnew.LoadBoard(str(args.board))
    net = board.FindNet(args.net)
    if net is None:
        raise RuntimeError(f"net {args.net!r} not found")
    net_code = net.GetNetCode()
    route_occupancy, via_occupancy = build_occupancy(board)

    first_escape = args.first_escape or args.first
    second_escape = args.second_escape or args.second
    path = multi_layer_a_star(
        route_occupancy,
        via_occupancy,
        args.first_layer,
        grid_cell(first_escape),
        args.second_layer,
        grid_cell(second_escape),
        net_code,
    )
    if path is None:
        raise RuntimeError(
            f"no conservative grid route for {args.net}: "
            f"{first_escape} -> {second_escape}"
        )

    add_track(
        board,
        args.first,
        first_escape,
        args.first_layer,
        net_code,
    )
    add_track(
        board,
        args.second,
        second_escape,
        args.second_layer,
        net_code,
    )
    add_multi_layer_route(
        board,
        path,
        first_escape,
        second_escape,
        net_code,
        route_occupancy,
        via_occupancy,
    )
    pcbnew.SaveBoard(str(args.output), board)

    used_layers: list[str] = []
    for layer, _ in path:
        if not used_layers or used_layers[-1] != layer:
            used_layers.append(layer)
    print(
        f"routed {args.net}: {args.first_layer} {args.first} -> "
        f"{'/'.join(used_layers)} -> {args.second_layer} {args.second}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
