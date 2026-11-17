"""הרצה, אתחול אקראי, ומדידת איכות.

הקובץ הזה הוא המוניטור שמחוץ לאוטומט. הוא מניח אורחים בתאים
אקראיים, מפעיל את כלל המעבר דור אחרי דור, ומחשב את הלחץ הגלובלי
ממיקומים אמיתיים. כלל המעבר לא קורא לפונקציות שבכאן.

הלחץ (מדד האיכות) הוא סכום |מרחק צ'בישב אמיתי − מרחק רצוי|
על כל הזוגות הסדורים (אורח, ישות אחרת), כולל השולחן.
ערך נמוך יותר הוא סידור מוצלח יותר. המדד לא נכנס לכלל המעבר.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ca_rules import Grid, phase_kind, transition
from constants import (
    CELLS_TOUCHED_BY_ONE_MOVE,
    CYCLE_LENGTH,
    DEFAULT_GENERATIONS,
    DEFAULT_SEEDS,
    EMPTY,
    ENTITY_COUNT,
    ENTITY_NAMES,
    ENTITY_OCCUPANTS,
    FIELD_DEMO_GENERATIONS,
    GUEST_NAMES,
    GUEST_OCCUPANTS,
    GRID_SIZE,
    INITIAL_CLOCK,
    MAX_DIST,
    MAX_GAIN,
    NO_BID,
    NUM_GUESTS,
    OUTPUT_DIR,
    PHASE_PROPOSE,
    SNAPSHOT_EVERY,
    SNAPSHOT_SEED,
    STAY,
    TABLE,
    TAIL_CYCLES,
    TABLE_COL,
    TABLE_ENTITY,
    TABLE_ROW,
    VERIFY_FIELD_BEFORE_PROPOSE,
)
from matrices import MATRICES, MATRIX_TITLES, format_matrix, validate_matrix

# שני הסרטונים של הריצה המלאה: מטריצה, זרע, ושם הקובץ.
VIDEO_RUNS = (
    ("example", 3, "party_example.mp4"),
    ("interesting", 0, "party_interesting.mp4"),
)
VIDEO_DIR_NAME = "videos"


class RunResult:
    """תוצאת ריצה אחת: סדרות שהמוניטור שמר, לא מצב פנימי של הכלל."""

    def __init__(
        self,
        seed: int,
        stress: np.ndarray,
        positions: np.ndarray,
        snapshots: dict[int, np.ndarray],
        field_frames: dict[int, np.ndarray],
        move_count: int,
        final_occupant: np.ndarray,
    ) -> None:
        self.seed = seed
        self.stress = stress
        self.positions = positions
        self.snapshots = snapshots
        self.field_frames = field_frames
        self.move_count = move_count
        self.final_occupant = final_occupant


def chebyshev(first, second) -> int:
    """מרחק צ'בישב בין שני תאים. זו המטריקה שהשכנות מור מודדת."""
    return max(abs(int(first[0]) - int(second[0])), abs(int(first[1]) - int(second[1])))


def locate_entities(occupant: np.ndarray) -> np.ndarray:
    """מיקום אמיתי של כל ישות, שורה ועמודה. קורא את כל הלוח — רק למוניטור."""
    positions = np.zeros((ENTITY_COUNT, 2), dtype=np.int16)
    for entity, occupant_id in enumerate(ENTITY_OCCUPANTS):
        found = np.argwhere(occupant == occupant_id)
        if len(found) != 1:
            raise RuntimeError(f"entity {ENTITY_NAMES[entity]} appears {len(found)} times")
        positions[entity] = found[0]
    return positions


def exact_distance_fields(occupant: np.ndarray) -> np.ndarray:
    """שדה המרחקים האמיתי לפי מיקומים. לבדיקה שהגל התייצב, לא לשימוש בכלל."""
    positions = locate_entities(occupant)
    fields = np.empty((ENTITY_COUNT, GRID_SIZE, GRID_SIZE), dtype=np.int16)
    row_index = np.arange(GRID_SIZE)[:, None]
    col_index = np.arange(GRID_SIZE)[None, :]
    for entity in range(ENTITY_COUNT):
        row = int(positions[entity, 0])
        col = int(positions[entity, 1])
        fields[entity] = np.maximum(np.abs(row_index - row), np.abs(col_index - col))
    return fields


