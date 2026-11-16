"""חלון אנימציה של המסיבה.

כל הציור נמצא ב-viz.py וכלל המעבר ב-ca_rules.py.
הקובץ הזה רק מחבר ביניהם: בכל פריים מפעילים את הכלל ומציירים מחדש.
בלי מסך (שרת) נשמרת אנימציית gif במקום חלון.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from constants import DEFAULT_GENERATIONS, OUTPUT_DIR, SNAPSHOT_SEED
from matrices import MATRICES, MATRIX_TITLES


GUI_INTERVAL_MS = 40
GUI_STRIDE = 1
HEADLESS_PREVIEW_GENERATIONS = 400


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Animate the party cellular automaton")
    parser.add_argument("--matrix", choices=tuple(MATRICES), default="example")
    parser.add_argument("--seed", type=int, default=SNAPSHOT_SEED)
    parser.add_argument("--generations", type=int, default=DEFAULT_GENERATIONS)
    parser.add_argument("--interval", type=int, default=GUI_INTERVAL_MS, help="Milliseconds between frames")
    parser.add_argument("--stride", type=int, default=GUI_STRIDE, help="Generations advanced per frame")
    parser.add_argument("--output", default=OUTPUT_DIR)
    return parser.parse_args(argv)


def _has_display() -> bool:
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    try:
        import tkinter  # noqa: F401
    except ImportError:
        return False
    return True


def main(argv=None) -> None:
    args = parse_args(argv)
    import matplotlib

    interactive = _has_display()
    if interactive:
        try:
            matplotlib.use("TkAgg")
        except Exception:
            interactive = False
            matplotlib.use("Agg")
    else:
        matplotlib.use("Agg")

    import viz
    from ca_rules import transition
    from simulation import create_initial_grid, measure_stress

    preferences = MATRICES[args.matrix]
    title = MATRIX_TITLES[args.matrix]
    grid = create_initial_grid(args.seed)
    initial_stress = measure_stress(grid.occupant, preferences)
    state = {"grid": grid, "generation": 0}

    if not interactive:
        from simulation import run_simulation

        generations = min(args.generations, HEADLESS_PREVIEW_GENERATIONS)
        result = run_simulation(preferences, seed=args.seed, generations=generations, verify_field=False)
        from constants import CYCLE_LENGTH

        frames = []
        for generation in range(len(result.stress)):
            if generation != 0 and generation % CYCLE_LENGTH != 0:
                continue
            from simulation import _occupant_from_positions

            frames.append(
                (
                    _occupant_from_positions(result.positions[generation]),
                    generation,
                    int(result.stress[generation]),
                    initial_stress,
                    title,
                )
            )
        path = Path(args.output) / args.matrix / f"gui_preview_seed{args.seed}.gif"
        path.parent.mkdir(parents=True, exist_ok=True)
        viz.save_animation(path, frames)
        print(f"No display. Wrote {path}")
        return

    plt = viz._pyplot()
    from matplotlib.animation import FuncAnimation

    fig, ax = plt.subplots(figsize=(7.2, 7.6))

    def update(frame_index: int):
        if frame_index > 0:
            for _step in range(args.stride):
                if state["generation"] >= args.generations:
                    break
                state["grid"] = transition(state["grid"], preferences)
                state["generation"] += 1
        ax.clear()
        stress = measure_stress(state["grid"].occupant, preferences)
        viz.draw_party(
            ax,
            state["grid"].occupant,
            state["generation"],
            stress,
            initial_stress,
            title,
        )
        return []

    frame_count = args.generations // args.stride + 1
    FuncAnimation(fig, update, frames=frame_count, interval=args.interval, repeat=False)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
