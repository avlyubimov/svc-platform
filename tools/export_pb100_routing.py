#!/usr/bin/env python3
"""Export PB-100 copper added to a generated base board as a CSV manifest.

The PB-100 board is generator-owned.  External routing tools are therefore
used only on disposable board copies; accepted tracks and vias are promoted
through ``PB-100-routing.csv`` and reproduced by ``generate_pb100_layout.py``.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

import pcbnew


FIELDNAMES = (
    "kind",
    "net",
    "start_x_mm",
    "start_y_mm",
    "end_x_mm",
    "end_y_mm",
    "width_mm",
    "layer",
    "diameter_mm",
    "drill_mm",
    "start_layer",
    "end_layer",
    "via_type",
)
PROTECTED_NETS = {
    "AGND",
    "BUCK_SW",
    "CAN1_HARNESS_H",
    "CAN1_HARNESS_L",
    "GND",
    "INPUT_COMMON_SOURCE",
    "LB_3V3_IO",
    "LM74930_VS",
    "PB_5V_OUT",
    "SW_12V_FUSED",
    "VBAT_PROT",
    "VBAT_PROT_PRELINK",
    "VBAT_RAW",
    "VBAT_REV_PROT",
}


def protected_net(net_name: str) -> bool:
    return (
        net_name in PROTECTED_NETS
        or re.fullmatch(r"OUT\d+_(?:FET_DRAIN|SWITCHED)", net_name) is not None
    )


def normalized_endpoints(item: pcbnew.PCB_TRACK) -> tuple[tuple[int, int], tuple[int, int]]:
    points = (
        (item.GetStart().x, item.GetStart().y),
        (item.GetEnd().x, item.GetEnd().y),
    )
    return tuple(sorted(points))  # type: ignore[return-value]


def item_identity(
    board: pcbnew.BOARD,
    item: pcbnew.PCB_TRACK,
) -> tuple[object, ...]:
    net_name = item.GetNetname()
    if isinstance(item, pcbnew.PCB_VIA):
        position = item.GetPosition()
        top_layer = item.TopLayer()
        bottom_layer = item.BottomLayer()
        return (
            "via",
            net_name,
            position.x,
            position.y,
            item.GetViaType(),
            item.GetWidth(top_layer),
            item.GetDrillValue(),
            board.GetLayerName(top_layer),
            board.GetLayerName(bottom_layer),
        )
    start, end = normalized_endpoints(item)
    return (
        "segment",
        net_name,
        start,
        end,
        item.GetWidth(),
        board.GetLayerName(item.GetLayer()),
    )


def mm(value: int) -> str:
    return f"{float(pcbnew.ToMM(value)):.6f}"


def routing_row(board: pcbnew.BOARD, item: pcbnew.PCB_TRACK) -> dict[str, str]:
    if isinstance(item, pcbnew.PCB_VIA):
        position = item.GetPosition()
        top_layer = item.TopLayer()
        bottom_layer = item.BottomLayer()
        via_type = {
            pcbnew.VIATYPE_MICROVIA: "micro",
            pcbnew.VIATYPE_BLIND: "blind",
            pcbnew.VIATYPE_BURIED: "blind",
        }.get(item.GetViaType(), "through")
        return {
            "kind": "via",
            "net": item.GetNetname(),
            "start_x_mm": mm(position.x),
            "start_y_mm": mm(position.y),
            "end_x_mm": "",
            "end_y_mm": "",
            "width_mm": "",
            "layer": "",
            "diameter_mm": mm(item.GetWidth(top_layer)),
            "drill_mm": mm(item.GetDrillValue()),
            "start_layer": board.GetLayerName(top_layer),
            "end_layer": board.GetLayerName(bottom_layer),
            "via_type": via_type,
        }
    start = item.GetStart()
    end = item.GetEnd()
    return {
        "kind": "segment",
        "net": item.GetNetname(),
        "start_x_mm": mm(start.x),
        "start_y_mm": mm(start.y),
        "end_x_mm": mm(end.x),
        "end_y_mm": mm(end.y),
        "width_mm": mm(item.GetWidth()),
        "layer": board.GetLayerName(item.GetLayer()),
        "diameter_mm": "",
        "drill_mm": "",
        "start_layer": "",
        "end_layer": "",
        "via_type": "",
    }


def normalized_protected_row(
    board: pcbnew.BOARD,
    item: pcbnew.PCB_TRACK,
) -> dict[str, str] | None:
    """Return only low-energy autorouter attachments on protected nets.

    The generator already owns the broad high-current segments and 1.0/0.5 mm
    transition fields.  Imported 0.20 mm/0.60 mm autorouter geometry is kept
    only as a pin, option-footprint, sense, or local zone attachment and is
    preserved at the DRC-clean preliminary width used by the router.  This
    copper is not credited for high-current capacity; the explicit zones and
    generator-owned broad segments remain the only current-path evidence.
    """

    if isinstance(item, pcbnew.PCB_VIA):
        is_reviewed_through_via = (
            item.GetViaType() != pcbnew.VIATYPE_MICROVIA
            and item.GetWidth(item.TopLayer()) == pcbnew.FromMM(0.60)
            and item.GetDrillValue() == pcbnew.FromMM(0.30)
        )
        is_reviewed_microvia = (
            item.GetViaType() == pcbnew.VIATYPE_MICROVIA
            and item.GetWidth(item.TopLayer()) == pcbnew.FromMM(0.30)
            and item.GetDrillValue() == pcbnew.FromMM(0.10)
        )
        if not is_reviewed_through_via and not is_reviewed_microvia:
            return None
        row = routing_row(board, item)
        if is_reviewed_through_via:
            row["diameter_mm"] = "0.600000"
            row["drill_mm"] = "0.300000"
        else:
            row["diameter_mm"] = "0.300000"
            row["drill_mm"] = "0.100000"
        return row
    if item.GetWidth() != pcbnew.FromMM(0.20):
        return None
    return routing_row(board, item)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--routed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--include-protected",
        action="store_true",
        help="include normalized low-energy attachments on protected power/CAN nets",
    )
    args = parser.parse_args()

    base = pcbnew.LoadBoard(str(args.base))
    routed = pcbnew.LoadBoard(str(args.routed))
    generated_copper = Counter(item_identity(base, item) for item in base.GetTracks())
    rows = []
    for item in routed.GetTracks():
        is_protected = protected_net(item.GetNetname())
        if is_protected and not args.include_protected:
            continue
        identity = item_identity(routed, item)
        if generated_copper[identity]:
            generated_copper[identity] -= 1
            continue
        if is_protected:
            row = normalized_protected_row(routed, item)
            if row is not None:
                rows.append(row)
        else:
            rows.append(routing_row(routed, item))
    rows.sort(
        key=lambda row: (
            row["net"],
            row["kind"],
            row["layer"],
            row["start_layer"],
            row["start_x_mm"],
            row["start_y_mm"],
            row["end_x_mm"],
            row["end_y_mm"],
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as routing_file:
        writer = csv.DictWriter(
            routing_file,
            fieldnames=FIELDNAMES,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"exported {len(rows)} PB-100 routing items to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
