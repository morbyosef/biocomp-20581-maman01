"""ציור בלבד: מקרא, שכונה, טבלת כללים, תמונות מצב וסרטון."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from ca import evolve_until, occupied
from constants import (
    ANY,
    EMPTY,
    NAMED_SETS,
    STATE_COLOR,
    STATE_NAME,
    STATE_TAG,
    VIDEO_CRF,
    VIDEO_DPI,
    VIDEO_FPS,
    VIDEO_HEIGHT_PX,
    VIDEO_MARGIN_CELLS,
    VIDEO_WIDTH_PX,
)
from matplotlib.patches import Rectangle
from rule_table import Rule, rules
from target import staircase_cells

# קבועי עיצוב
FIGURE_FACE = "#FFFcf7"
ANY_COLOR = "#E4DDD2"
SET_COLOR = "#F4E4B8"
GRID_EDGE = "#5C5146"
CELL_EDGE = "#2C241C"
ARROW_COLOR = "#5C5146"
RULES_PER_ROW = 4
RULES_PER_PAGE = 8
SNAPSHOT_DPI = 140
KEY_ORDER = (
    ("nw", "n", "ne"),
    ("w", "c", "e"),
    ("sw", "s", "se"),
)

_CONFIGURED = False


def _pyplot():
    global _CONFIGURED
    import matplotlib.pyplot as plt

    if not _CONFIGURED:
        plt.rcParams.update(
            {
                "font.family": "DejaVu Sans",
                "axes.unicode_minus": False,
                "figure.facecolor": FIGURE_FACE,
                "savefig.facecolor": FIGURE_FACE,
            }
        )
        _CONFIGURED = True
    return plt


def _hebrew():
    # DejaVu Sans כולל גם עברית וגם ספרות. גופן עברי בלבד מפיל סוגריים ומספרים.
    return None


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=SNAPSHOT_DPI)
    _pyplot().close(fig)


def _swatch(ax, value) -> str:
    tag = "?"
    color = ANY_COLOR
    if value is ANY:
        color = ANY_COLOR
        tag = "?"
    elif isinstance(value, frozenset):
        color = SET_COLOR
        tag = NAMED_SETS.get(value, "*")
    else:
        color = STATE_COLOR[value]
        tag = STATE_TAG[value]
    ax.set_facecolor(color)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(CELL_EDGE)
        spine.set_linewidth(0.8)
    ax.text(0.5, 0.5, tag, ha="center", va="center", fontsize=8, color="#1b1b1b", transform=ax.transAxes)
    return tag


def draw_rule(fig, outer, rule: Rule, hebrew) -> None:
    """מצייר כלל אחד: שכונת 3×3, חץ, והמצב הבא."""
    grid = outer.subgridspec(4, 5, height_ratios=(0.9, 1, 1, 1), width_ratios=(1, 1, 1, 0.45, 1), hspace=0.08, wspace=0.08)
    caption = fig.add_subplot(grid[0, :])
    caption.axis("off")
    caption.set_facecolor(FIGURE_FACE)
    kwargs = {"fontproperties": hebrew} if hebrew is not None else {}
    caption.text(0.0, 0.5, rule.caption, ha="left", va="center", fontsize=7.5, color="#2a241c", wrap=True, **kwargs)
    for row_index, keys in enumerate(KEY_ORDER):
        for col_index, key in enumerate(keys):
            ax = fig.add_subplot(grid[row_index + 1, col_index])
            value = rule.pattern.get(key, ANY)
            _swatch(ax, value)
            if key == "c":
                for spine in ax.spines.values():
                    spine.set_linewidth(2.2)
                    spine.set_color("#111111")
    arrow = fig.add_subplot(grid[2, 3])
    arrow.axis("off")
    arrow.set_facecolor(FIGURE_FACE)
    arrow.annotate(
        "",
        xy=(0.9, 0.5),
        xytext=(0.1, 0.5),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "color": ARROW_COLOR, "lw": 1.2},
    )
    result = fig.add_subplot(grid[2, 4])
    _swatch(result, rule.result)


def save_legend(path: Path) -> None:
    plt = _pyplot()
    hebrew = _hebrew()
    names = list(STATE_NAME)
    columns = 2
    rows = (len(names) + columns - 1) // columns
    fig, axes = plt.subplots(rows, columns, figsize=(10.5, 0.42 * rows + 0.8))
    fig.patch.set_facecolor(FIGURE_FACE)
    for ax, state in zip(axes.ravel(), names):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(Rectangle((0.2, 0.15), 0.9, 0.7, facecolor=STATE_COLOR[state], edgecolor=CELL_EDGE, linewidth=0.8))
        ax.text(0.65, 0.5, STATE_TAG[state], ha="center", va="center", fontsize=8)
        label = f"{STATE_NAME[state]}  ({state})"
        kwargs = {"fontproperties": hebrew} if hebrew is not None else {}
        ax.text(1.4, 0.5, label, ha="left", va="center", fontsize=10, **kwargs)
    for ax in axes.ravel()[len(names):]:
        ax.axis("off")
    fig.tight_layout()
    _save(fig, path)


def save_default_rule(path: Path) -> None:
    plt = _pyplot()
    hebrew = _hebrew()
    fig = plt.figure(figsize=(4.8, 3.2))
    fig.patch.set_facecolor(FIGURE_FACE)
    outer = fig.add_gridspec(1, 1, left=0.04, right=0.96, top=0.82, bottom=0.06)
    grid = outer[0, 0].subgridspec(3, 5, width_ratios=(1, 1, 1, 0.45, 1), wspace=0.08, hspace=0.08)
    for row_index, keys in enumerate(KEY_ORDER):
        for col_index, key in enumerate(keys):
            ax = fig.add_subplot(grid[row_index, col_index])
            _swatch(ax, ANY)
            if key == "c":
                for spine in ax.spines.values():
                    spine.set_linewidth(2.2)
    arrow = fig.add_subplot(grid[1, 3])
    arrow.axis("off")
    arrow.annotate(
        "",
        xy=(0.9, 0.5),
        xytext=(0.1, 0.5),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "color": ARROW_COLOR, "lw": 1.2},
    )
    result = fig.add_subplot(grid[1, 4])
    result.set_xticks([])
    result.set_yticks([])
    result.set_facecolor(ANY_COLOR)
    kwargs = {"fontproperties": hebrew} if hebrew is not None else {}
    result.text(0.5, 0.5, "אותו\nמצב", ha="center", va="center", fontsize=9, **kwargs)
    fig.suptitle("ברירת מחדל", fontsize=14, **kwargs)
    fig.savefig(path, dpi=SNAPSHOT_DPI)
    plt.close(fig)


def save_neighborhood(path: Path) -> None:
    plt = _pyplot()
    hebrew = _hebrew()
    labels = {
        "nw": "צפון־מערב\nNW",
        "n": "צפון\nN",
        "ne": "צפון־מזרח\nNE",
        "w": "מערב\nW",
        "c": "התא\nC",
        "e": "מזרח\nE",
        "sw": "דרום־מערב\nSW",
        "s": "דרום\nS",
        "se": "דרום־מזרח\nSE",
    }
    fig, axes = plt.subplots(3, 3, figsize=(6.4, 5.6))
    fig.patch.set_facecolor(FIGURE_FACE)
    for ax, key in zip(axes.ravel(), ("nw", "n", "ne", "w", "c", "e", "sw", "s", "se")):
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor("#D6E6F5" if key == "c" else "#F4EFE4")
        for spine in ax.spines.values():
            spine.set_color("#111111" if key == "c" else CELL_EDGE)
            spine.set_linewidth(2.2 if key == "c" else 0.8)
        kwargs = {"fontproperties": hebrew} if hebrew is not None else {}
        ax.text(0.5, 0.5, labels[key], ha="center", va="center", fontsize=12, **kwargs)
    fig.tight_layout()
    _save(fig, path)


def save_rule_pages(folder: Path) -> list[Path]:
    plt = _pyplot()
    hebrew = _hebrew()
    folder.mkdir(parents=True, exist_ok=True)
    pages: list[list[Rule]] = []
    bucket: list[Rule] = []
    for rule in rules():
        if bucket and bucket[-1].group != rule.group:
            pages.append(bucket)
            bucket = []
        bucket.append(rule)
        if len(bucket) >= RULES_PER_PAGE:
            pages.append(bucket)
            bucket = []
    if bucket:
        pages.append(bucket)
    paths = []
    for index, page in enumerate(pages, start=1):
        rows = (len(page) + RULES_PER_ROW - 1) // RULES_PER_ROW
        fig = plt.figure(figsize=(12.2, 2.15 * rows + 0.55))
        fig.patch.set_facecolor(FIGURE_FACE)
        outer = fig.add_gridspec(rows, RULES_PER_ROW, left=0.02, right=0.98, top=0.92, bottom=0.04, wspace=0.18, hspace=0.28)
        title = page[0].group_title
        kwargs = {"fontproperties": hebrew} if hebrew is not None else {}
        fig.suptitle(title, fontsize=15, color="#2a241c", **kwargs)
        for slot, rule in enumerate(page):
            draw_rule(fig, outer[slot // RULES_PER_ROW, slot % RULES_PER_ROW], rule, hebrew)
        for slot in range(len(page), rows * RULES_PER_ROW):
            ax = fig.add_subplot(outer[slot // RULES_PER_ROW, slot % RULES_PER_ROW])
            ax.axis("off")
        path = folder / f"rules_{index:02d}.png"
        fig.savefig(path, dpi=SNAPSHOT_DPI)
        plt.close(fig)
        paths.append(path)
    return paths


def _bounds(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return min(rows), max(rows), min(cols), max(cols)


def draw_grid(ax, grid, bounds, title: str) -> None:
    row0, row1, col0, col1 = bounds
    pad = VIDEO_MARGIN_CELLS
    ax.set_xlim(col0 - pad - 0.5, col1 + pad + 0.5)
    ax.set_ylim(row0 - pad - 0.5, row1 + pad + 0.5)
    ax.set_aspect("equal")
    ax.set_facecolor(FIGURE_FACE)
    ax.set_xticks(range(col0 - pad, col1 + pad + 1))
    ax.set_yticks(range(row0 - pad, row1 + pad + 1))
    ax.set_xticks([tick - 0.5 for tick in range(col0 - pad, col1 + pad + 2)], minor=True)
    ax.set_yticks([tick - 0.5 for tick in range(row0 - pad, row1 + pad + 2)], minor=True)
    ax.grid(which="minor", color="#E3D6C4", linewidth=0.4)
    ax.tick_params(labelsize=7)
    ax.set_xlabel("column")
    ax.set_ylabel("row")
    for (row, col), state in grid.items():
        ax.add_patch(
            Rectangle(
                (col - 0.5, row - 0.5),
                1,
                1,
                facecolor=STATE_COLOR[state],
                edgecolor="#FFFFFF",
                linewidth=0.4,
                zorder=2,
            )
        )
        ax.text(col, row, STATE_TAG[state], ha="center", va="center", fontsize=7, zorder=3, color="#1b1b1b")
    ax.set_title(title, fontsize=11, color="#2a241c")


def milestone_indices(history, length: int, tread_count: int) -> list[int]:
    marks = [0]
    for count in range(2, tread_count + 1):
        target = staircase_cells(length, count)
        for index, grid in enumerate(history):
            if target <= occupied(grid):
                if index not in marks:
                    marks.append(index)
                break
    return marks


def save_montage(path: Path, length: int, tread_count: int = 5) -> tuple[int, list[int]]:
    plt = _pyplot()
    history = evolve_until(length, tread_count)
    marks = milestone_indices(history, length, tread_count)
    bounds = _bounds(occupied(history[-1]))
    columns = 3
    rows = (len(marks) + columns - 1) // columns
    fig, axes = plt.subplots(rows, columns, figsize=(10.8, 3.3 * rows))
    fig.patch.set_facecolor(FIGURE_FACE)
    flat = np.atleast_1d(axes).ravel()
    for ax, index in zip(flat, marks):
        draw_grid(ax, history[index], bounds, f"L = {length}    generation {index}")
    for ax in flat[len(marks):]:
        ax.axis("off")
    fig.tight_layout()
    _save(fig, path)
    return len(history) - 1, marks


def save_video(path: Path, length: int, tread_count: int = 6) -> None:
    plt = _pyplot()
    history = evolve_until(length, tread_count)
    bounds = _bounds(occupied(history[-1]))
    fig = plt.figure(figsize=(VIDEO_WIDTH_PX / VIDEO_DPI, VIDEO_HEIGHT_PX / VIDEO_DPI), dpi=VIDEO_DPI)
    fig.patch.set_facecolor(FIGURE_FACE)
    ax = fig.add_axes((0.07, 0.08, 0.9, 0.78))
    path.parent.mkdir(parents=True, exist_ok=True)
    encoder = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{VIDEO_WIDTH_PX}x{VIDEO_HEIGHT_PX}",
            "-pix_fmt",
            "rgb24",
            "-r",
            str(VIDEO_FPS),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            str(VIDEO_CRF),
            "-movflags",
            "+faststart",
            str(path),
        ],
        stdin=subprocess.PIPE,
    )
    try:
        for index, grid in enumerate(history):
            ax.clear()
            draw_grid(ax, grid, bounds, "")
            fig.suptitle(f"L = {length}     generation {index}", fontsize=20, color="#2a241c")
            fig.canvas.draw()
            width, height = fig.canvas.get_width_height()
            if (width, height) != (VIDEO_WIDTH_PX, VIDEO_HEIGHT_PX):
                raise RuntimeError(f"frame is {width}x{height}")
            raw = np.ascontiguousarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3])
            encoder.stdin.write(raw.tobytes())
    finally:
        if encoder.stdin is not None:
            encoder.stdin.close()
        code = encoder.wait()
        plt.close(fig)
    if code != 0:
        raise RuntimeError(f"ffmpeg exited with {code}")
    print(f"Wrote {path} ({len(history)} frames, {len(history) / VIDEO_FPS:.1f}s)")
