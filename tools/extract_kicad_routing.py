#!/usr/bin/env python3
"""Export deterministic straight-track/via copper from a KiCad board to CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pcbnew


FIELDS = (
    "kind", "net", "layer", "width_mm", "start_x_mm", "start_y_mm",
    "end_x_mm", "end_y_mm", "diameter_mm", "drill_mm", "start_layer",
    "end_layer",
)


def value(number: int) -> str:
    return f"{pcbnew.ToMM(number):.6f}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--layer-map", action="append", default=[])
    args = parser.parse_args()
    layer_map = dict(item.split("=", 1) for item in args.layer_map)

    board = pcbnew.LoadBoard(str(args.board))
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    for item in board.GetTracks():
        net = item.GetNetname()
        if item.Type() == pcbnew.PCB_VIA_T:
            via = pcbnew.Cast_to_PCB_VIA(item)
            row = {
                "kind": "via", "net": net, "layer": "", "width_mm": "",
                "start_x_mm": value(via.GetPosition().x),
                "start_y_mm": value(via.GetPosition().y), "end_x_mm": "",
                "end_y_mm": "", "diameter_mm": value(via.GetWidth(via.TopLayer())),
                "drill_mm": value(via.GetDrillValue()),
                "start_layer": layer_map.get(board.GetLayerName(via.TopLayer()), board.GetLayerName(via.TopLayer())),
                "end_layer": layer_map.get(board.GetLayerName(via.BottomLayer()), board.GetLayerName(via.BottomLayer())),
            }
        elif item.Type() == pcbnew.PCB_TRACE_T:
            start = (value(item.GetStart().x), value(item.GetStart().y))
            end = (value(item.GetEnd().x), value(item.GetEnd().y))
            if end < start:
                start, end = end, start
            layer = board.GetLayerName(item.GetLayer())
            row = {
                "kind": "segment", "net": net,
                "layer": layer_map.get(layer, layer),
                "width_mm": value(item.GetWidth()),
                "start_x_mm": start[0], "start_y_mm": start[1],
                "end_x_mm": end[0], "end_y_mm": end[1],
                "diameter_mm": "", "drill_mm": "", "start_layer": "",
                "end_layer": "",
            }
        else:
            raise ValueError(f"unsupported routed item type {item.Type()}")
        key = tuple(row[field] for field in FIELDS)
        if key not in seen:
            seen.add(key)
            rows.append(row)
    rows.sort(key=lambda row: tuple(row[field] for field in FIELDS))
    with args.output.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"exported={len(rows)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
