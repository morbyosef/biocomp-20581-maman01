"""בדיקות: לכל אורך מ־2 עד 10 הזיגזג תואם את היעד, ואין תאים מיותרים."""

from __future__ import annotations

import unittest

from ca import conflicts_in, first_complete_generation, initial_line, occupied, step
from constants import (
    BRICK,
    DONE,
    EMPTY,
    NEIGHBOR_KEYS,
    TEST_MAX_LENGTH,
    TEST_MIN_LENGTH,
    TREADS_TO_VERIFY,
)
from rule_table import next_state, rules
from target import on_staircase, staircase_cells


def _assignment_L3() -> set[tuple[int, int]]:
    spans = (
        (0, range(0, 3)),
        (1, (2,)),
        (2, range(2, 5)),
        (3, (4,)),
        (4, range(4, 7)),
        (5, (6,)),
        (6, range(6, 9)),
        (7, (8,)),
        (8, range(8, 11)),
    )
    cells = set()
    for row, cols in spans:
        for col in cols:
            cells.add((row, col))
    return cells


class ZigzagTests(unittest.TestCase):
    def test_rule_table_is_nonempty(self) -> None:
        self.assertGreater(len(rules()), 0)
        for rule in rules():
            self.assertIsInstance(rule.result, int)

    def test_quiescent_empty_stays_empty(self) -> None:
        neighborhood = {key: EMPTY for key in NEIGHBOR_KEYS}
        self.assertEqual(next_state(neighborhood), EMPTY)
        self.assertEqual(step({}), {})

    def test_isolated_done_is_stable(self) -> None:
        neighborhood = {key: EMPTY for key in NEIGHBOR_KEYS}
        neighborhood["c"] = DONE
        self.assertEqual(next_state(neighborhood), DONE)

    def test_single_brick_is_not_a_required_case_and_stays(self) -> None:
        grid = {(0, 0): BRICK}
        self.assertEqual(step(grid), grid)

    def test_L3_matches_the_assignment_figure(self) -> None:
        self.assertEqual(staircase_cells(3, TREADS_TO_VERIFY), _assignment_L3())

    def test_every_length_builds_the_staircase(self) -> None:
        for length in range(TEST_MIN_LENGTH, TEST_MAX_LENGTH + 1):
            with self.subTest(length=length):
                generation, grid = first_complete_generation(length, TREADS_TO_VERIFY)
                target = staircase_cells(length, TREADS_TO_VERIFY)
                cells = occupied(grid)
                self.assertTrue(target <= cells)
                for row, col in cells:
                    self.assertTrue(on_staircase(length, row, col))
                self.assertGreater(generation, 0)

    def test_reachable_neighborhoods_match_one_rule(self) -> None:
        for length in (2, 3, 4):
            grid = initial_line(length)
            _generation, final = first_complete_generation(length, TREADS_TO_VERIFY)
            seen = initial_line(length)
            while seen != final:
                overlap = conflicts_in(seen)
                self.assertEqual(overlap, [], f"L={length}")
                seen = step(seen)
            self.assertEqual(conflicts_in(final), [])


if __name__ == "__main__":
    unittest.main()
