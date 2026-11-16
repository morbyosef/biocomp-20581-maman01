"""מטריצות המרחקים הרצויים.

כל שורה היא אורח, כל עמודה היא יעד: A B C D E T.
הערך בשורה i ועמודה k הוא המרחק שאורח i רוצה מן הישות k.
המטריצה אינה חייבת להיות סימטרית. האלכסון (מרחק אורח מעצמו) הוא 0.
השולחן אינו שורה: הוא לא זז ואין לו העדפות.

המטריצה היא פרמטר קבוע של כלל המעבר, זהה לכל תא. היא לא מידע
שהאורח מודד על הלוח.
"""

import numpy as np

from constants import ENTITY_COUNT, ENTITY_NAMES, GUEST_NAMES, MAX_DIST, NUM_GUESTS

# מטריצת הדוגמה מן המטלה, כפי שניתנה.
EXAMPLE_MATRIX = np.array(
    [
        [0, 5, 8, 7, 7, 0],
        [0, 0, 1, 0, 3, 8],
        [6, 1, 0, 1, 0, 6],
        [5, 7, 0, 0, 4, 5],
        [4, 4, 0, 2, 0, 6],
    ],
    dtype=np.int16,
)

# שלוש אישיויות מן המאמר, במטריצה אחת:
# A רודף אחרי B (מרחק 1) אבל B רוצה לברוח מ-A עד למרחק 16, ורחוק מן השולחן.
# C בודד: רחוק מכולם ומן השולחן, ולכן נדחק לפינה.
# D ו-E חבורה: צמודים זה לזה וצמודים לשולחן.
# אין שיכון שמרצה את כולם, כי A ו-B דורשים מרחקים סותרים.
INTERESTING_MATRIX = np.array(
    [
        [0, 1, 9, 8, 8, 4],
        [16, 0, 9, 10, 10, 14],
        [14, 14, 0, 14, 14, 14],
        [8, 8, 12, 0, 1, 1],
        [8, 8, 12, 1, 0, 1],
    ],
    dtype=np.int16,
)

MATRICES = {
    "example": EXAMPLE_MATRIX,
    "interesting": INTERESTING_MATRIX,
}

MATRIX_TITLES = {
    "example": "Example matrix",
    "interesting": "Chase, loner, and table pair",
}


def validate_matrix(matrix: np.ndarray) -> None:
    """מוודאת צורה, טווח, ואלכסון אפס לפני שמריצים אוטומט."""
    if matrix.shape != (NUM_GUESTS, ENTITY_COUNT):
        raise ValueError(
            f"preference matrix must have shape {(NUM_GUESTS, ENTITY_COUNT)}, got {matrix.shape}"
        )
    if np.any(matrix < 0):
        raise ValueError("preference matrix has a negative distance")
    if np.any(matrix > MAX_DIST):
        raise ValueError(f"preference matrix has a distance above MAX_DIST={MAX_DIST}")
    for guest in range(NUM_GUESTS):
        if int(matrix[guest, guest]) != 0:
            raise ValueError(f"diagonal entry for {GUEST_NAMES[guest]} must be 0")


def format_matrix(matrix: np.ndarray) -> str:
    """טבלה טקסטואלית להדפסה ולדוח."""
    header = "    " + " ".join(f"{name:>3}" for name in ENTITY_NAMES)
    lines = [header]
    for row_index, name in enumerate(GUEST_NAMES):
        cells = " ".join(f"{int(matrix[row_index, col]):>3}" for col in range(ENTITY_COUNT))
        lines.append(f"{name:>3} {cells}")
    return "\n".join(lines)
