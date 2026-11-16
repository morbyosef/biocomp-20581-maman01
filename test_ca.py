"""בדיקות לכלל המעבר ולמוניטור. אין כאן גרפיקה."""

from __future__ import annotations

import unittest

import numpy as np

from ca_rules import Grid, choose_direction, transition
from constants import (
    BID_CLOCK,
    CYCLE_LENGTH,
    DIRECTION_COUNT,
    EAST,
    EMPTY,
    ENTITY_COUNT,
    GUEST_A,
    GUEST_B,
    GUEST_E,
    MAX_DIST,
    MAX_GAIN,
    NEIGHBORHOOD_RADIUS,
    NORTH,
    NORTHEAST,
    NUM_GUESTS,
    SOUTHEAST,
    STAY,
    TABLE,
    TABLE_COL,
    TABLE_ENTITY,
    TABLE_ROW,
    WEST,
)
from matrices import EXAMPLE_MATRIX, validate_matrix
from simulation import (
    create_initial_grid,
    exact_distance_fields,
    measure_stress,
    run_simulation,
)


def _easy_matrix() -> np.ndarray:
    """כולם רוצים את השולחן במרחק 1 וזה את זה במרחק 3. נוח לבדיקת ירידה."""
    matrix = np.zeros((NUM_GUESTS, ENTITY_COUNT), dtype=np.int16)
    for guest in range(NUM_GUESTS):
        for entity in range(ENTITY_COUNT):
            if guest == entity:
                matrix[guest, entity] = 0
            elif entity == TABLE_ENTITY:
                matrix[guest, entity] = 1
            else:
                matrix[guest, entity] = 3
    return matrix


def _cell_state(grid: Grid, row: int, col: int):
    return (
        int(grid.occupant[row, col]),
        tuple(int(value) for value in grid.dist[:, row, col]),
        int(grid.clock[row, col]),
        int(grid.proposal[row, col]),
        int(grid.gain[row, col]),
        int(grid.bid[row, col]),
    )


def _random_grid(rng: np.random.Generator) -> Grid:
    grid = Grid()
    grid.occupant = rng.integers(EMPTY, TABLE + 1, size=grid.occupant.shape, dtype=np.int16)
    grid.dist = rng.integers(0, MAX_DIST + 1, size=grid.dist.shape, dtype=np.int16)
    grid.clock = rng.integers(0, CYCLE_LENGTH, size=grid.clock.shape, dtype=np.int16)
    grid.proposal = rng.integers(STAY, DIRECTION_COUNT, size=grid.proposal.shape, dtype=np.int16)
    grid.gain = rng.integers(0, MAX_GAIN + 1, size=grid.gain.shape, dtype=np.int16)
    grid.bid = rng.integers(0, GUEST_E + 1, size=grid.bid.shape, dtype=np.int16)
    return grid


