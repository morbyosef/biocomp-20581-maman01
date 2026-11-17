"""ציור בלבד. אין כאן כלל מעבר ואין קריאת שדה מרחקים לצורך החלטה.

כל המספרים של העיצוב (גודל דמות, צבעים, קצב אנימציה) יושבים בראש הקובץ.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from constants import (
    CYCLE_LENGTH,
    EMPTY,
    ENTITY_COUNT,
    ENTITY_NAMES,
    GRID_SIZE,
    GUEST_A,
    GUEST_B,
    GUEST_C,
    GUEST_D,
    GUEST_E,
    GUEST_NAMES,
    GUEST_OCCUPANTS,
    NUM_GUESTS,
    TABLE,
    TABLE_COL,
    TABLE_ROW,
)

FIGURE_FACE = "#FFFcf7"
FLOOR_COLOR = "#F4EFE4"
GRID_LINE_COLOR = "#E3D6C4"
MAJOR_GRID_COLOR = "#CDBFAE"
TABLE_COLOR = "#C6A15B"
TABLE_EDGE = "#5C4314"
GUEST_COLORS = {
    GUEST_A: "#0072B2",
    GUEST_B: "#E69F00",
    GUEST_C: "#009E73",
    GUEST_D: "#CC79A7",
    GUEST_E: "#D55E00",
}
GUEST_MARKER_AREA = 170
TABLE_MARKER_AREA = 220
SNAPSHOT_DPI = 130
ANIMATION_DPI = 90
ANIMATION_FPS = 5
SNAPSHOT_FIGSIZE = (7.2, 7.6)
QUALITY_FIGSIZE = (9.2, 5.2)
TRAIL_FIGSIZE = (7.2, 7.2)
HEATMAP_FIGSIZE = (11.5, 4.2)
STORY_GENERATIONS = (0, 100, 200, 400, 800, 1200, 2000)
QUALITY_ZOOM_GENERATIONS = 400
HEBREW_FONT = "/usr/share/fonts/truetype/noto/NotoSerifHebrew-Regular.ttf"
SEED_LINE_COLORS = ("#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9")
VIDEO_FPS = 10
VIDEO_TARGET_SECONDS = 45
VIDEO_MIN_SECONDS = 30
VIDEO_MAX_SECONDS = 60
VIDEO_WIDTH_PX = 1280
VIDEO_HEIGHT_PX = 720
VIDEO_DPI = 100
VIDEO_CRF = 18
STRESS_CURVE_COLOR = "#0072B2"
STRESS_MARKER_COLOR = "#D55E00"
VIDEO_CURVE_FACE = "#FFFCF7"
VIDEO_Y_HEADROOM = 1.08
VIDEO_PARTY_WIDTH_RATIO = 1.05
VIDEO_CURVE_WIDTH_RATIO = 0.95

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
                "axes.facecolor": FLOOR_COLOR,
            }
        )
        _CONFIGURED = True
    return plt


def _finish(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=SNAPSHOT_DPI)
    _pyplot().close(fig)


def draw_party(
    ax,
    occupant: np.ndarray,
    generation: int,
    stress: int,
    initial_stress: int,
    title: str,
    *,
    with_heading: bool = True,
    with_legend: bool = True,
) -> None:
    """מצייר את החדר: שולחן, אורחים, ורשת. לא נוגע בכללים."""
    ax.set_xlim(-0.5, GRID_SIZE - 0.5)
    ax.set_ylim(GRID_SIZE - 0.5, -0.5)
    ax.set_aspect("equal")
    ax.set_facecolor(FLOOR_COLOR)
    ax.set_xticks(np.arange(0, GRID_SIZE, 5))
    ax.set_yticks(np.arange(0, GRID_SIZE, 5))
    ax.set_xticks(np.arange(-0.5, GRID_SIZE, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, GRID_SIZE, 1), minor=True)
    ax.grid(which="minor", color=GRID_LINE_COLOR, linewidth=0.35)
    ax.grid(which="major", color=MAJOR_GRID_COLOR, linewidth=0.7)
    ax.set_xlabel("column")
    ax.set_ylabel("row")
    ax.tick_params(labelsize=8)

    table_rows, table_cols = np.where(occupant == TABLE)
    ax.scatter(
        table_cols,
        table_rows,
        s=TABLE_MARKER_AREA,
        c=TABLE_COLOR,
        marker="s",
        zorder=3,
        edgecolors=TABLE_EDGE,
        linewidths=0.8,
        label="T table",
    )
    for row, col in zip(table_rows, table_cols):
        _label(ax, col, row, "T", "#3a2a10")

    for occupant_id, name in zip(GUEST_OCCUPANTS, GUEST_NAMES):
        rows, cols = np.where(occupant == occupant_id)
        color = GUEST_COLORS[occupant_id]
        ax.scatter(
            cols,
            rows,
            s=GUEST_MARKER_AREA,
            c=color,
            marker="o",
            zorder=4,
            edgecolors="white",
            linewidths=0.9,
            label=name,
        )
        for row, col in zip(rows, cols):
            _label(ax, col, row, name, "white")

    change = stress - initial_stress
    if with_heading:
        ax.set_title(
            f"{title}\ngeneration {generation}    stress {stress}    (start {initial_stress}, {change:+d})",
            fontsize=11,
        )
    if with_legend:
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.08),
            ncol=6,
            frameon=False,
            fontsize=8,
        )


def _label(ax, col, row, text: str, color: str) -> None:
    import matplotlib.patheffects as path_effects

    artist = ax.text(
        col,
        row,
        text,
        ha="center",
        va="center",
        color=color,
        fontsize=8,
        fontweight="bold",
        zorder=5,
    )
    artist.set_path_effects([path_effects.withStroke(linewidth=2.2, foreground="#1b1b1b" if color == "white" else "white")])


def save_snapshot(path, occupant, generation, stress, initial_stress, title) -> None:
    plt = _pyplot()
    fig, ax = plt.subplots(figsize=SNAPSHOT_FIGSIZE)
    draw_party(ax, occupant, generation, stress, initial_stress, title)
    fig.tight_layout()
    _finish(fig, Path(path))


def save_quality_plot(path, stress_by_seed: dict[int, np.ndarray], title: str, xlim=None) -> None:
    plt = _pyplot()
    fig, ax = plt.subplots(figsize=QUALITY_FIGSIZE)
    peak = 0
    for index, (seed, series) in enumerate(stress_by_seed.items()):
        color = SEED_LINE_COLORS[index % len(SEED_LINE_COLORS)]
        ax.plot(np.arange(len(series)), series, color=color, linewidth=1.5, label=f"seed {seed}")
        peak = max(peak, int(series.max()))
    ax.set_ylim(0, peak * 1.08 if peak else 1)
    if xlim is None:
        ax.set_xlim(0, len(next(iter(stress_by_seed.values()))) - 1)
    else:
        ax.set_xlim(*xlim)
    initials = [int(series[0]) for series in stress_by_seed.values()]
    finals = [int(series[-1]) for series in stress_by_seed.values()]
    mean_initial = sum(initials) / len(initials)
    mean_final = sum(finals) / len(finals)
    ax.set_xlabel("generation")
    ax.set_ylabel("stress   Σ |actual distance − desired|")
    ax.set_title(title)
    ax.grid(True, color="#e6e0d6", linewidth=0.6)
    ax.legend(frameon=False, ncol=3)
    ax.text(
        0.99,
        0.98,
        f"mean {mean_initial:.0f} → {mean_final:.0f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        color="#333333",
    )
    fig.tight_layout()
    _finish(fig, Path(path))


def save_trails(path, positions: np.ndarray, title: str) -> None:
    plt = _pyplot()
    fig, ax = plt.subplots(figsize=TRAIL_FIGSIZE)
    ax.set_xlim(-0.5, GRID_SIZE - 0.5)
    ax.set_ylim(GRID_SIZE - 0.5, -0.5)
    ax.set_aspect("equal")
    ax.set_facecolor(FLOOR_COLOR)
    ax.set_xlabel("column")
    ax.set_ylabel("row")
    ax.scatter(
        [TABLE_COL],
        [TABLE_ROW],
        s=TABLE_MARKER_AREA,
        c=TABLE_COLOR,
        marker="s",
        edgecolors=TABLE_EDGE,
        zorder=3,
        label="T table",
    )
    for guest, name in enumerate(GUEST_NAMES):
        color = GUEST_COLORS[GUEST_OCCUPANTS[guest]]
        cols = positions[:, guest, 1]
        rows = positions[:, guest, 0]
        ax.plot(cols, rows, color=color, linewidth=1.35, alpha=0.9, label=name, zorder=2)
        ax.scatter(cols[0], rows[0], s=36, facecolors="none", edgecolors=color, linewidths=1.4, zorder=4)
        ax.scatter(cols[-1], rows[-1], s=42, c=color, edgecolors="white", linewidths=0.6, zorder=5)
    ax.set_title(title + "\nopen marker = start, filled = end")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=6, frameon=False, fontsize=8)
    fig.tight_layout()
    _finish(fig, Path(path))


def save_montage(path, snapshots: dict[int, np.ndarray], stress: np.ndarray, initial: int, title: str) -> None:
    plt = _pyplot()
    generations = [generation for generation in STORY_GENERATIONS if generation in snapshots]
    if not generations:
        generations = sorted(snapshots)
    columns = 4
    rows = int(np.ceil(len(generations) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(14.5, 3.6 * rows))
    flat = np.atleast_1d(axes).ravel()
    for axis, generation in zip(flat, generations):
        draw_party(axis, snapshots[generation], generation, int(stress[generation]), initial, "")
        legend = axis.get_legend()
        if legend is not None:
            legend.remove()
        axis.set_title(f"gen {generation}\nstress {int(stress[generation])}", fontsize=10)
        axis.set_xlabel("")
        axis.set_ylabel("")
    for axis in flat[len(generations) :]:
        axis.axis("off")
    fig.suptitle(title + "  —  selected generations", fontsize=14)
    fig.tight_layout()
    _finish(fig, Path(path))


def save_row_stress(path, positions: np.ndarray, preferences: np.ndarray, title: str) -> None:
    """לחץ אישי אמיתי של כל אורח לאורך הזמן. הסכום הוא הלחץ הגלובלי."""
    plt = _pyplot()
    generations = positions.shape[0]
    series = np.zeros((generations, NUM_GUESTS), dtype=np.int32)
    for generation in range(generations):
        for guest in range(NUM_GUESTS):
            total = 0
            guest_pos = positions[generation, guest]
            for entity in range(ENTITY_COUNT):
                if entity == guest:
                    continue
                if entity < NUM_GUESTS:
                    other = positions[generation, entity]
                else:
                    other = (TABLE_ROW, TABLE_COL)
                actual = max(abs(int(guest_pos[0]) - int(other[0])), abs(int(guest_pos[1]) - int(other[1])))
                total += abs(actual - int(preferences[guest, entity]))
            series[generation, guest] = total
    fig, ax = plt.subplots(figsize=QUALITY_FIGSIZE)
    for guest, name in enumerate(GUEST_NAMES):
        ax.plot(
            np.arange(generations),
            series[:, guest],
            color=GUEST_COLORS[GUEST_OCCUPANTS[guest]],
            linewidth=1.4,
            label=name,
        )
    ax.plot(np.arange(generations), series.sum(axis=1), color="#222222", linewidth=1.8, linestyle="--", label="total")
    ax.set_xlim(0, generations - 1)
    ax.set_ylim(0, max(int(series.sum(axis=1).max()), 1) * 1.05)
    ax.set_xlabel("generation")
    ax.set_ylabel("personal stress (true distances)")
    ax.set_title(title)
    ax.grid(True, color="#e6e0d6", linewidth=0.6)
    ax.legend(frameon=False, ncol=6)
    fig.tight_layout()
    _finish(fig, Path(path))


def save_distance_comparison(path, desired: np.ndarray, actual: np.ndarray, title: str) -> None:
    plt = _pyplot()
    error = np.abs(actual.astype(int) - desired.astype(int))
    fig, axes = plt.subplots(1, 3, figsize=HEATMAP_FIGSIZE)
    panels = (
        (desired, "desired", "Blues"),
        (actual, "actual at the end", "Blues"),
        (error, "absolute error", "Reds"),
    )
    for axis, (values, label, cmap) in zip(axes, panels):
        image = axis.imshow(values, cmap=cmap, vmin=0, vmax=max(int(np.max(values)), 1))
        axis.set_xticks(range(ENTITY_COUNT), ENTITY_NAMES)
        axis.set_yticks(range(NUM_GUESTS), GUEST_NAMES)
        axis.set_title(label)
        for row in range(NUM_GUESTS):
            for col in range(ENTITY_COUNT):
                axis.text(col, row, str(int(values[row, col])), ha="center", va="center", color="black", fontsize=8)
        fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    fig.suptitle(title)
    fig.tight_layout()
    _finish(fig, Path(path))


def save_finals(path, occupants_by_seed: dict[int, np.ndarray], stress_by_seed: dict[int, np.ndarray], title: str) -> None:
    plt = _pyplot()
    seeds = list(occupants_by_seed)
    fig, axes = plt.subplots(1, len(seeds), figsize=(3.3 * len(seeds), 4.2))
    flat = np.atleast_1d(axes).ravel()
    for axis, seed in zip(flat, seeds):
        initial = int(stress_by_seed[seed][0])
        final = int(stress_by_seed[seed][-1])
        draw_party(
            axis,
            occupants_by_seed[seed],
            len(stress_by_seed[seed]) - 1,
            final,
            initial,
            "",
        )
        legend = axis.get_legend()
        if legend is not None:
            legend.remove()
        axis.set_title(f"seed {seed}\n{initial} → {final}", fontsize=11)
        axis.set_xlabel("")
        axis.set_ylabel("")
    fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    _finish(fig, Path(path))


def save_field_spread(path, frames: dict[int, np.ndarray], title: str) -> None:
    plt = _pyplot()
    generations = sorted(frames)
    fig, axes = plt.subplots(1, len(generations), figsize=(3.1 * len(generations), 3.8))
    flat = np.atleast_1d(axes).ravel()
    for axis, generation in zip(flat, generations):
        image = axis.imshow(frames[generation], cmap="YlGnBu", vmin=0, vmax=GRID_SIZE - 1, origin="upper")
        axis.scatter([TABLE_COL], [TABLE_ROW], c="black", marker="s", s=18, zorder=3)
        axis.set_title(f"gen {generation}")
        axis.set_xticks([])
        axis.set_yticks([])
    fig.colorbar(image, ax=flat.tolist(), fraction=0.02, pad=0.02, label="distance to table")
    fig.suptitle(title)
    fig.subplots_adjust(top=0.78, wspace=0.18)
    _finish(fig, Path(path))


def save_animation(path, frames) -> None:
    plt = _pyplot()
    from matplotlib.animation import PillowWriter

    fig, ax = plt.subplots(figsize=(6.3, 6.9))
    writer = PillowWriter(fps=ANIMATION_FPS)
    with writer.saving(fig, str(path), dpi=ANIMATION_DPI):
        for occupant, generation, stress, initial, title in frames:
            ax.clear()
            draw_party(ax, occupant, generation, stress, initial, title)
            fig.subplots_adjust(bottom=0.16, top=0.88)
            writer.grab_frame()
    plt.close(fig)


def save_rule_diagram(path) -> None:
    """תרשים ארבעת השלבים. הציור לא משפיע על הכלל."""
    plt = _pyplot()
    from matplotlib import font_manager
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    # matplotlib מצייר עברית בסדר לוגי עם הגופן הזה. אין להפוך עם bidi.
    font_properties = None
    if Path(HEBREW_FONT).is_file():
        font_manager.fontManager.addfont(HEBREW_FONT)
        font_properties = font_manager.FontProperties(fname=HEBREW_FONT, size=11)

    fig, ax = plt.subplots(figsize=(11.2, 5.2))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 46)
    ax.axis("off")
    ax.set_facecolor(FIGURE_FACE)

    def box(x, y, w, h, face, title, body):
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.4,rounding_size=0.8",
            facecolor=face,
            edgecolor="#5c5146",
            linewidth=1.1,
        )
        ax.add_patch(patch)
        kwargs = {"fontproperties": font_properties} if font_properties is not None else {}
        ax.text(x + w / 2, y + h * 0.70, title, ha="center", va="center", fontsize=13, fontweight="bold", **kwargs)
        ax.text(x + w / 2, y + h * 0.34, body, ha="center", va="center", fontsize=9.5, **kwargs)

    box(6, 30, 88, 12, "#F3E6C8", "בכל דור ובכל תא", "גל המרחק מתקדם צעד אחד מן השכנים\nוהשעון שבתוך התא עולה באחד")
    phases = (
        (4, "#D6E6F5", "חישה", "האורחים נשארים\nהגל חוצה את החדר"),
        (28, "#F7E3B0", "הצעה", "אורח בוחר צעד\nלתא ריק שמשפר"),
        (52, "#E4D4EE", "מכרז", "תא ריק בוחר\nאת השיפור הגדול"),
        (76, "#D5E8D4", "ביצוע", "הזוכה זז צעד\nהמפסיד נשאר"),
    )
    for x, color, title, body in phases:
        box(x, 4, 20, 13, color, title, body)
    for x in (24, 48, 72):
        ax.add_patch(FancyArrowPatch((x, 10.5), (x + 4, 10.5), arrowstyle="-|>", mutation_scale=12, color="#5c5146"))
    ax.annotate(
        "",
        xy=(14, 19.5),
        xytext=(86, 19.5),
        arrowprops={"arrowstyle": "-|>", "color": "#8a7b68", "connectionstyle": "arc3,rad=0.25"},
    )
    if font_properties is not None:
        ax.text(50, 23.2, "חוזרים לחישה", ha="center", va="center", fontsize=10, color="#5c5146", fontproperties=font_properties)
    fig.tight_layout()
    _finish(fig, Path(path))


def video_frame_generations(last_generation: int) -> list[int]:
    """דורות שמצוירים בסרטון.

    תזוזה יכולה לקרות רק בכפולה של אורך המחזור, וכל דור כזה נשמר.
    דורות ביניים נוספים כדי שמונה הדור ועקומת הלחץ יעברו את כל הריצה,
    והאורך יישאר בין VIDEO_MIN_SECONDS ל־VIDEO_MAX_SECONDS בקצב VIDEO_FPS.
    """
    if last_generation < 1:
        raise ValueError("last_generation must be positive")
    target_frames = VIDEO_FPS * VIDEO_TARGET_SECONDS
    stride = max(1, int(round(last_generation / target_frames)))
    while True:
        chosen = set(range(0, last_generation + 1, stride))
        chosen.add(last_generation)
        chosen.update(range(0, last_generation + 1, CYCLE_LENGTH))
        frames = sorted(chosen)
        duration = len(frames) / VIDEO_FPS
        if duration > VIDEO_MAX_SECONDS and stride < last_generation:
            stride += 1
            continue
        if duration < VIDEO_MIN_SECONDS and stride > 1:
            stride -= 1
            continue
        return frames


def _occupant_from_positions(guest_positions: np.ndarray) -> np.ndarray:
    occupant = np.full((GRID_SIZE, GRID_SIZE), EMPTY, dtype=np.int16)
    occupant[TABLE_ROW, TABLE_COL] = TABLE
    for guest, occupant_id in enumerate(GUEST_OCCUPANTS):
        row = int(guest_positions[guest, 0])
        col = int(guest_positions[guest, 1])
        occupant[row, col] = occupant_id
    return occupant


def _draw_video_frame(fig, party, curve, positions, stress, generation: int, title: str) -> None:
    initial = int(stress[0])
    current = int(stress[generation])
    party.clear()
    curve.clear()
    draw_party(
        party,
        _occupant_from_positions(positions[generation]),
        generation,
        current,
        initial,
        title,
        with_heading=False,
        with_legend=False,
    )
    fig.suptitle(
        f"{title}     generation {generation}     stress {current}",
        fontsize=18,
        color="#2a241c",
    )
    shown = np.arange(generation + 1)
    curve.set_facecolor(VIDEO_CURVE_FACE)
    curve.plot(shown, stress[: generation + 1], color=STRESS_CURVE_COLOR, linewidth=1.8)
    curve.scatter([generation], [current], s=42, color=STRESS_MARKER_COLOR, zorder=3)
    curve.set_xlim(0, max(generation, 1))
    curve.set_ylim(0, max(int(stress.max()), 1) * VIDEO_Y_HEADROOM)
    curve.set_xlabel("generation")
    curve.set_ylabel("stress  |actual − desired|")
    curve.set_title(f"stress {initial} → {current}", fontsize=12, color="#2a241c")
    curve.grid(True, color=GRID_LINE_COLOR, linewidth=0.6)
    curve.tick_params(labelsize=9)


def save_run_video(path, positions: np.ndarray, stress: np.ndarray, title: str) -> None:
    """כותב MP4 של הריצה: H.264, yuv420p, רוחב VIDEO_WIDTH_PX, קצב VIDEO_FPS."""
    plt = _pyplot()
    last_generation = len(stress) - 1
    if len(positions) != len(stress):
        raise ValueError("positions and stress must cover the same generations")
    frames = video_frame_generations(last_generation)
    fig = plt.figure(figsize=(VIDEO_WIDTH_PX / VIDEO_DPI, VIDEO_HEIGHT_PX / VIDEO_DPI), dpi=VIDEO_DPI)
    fig.patch.set_facecolor(FIGURE_FACE)
    grid = fig.add_gridspec(
        1,
        2,
        width_ratios=(VIDEO_PARTY_WIDTH_RATIO, VIDEO_CURVE_WIDTH_RATIO),
        left=0.05,
        right=0.975,
        top=0.84,
        bottom=0.09,
        wspace=0.22,
    )
    party = fig.add_subplot(grid[0])
    curve = fig.add_subplot(grid[1])

    path = Path(path)
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
        for index, generation in enumerate(frames):
            _draw_video_frame(fig, party, curve, positions, stress, generation, title)
            fig.canvas.draw()
            width, height = fig.canvas.get_width_height()
            if (width, height) != (VIDEO_WIDTH_PX, VIDEO_HEIGHT_PX):
                raise RuntimeError(f"frame is {width}x{height}, expected {VIDEO_WIDTH_PX}x{VIDEO_HEIGHT_PX}")
            raw = np.ascontiguousarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3])
            encoder.stdin.write(raw.tobytes())
            if index % 50 == 0:
                print(f"  {title}: frame {index + 1}/{len(frames)} (generation {generation})", flush=True)
    finally:
        if encoder.stdin is not None:
            encoder.stdin.close()
        return_code = encoder.wait()
        plt.close(fig)
    if return_code != 0:
        raise RuntimeError(f"ffmpeg exited with {return_code} while writing {path}")
    duration = len(frames) / VIDEO_FPS
    print(f"Wrote {path} ({len(frames)} frames, {duration:.1f}s at {VIDEO_FPS} fps)")
