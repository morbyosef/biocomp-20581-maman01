"""צורת המדרגות שהאוטומט אמור לבנות. זה יעד חיצוני, לא חלק מן הכלל."""

from constants import ORIGIN_COL, ORIGIN_ROW


def tread_row(length: int, index: int) -> int:
    return ORIGIN_ROW + index * (length - 1)


def tread_origin_col(length: int, index: int) -> int:
    return ORIGIN_COL + index * (length - 1)


def staircase_cells(length: int, tread_count: int) -> set[tuple[int, int]]:
    """tread_count שלבים, כולל הקו המקורי, והניצבים שביניהם."""
    if length < 2:
        raise ValueError("length must be at least 2")
    if tread_count < 1:
        raise ValueError("tread_count must be positive")
    cells: set[tuple[int, int]] = set()
    for index in range(tread_count):
        row = tread_row(length, index)
        col0 = tread_origin_col(length, index)
        for offset in range(length):
            cells.add((row, col0 + offset))
        if index + 1 < tread_count:
            next_row = tread_row(length, index + 1)
            riser_col = tread_origin_col(length, index + 1)
            for riser_row in range(row + 1, next_row):
                cells.add((riser_row, riser_col))
    return cells


def on_staircase(length: int, row: int, col: int) -> bool:
    """האם התא שייך לזיגזג האינסופי, בלי הגבלת מספר שלבים."""
    if row < ORIGIN_ROW or col < ORIGIN_COL:
        return False
    step = length - 1
    if row % step == 0:
        index = row // step
        col0 = index * step
        if col0 <= col <= col0 + length - 1:
            return True
    if col % step == 0 and col >= step:
        stage = col // step
        low = (stage - 1) * step
        high = stage * step
        if low < row < high:
            return True
    return False
