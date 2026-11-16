"""כללי המעבר של האוטומט התאי. אין כאן גרפיקה ואין מדידת איכות.

המצב של תא הוא וקטור סופי:
    occupant, dist[6], clock, proposal, gain, bid

השכנות היא מור ברדיוס 1 (שמונה שכנים). אותו כלל חל על כל תא,
בסנכרון, והמצב הבא נגזר רק מן התא ומשכניו.

מטריצת ההעדפות היא חלק מן הכלל (כמו טבלת מעברים), לא קריאה
של מיקומים על הלוח. גל המרחק מתקדם תא אחד בדור, והאורחים זזים
רק אחרי שהגל מספיק לחצות את החדר.

פרוטוקול תנועה בשלושה דורות, כדי שההכרעה תישאר מקומית:
    1. הצעה — האורח כותב כיוון על התא שלו.
    2. מכרז — תא ריק בוחר מציע אחד וכותב את זהותו.
    3. ביצוע — המציע הזוכה זז, ומי שהפסיד נשאר.
"""

from __future__ import annotations

import numpy as np

from constants import (
    BID_CLOCK,
    COMMIT_CLOCK,
    CYCLE_LENGTH,
    DIRECTION_COUNT,
    DIRECTION_DELTAS,
    DISTANCE_STEP,
    EMPTY,
    ENTITY_COUNT,
    ENTITY_OCCUPANTS,
    GRID_SIZE,
    GUEST_A,
    GUEST_OCCUPANTS,
    MAX_DIST,
    MAX_GAIN,
    NEIGHBOR_OFFSETS,
    NEIGHBORHOOD_RADIUS,
    NO_BID,
    NORTH,
    NUM_GUESTS,
    PHASE_BID,
    PHASE_COMMIT,
    PHASE_PROPOSE,
    PHASE_SENSE,
    PROPOSE_CLOCK,
    STAY,
    STEP_LENGTH,
    TABLE,
)

GUEST_OCCUPANT_SET = frozenset(GUEST_OCCUPANTS)
DELTA_TO_DIRECTION = {delta: code for code, delta in enumerate(DIRECTION_DELTAS)}


class Grid:
    """מצב הלוח כולו: לכל תא אותם רכיבים. זה מערך של מצבים, לא כלל."""

    def __init__(self) -> None:
        shape = (GRID_SIZE, GRID_SIZE)
        self.occupant = np.full(shape, EMPTY, dtype=np.int16)
        self.dist = np.full((ENTITY_COUNT, shape[0], shape[1]), MAX_DIST, dtype=np.int16)
        self.clock = np.zeros(shape, dtype=np.int16)
        self.proposal = np.full(shape, STAY, dtype=np.int16)
        self.gain = np.zeros(shape, dtype=np.int16)
        self.bid = np.full(shape, NO_BID, dtype=np.int16)

    def copy(self) -> "Grid":
        other = Grid()
        other.occupant = self.occupant.copy()
        other.dist = self.dist.copy()
        other.clock = self.clock.copy()
        other.proposal = self.proposal.copy()
        other.gain = self.gain.copy()
        other.bid = self.bid.copy()
        return other


def phase_kind(clock_value: int) -> int:
    """השלב שתא נמצא בו, לפי השעון שלו בלבד."""
    clock_value = int(clock_value) % CYCLE_LENGTH
    if clock_value == PROPOSE_CLOCK:
        return PHASE_PROPOSE
    if clock_value == BID_CLOCK:
        return PHASE_BID
    if clock_value == COMMIT_CLOCK:
        return PHASE_COMMIT
    return PHASE_SENSE


def kinds_from_clocks(clock: np.ndarray) -> np.ndarray:
    """מפה במקביל: השלב של כל תא תלוי רק בשעון של אותו תא."""
    kind = np.full(clock.shape, PHASE_SENSE, dtype=np.int16)
    kind[clock == PROPOSE_CLOCK] = PHASE_PROPOSE
    kind[clock == BID_CLOCK] = PHASE_BID
    kind[clock == COMMIT_CLOCK] = PHASE_COMMIT
    return kind


def propagate_distances(occupant: np.ndarray, dist: np.ndarray) -> np.ndarray:
    """גל מרחק: בתא של הישות המרחק 0, אחרת מינימום השכנים ועוד צעד אחד.

    זהו מרחק בת גרף של שכנות מור, והוא שווה למרחק צ'בישב
    אחרי שהגל מספיק להתפשט. תא מחוץ ללוח נקרא כמרחק רווי (MAX_DIST),
    כלומר שפת האפס הקבועה לא מייצרת קיצור דרך.
    """
    entity_count, height, width = dist.shape
    radius = NEIGHBORHOOD_RADIUS
    padded = np.full(
        (entity_count, height + 2 * radius, width + 2 * radius),
        MAX_DIST,
        dtype=np.int16,
    )
    padded[:, radius : radius + height, radius : radius + width] = dist
    neighbor_views = []
    for d_row, d_col in NEIGHBOR_OFFSETS:
        neighbor_views.append(
            padded[
                :,
                radius + d_row : radius + d_row + height,
                radius + d_col : radius + d_col + width,
            ]
        )
    nearest = np.minimum.reduce(neighbor_views)
    updated = np.minimum(nearest + DISTANCE_STEP, MAX_DIST).astype(np.int16)
    for entity, occupant_id in enumerate(ENTITY_OCCUPANTS):
        updated[entity, occupant == occupant_id] = 0
    return updated