def measure_stress(occupant: np.ndarray, preferences: np.ndarray) -> int:
    """לחץ גלובלי. נמוך יותר — קרוב יותר למטריצה. לא נקרא מתוך ca_rules."""
    positions = locate_entities(occupant)
    total = 0
    for guest in range(NUM_GUESTS):
        for entity in range(ENTITY_COUNT):
            if guest == entity:
                continue
            actual = chebyshev(positions[guest], positions[entity])
            total += abs(actual - int(preferences[guest, entity]))
    return total


def actual_distance_matrix(occupant: np.ndarray) -> np.ndarray:
    """המרחקים האמיתיים באותו סידור שורות/עמודות כמו מטריצת ההעדפות."""
    positions = locate_entities(occupant)
    actual = np.zeros((NUM_GUESTS, ENTITY_COUNT), dtype=np.int16)
    for guest in range(NUM_GUESTS):
        for entity in range(ENTITY_COUNT):
            actual[guest, entity] = chebyshev(positions[guest], positions[entity])
    return actual


def create_initial_grid(seed: int) -> Grid:
    """דור 0: השולחן קבוע במרכז, האורחים מפוזרים אקראית בתאים פנויים.

    שדה המרחקים מתחיל ב־0 רק על תא הישות עצמה, ובערך הרווי בכל מקום אחר.
    הגל ממלא אותו בדורות הבאים. אין כאן הגרלה בתוך כלל המעבר.
    """
    rng = np.random.default_rng(seed)
    grid = Grid()
    grid.occupant[TABLE_ROW, TABLE_COL] = TABLE
    grid.dist[TABLE_ENTITY, TABLE_ROW, TABLE_COL] = 0
    free = [
        (row, col)
        for row in range(GRID_SIZE)
        for col in range(GRID_SIZE)
        if not (row == TABLE_ROW and col == TABLE_COL)
    ]
    picks = rng.choice(len(free), size=NUM_GUESTS, replace=False)
    for guest_index, pick in enumerate(picks):
        row, col = free[int(pick)]
        grid.occupant[row, col] = GUEST_OCCUPANTS[guest_index]
        grid.dist[guest_index, row, col] = 0
    grid.clock.fill(INITIAL_CLOCK)
    grid.proposal.fill(STAY)
    grid.gain.fill(0)
    grid.bid.fill(NO_BID)
    return grid


def assert_invariants(grid: Grid, generation: int) -> None:
    """שומר על מה שהכלל חייב לקיים: דייר אחד מכל סוג, שולחן במקומו, שעון אחיד."""
    for occupant_id in ENTITY_OCCUPANTS:
        count = int(np.sum(grid.occupant == occupant_id))
        if count != 1:
            raise AssertionError(f"generation {generation}: occupant {occupant_id} count is {count}")
    if int(grid.occupant[TABLE_ROW, TABLE_COL]) != TABLE:
        raise AssertionError(f"generation {generation}: the table moved")
    empty_or_known = int(np.sum((grid.occupant == EMPTY) | np.isin(grid.occupant, ENTITY_OCCUPANTS)))
    if empty_or_known != GRID_SIZE * GRID_SIZE:
        raise AssertionError(f"generation {generation}: unknown occupant value")
    if not np.all(grid.clock == grid.clock[0, 0]):
        raise AssertionError(f"generation {generation}: clocks are not uniform")
    if int(grid.dist.min()) < 0 or int(grid.dist.max()) > MAX_DIST:
        raise AssertionError(f"generation {generation}: distance field left its range")
    if int(grid.gain.min()) < 0 or int(grid.gain.max()) > MAX_GAIN:
        raise AssertionError(f"generation {generation}: gain left its range")


def _field_error_message(grid: Grid, generation: int) -> str:
    expected = exact_distance_fields(grid.occupant)
    diff = np.abs(grid.dist.astype(np.int32) - expected.astype(np.int32))
    where = np.unravel_index(int(diff.argmax()), diff.shape)
    return (
        f"distance field inexact at generation {generation}, "
        f"max error {int(diff.max())} at index {where}"
    )


