#!/usr/bin/env python3
"""Seed safe PB-100 plane attachments before signal autorouting.

Only sufficiently large SMD lands on the continuous GND and VBAT_PROT planes
receive filled/capped 0.60/0.30 mm conventional through vias.  Fine-pitch
controller lands and any site blocked on another copper layer remain untouched.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pcbnew

from route_pb100_residual import (
    add_via,
    build_occupancy,
    free_via_site,
    grid_cell,
    mark_disc,
)


PLANE_NETS = {"GND", "VBAT_PROT"}
MIN_PAD_DIMENSION_MM = 0.75


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.input))
    route_occupancy, via_occupancy = build_occupancy(board)
    via_points = [
        tuple(float(value) for value in pcbnew.ToMM(item.GetPosition()))
        for item in board.GetTracks()
        if isinstance(item, pcbnew.PCB_VIA)
    ]
    added = {net_name: 0 for net_name in PLANE_NETS}
    skipped = {net_name: 0 for net_name in PLANE_NETS}

    pads = sorted(
        (
            pad
            for footprint in board.GetFootprints()
            for pad in footprint.Pads()
            if pad.GetNetname() in PLANE_NETS
        ),
        key=lambda pad: (
            pad.GetNetname(),
            pad.GetParentFootprint().GetReference(),
            pad.GetNumber(),
        ),
    )
    for pad in pads:
        net_name = pad.GetNetname()
        if pad.IsOnLayer(board.GetLayerID("F.Cu")) == pad.IsOnLayer(
            board.GetLayerID("B.Cu")
        ):
            skipped[net_name] += 1
            continue
        width_mm, height_mm = pcbnew.ToMM(pad.GetSize())
        if min(float(width_mm), float(height_mm)) < MIN_PAD_DIMENSION_MM:
            skipped[net_name] += 1
            continue
        point = tuple(float(value) for value in pcbnew.ToMM(pad.GetPosition()))
        if any(
            math.hypot(point[0] - x_mm, point[1] - y_mm) < 0.81
            for x_mm, y_mm in via_points
        ):
            skipped[net_name] += 1
            continue
        net_code = pad.GetNetCode()
        cell = grid_cell(point)
        if not free_via_site(via_occupancy, cell, net_code):
            skipped[net_name] += 1
            continue
        add_via(board, point, net_code)
        via_points.append(point)
        for layer in route_occupancy:
            mark_disc(route_occupancy[layer], point, 0.60, net_code)
            mark_disc(via_occupancy[layer], point, 0.80, net_code)
        added[net_name] += 1
        print(
            f"seeded {net_name} via-in-pad at "
            f"{pad.GetParentFootprint().GetReference()}.{pad.GetNumber()} {point}",
            flush=True,
        )

    pcbnew.SaveBoard(str(args.output), board)
    for net_name in sorted(PLANE_NETS):
        print(
            f"{net_name}: seeded {added[net_name]}, skipped {skipped[net_name]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