def personal_stress(distance_vector: np.ndarray, guest_index: int, preferences: np.ndarray) -> int:
    """הלחץ האישי של אורח: סכום |מרחק נתפס − מרחק רצוי| מול כל השאר.

    זה לא מדד האיכות הגלובלי. האורח מסתכל רק על השורה שלו במטריצה,
    ועל וקטור המרחקים שיושב בתא המועמד (מה שהשדה המקומי אומר).
    """
    total = 0
    desired_row = preferences[guest_index]
    for entity in range(ENTITY_COUNT):
        if entity == guest_index:
            continue
        total += abs(int(distance_vector[entity]) - int(desired_row[entity]))
    return total


def choose_direction(
    vectors: dict[int, np.ndarray],
    guest_index: int,
    preferences: np.ndarray,
) -> tuple[int, int]:
    """בוחר כיוון לפי וקטורי המרחק של התא ושל שכנים פנויים.

    שוויון בלחץ נשבר כך: להישאר עדיף על לזוז, צעד ישר עדיף על אלכסון,
    ואחר כך קוד הכיוון הקטן. בלי זה צ'בישב (שיש לו כמה שכנים באותו מרחק)
    היה דוחף את כולם לאותו כיוון שרירותי.
    """
    best_direction = STAY
    best_stress = personal_stress(vectors[STAY], guest_index, preferences)
    best_length = STEP_LENGTH[STAY]
    for direction in range(NORTH, DIRECTION_COUNT):
        vector = vectors.get(direction)
        if vector is None:
            continue
        stress = personal_stress(vector, guest_index, preferences)
        step_length = STEP_LENGTH[direction]
        better_stress = stress < best_stress
        same_stress_shorter = stress == best_stress and step_length < best_length
        same_stress_same_length_lower_code = (
            stress == best_stress and step_length == best_length and direction < best_direction
        )
        if better_stress or same_stress_shorter or same_stress_same_length_lower_code:
            best_direction = direction
            best_stress = stress
            best_length = step_length
    stay_stress = personal_stress(vectors[STAY], guest_index, preferences)
    gain = stay_stress - best_stress
    if gain <= 0:
        return STAY, 0
    if gain > MAX_GAIN:
        gain = MAX_GAIN
    return best_direction, gain


def _in_bounds(row: int, col: int, height: int, width: int) -> bool:
    return 0 <= row < height and 0 <= col < width


def _guest_index(occupant_id: int) -> int:
    return occupant_id - GUEST_A


def _write_proposals(grid: Grid, nxt: Grid, preferences: np.ndarray, kind: np.ndarray) -> None:
    height, width = grid.occupant.shape
    propose_cells = np.argwhere(kind == PHASE_PROPOSE)
    for row, col in propose_cells:
        occupant_id = int(grid.occupant[row, col])
        if occupant_id not in GUEST_OCCUPANT_SET:
            continue
        guest_index = _guest_index(occupant_id)
        if not 0 <= guest_index < NUM_GUESTS:
            continue
        vectors: dict[int, np.ndarray] = {STAY: grid.dist[:, row, col]}
        for direction in range(NORTH, DIRECTION_COUNT):
            d_row, d_col = DIRECTION_DELTAS[direction]
            next_row = int(row) + d_row
            next_col = int(col) + d_col
            if not _in_bounds(next_row, next_col, height, width):
                continue
            if int(grid.occupant[next_row, next_col]) != EMPTY:
                continue
            vectors[direction] = grid.dist[:, next_row, next_col]
        direction, gain = choose_direction(vectors, guest_index, preferences)
        nxt.proposal[row, col] = direction
        nxt.gain[row, col] = gain


def _neighbor_points_at(grid: Grid, row: int, col: int, d_row: int, d_col: int) -> bool:
    """האם השכן שבכיוון (d_row, d_col) הציע לזוז בדיוק לתוך התא הזה."""
    height, width = grid.occupant.shape
    next_row = row + d_row
    next_col = col + d_col
    if not _in_bounds(next_row, next_col, height, width):
        return False
    return int(grid.proposal[next_row, next_col]) == DELTA_TO_DIRECTION[(-d_row, -d_col)]


