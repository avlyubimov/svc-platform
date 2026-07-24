#!/usr/bin/env python3
"""Describe the real KiCad items behind PB-100 unconnected DRC findings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


def mm_point(point: pcbnew.VECTOR2I) -> tuple[float, float]:
    x_mm, y_mm = pcbnew.ToMM(point)
    return round(float(x_mm), 6), round(float(y_mm), 6)


def item_uuid(item: pcbnew.BOARD_ITEM) -> str:
    return item.m_Uuid.AsString()


def describe(board: pcbnew.BOARD, item: pcbnew.BOARD_ITEM) -> str:
    parts = [type(item).__name__, item_uuid(item)]
    if hasattr(item, "GetNetname"):
        parts.append(f"net={item.GetNetname()}")
    if isinstance(item, pcbnew.PAD):
        footprint = item.GetParentFootprint()
        parts.extend(
            (
                f"pad={footprint.GetReference()}.{item.GetNumber()}",
                f"at={mm_point(item.GetPosition())}",
            )
        )
    elif isinstance(item, pcbnew.PCB_VIA):
        parts.extend(
            (
                f"via={mm_point(item.GetPosition())}",
                f"layers={board.GetLayerName(item.TopLayer())}/{board.GetLayerName(item.BottomLayer())}",
            )
        )
    elif isinstance(item, pcbnew.PCB_TRACK):
        parts.extend(
            (
                f"start={mm_point(item.GetStart())}",
                f"end={mm_point(item.GetEnd())}",
                f"layer={board.GetLayerName(item.GetLayer())}",
            )
        )
    elif isinstance(item, pcbnew.ZONE):
        layers = [
            board.GetLayerName(layer)
            for layer in range(pcbnew.PCB_LAYER_ID_COUNT)
            if item.IsOnLayer(layer)
        ]
        parts.append(f"layers={','.join(layers)}")
    elif hasattr(item, "GetPosition"):
        parts.append(f"at={mm_point(item.GetPosition())}")
    return " ".join(parts)


def board_items(board: pcbnew.BOARD) -> dict[str, pcbnew.BOARD_ITEM]:
    items: list[pcbnew.BOARD_ITEM] = []
    items.extend(board.GetTracks())
    items.extend(board.Zones())
    for footprint in board.GetFootprints():
        items.append(footprint)
        items.extend(footprint.Pads())
    return {item_uuid(item): item for item in items}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--drc-json", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    connectivity = board.GetConnectivity()
    by_uuid = board_items(board)
    report = json.loads(args.drc_json.read_text(encoding="utf-8"))

    for index, finding in enumerate(report.get("unconnected_items", []), 1):
        print(f"\n[{index:02d}] {finding.get('description', '')}")
        for report_item in finding.get("items", []):
            uuid = str(report_item.get("uuid", ""))
            item = by_uuid.get(uuid)
            print(f"  DRC: {report_item.get('description', '')}")
            if item is None:
                print(f"  PCB: missing UUID {uuid}")
                continue
            print(f"  PCB: {describe(board, item)}")
            connected = connectivity.GetConnectedItems(item)
            descriptions = sorted(
                describe(board, connected_item)
                for connected_item in connected
                if item_uuid(connected_item) != uuid
            )
            print(f"  CLUSTER: {len(descriptions)} other items")
            for connected_description in descriptions[:12]:
                print(f"    {connected_description}")
            if len(descriptions) > 12:
                print(f"    ... {len(descriptions) - 12} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