class AutomatonTests(unittest.TestCase):
    def test_example_matrix_matches_the_assignment(self) -> None:
        expected = [
            [0, 5, 8, 7, 7, 0],
            [0, 0, 1, 0, 3, 8],
            [6, 1, 0, 1, 0, 6],
            [5, 7, 0, 0, 4, 5],
            [4, 4, 0, 2, 0, 6],
        ]
        self.assertTrue(np.array_equal(EXAMPLE_MATRIX, np.array(expected, dtype=np.int16)))
        validate_matrix(EXAMPLE_MATRIX)

    def test_rules_source_has_no_graphics_or_quality_monitor(self) -> None:
        text = __import__("pathlib").Path("ca_rules.py").read_text(encoding="utf-8")
        self.assertNotIn("matplotlib", text)
        self.assertNotIn("pyplot", text)
        self.assertNotIn("measure_stress", text)

    def test_wave_advances_one_cell_and_sources_emit_zero(self) -> None:
        grid = Grid()
        grid.dist[:, :, :] = MAX_DIST
        grid.dist[0, 9, 10] = 0
        nxt = transition(grid, EXAMPLE_MATRIX)
        self.assertEqual(int(nxt.dist[0, 10, 10]), 1)
        self.assertEqual(int(nxt.dist[0, 8, 10]), 1)
        self.assertEqual(int(nxt.dist[0, 10, 12]), MAX_DIST)
        grid.occupant[4, 4] = GUEST_A
        grid.dist[0, 4, 4] = MAX_DIST
        nxt = transition(grid, EXAMPLE_MATRIX)
        self.assertEqual(int(nxt.dist[0, 4, 4]), 0)

    def test_field_matches_chebyshev_before_the_first_move_and_after(self) -> None:
        # verify_field זורק אם השדה לא מדויק ברגע ההצעה, גם אחרי תזוזות.
        result = run_simulation(EXAMPLE_MATRIX, seed=0, generations=CYCLE_LENGTH * 4, verify_field=True)
        self.assertTrue(np.array_equal(result.positions[0], result.positions[CYCLE_LENGTH - 1]))
        self.assertFalse(np.array_equal(result.positions[0], result.positions[CYCLE_LENGTH]))
        settled = create_initial_grid(0)
        for _ in range(MAX_DIST):
            settled = transition(settled, EXAMPLE_MATRIX)
        self.assertTrue(np.array_equal(settled.dist, exact_distance_fields(settled.occupant)))

    def test_positions_constant_between_moves(self) -> None:
        result = run_simulation(_easy_matrix(), seed=2, generations=CYCLE_LENGTH * 3, verify_field=True)
        for generation in range(1, len(result.stress)):
            if generation % CYCLE_LENGTH != 0:
                self.assertTrue(np.array_equal(result.positions[generation], result.positions[generation - 1]))

    def test_locality_center_ignores_cells_outside_the_neighborhood(self) -> None:
        rng = np.random.default_rng(7)
        center_row, center_col = 12, 17
        for _trial in range(24):
            original = _random_grid(rng)
            mutated = original.copy()
            for row in range(original.occupant.shape[0]):
                for col in range(original.occupant.shape[1]):
                    if max(abs(row - center_row), abs(col - center_col)) <= NEIGHBORHOOD_RADIUS:
                        continue
                    mutated.occupant[row, col] = int(rng.integers(EMPTY, TABLE + 1))
                    mutated.dist[:, row, col] = rng.integers(0, MAX_DIST + 1, size=ENTITY_COUNT)
                    mutated.clock[row, col] = int(rng.integers(0, CYCLE_LENGTH))
                    mutated.proposal[row, col] = int(rng.integers(STAY, DIRECTION_COUNT))
                    mutated.gain[row, col] = int(rng.integers(0, MAX_GAIN + 1))
                    mutated.bid[row, col] = int(rng.integers(0, GUEST_E + 1))
            left = transition(original, EXAMPLE_MATRIX)
            right = transition(mutated, EXAMPLE_MATRIX)
            self.assertEqual(_cell_state(left, center_row, center_col), _cell_state(right, center_row, center_col))

    def test_tie_break_prefers_a_straight_step_over_a_diagonal(self) -> None:
        preferences = np.zeros((NUM_GUESTS, ENTITY_COUNT), dtype=np.int16)

        def vector(table_distance: int) -> np.ndarray:
            values = np.zeros(ENTITY_COUNT, dtype=np.int16)
            values[TABLE_ENTITY] = table_distance
            return values

        tied = {STAY: vector(5), EAST: vector(4), NORTHEAST: vector(4), SOUTHEAST: vector(4)}
        direction, gain = choose_direction(tied, guest_index=0, preferences=preferences)
        self.assertEqual(direction, EAST)
        self.assertEqual(gain, 1)

        diagonal = {STAY: vector(5), EAST: vector(5), SOUTHEAST: vector(4)}
        direction, gain = choose_direction(diagonal, guest_index=0, preferences=preferences)
        self.assertEqual(direction, SOUTHEAST)
        self.assertEqual(gain, 1)

        no_improvement = {STAY: vector(5), NORTH: vector(6), EAST: vector(6)}
        direction, gain = choose_direction(no_improvement, guest_index=0, preferences=preferences)
        self.assertEqual(direction, STAY)
        self.assertEqual(gain, 0)

    def test_higher_gain_wins_the_cell_and_the_loser_stays(self) -> None:
        grid = Grid()
        grid.clock.fill(BID_CLOCK)
        grid.occupant[TABLE_ROW, TABLE_COL] = TABLE
        grid.occupant[10, 10] = GUEST_A
        grid.occupant[10, 12] = GUEST_B
        grid.proposal[10, 10] = EAST
        grid.proposal[10, 12] = WEST
        grid.gain[10, 10] = 3
        grid.gain[10, 12] = 5
        offered = transition(grid, EXAMPLE_MATRIX)
        self.assertEqual(int(offered.bid[10, 11]), GUEST_B)
        self.assertEqual(int(offered.occupant[10, 10]), GUEST_A)
        moved = transition(offered, EXAMPLE_MATRIX)
        self.assertEqual(int(moved.occupant[10, 11]), GUEST_B)
        self.assertEqual(int(moved.occupant[10, 12]), EMPTY)
        self.assertEqual(int(moved.occupant[10, 10]), GUEST_A)
        self.assertEqual(int(moved.occupant[TABLE_ROW, TABLE_COL]), TABLE)

    def test_equal_gain_goes_to_the_smaller_id(self) -> None:
        grid = Grid()
        grid.clock.fill(BID_CLOCK)
        grid.occupant[10, 10] = GUEST_A
        grid.occupant[10, 12] = GUEST_B
        grid.proposal[10, 10] = EAST
        grid.proposal[10, 12] = WEST
        grid.gain[10, 10] = 4
        grid.gain[10, 12] = 4
        offered = transition(grid, EXAMPLE_MATRIX)
        self.assertEqual(int(offered.bid[10, 11]), GUEST_A)

    def test_transition_does_not_mutate_its_input(self) -> None:
        grid = create_initial_grid(3)
        before = grid.copy()
        transition(grid, EXAMPLE_MATRIX)
        self.assertTrue(np.array_equal(grid.occupant, before.occupant))
        self.assertTrue(np.array_equal(grid.dist, before.dist))
        self.assertTrue(np.array_equal(grid.clock, before.clock))

    def test_same_seed_is_reproducible(self) -> None:
        first = run_simulation(EXAMPLE_MATRIX, seed=4, generations=CYCLE_LENGTH * 2, verify_field=True)
        second = run_simulation(EXAMPLE_MATRIX, seed=4, generations=CYCLE_LENGTH * 2, verify_field=True)
        self.assertTrue(np.array_equal(first.stress, second.stress))
        self.assertTrue(np.array_equal(first.positions, second.positions))

    def test_easy_preferences_improve_on_the_global_stress(self) -> None:
        result = run_simulation(_easy_matrix(), seed=1, generations=CYCLE_LENGTH * 18, verify_field=True)
        self.assertLess(int(result.stress[-1]), int(result.stress[0]) * 0.6)
        self.assertGreater(result.move_count, 0)

    def test_quality_uses_true_distance_not_the_field(self) -> None:
        grid = create_initial_grid(0)
        # לפני שהגל מתפשט השדה רווי, אבל המדד משתמש במיקומים.
        stress = measure_stress(grid.occupant, EXAMPLE_MATRIX)
        self.assertGreater(stress, 0)
        positions = exact_distance_fields(grid.occupant)
        self.assertFalse(np.array_equal(positions, grid.dist))


if __name__ == "__main__":
    unittest.main()