def run_simulation(
    preferences: np.ndarray,
    seed: int,
    generations: int = DEFAULT_GENERATIONS,
    verify_field: bool = VERIFY_FIELD_BEFORE_PROPOSE,
) -> RunResult:
    """מריץ את האוטומט `generations` דורות מן הדור ההתחלתי של הזרע הנתון."""
    validate_matrix(preferences)
    if generations < 1:
        raise ValueError("generations must be positive")
    grid = create_initial_grid(seed)
    assert_invariants(grid, 0)
    stress = np.zeros(generations + 1, dtype=np.int32)
    positions = np.zeros((generations + 1, NUM_GUESTS, 2), dtype=np.int16)
    stress[0] = measure_stress(grid.occupant, preferences)
    positions[0] = locate_entities(grid.occupant)[:NUM_GUESTS]
    snapshots: dict[int, np.ndarray] = {0: grid.occupant.copy()}
    field_frames: dict[int, np.ndarray] = {}
    if 0 in FIELD_DEMO_GENERATIONS:
        field_frames[0] = grid.dist[TABLE_ENTITY].copy()
    move_count = 0

    for step in range(generations):
        generation = step
        if verify_field and phase_kind(int(grid.clock[0, 0])) == PHASE_PROPOSE:
            expected = exact_distance_fields(grid.occupant)
            if not np.array_equal(grid.dist, expected):
                raise RuntimeError(_field_error_message(grid, generation))
        previous = grid.occupant
        grid = transition(grid, preferences)
        new_generation = step + 1
        if not np.array_equal(previous, grid.occupant):
            changed = int(np.sum(previous != grid.occupant))
            if changed % CELLS_TOUCHED_BY_ONE_MOVE != 0:
                raise RuntimeError(f"odd number of occupant changes at generation {new_generation}")
            move_count += changed // CELLS_TOUCHED_BY_ONE_MOVE
        assert_invariants(grid, new_generation)
        stress[new_generation] = measure_stress(grid.occupant, preferences)
        positions[new_generation] = locate_entities(grid.occupant)[:NUM_GUESTS]
        if new_generation % SNAPSHOT_EVERY == 0 or new_generation == generations:
            snapshots[new_generation] = grid.occupant.copy()
        if new_generation in FIELD_DEMO_GENERATIONS:
            field_frames[new_generation] = grid.dist[TABLE_ENTITY].copy()

    return RunResult(
        seed=seed,
        stress=stress,
        positions=positions,
        snapshots=snapshots,
        field_frames=field_frames,
        move_count=move_count,
        final_occupant=grid.occupant.copy(),
    )


def movement_report(stress: np.ndarray) -> dict[str, int]:
    """כמה פעמים הלחץ ירד, עלה, או קפא ברגע שבו תנועה נראית על הלוח."""
    downs = 0
    ups = 0
    flats = 0
    previous = 0
    for generation in range(CYCLE_LENGTH, len(stress), CYCLE_LENGTH):
        if stress[generation] < stress[previous]:
            downs += 1
        elif stress[generation] > stress[previous]:
            ups += 1
        else:
            flats += 1
        previous = generation
    tail_start = max(0, len(stress) - TAIL_CYCLES * CYCLE_LENGTH)
    tail = stress[tail_start:]
    return {
        "steps_down": downs,
        "steps_up": ups,
        "steps_flat": flats,
        "tail_min": int(tail.min()),
        "tail_max": int(tail.max()),
        "tail_span": int(tail.max() - tail.min()),
    }


def summarize_run(result: RunResult, preferences: np.ndarray) -> dict:
    initial = int(result.stress[0])
    final = int(result.stress[-1])
    minimum = int(result.stress.min())
    moves = movement_report(result.stress)
    summary = {
        "seed": result.seed,
        "initial_stress": initial,
        "final_stress": final,
        "min_stress": minimum,
        "min_stress_generation": int(result.stress.argmin()),
        "reduction": initial - final,
        "reduction_percent": (100.0 * (initial - final) / initial) if initial else 0.0,
        "move_count": result.move_count,
        **moves,
        "actual_final": actual_distance_matrix(result.final_occupant).astype(int).tolist(),
        "desired": preferences.astype(int).tolist(),
    }
    return summary


def _write_stress_csv(path: Path, stress_by_seed: dict[int, np.ndarray]) -> None:
    seeds = list(stress_by_seed)
    length = len(next(iter(stress_by_seed.values())))
    with path.open("w", encoding="utf-8") as handle:
        handle.write("generation," + ",".join(f"seed_{seed}" for seed in seeds) + "\n")
        for generation in range(length):
            values = ",".join(str(int(stress_by_seed[seed][generation])) for seed in seeds)
            handle.write(f"{generation},{values}\n")


