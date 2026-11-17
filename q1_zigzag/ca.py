"""מנוע האוטומט. קורא רק את טבלת הכללים, בלי ציור."""

from __future__ import annotations

from constants import (
    BRICK,
    EMPTY,
    MAX_GENERATIONS,
    MOORE_OFFSETS,
    NEIGHBOR_KEYS,
    ORIGIN_COL,
    ORIGIN_ROW,
    STATE_TAG,
    STUCK_WINDOW,
    TREADS_TO_VERIFY,
)
from rule_table import matching_rules, next_state
from target import on_staircase, staircase_cells

Grid = dict[tuple[int, int], int]


def initial_line(length: int) -> Grid:
    if length < 2:
        raise ValueError("length must be at least 2")
    return {(ORIGIN_ROW, ORIGIN_COL + offset): BRICK for offset in range(length)}


def neighborhood(grid: Grid, row: int, col: int) -> dict[str, int]:
    values = {}
    for key in NEIGHBOR_KEYS:
        dr, dc = MOORE_OFFSETS[key]
        values[key] = grid.get((row + dr, col + dc), EMPTY)
    return values


def step(grid: Grid) -> Grid:
    halo: set[tuple[int, int]] = set()
    for row, col in grid:
        for dr, dc in MOORE_OFFSETS.values():
            halo.add((row + dr, col + dc))
    nxt: Grid = {}
    for row, col in halo:
        state = next_state(neighborhood(grid, row, col))
        if state != EMPTY:
            nxt[(row, col)] = state
    return nxt


def run(grid: Grid, generations: int) -> list[Grid]:
    history = [grid]
    current = grid
    for _generation in range(generations):
        current = step(current)
        history.append(current)
    return history


def occupied(grid: Grid) -> set[tuple[int, int]]:
    return set(grid)


def render(grid: Grid) -> str:
    if not grid:
        return "(empty)"
    rows = [row for row, _col in grid]
    cols = [col for _row, col in grid]
    lines = []
    for row in range(max(rows), min(rows) - 1, -1):
        chars = []
        for col in range(min(cols), max(cols) + 1):
            chars.append(STATE_TAG[grid.get((row, col), EMPTY)])
        lines.append(f"{row:3d} " + "".join(chars))
    return "\n".join(lines)


def conflicts_in(grid: Grid) -> list[tuple[tuple[int, int], int]]:
    found = []
    halo: set[tuple[int, int]] = set()
    for row, col in grid:
        for dr, dc in MOORE_OFFSETS.values():
            halo.add((row + dr, col + dc))
    for row, col in halo:
        matched = matching_rules(neighborhood(grid, row, col))
        if len(matched) > 1:
            found.append(((row, col), len(matched)))
    return found


def _completed(grid: Grid, length: int, tread_count: int) -> bool:
    target = staircase_cells(length, tread_count)
    cells = occupied(grid)
    return target <= cells and all(on_staircase(length, row, col) for row, col in cells)


def evolve_until(length: int, tread_count: int = TREADS_TO_VERIFY, limit: int = MAX_GENERATIONS) -> list[Grid]:
    """היסטוריה מדור 0 ועד הדור שבו tread_count השלבים הראשונים שלמים."""
    grid = initial_line(length)
    history = [grid]
    stagnant = 0
    previous_count = len(grid)
    for generation in range(limit):
        if _completed(grid, length, tread_count):
            return history
        grid = step(grid)
        history.append(grid)
        count = len(grid)
        if count == previous_count:
            stagnant += 1
            if stagnant >= STUCK_WINDOW and generation > STUCK_WINDOW:
                break
        else:
            stagnant = 0
            previous_count = count
    raise RuntimeError(
        f"L={length} did not complete {tread_count} treads\n{render(grid)}"
    )


def first_complete_generation(length: int, tread_count: int = TREADS_TO_VERIFY, limit: int = MAX_GENERATIONS) -> tuple[int, Grid]:
    """הדור הראשון שבו tread_count השלבים מלאים ואין תא מחוץ לזיגזג."""
    history = evolve_until(length, tread_count, limit)
    return len(history) - 1, history[-1]
