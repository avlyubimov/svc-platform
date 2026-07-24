#!/usr/bin/env python3
"""Add explicitly reviewed PB-100 tracks and conventional through vias.

This intentionally small helper is used for deterministic connectivity
closeout after the exact copper anchors have been inspected in KiCad.  It does
not infer nets or endpoints, move placement, or change design rules.  Every
output still requires a refilled KiCad DRC before it can be promoted.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from route_pb100_residual import add_track, add_via


def csv_fields(value: str, expected: int) -> list[str]:
    fields = [field.strip() for field in value.split(",")]
    if len(fields) != expected:
        raise argparse.ArgumentTypeError(
            f"expected {expected} comma-separated fields, received {value!r}"
        )
    return fields


def parse_track(value: str) -> tuple[str, str, float, float, float, float]:
    net, layer, x1, y1, x2, y2 = csv_fields(value, 6)
    return net, layer, float(x1), float(y1), float(x2), float(y2)


def parse_via(value: str) -> tuple[str, float, float]:
    net, x, y = csv_fields(value, 3)
    return net, float(x), float(y)


def parse_microvia(
    value: str,
) -> tuple[str, float, float, str, str]:
    net, x, y, start_layer, end_layer = csv_fields(value, 5)
    return net, float(x), float(y), start_layer, end_layer


def net_code(board: pcbnew.BOARD, net_name: str) -> int:
    net = board.FindNet(net_name)
    if net is None:
        raise RuntimeError(f"net {net_name!r} not found")
    return net.GetNetCode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--track",
        action="append",
        type=parse_track,
        default=[],
        metavar="NET,LAYER,X1,Y1,X2,Y2",
    )
    parser.add_argument(
        "--via",
        action="append",
        type=parse_via,
        default=[],
        metavar="NET,X,Y",
    )
    parser.add_argument(
        "--microvia",
        action="append",
        type=parse_microvia,
        default=[],
        metavar="NET,X,Y,START_LAYER,END_LAYER",
        help="add one reviewed 0.30/0.10 mm adjacent-layer laser microvia",
    )
    parser.add_argument(
        "--delete-track-uuid",
        action="append",
        default=[],
        metavar="UUID",
        help="delete one inspected track or via by its stable board UUID",
    )
    args = parser.parse_args()
    if (
        not args.track
        and not args.via
        and not args.microvia
        and not args.delete_track_uuid
    ):
        parser.error(
            "at least one --track, --via, or --delete-track-uuid is required"
        )

    board = pcbnew.LoadBoard(str(args.board))
    delete_uuids = set(args.delete_track_uuid)
    deleted = 0
    for item in list(board.GetTracks()):
        uuid = item.m_Uuid.AsString()
        if uuid not in delete_uuids:
            continue
        board.Delete(item)
        delete_uuids.remove(uuid)
        deleted += 1
    if delete_uuids:
        missing = ", ".join(sorted(delete_uuids))
        raise RuntimeError(f"track/via UUIDs not found: {missing}")
    for net_name, layer, x1, y1, x2, y2 in args.track:
        add_track(
            board,
            (x1, y1),
            (x2, y2),
            layer,
            net_code(board, net_name),
        )
    for net_name, x, y in args.via:
        add_via(board, (x, y), net_code(board, net_name))
    for net_name, x, y, start_layer, end_layer in args.microvia:
        microvia = pcbnew.PCB_VIA(board)
        microvia.SetPosition(
            pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        )
        microvia.SetViaType(pcbnew.VIATYPE_MICROVIA)
        microvia.SetWidth(pcbnew.FromMM(0.30))
        microvia.SetDrill(pcbnew.FromMM(0.10))
        microvia.SetLayerPair(
            board.GetLayerID(start_layer),
            board.GetLayerID(end_layer),
        )
        microvia.SetNetCode(net_code(board, net_name))
        board.Add(microvia)
    pcbnew.SaveBoard(str(args.output), board)
    print(
        f"deleted {deleted} items; added {len(args.track)} tracks "
        f"and {len(args.via)} vias and {len(args.microvia)} microvias"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