def _write_positions_csv(path: Path, positions: np.ndarray) -> None:
    with path.open("w", encoding="utf-8") as handle:
        header = ["generation"]
        for name in GUEST_NAMES:
            header.extend([f"{name}_row", f"{name}_col"])
        handle.write(",".join(header) + "\n")
        for generation in range(positions.shape[0]):
            cells = [str(generation)]
            for guest in range(NUM_GUESTS):
                cells.append(str(int(positions[generation, guest, 0])))
                cells.append(str(int(positions[generation, guest, 1])))
            handle.write(",".join(cells) + "\n")


def _write_summary_text(path: Path, matrix_name: str, preferences: np.ndarray, stats: list[dict]) -> None:
    lines = [
        f"matrix: {matrix_name}",
        format_matrix(preferences),
        "",
    ]
    for item in stats:
        lines.append(
            "seed {seed}: {initial_stress} → {final_stress} "
            "({reduction_percent:.1f}% lower if positive), min {min_stress} at gen {min_stress_generation}, "
            "moves {move_count}, steps down/up/flat {steps_down}/{steps_up}/{steps_flat}, "
            "last-10-cycles span {tail_span}".format(**item)
        )
    initials = [item["initial_stress"] for item in stats]
    finals = [item["final_stress"] for item in stats]
    lines.append(
        f"mean initial {sum(initials) / len(initials):.2f} → mean final {sum(finals) / len(finals):.2f}"
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_run_bundle(
    matrix_name: str,
    preferences: np.ndarray,
    results: dict[int, RunResult],
    output_root: Path,
    with_figures: bool,
) -> list[dict]:
    """שומר מספרים, ואופציונלית את כל האיורים, לתיקיית המטריצה."""
    folder = output_root / matrix_name
    folder.mkdir(parents=True, exist_ok=True)
    if with_figures:
        import matplotlib

        matplotlib.use("Agg")
        import viz
    np.savetxt(
        folder / "matrix.csv",
        preferences,
        fmt="%d",
        delimiter=",",
        header=",".join(ENTITY_NAMES),
        comments="",
    )
    stress_by_seed = {seed: result.stress for seed, result in results.items()}
    _write_stress_csv(folder / "stress.csv", stress_by_seed)
    stats = [summarize_run(results[seed], preferences) for seed in results]
    (folder / "summary.json").write_text(
        json.dumps({"matrix": matrix_name, "runs": stats}, indent=2),
        encoding="utf-8",
    )
    _write_summary_text(folder / "summary.txt", matrix_name, preferences, stats)

    spotlight = results[SNAPSHOT_SEED] if SNAPSHOT_SEED in results else next(iter(results.values()))
    _write_positions_csv(folder / f"positions_seed{spotlight.seed}.csv", spotlight.positions)
    title = MATRIX_TITLES[matrix_name]

    if with_figures:
        snapshot_dir = folder / f"seed_{spotlight.seed}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        initial = int(spotlight.stress[0])
        for generation, occupant in sorted(spotlight.snapshots.items()):
            viz.save_snapshot(
                snapshot_dir / f"gen_{generation:04d}.png",
                occupant,
                generation,
                int(spotlight.stress[generation]),
                initial,
                title,
            )
        viz.save_quality_plot(
            folder / "quality.png",
            stress_by_seed,
            f"{title}: stress vs generation",
        )
        zoom = min(viz.QUALITY_ZOOM_GENERATIONS, len(spotlight.stress) - 1)
        viz.save_quality_plot(
            folder / "quality_early.png",
            stress_by_seed,
            f"{title}: stress over the first {zoom} generations",
            xlim=(0, zoom),
        )
        viz.save_trails(
            folder / f"trails_seed{spotlight.seed}.png",
            spotlight.positions,
            f"{title}: paths, seed {spotlight.seed}",
        )
        viz.save_montage(
            folder / f"montage_seed{spotlight.seed}.png",
            spotlight.snapshots,
            spotlight.stress,
            initial,
            title,
        )
        viz.save_row_stress(
            folder / f"rows_seed{spotlight.seed}.png",
            spotlight.positions,
            preferences,
            f"{title}: personal stress, seed {spotlight.seed}",
        )
        viz.save_distance_comparison(
            folder / f"actual_vs_desired_seed{spotlight.seed}.png",
            preferences,
            actual_distance_matrix(spotlight.final_occupant),
            f"{title}: desired vs actual at generation {len(spotlight.stress) - 1}, seed {spotlight.seed}",
        )
        viz.save_finals(
            folder / "finals_all_seeds.png",
            {seed: result.final_occupant for seed, result in results.items()},
            stress_by_seed,
            f"{title}: final positions by seed",
        )
        if spotlight.field_frames:
            viz.save_field_spread(
                folder / "field_spread.png",
                spotlight.field_frames,
                "Distance-to-table wave during the opening generations",
            )
        frames = []
        for generation in range(len(spotlight.stress)):
            if generation != 0 and generation % CYCLE_LENGTH != 0:
                continue
            occupant = spotlight.snapshots.get(generation)
            if occupant is None:
                # לשחזר מתמונת המיקומים אין תא-תא; נשתמש רק בדורות ששמרנו
                # ובדור האחרון. האנימציה נבנית מחדש מן המיקומים השמורים.
                occupant = _occupant_from_positions(spotlight.positions[generation])
            frames.append(
                (occupant, generation, int(spotlight.stress[generation]), initial, title)
            )
        viz.save_animation(folder / f"animation_seed{spotlight.seed}.gif", frames)
    return stats


def _occupant_from_positions(guest_positions: np.ndarray) -> np.ndarray:
    """משחזר לוח דיירים ממיקומי האורחים. השולחן תמיד במרכז."""
    occupant = np.full((GRID_SIZE, GRID_SIZE), EMPTY, dtype=np.int16)
    occupant[TABLE_ROW, TABLE_COL] = TABLE
    for guest, occupant_id in enumerate(GUEST_OCCUPANTS):
        row = int(guest_positions[guest, 0])
        col = int(guest_positions[guest, 1])
        occupant[row, col] = occupant_id
    return occupant


def run_matrix(
    matrix_name: str,
    seeds: tuple[int, ...] | list[int],
    generations: int,
    output_root: Path,
    with_figures: bool,
) -> list[dict]:
    preferences = MATRICES[matrix_name]
    results: dict[int, RunResult] = {}
    for seed in seeds:
        result = run_simulation(preferences, seed=seed, generations=generations)
        results[seed] = result
        initial = int(result.stress[0])
        final = int(result.stress[-1])
        percent = 100.0 * (initial - final) / initial if initial else 0.0
        print(
            f"{matrix_name} seed {seed}: stress {initial} → {final} ({percent:.1f}% ), "
            f"min {int(result.stress.min())}, moves {result.move_count}"
        )
    stats = save_run_bundle(matrix_name, preferences, results, output_root, with_figures)
    return stats


def render_videos(output_root: Path, generations: int = DEFAULT_GENERATIONS) -> None:
    """מריץ את שתי הריצות המצולמות וכותב MP4 תחת output/videos."""
    import matplotlib

    matplotlib.use("Agg")
    import viz

    folder = output_root / VIDEO_DIR_NAME
    folder.mkdir(parents=True, exist_ok=True)
    for matrix_name, seed, filename in VIDEO_RUNS:
        preferences = MATRICES[matrix_name]
        print(f"Running {matrix_name} seed {seed} for {generations} generations")
        result = run_simulation(preferences, seed=seed, generations=generations)
        initial = int(result.stress[0])
        final = int(result.stress[-1])
        print(f"  stress {initial} → {final}, moves {result.move_count}")
        viz.save_run_video(folder / filename, result.positions, result.stress, MATRIX_TITLES[matrix_name])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the party cellular automaton")
    parser.add_argument(
        "--matrix",
        action="append",
        choices=tuple(MATRICES),
        help="Which preference matrix to run. Repeatable. Default: both.",
    )
    parser.add_argument("--seeds", type=int, nargs="+", help="Random seeds. Default: 0 1 2 3 4.")
    parser.add_argument("--generations", type=int, default=DEFAULT_GENERATIONS)
    parser.add_argument("--output", default=OUTPUT_DIR)
    parser.add_argument("--no-figures", action="store_true", help="Write numbers only, skip images.")
    parser.add_argument(
        "--videos",
        action="store_true",
        help="Render party_example.mp4 and party_interesting.mp4, and skip the snapshot bundle.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    names = args.matrix if args.matrix else list(MATRICES)
    seeds = tuple(args.seeds) if args.seeds is not None else DEFAULT_SEEDS
    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)
    if args.videos:
        render_videos(output_root, args.generations)
        return
    if not args.no_figures:
        import matplotlib

        matplotlib.use("Agg")
        import viz

        viz.save_rule_diagram(output_root / "rule_diagram.png")
    for name in names:
        run_matrix(name, seeds, args.generations, output_root, with_figures=not args.no_figures)


if __name__ == "__main__":
    main()
