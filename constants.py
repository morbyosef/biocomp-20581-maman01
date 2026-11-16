"""כל הקבועים של הסימולציה.

אין מספרים חשופים בשאר הקבצים: גודל החדר, זהות הדיירים,
השכנות, השעון, ופרמטרי הריצה מוגדרים כאן בשם.
"""

# --- החדר ---
# לפחות 30×30, כפי שנדרש במטלה. קוטר צ'בישב של הלוח הוא GRID_SIZE - 1.
GRID_SIZE = 30
TABLE_ROW = GRID_SIZE // 2
TABLE_COL = GRID_SIZE // 2

# --- מי יכול לשבת בתא ---
# אפס הוא תא ריק. האורחים ממוספרים 1..5 לפי סדר העמודות במטריצה,
# והשולחן הוא 6. הסדר הזה זהה לסדר הערוצים בשדה המרחקים.
EMPTY = 0
GUEST_A = 1
GUEST_B = 2
GUEST_C = 3
GUEST_D = 4
GUEST_E = 5
TABLE = 6

NUM_GUESTS = 5
ENTITY_COUNT = NUM_GUESTS + 1
GUEST_OCCUPANTS = (GUEST_A, GUEST_B, GUEST_C, GUEST_D, GUEST_E)
ENTITY_OCCUPANTS = GUEST_OCCUPANTS + (TABLE,)
GUEST_NAMES = ("A", "B", "C", "D", "E")
ENTITY_NAMES = GUEST_NAMES + ("T",)
TABLE_ENTITY = ENTITY_OCCUPANTS.index(TABLE)

# --- שדה המרחקים ---
# הערך הגדול ביותר שמרחק צ'בישב יכול לקבל על הלוח (פינה מול פינה).
MAX_DIST = GRID_SIZE - 1
DISTANCE_STEP = 1
# אורח מסכם סטייה מול כל ישות חוץ מעצמו, וכל סטייה היא לכל היותר MAX_DIST.
MAX_GAIN = (ENTITY_COUNT - 1) * MAX_DIST

# --- שכנות מור ברדיוס 1: צעד אחד בכל כיוון, כולל אלכסונים ---
NEIGHBORHOOD_RADIUS = 1
STAY = 0
NORTH = 1
NORTHEAST = 2
EAST = 3
SOUTHEAST = 4
SOUTH = 5
SOUTHWEST = 6
WEST = 7
NORTHWEST = 8
DIRECTION_COUNT = 9

# (שינוי שורה, שינוי עמודה). שורה גדלה דרומה, עמודה גדלה מזרחה.
DIRECTION_DELTAS = (
    (0, 0),
    (-1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, -1),
)
DIRECTION_NAMES = ("stay", "N", "NE", "E", "SE", "S", "SW", "W", "NW")
# אורך מנהטן של הצעד. שובר שוויון דטרמיניסטי: צעד ישר עדיף על אלכסון.
STEP_LENGTH = tuple(abs(dr) + abs(dc) for dr, dc in DIRECTION_DELTAS)
NEIGHBOR_OFFSETS = tuple(DIRECTION_DELTAS[code] for code in range(NORTH, DIRECTION_COUNT))

# --- שעון פנימי של כל תא ---
# בין החלטה להחלטה ממתינים די דורות כדי שגל המרחק יחצה את החדר
# וצל של מיקום ישן יספיק להתנדף. קוטר הלוח הוא GRID_SIZE - 1,
# ולכן GRID_SIZE דורות של התפשטות מספיקים.
SENSE_PHASES = GRID_SIZE
PROPOSE_CLOCK = SENSE_PHASES
BID_CLOCK = SENSE_PHASES + 1
COMMIT_CLOCK = SENSE_PHASES + 2
CYCLE_LENGTH = SENSE_PHASES + 3
INITIAL_CLOCK = 0

PHASE_SENSE = 0
PHASE_PROPOSE = 1
PHASE_BID = 2
PHASE_COMMIT = 3

# אין מציע. אפס אינו מזהה של אורח (האורחים הם 1..5).
NO_BID = 0

# --- ריצה, תמונות, בדיקות ---
DEFAULT_GENERATIONS = 2000
SNAPSHOT_EVERY = 100
DEFAULT_SEEDS = (0, 1, 2, 3, 4)
SNAPSHOT_SEED = 0
# דורות שבהם מציירים את התפשטות הגל מן השולחן (לפני הזזה הראשונה).
FIELD_DEMO_GENERATIONS = (0, 1, 2, 5, 10, 20, 29)
OUTPUT_DIR = "output"
# המוניטור בודק שהשדה מדויק ברגע ההחלטה. זה לא חלק מכלל המעבר.
VERIFY_FIELD_BEFORE_PROPOSE = True
# כל תזוזה מפנה תא אחד ותופסת תא אחד.
CELLS_TOUCHED_BY_ONE_MOVE = 2
# כמה מחזורים אחרונים נכנסים לסיכום התנודתיות.
TAIL_CYCLES = 10
