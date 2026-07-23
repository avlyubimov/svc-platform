#!/usr/bin/env python3
"""Stitch PB-100 outer GND islands and protected-battery loads to inner planes.

The final authority remains a refilled KiCad DRC.  This helper only adds
ordinary 0.60/0.30 mm F.Cu-to-B.Cu plated through vias and 0.20 mm local
attachments; it does not create or widen any high-current path.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew
import route_pb100_residual as residual_router

from route_pb100_residual import (
    a_star_between,
    add_track,
    add_via,
    blocked,
    build_occupancy,
    cell_point,
    compress_path,
    free_via_site,
    grid_cell,
    in_bounds,
    line_is_free,
    mark_disc,
    mark_segment,
    parse_endpoint,
)


GND_NET = "GND"
PROTECTED_NET = "VBAT_PROT"


def remove_rejected_copper(board: pcbnew.BOARD, drc: dict[str, object]) -> tuple[int, int]:
    """Remove externally routed edge offenders and vias proven dangling."""

    edge_uuids = set()
    dangling_uuids = set()
    for finding in drc.get("violations", []):
        if not isinstance(finding, dict):
            continue
        finding_type = finding.get("type")
        target = (
            edge_uuids
            if finding_type in {"clearance", "copper_edge_clearance", "track_dangling"}
            else dangling_uuids
            if finding_type in {"hole_to_hole", "via_dangling"}
            else None
        )
        if target is None:
            continue
        for item in finding.get("items", []):
            if not isinstance(item, dict):
                continue
            item_uuid = item.get("uuid")
            description = str(item.get("description", ""))
            if (
                finding_type == "clearance"
                and not any(f"[{net_name}]" in description for net_name in (GND_NET, PROTECTED_NET))
            ):
                continue
            if item_uuid:
                target.add(str(item_uuid))

    removed_edges = 0
    removed_vias = 0
    for item in list(board.GetTracks()):
        item_uuid = item.m_Uuid.AsString()
        if item_uuid in edge_uuids:
            board.RemoveNative(item)
            removed_edges += 1
        elif item_uuid in dangling_uuids and isinstance(item, pcbnew.PCB_VIA):
            board.RemoveNative(item)
            removed_vias += 1
    return removed_edges, removed_vias


def pad_keepouts(board: pcbnew.BOARD) -> list[tuple[float, float, float, float]]:
    keepouts = []
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            box = pad.GetBoundingBox()
            x_mm, y_mm = pcbnew.ToMM(box.GetOrigin())
            width_mm, height_mm = pcbnew.ToMM(box.GetSize())
            keepouts.append(
                (
                    float(x_mm) - 0.31,
                    float(y_mm) - 0.31,
                    float(x_mm + width_mm) + 0.31,
                    float(y_mm + height_mm) + 0.31,
                )
            )
    return keepouts


def existing_vias(board: pcbnew.BOARD) -> list[tuple[float, float]]:
    return [
        tuple(float(value) for value in pcbnew.ToMM(item.GetPosition()))
        for item in board.GetTracks()
        if isinstance(item, pcbnew.PCB_VIA)
    ]


def safe_via_site(
    cell: tuple[int, int],
    net_code: int,
    via_occupancy: dict,
    pad_boxes: list[tuple[float, float, float, float]],
    via_points: list[tuple[float, float]],
) -> bool:
    """Allow same-net copper, but reject via-in-pad and drilled-hole overlap."""

    if not free_via_site(via_occupancy, cell, net_code):
        return False
    point = cell_point(cell)
    if not (0.80 <= point[0] <= 149.20 and 0.80 <= point[1] <= 89.20):
        return False
    if any(x1 <= point[0] <= x2 and y1 <= point[1] <= y2 for x1, y1, x2, y2 in pad_boxes):
        return False
    if any(math.hypot(point[0] - x_mm, point[1] - y_mm) < 0.81 for x_mm, y_mm in via_points):
        return False
    return True


def reserve_via(route_occupancy: dict, via_occupancy: dict, point: tuple[float, float], net_code: int) -> None:
    for layer in route_occupancy:
        mark_disc(route_occupancy[layer], point, 0.60, net_code)
        mark_disc(via_occupancy[layer], point, 0.80, net_code)


def reserve_track(
    route_occupancy: dict,
    via_occupancy: dict,
    layer: str,
    start: tuple[float, float],
    end: tuple[float, float],
    net_code: int,
) -> None:
    mark_segment(route_occupancy[layer], start, end, 0.40, net_code)
    mark_segment(via_occupancy[layer], start, end, 0.60, net_code)


def outline_contains_via(outline: pcbnew.SHAPE_LINE_CHAIN, point: tuple[float, float]) -> bool:
    """Place the via centre on the island; refill grows copper to its annulus."""

    candidate = pcbnew.VECTOR2I(
        pcbnew.FromMM(point[0]),
        pcbnew.FromMM(point[1]),
    )
    return outline.PointInside(candidate)


def island_via_site(
    outline: pcbnew.SHAPE_LINE_CHAIN,
    via_occupancy: dict,
    net_code: int,
    pad_boxes: list[tuple[float, float, float, float]],
    via_points: list[tuple[float, float]],
) -> tuple[float, float] | None:
    box = outline.BBox()
    origin_x, origin_y = pcbnew.ToMM(box.GetOrigin())
    size_x, size_y = pcbnew.ToMM(box.GetSize())
    centre = (float(origin_x + size_x / 2), float(origin_y + size_y / 2))
    first = grid_cell((float(origin_x), float(origin_y)))
    last = grid_cell((float(origin_x + size_x), float(origin_y + size_y)))
    candidates = []
    # A 0.20 mm sampling pitch finds narrow islands while keeping the search
    # bounded on the 150 mm x 90 mm board.
    for x_index in range(first[0], last[0] + 1, 2):
        for y_index in range(first[1], last[1] + 1, 2):
            cell = (x_index, y_index)
            if (
                not in_bounds(cell)
                or not safe_via_site(cell, net_code, via_occupancy, pad_boxes, via_points)
            ):
                continue
            point = cell_point(cell)
            candidates.append((math.hypot(point[0] - centre[0], point[1] - centre[1]), point))
    for _, point in sorted(candidates):
        if outline_contains_via(outline, point):
            return point
    return None


def stitch_ground_islands(
    board: pcbnew.BOARD,
    route_occupancy: dict,
    via_occupancy: dict,
    pad_boxes: list[tuple[float, float, float, float]],
    via_points: list[tuple[float, float]],
) -> tuple[int, list[str]]:
    net = board.FindNet(GND_NET)
    if net is None:
        raise RuntimeError("GND net is missing")
    net_code = net.GetNetCode()
    added = 0
    failures = []
    for zone in board.Zones():
        layer_name = board.GetLayerName(zone.GetLayer())
        if zone.GetNetname() != GND_NET or layer_name not in {"F.Cu", "B.Cu"}:
            continue
        filled = zone.GetFilledPolysList(zone.GetLayer())
        for island_index in range(filled.OutlineCount()):
            outline = filled.COutline(island_index)
            point = island_via_site(
                outline,
                via_occupancy,
                net_code,
                pad_boxes,
                via_points,
            )
            if point is None:
                failures.append(f"{layer_name} GND island {island_index}: no safe via site")
                continue
            add_via(board, point, net_code)
            via_points.append(point)
            reserve_via(route_occupancy, via_occupancy, point, net_code)
            added += 1
            print(f"stitched {layer_name} GND island {island_index} at {point}", flush=True)
    return added, failures


def nearby_attachment_route(
    endpoint: tuple[float, float],
    source_layer: str,
    route_occupancy: dict,
    via_occupancy: dict,
    net_code: int,
    pad_boxes: list[tuple[float, float, float, float]],
    via_points: list[tuple[float, float]],
) -> list[tuple[float, float]] | None:
    centre = grid_cell(endpoint)
    goal_cells = []
    for radius in range(4, 41):
        candidates = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                cell = (centre[0] + dx, centre[1] + dy)
                if (
                    not in_bounds(cell)
                    or not safe_via_site(
                        cell,
                        net_code,
                        via_occupancy,
                        pad_boxes,
                        via_points,
                    )
                ):
                    continue
                point = cell_point(cell)
                if not line_is_free(route_occupancy[source_layer], endpoint, point, net_code):
                    continue
                candidates.append((math.hypot(dx, dy), point))
        if candidates:
            return [endpoint, min(candidates)[1]]
    for radius in range(4, 101):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                cell = (centre[0] + dx, centre[1] + dy)
                if (
                    in_bounds(cell)
                    and safe_via_site(
                        cell,
                        net_code,
                        via_occupancy,
                        pad_boxes,
                        via_points,
                    )
                ):
                    goal_cells.append(cell)
        if len(goal_cells) >= 128:
            break
    path = a_star_between(
        route_occupancy[source_layer],
        [centre],
        goal_cells,
        net_code,
    )
    if path is None:
        return None
    return [
        endpoint,
        *(
            point
            for point in (cell_point(cell) for cell in compress_path(path))
            if math.hypot(point[0] - endpoint[0], point[1] - endpoint[1]) >= 0.15
        ),
    ]


def attach_plane_clusters(
    board: pcbnew.BOARD,
    drc: dict[str, object],
    route_occupancy: dict,
    via_occupancy: dict,
    net_name: str,
    pad_boxes: list[tuple[float, float, float, float]],
    via_points: list[tuple[float, float]],
) -> tuple[int, list[str]]:
    net = board.FindNet(net_name)
    if net is None:
        raise RuntimeError(f"{net_name} net is missing")
    net_code = net.GetNetCode()
    endpoints: dict[tuple[tuple[float, float], str], str] = {}
    for finding in drc.get("unconnected_items", []):
        if not isinstance(finding, dict):
            continue
        for item in finding.get("items", []):
            if not isinstance(item, dict):
                continue
            description = str(item.get("description", ""))
            if f"[{net_name}]" not in description:
                continue
            if any(token in description for token in ("Зона", "Zone", "Перех. отв.", "Via", "via")):
                continue
            point, layer = parse_endpoint(item)
            endpoints[(point, layer)] = description

    added = 0
    failures = []
    for (endpoint, layer), description in sorted(endpoints.items()):
        if layer not in route_occupancy:
            failures.append(f"{description}: unsupported source layer {layer}")
            continue
        route = nearby_attachment_route(
            endpoint,
            layer,
            route_occupancy,
            via_occupancy,
            net_code,
            pad_boxes,
            via_points,
        )
        via_in_pad = False
        if route is None:
            endpoint_cell = grid_cell(endpoint)
            if (
                free_via_site(via_occupancy, endpoint_cell, net_code)
                and not any(
                    math.hypot(endpoint[0] - x_mm, endpoint[1] - y_mm) < 0.81
                    for x_mm, y_mm in via_points
                )
            ):
                route = [endpoint]
                via_in_pad = True
        if route is None:
            failures.append(f"{description}: no safe protected-plane attachment")
            continue
        for start, end in zip(route, route[1:]):
            add_track(board, start, end, layer, net_code)
            reserve_track(route_occupancy, via_occupancy, layer, start, end, net_code)
        point = route[-1]
        add_via(board, point, net_code)
        via_points.append(point)
        reserve_via(route_occupancy, via_occupancy, point, net_code)
        added += 1
        print(f"attached {net_name} {layer} {endpoint} at {point}", flush=True)
    return added, failures


def attach_disconnected_pad_clusters(
    board: pcbnew.BOARD,
    route_occupancy: dict,
    via_occupancy: dict,
    net_name: str,
    pad_boxes: list[tuple[float, float, float, float]],
    via_points: list[tuple[float, float]],
) -> tuple[int, list[str]]:
    """Attach every pad cluster not already joined to the inner plane."""

    net = board.FindNet(net_name)
    if net is None:
        raise RuntimeError(f"{net_name} net is missing")
    net_code = net.GetNetCode()
    connectivity = board.GetConnectivity()
    pads = [
        pad
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
        if pad.GetNetname() == net_name
    ]
    clusters: dict[tuple[str, ...], list[pcbnew.PAD]] = {}
    for pad in pads:
        connected = connectivity.GetConnectedItems(pad)
        identity = tuple(
            sorted(
                item.m_Uuid.AsString()
                for item in connected
                if hasattr(item, "m_Uuid")
            )
        )
        if not identity:
            identity = (pad.m_Uuid.AsString(),)
        clusters.setdefault(identity, []).append(pad)
    if len(clusters) <= 1:
        return 0, []

    main_identity = max(
        clusters,
        key=lambda identity: (
            len(identity),
            len(clusters[identity]),
        ),
    )
    added = 0
    failures = []
    for identity, cluster_pads in sorted(
        clusters.items(),
        key=lambda item: item[1][0].GetParentFootprint().GetReference(),
    ):
        if identity == main_identity:
            continue
        pad = cluster_pads[0]
        reference = pad.GetParentFootprint().GetReference()
        layer = (
            "B.Cu"
            if pad.IsOnLayer(board.GetLayerID("B.Cu"))
            and not pad.IsOnLayer(board.GetLayerID("F.Cu"))
            else "F.Cu"
        )
        endpoint = tuple(float(value) for value in pcbnew.ToMM(pad.GetPosition()))
        route = nearby_attachment_route(
            endpoint,
            layer,
            route_occupancy,
            via_occupancy,
            net_code,
            pad_boxes,
            via_points,
        )
        via_in_pad = False
        if route is None:
            endpoint_cell = grid_cell(endpoint)
            if (
                free_via_site(via_occupancy, endpoint_cell, net_code)
                and not any(
                    math.hypot(endpoint[0] - x_mm, endpoint[1] - y_mm) < 0.81
                    for x_mm, y_mm in via_points
                )
            ):
                route = [endpoint]
                via_in_pad = True
        if route is None:
            failures.append(
                f"{reference}.{pad.GetNumber()} [{net_name}]: no safe plane attachment"
            )
            continue
        for start, end in zip(route, route[1:]):
            add_track(board, start, end, layer, net_code)
            reserve_track(route_occupancy, via_occupancy, layer, start, end, net_code)
        point = route[-1]
        add_via(board, point, net_code)
        via_points.append(point)
        reserve_via(route_occupancy, via_occupancy, point, net_code)
        added += 1
        print(
            f"attached {net_name} cluster at {reference}.{pad.GetNumber()} "
            f"{layer} {endpoint} through {point}"
            f"{' (filled/capped via-in-pad)' if via_in_pad else ''}",
            flush=True,
        )
    return added, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--drc-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-ground-islands", action="store_true")
    parser.add_argument("--cleanup-only", action="store_true")
    parser.add_argument("--grid-mm", type=float, default=0.10)
    args = parser.parse_args()
    if args.grid_mm <= 0:
        parser.error("--grid-mm must be positive")
    residual_router.GRID_MM = args.grid_mm

    board = pcbnew.LoadBoard(str(args.input))
    drc = json.loads(args.drc_json.read_text(encoding="utf-8"))
    removed_edges, removed_vias = remove_rejected_copper(board, drc)
    route_occupancy, via_occupancy = build_occupancy(board)
    pad_boxes = pad_keepouts(board)
    via_points = existing_vias(board)
    if args.skip_ground_islands or args.cleanup_only:
        ground_count, ground_failures = 0, []
    else:
        ground_count, ground_failures = stitch_ground_islands(
            board,
            route_occupancy,
            via_occupancy,
            pad_boxes,
            via_points,
        )
    if args.cleanup_only:
        ground_attachment_count, ground_attachment_failures = 0, []
        protected_count, protected_failures = 0, []
    else:
        ground_attachment_count, ground_attachment_failures = attach_disconnected_pad_clusters(
            board,
            route_occupancy,
            via_occupancy,
            GND_NET,
            pad_boxes,
            via_points,
        )
        protected_count, protected_failures = attach_disconnected_pad_clusters(
            board,
            route_occupancy,
            via_occupancy,
            PROTECTED_NET,
            pad_boxes,
            via_points,
        )
    pcbnew.SaveBoard(str(args.output), board)
    print(f"removed rejected copper items: {removed_edges}")
    print(f"removed dangling vias: {removed_vias}")
    print(f"added GND stitching vias: {ground_count}")
    print(f"added GND local attachments: {ground_attachment_count}")
    print(f"added {PROTECTED_NET} attachments: {protected_count}")
    for failure in (
        *ground_failures,
        *ground_attachment_failures,
        *protected_failures,
    ):
        print(f"unstitched: {failure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