def _write_bids(grid: Grid, nxt: Grid, kind: np.ndarray) -> None:
    """תא ריק בשלב המכרז בוחר את ההצעה עם השיפור הגדול ביותר.

    שוויון נשבר לפי מזהה האורח הקטן, כך שהתוצאה לא תלויה בסדר הסריקה.
    """
    height, width = grid.occupant.shape
    bid_mask = kind == PHASE_BID
    nxt.proposal[bid_mask] = grid.proposal[bid_mask]
    nxt.gain[bid_mask] = grid.gain[bid_mask]
    bid_cells = np.argwhere(bid_mask)
    for row, col in bid_cells:
        if int(grid.occupant[row, col]) != EMPTY:
            continue
        best_guest = NO_BID
        best_gain = 0
        for d_row, d_col in NEIGHBOR_OFFSETS:
            next_row = int(row) + d_row
            next_col = int(col) + d_col
            if not _in_bounds(next_row, next_col, height, width):
                continue
            if not _neighbor_points_at(grid, int(row), int(col), d_row, d_col):
                continue
            guest_id = int(grid.occupant[next_row, next_col])
            if guest_id not in GUEST_OCCUPANT_SET:
                continue
            gain = int(grid.gain[next_row, next_col])
            if gain <= 0:
                continue
            if best_guest == NO_BID or gain > best_gain or (gain == best_gain and guest_id < best_guest):
                best_guest = guest_id
                best_gain = gain
        nxt.bid[row, col] = best_guest


def _guest_move_accepted(grid: Grid, row: int, col: int) -> bool:
    """האם תא היעד הריק בחר בי, לפי מה שכתוב אצלו מן הדור הקודם."""
    direction = int(grid.proposal[row, col])
    if direction == STAY:
        return False
    d_row, d_col = DIRECTION_DELTAS[direction]
    next_row = row + d_row
    next_col = col + d_col
    height, width = grid.occupant.shape
    if not _in_bounds(next_row, next_col, height, width):
        return False
    if int(grid.occupant[next_row, next_col]) != EMPTY:
        return False
    return int(grid.bid[next_row, next_col]) == int(grid.occupant[row, col])


def _accepted_arrival(grid: Grid, row: int, col: int) -> int:
    """אם התא הריק הבטיח מקום לאורח שכנה שמכוון אליו — מחזירים את מזהה האורח."""
    guest_id = int(grid.bid[row, col])
    if guest_id == NO_BID:
        return EMPTY
    for d_row, d_col in NEIGHBOR_OFFSETS:
        next_row = row + d_row
        next_col = col + d_col
        height, width = grid.occupant.shape
        if not _in_bounds(next_row, next_col, height, width):
            continue
        if int(grid.occupant[next_row, next_col]) != guest_id:
            continue
        if _neighbor_points_at(grid, row, col, d_row, d_col):
            return guest_id
    return EMPTY


def _write_commits(grid: Grid, nxt: Grid, kind: np.ndarray) -> None:
    commit_cells = np.argwhere(kind == PHASE_COMMIT)
    for row, col in commit_cells:
        occupant_id = int(grid.occupant[row, col])
        if occupant_id == TABLE:
            nxt.occupant[row, col] = TABLE
        elif occupant_id in GUEST_OCCUPANT_SET:
            if _guest_move_accepted(grid, int(row), int(col)):
                nxt.occupant[row, col] = EMPTY
            else:
                nxt.occupant[row, col] = occupant_id
        else:
            nxt.occupant[row, col] = _accepted_arrival(grid, int(row), int(col))


def transition(grid: Grid, preferences: np.ndarray) -> Grid:
    """כלל המעבר האחיד. הקלט אינו משתנה; מוחזר לוח חדש.

    בכל דור, בכל תא:
        השדה מתעדכן מן השכנים, והשעון מתקדם באחד מודולו אורך המחזור.
        שאר הרכיבים נקבעים לפי השלב שכתוב בשעון של התא עצמו.
    """
    nxt = Grid()
    # השדה הבא נכתב מתוך המצב הנוכחי. ההצעות בהמשך קוראות את השדה הישן,
    # לא את זה שחושב ברגע זה — אחרת זה לא היה עדכון סינכרוני.
    nxt.dist = propagate_distances(grid.occupant, grid.dist)
    nxt.clock = ((grid.clock.astype(np.int16) + 1) % CYCLE_LENGTH).astype(np.int16)
    nxt.occupant = grid.occupant.copy()
    nxt.proposal.fill(STAY)
    nxt.gain.fill(0)
    nxt.bid.fill(NO_BID)

    kind = kinds_from_clocks(grid.clock)
    _write_proposals(grid, nxt, preferences, kind)
    _write_bids(grid, nxt, kind)
    _write_commits(grid, nxt, kind)
    return nxt
