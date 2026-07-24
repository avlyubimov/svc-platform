#!/usr/bin/env python3
"""Route residual PB-100 signal islands without disturbing accepted copper.

This is an engineering closeout helper, not a replacement for KiCad DRC.  It
uses a conservative 0.10 mm occupancy grid on the signal-capable layers, adds
only conventional F.Cu-to-B.Cu through vias, and leaves the In2 GND and In5
VBAT_PROT planes untouched.  The resulting board must still pass a full
refilled KiCad DRC before any routing is promoted to the generated manifest.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import pcbnew


GRID_MM = 0.10
TRACK_WIDTH_MM = 0.20
VIA_SIZE_MM = 0.60
VIA_DRILL_MM = 0.30
CLEARANCE_MARGIN_MM = 0.00
MAX_EXPANDED_STATES = 300_000
BOARD_X_MIN = 0.50
BOARD_X_MAX = 149.50
BOARD_Y_MIN = 0.50
BOARD_Y_MAX = 89.50
POWER_NETS = {
    "AGND",
    "BUCK_SW",
    "GND",
    "INPUT_COMMON_SOURCE",
    "LB_3V3_IO",
    "LM74930_VS",
    "PB_5V_OUT",
    "SW_12V_FUSED",
    "VBAT_PROT",
    "VBAT_RAW",
    "VBAT_REV_PROT",
    "VBAT_PROT_PRELINK",
}
INNER_SIGNAL_LAYERS = ("In1.Cu", "In3.Cu", "In4.Cu", "In6.Cu")
ROUTING_LAYERS = ("F.Cu", *INNER_SIGNAL_LAYERS, "B.Cu")
LAYER_RE = re.compile(r"\b(?:на|on) ([A-Za-z0-9.]+\.Cu)\b")
NET_RE = re.compile(r"\[([^\]]+)\]")


Cell = tuple[int, int]
Point = tuple[float, float]
Occupancy = dict[str, dict[Cell, set[int]]]


def grid_cell(point: Point) -> Cell:
    return (
        round((point[0] - BOARD_X_MIN) / GRID_MM),
        round((point[1] - BOARD_Y_MIN) / GRID_MM),
    )


def cell_point(cell: Cell) -> Point:
    return (
        BOARD_X_MIN + cell[0] * GRID_MM,
        BOARD_Y_MIN + cell[1] * GRID_MM,
    )


def in_bounds(cell: Cell) -> bool:
    point = cell_point(cell)
    return (
        BOARD_X_MIN <= point[0] <= BOARD_X_MAX
        and BOARD_Y_MIN <= point[1] <= BOARD_Y_MAX
    )


def mark_disc(
    layer_cells: dict[Cell, set[int]],
    centre: Point,
    radius_mm: float,
    net_code: int,
) -> None:
    centre_cell = grid_cell(centre)
    radius_cells = math.ceil(radius_mm / GRID_MM)
    for dx in range(-radius_cells, radius_cells + 1):
        for dy in range(-radius_cells, radius_cells + 1):
            cell = (centre_cell[0] + dx, centre_cell[1] + dy)
            if not in_bounds(cell):
                continue
            point = cell_point(cell)
            if math.hypot(point[0] - centre[0], point[1] - centre[1]) <= radius_mm:
                layer_cells[cell].add(net_code)


def mark_segment(
    layer_cells: dict[Cell, set[int]],
    start: Point,
    end: Point,
    radius_mm: float,
    net_code: int,
) -> None:
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    steps = max(1, math.ceil(length / (GRID_MM / 2)))
    for step in range(steps + 1):
        ratio = step / steps
        mark_disc(
            layer_cells,
            (
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
            ),
            radius_mm,
            net_code,
        )


def mark_box(
    layer_cells: dict[Cell, set[int]],
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    expansion_mm: float,
    net_code: int,
) -> None:
    cell1 = grid_cell((x1 - expansion_mm, y1 - expansion_mm))
    cell2 = grid_cell((x2 + expansion_mm, y2 + expansion_mm))
    for x_index in range(max(0, cell1[0]), cell2[0] + 1):
        for y_index in range(max(0, cell1[1]), cell2[1] + 1):
            cell = (x_index, y_index)
            if in_bounds(cell):
                layer_cells[cell].add(net_code)


def mm_point(vector: pcbnew.VECTOR2I) -> Point:
    point = pcbnew.ToMM(vector)
    return float(point[0]), float(point[1])


def copper_layers(board: pcbnew.BOARD) -> list[str]:
    return [
        name
        for name in (
            "F.Cu",
            "In1.Cu",
            "In2.Cu",
            "In3.Cu",
            "In4.Cu",
            "In5.Cu",
            "In6.Cu",
            "B.Cu",
        )
        if board.GetLayerID(name) >= 0
    ]


def build_occupancy(board: pcbnew.BOARD) -> tuple[Occupancy, Occupancy]:
    route: Occupancy = {
        layer: defaultdict(set)
        for layer in copper_layers(board)
    }
    via: Occupancy = {
        layer: defaultdict(set)
        for layer in copper_layers(board)
    }

    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            net_code = pad.GetNetCode()
            box = pad.GetBoundingBox()
            x1, y1 = mm_point(box.GetOrigin())
            size_x, size_y = pcbnew.ToMM(box.GetSize())
            x2 = x1 + float(size_x)
            y2 = y1 + float(size_y)
            for layer in route:
                if pad.IsOnLayer(board.GetLayerID(layer)):
                    mark_box(
                        route[layer],
                        x1,
                        y1,
                        x2,
                        y2,
                        0.30 + CLEARANCE_MARGIN_MM,
                        net_code,
                    )
                    mark_box(
                        via[layer],
                        x1,
                        y1,
                        x2,
                        y2,
                        0.50 + CLEARANCE_MARGIN_MM,
                        net_code,
                    )

    all_layers = list(route)
    for item in board.GetTracks():
        net_code = item.GetNetCode()
        if isinstance(item, pcbnew.PCB_VIA):
            centre = mm_point(item.GetPosition())
            # PCB_VIA::GetWidth requires the layer whose annulus is queried.
            # PB-100 uses conventional through vias, so the F.Cu diameter is
            # representative for the conservative all-layer keep-clear model.
            item_radius = float(
                pcbnew.ToMM(item.GetWidth(board.GetLayerID("F.Cu")))
            ) / 2
            for layer in all_layers:
                mark_disc(
                    route[layer],
                    centre,
                    item_radius + 0.30 + CLEARANCE_MARGIN_MM,
                    net_code,
                )
                mark_disc(
                    via[layer],
                    centre,
                    item_radius + 0.50 + CLEARANCE_MARGIN_MM,
                    net_code,
                )
            continue
        layer = board.GetLayerName(item.GetLayer())
        if layer not in route:
            continue
        start = mm_point(item.GetStart())
        end = mm_point(item.GetEnd())
        item_radius = float(pcbnew.ToMM(item.GetWidth())) / 2
        mark_segment(
            route[layer],
            start,
            end,
            item_radius + 0.30 + CLEARANCE_MARGIN_MM,
            net_code,
        )
        mark_segment(
            via[layer],
            start,
            end,
            item_radius + 0.50 + CLEARANCE_MARGIN_MM,
            net_code,
        )
    return route, via


def blocked(layer_cells: dict[Cell, set[int]], cell: Cell, net_code: int) -> bool:
    # Net code 0 is not empty space: it is also used by NPTH mounting lands,
    # intentionally unconnected package pads and other physical obstacles.
    return any(code != net_code for code in layer_cells.get(cell, ()))


def free_via_site(
    via_occupancy: Occupancy,
    cell: Cell,
    net_code: int,
) -> bool:
    return all(
        not blocked(layer_cells, cell, net_code)
        for layer_cells in via_occupancy.values()
    )


def line_is_free(
    layer_cells: dict[Cell, set[int]],
    start: Point,
    end: Point,
    net_code: int,
) -> bool:
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    steps = max(1, math.ceil(length / (GRID_MM / 2)))
    for step in range(steps + 1):
        ratio = step / steps
        cell = grid_cell(
            (
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
            )
        )
        if blocked(layer_cells, cell, net_code):
            return False
    return True


def candidate_via_sites(
    endpoint: Point,
    source_layer: str,
    route_occupancy: Occupancy,
    via_occupancy: Occupancy,
    net_code: int,
) -> list[Cell]:
    centre = grid_cell(endpoint)
    candidates: list[tuple[float, Cell]] = []
    for radius in range(0, 13):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                cell = (centre[0] + dx, centre[1] + dy)
                if not in_bounds(cell) or not free_via_site(via_occupancy, cell, net_code):
                    continue
                point = cell_point(cell)
                if source_layer not in route_occupancy:
                    continue
                if not line_is_free(
                    route_occupancy[source_layer],
                    endpoint,
                    point,
                    net_code,
                ):
                    continue
                candidates.append((math.hypot(dx, dy), cell))
        if len(candidates) >= 8:
            break
    return [cell for _, cell in sorted(candidates)[:8]]


def a_star_between(
    layer_cells: dict[Cell, set[int]],
    starts: list[Cell],
    goals: list[Cell],
    net_code: int,
) -> list[Cell] | None:
    if not starts or not goals:
        return None
    neighbours = (
        (-1, 0, 1.0),
        (1, 0, 1.0),
        (0, -1, 1.0),
        (0, 1, 1.0),
        (-1, -1, math.sqrt(2)),
        (-1, 1, math.sqrt(2)),
        (1, -1, math.sqrt(2)),
        (1, 1, math.sqrt(2)),
    )

    goal_set = set(goals)

    def heuristic(cell: Cell) -> float:
        distances = []
        for goal in goals:
            dx = abs(cell[0] - goal[0])
            dy = abs(cell[1] - goal[1])
            distances.append(max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy))
        return min(distances)

    queue: list[tuple[float, float, Cell]] = []
    best: dict[Cell, float] = {}
    previous: dict[Cell, Cell] = {}
    for start in starts:
        best[start] = 0.0
        heapq.heappush(queue, (heuristic(start), 0.0, start))
    final_cell: Cell | None = None

    while queue:
        _, cost, cell = heapq.heappop(queue)
        if cost != best.get(cell):
            continue
        if cell in goal_set:
            final_cell = cell
            break
        for dx, dy, move_cost in neighbours:
            next_cell = (cell[0] + dx, cell[1] + dy)
            if not in_bounds(next_cell):
                continue
            if (
                next_cell not in goal_set
                and next_cell not in starts
                and blocked(layer_cells, next_cell, net_code)
            ):
                continue
            # Do not squeeze a diagonal segment between two occupied cells.
            if dx and dy:
                side_a = (cell[0] + dx, cell[1])
                side_b = (cell[0], cell[1] + dy)
                if blocked(layer_cells, side_a, net_code) or blocked(
                    layer_cells, side_b, net_code
                ):
                    continue
            next_cost = cost + move_cost
            if next_cost >= best.get(next_cell, math.inf):
                continue
            best[next_cell] = next_cost
            previous[next_cell] = cell
            heapq.heappush(
                queue,
                (next_cost + heuristic(next_cell), next_cost, next_cell),
            )

    if final_cell is None:
        return None
    path = []
    cell = final_cell
    while True:
        path.append(cell)
        if cell not in previous:
            break
        cell = previous[cell]
    path.reverse()
    return path


LayerCell = tuple[str, Cell]


def multi_layer_a_star(
    route_occupancy: Occupancy,
    via_occupancy: Occupancy,
    start_layer: str,
    start: Cell,
    goal_layer: str,
    goal: Cell,
    net_code: int,
) -> list[LayerCell] | None:
    """Find one ordinary-through-via route over F/In1/In3/B.

    A layer change represents one conventional F.Cu-to-B.Cu via; In2 and In5
    remain reserved for the continuous GND and VBAT_PROT planes.
    """

    if start_layer not in ROUTING_LAYERS or goal_layer not in ROUTING_LAYERS:
        return None
    neighbours = (
        (-1, 0, 1.0),
        (1, 0, 1.0),
        (0, -1, 1.0),
        (0, 1, 1.0),
        (-1, -1, math.sqrt(2)),
        (-1, 1, math.sqrt(2)),
        (1, -1, math.sqrt(2)),
        (1, 1, math.sqrt(2)),
    )
    start_state = (start_layer, start)
    goal_state = (goal_layer, goal)

    def heuristic(state: LayerCell) -> float:
        layer, cell = state
        dx = abs(cell[0] - goal[0])
        dy = abs(cell[1] - goal[1])
        distance = max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        return distance + (8.0 if layer != goal_layer else 0.0)

    queue: list[tuple[float, float, LayerCell]] = [
        (heuristic(start_state), 0.0, start_state)
    ]
    best: dict[LayerCell, float] = {start_state: 0.0}
    previous: dict[LayerCell, LayerCell] = {}
    expanded = 0

    while queue:
        _, cost, state = heapq.heappop(queue)
        if cost != best.get(state):
            continue
        expanded += 1
        if expanded > MAX_EXPANDED_STATES:
            return None
        if state == goal_state:
            path = [state]
            while path[-1] in previous:
                path.append(previous[path[-1]])
            path.reverse()
            return path

        layer, cell = state
        layer_cells = route_occupancy[layer]
        for dx, dy, move_cost in neighbours:
            next_cell = (cell[0] + dx, cell[1] + dy)
            if not in_bounds(next_cell):
                continue
            next_state = (layer, next_cell)
            if next_state != goal_state and blocked(layer_cells, next_cell, net_code):
                continue
            if dx and dy:
                side_a = (cell[0] + dx, cell[1])
                side_b = (cell[0], cell[1] + dy)
                if blocked(layer_cells, side_a, net_code) or blocked(
                    layer_cells, side_b, net_code
                ):
                    continue
            # Prefer the two inner signal layers while still allowing short
            # surface fan-outs around dense pads.
            layer_factor = 1.0 if layer in INNER_SIGNAL_LAYERS else 1.25
            next_cost = cost + move_cost * layer_factor
            if next_cost >= best.get(next_state, math.inf):
                continue
            best[next_state] = next_cost
            previous[next_state] = state
            heapq.heappush(
                queue,
                (next_cost + heuristic(next_state), next_cost, next_state),
            )

        if free_via_site(via_occupancy, cell, net_code):
            for next_layer in ROUTING_LAYERS:
                if next_layer == layer:
                    continue
                next_state = (next_layer, cell)
                next_cost = cost + 8.0
                if next_cost >= best.get(next_state, math.inf):
                    continue
                best[next_state] = next_cost
                previous[next_state] = state
                heapq.heappush(
                    queue,
                    (next_cost + heuristic(next_state), next_cost, next_state),
                )
    return None


def compress_path(path: list[Cell]) -> list[Cell]:
    if len(path) <= 2:
        return path
    result = [path[0]]
    last_direction = (
        path[1][0] - path[0][0],
        path[1][1] - path[0][1],
    )
    for index in range(1, len(path) - 1):
        direction = (
            path[index + 1][0] - path[index][0],
            path[index + 1][1] - path[index][1],
        )
        if direction != last_direction:
            result.append(path[index])
            last_direction = direction
    result.append(path[-1])
    return result


def vector(point: Point) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(point[0]), pcbnew.FromMM(point[1]))


def add_track(
    board: pcbnew.BOARD,
    start: Point,
    end: Point,
    layer_name: str,
    net_code: int,
) -> None:
    if start == end:
        return
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(vector(start))
    track.SetEnd(vector(end))
    track.SetWidth(pcbnew.FromMM(TRACK_WIDTH_MM))
    track.SetLayer(board.GetLayerID(layer_name))
    track.SetNetCode(net_code)
    board.Add(track)


def add_via(board: pcbnew.BOARD, point: Point, net_code: int) -> None:
    position = vector(point)
    for item in board.GetTracks():
        if not isinstance(item, pcbnew.PCB_VIA) or item.GetPosition() != position:
            continue
        if item.GetNetCode() != net_code:
            raise RuntimeError(
                f"attempted to reuse occupied via site {point} for net {net_code}"
            )
        # A conventional F.Cu-to-B.Cu via already joins every copper layer.
        # Reuse it when another branch of the same net reaches the same grid
        # point instead of creating co-located drilled holes.
        return
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(position)
    via.SetWidth(pcbnew.FromMM(VIA_SIZE_MM))
    via.SetDrill(pcbnew.FromMM(VIA_DRILL_MM))
    via.SetLayerPair(board.GetLayerID("F.Cu"), board.GetLayerID("B.Cu"))
    via.SetNetCode(net_code)
    board.Add(via)


def mark_new_route(
    route_occupancy: Occupancy,
    via_occupancy: Occupancy,
    fanouts: list[tuple[str, Point, Point]],
    inner_layer: str,
    path_points: list[Point],
    via_points: list[Point],
    net_code: int,
) -> None:
    for layer, start, end in fanouts:
        mark_segment(
            route_occupancy[layer],
            start,
            end,
            0.40 + CLEARANCE_MARGIN_MM,
            net_code,
        )
        mark_segment(
            via_occupancy[layer],
            start,
            end,
            0.60 + CLEARANCE_MARGIN_MM,
            net_code,
        )
    for start, end in zip(path_points, path_points[1:]):
        mark_segment(
            route_occupancy[inner_layer],
            start,
            end,
            0.40 + CLEARANCE_MARGIN_MM,
            net_code,
        )
        mark_segment(
            via_occupancy[inner_layer],
            start,
            end,
            0.60 + CLEARANCE_MARGIN_MM,
            net_code,
        )
    for point in via_points:
        for layer in route_occupancy:
            mark_disc(
                route_occupancy[layer],
                point,
                0.60 + CLEARANCE_MARGIN_MM,
                net_code,
            )
            mark_disc(
                via_occupancy[layer],
                point,
                0.80 + CLEARANCE_MARGIN_MM,
                net_code,
            )


def add_multi_layer_route(
    board: pcbnew.BOARD,
    path: list[LayerCell],
    first: Point,
    second: Point,
    net_code: int,
    route_occupancy: Occupancy,
    via_occupancy: Occupancy,
) -> None:
    """Materialize and reserve one multilayer grid path."""

    layer_runs: list[tuple[str, list[Cell]]] = []
    via_points: list[Point] = []
    current_layer = path[0][0]
    current_cells = [path[0][1]]
    for layer, cell in path[1:]:
        if layer == current_layer:
            current_cells.append(cell)
            continue
        layer_runs.append((current_layer, current_cells))
        via_point = cell_point(cell)
        if not via_points or via_points[-1] != via_point:
            add_via(board, via_point, net_code)
            via_points.append(via_point)
        current_layer = layer
        current_cells = [cell]
    layer_runs.append((current_layer, current_cells))

    fanouts: list[tuple[str, Point, Point]] = []
    start_point = cell_point(path[0][1])
    end_point = cell_point(path[-1][1])
    add_track(board, first, start_point, path[0][0], net_code)
    add_track(board, end_point, second, path[-1][0], net_code)
    fanouts.append((path[0][0], first, start_point))
    fanouts.append((path[-1][0], end_point, second))

    for layer, cells in layer_runs:
        points = [cell_point(cell) for cell in compress_path(cells)]
        for start_point, end_point in zip(points, points[1:]):
            add_track(board, start_point, end_point, layer, net_code)
        for start_point, end_point in zip(points, points[1:]):
            mark_segment(
                route_occupancy[layer],
                start_point,
                end_point,
                0.40 + CLEARANCE_MARGIN_MM,
                net_code,
            )
            mark_segment(
                via_occupancy[layer],
                start_point,
                end_point,
                0.60 + CLEARANCE_MARGIN_MM,
                net_code,
            )

    for layer, start_point, end_point in fanouts:
        mark_segment(
            route_occupancy[layer],
            start_point,
            end_point,
            0.40 + CLEARANCE_MARGIN_MM,
            net_code,
        )
        mark_segment(
            via_occupancy[layer],
            start_point,
            end_point,
            0.60 + CLEARANCE_MARGIN_MM,
            net_code,
        )
    for point in via_points:
        for layer in route_occupancy:
            mark_disc(
                route_occupancy[layer],
                point,
                0.60 + CLEARANCE_MARGIN_MM,
                net_code,
            )
            mark_disc(
                via_occupancy[layer],
                point,
                0.80 + CLEARANCE_MARGIN_MM,
                net_code,
            )


def parse_endpoint(item: dict[str, object]) -> tuple[Point, str]:
    position = item["pos"]
    assert isinstance(position, dict)
    description = str(item.get("description", ""))
    match = LAYER_RE.search(description)
    layer = match.group(1) if match else "F.Cu"
    return (float(position["x"]), float(position["y"])), layer


def excluded_from_signal_autoroute(net_name: str) -> bool:
    """Keep power copper and the CAN bus pair out of generic signal routing."""

    return (
        net_name in POWER_NETS
        or net_name in {"CAN1_HARNESS_H", "CAN1_HARNESS_L"}
        or re.fullmatch(r"OUT\d+_(?:FET_DRAIN|SWITCHED)", net_name) is not None
    )


def route_residual(
    board: pcbnew.BOARD,
    drc: dict[str, object],
    maximum: int | None,
    selected_nets: set[str] | None = None,
) -> tuple[int, list[str]]:
    route_occupancy, via_occupancy = build_occupancy(board)
    routed = 0
    failures: list[str] = []
    seen_pairs: set[tuple[str, Point, Point]] = set()

    findings = []
    for finding in drc.get("unconnected_items", []):
        if not isinstance(finding, dict):
            continue
        items = finding.get("items", [])
        if not isinstance(items, list) or len(items) < 2:
            continue
        if any(
            token in str(item.get("description", ""))
            for item in items
            for token in ("Зона", "Zone")
        ):
            # KiCad reports a representative zone coordinate rather than a
            # routable copper endpoint.  Zone/pad and zone/island attachment
            # is handled by the dedicated plane-stitching workflow.
            continue
        first, _ = parse_endpoint(items[0])
        second, _ = parse_endpoint(items[1])
        findings.append(
            (
                math.hypot(second[0] - first[0], second[1] - first[1]),
                finding,
            )
        )

    # Close short component-local nets before consuming the shared inner-layer
    # corridors with long JPB1 fan-out routes.  This mirrors the accepted
    # LB-100 routing sequence and avoids trapping bootstrap, sense and timing
    # loops behind routes that can use many equivalent paths.
    for _, finding in sorted(findings, key=lambda item: item[0]):
        assert isinstance(finding, dict)
        items = finding.get("items", [])
        if not isinstance(items, list) or len(items) < 2:
            continue
        description = " ".join(str(item.get("description", "")) for item in items)
        net_match = NET_RE.search(description)
        if not net_match:
            continue
        net_name = net_match.group(1)
        if selected_nets is not None and net_name not in selected_nets:
            continue
        if excluded_from_signal_autoroute(net_name) and (
            selected_nets is None
            or net_name in {"CAN1_HARNESS_H", "CAN1_HARNESS_L"}
        ):
            continue
        first, first_layer = parse_endpoint(items[0])
        second, second_layer = parse_endpoint(items[1])
        if first == second:
            continue
        identity = (net_name, first, second)
        reverse_identity = (net_name, second, first)
        if identity in seen_pairs or reverse_identity in seen_pairs:
            continue
        seen_pairs.add(identity)
        net = board.FindNet(net_name)
        if net is None:
            failures.append(f"{net_name}: net not found")
            continue
        net_code = net.GetNetCode()

        path = multi_layer_a_star(
            route_occupancy,
            via_occupancy,
            first_layer,
            grid_cell(first),
            second_layer,
            grid_cell(second),
            net_code,
        )
        if path is None:
            failures.append(f"{net_name}: no grid route from {first} to {second}")
            continue

        add_multi_layer_route(
            board,
            path,
            first,
            second,
            net_code,
            route_occupancy,
            via_occupancy,
        )
        routed += 1
        used_layers = []
        for layer, _ in path:
            if not used_layers or used_layers[-1] != layer:
                used_layers.append(layer)
        print(
            f"routed {net_name}: {first_layer} {first} -> "
            f"{'/'.join(used_layers)} -> {second_layer} {second}"
        , flush=True)
        if maximum is not None and routed >= maximum:
            break
    return routed, failures


def main() -> int:
    global CLEARANCE_MARGIN_MM, GRID_MM, MAX_EXPANDED_STATES

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--drc-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-routes", type=int)
    parser.add_argument(
        "--net",
        action="append",
        dest="nets",
        help="route only the named net (repeatable)",
    )
    parser.add_argument(
        "--grid-mm",
        type=float,
        default=GRID_MM,
        help="routing occupancy grid in millimetres",
    )
    parser.add_argument(
        "--max-expanded-states",
        type=int,
        default=MAX_EXPANDED_STATES,
        help="maximum A* states expanded per residual connection",
    )
    parser.add_argument(
        "--clearance-margin-mm",
        type=float,
        default=CLEARANCE_MARGIN_MM,
        help=(
            "additional occupancy margin; a small negative value may offset "
            "grid quantization, but KiCad DRC remains authoritative"
        ),
    )
    args = parser.parse_args()
    if args.grid_mm <= 0:
        parser.error("--grid-mm must be positive")
    if args.max_expanded_states <= 0:
        parser.error("--max-expanded-states must be positive")
    GRID_MM = args.grid_mm
    MAX_EXPANDED_STATES = args.max_expanded_states
    CLEARANCE_MARGIN_MM = args.clearance_margin_mm
    board = pcbnew.LoadBoard(str(args.input))
    drc = json.loads(args.drc_json.read_text(encoding="utf-8"))
    routed, failures = route_residual(
        board,
        drc,
        args.max_routes,
        set(args.nets) if args.nets else None,
    )
    pcbnew.SaveBoard(str(args.output), board)
    print(f"routed residual items: {routed}")
    for failure in failures:
        print(f"unrouted residual: {failure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
