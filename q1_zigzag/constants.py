"""קבועים של אוטומט הזיגזג. אין מספרים חשופים בשאר הקבצים."""

# הסריג האינסופי. שורה 0 היא הקו ההתחלתי, והשורה גדלה כלפי מעלה.
# העמודה גדלה ימינה. הקצה השמאלי של הקו יושב ב-(0, 0).
ORIGIN_ROW = 0
ORIGIN_COL = 0

# אורך מינימלי שהכללים מחויבים לטפל בו. תא בודד לא נדרש.
MIN_LINE_LENGTH = 2
TEST_MIN_LENGTH = 2
TEST_MAX_LENGTH = 10
TREADS_TO_VERIFY = 5
MAX_GENERATIONS = 80000
STUCK_WINDOW = 400

# שכונת מור ברדיוס 1.
NEIGHBORHOOD_RADIUS = 1
NEIGHBOR_KEYS = ("nw", "n", "ne", "w", "c", "e", "sw", "s", "se")
MOORE_OFFSETS = {
    "nw": (1, -1),
    "n": (1, 0),
    "ne": (1, 1),
    "w": (0, -1),
    "c": (0, 0),
    "e": (0, 1),
    "sw": (-1, -1),
    "s": (-1, 0),
    "se": (-1, 1),
}

# מצבים. 0 הוא הרקע השקט.
EMPTY = 0
BRICK = 1
DONE = 2
CAP_A = 3
MID = 4
CAP_B = 5
TOKEN = 6
TOK_A = 7
SIG_A = 8
SIG_B = 9
SIG_A_TOK = 10
SIG_B_TOK = 11
SIG_ON_A = 12
CAP_B_WAIT = 13
BURST = 14
BURST_END = 15
CAP_B_HOLD = 16
HOLD_END = 17
TIP = 18
SHAFT = 19
GROW = 20
EXTEND = 21
ECHO = 22
RELABEL = 23
WAVE = 24
WAVE_TIP = 25
FREEZE = 26

STATE_COUNT = FREEZE + 1

STATE_NAME = {
    EMPTY: "ריק",
    BRICK: "קו התחלתי",
    DONE: "זיגזג קבוע",
    CAP_A: "קצה רחוק",
    MID: "גוף הסרגל",
    CAP_B: "קצה הבנייה",
    TOKEN: "אסימון",
    TOK_A: "אסימון בקצה",
    SIG_A: "אות אל הקצה הרחוק",
    SIG_B: "אות אל קצה הבנייה",
    SIG_A_TOK: "אות שפגע באסימון",
    SIG_B_TOK: "אות שנושא אסימון",
    SIG_ON_A: "אות בקצה הרחוק",
    CAP_B_WAIT: "ממתין לאות",
    BURST: "פקודת בנייה",
    BURST_END: "בנייה אחרונה",
    CAP_B_HOLD: "ממתין להד",
    HOLD_END: "סיום שלב",
    TIP: "ראש הזיגזג",
    SHAFT: "גוף ההארכה",
    GROW: "דופק בנייה",
    EXTEND: "הארכת הראש",
    ECHO: "הד",
    RELABEL: "העברת סרגל",
    WAVE: "גל העברה",
    WAVE_TIP: "גל בראש",
    FREEZE: "הקפאה",
}

STATE_TAG = {
    EMPTY: "·",
    BRICK: "1",
    DONE: "#",
    CAP_A: "A",
    MID: "M",
    CAP_B: "B",
    TOKEN: "T",
    TOK_A: "a",
    SIG_A: "<",
    SIG_B: ">",
    SIG_A_TOK: "x",
    SIG_B_TOK: "X",
    SIG_ON_A: "o",
    CAP_B_WAIT: "W",
    BURST: "!",
    BURST_END: "*",
    CAP_B_HOLD: "H",
    HOLD_END: "E",
    TIP: "^",
    SHAFT: "|",
    GROW: "g",
    EXTEND: "e",
    ECHO: "c",
    RELABEL: "R",
    WAVE: "w",
    WAVE_TIP: "v",
    FREEZE: "f",
}

# צבעים לציור. הריק כמעט לבן, הזיגזג כחול כהה, האותות חמים.
STATE_COLOR = {
    EMPTY: "#F7F4EE",
    BRICK: "#4C78A8",
    DONE: "#1F4E79",
    CAP_A: "#59A14F",
    MID: "#8CD17D",
    CAP_B: "#B6992D",
    TOKEN: "#F28E2B",
    TOK_A: "#E15759",
    SIG_A: "#FF9DA7",
    SIG_B: "#B07AA1",
    SIG_A_TOK: "#D37295",
    SIG_B_TOK: "#9D7660",
    SIG_ON_A: "#FABFD2",
    CAP_B_WAIT: "#EDC948",
    BURST: "#F1CE63",
    BURST_END: "#D4A017",
    CAP_B_HOLD: "#C4B454",
    HOLD_END: "#8D6E00",
    TIP: "#76B7B2",
    SHAFT: "#4E9A96",
    GROW: "#86BCB6",
    EXTEND: "#2E8B87",
    ECHO: "#B279A2",
    RELABEL: "#499894",
    WAVE: "#6DB6B0",
    WAVE_TIP: "#2A6F6B",
    FREEZE: "#9C755F",
}

ANY = None

REST = frozenset({CAP_A, MID, TOKEN, TOK_A})
LAUNCH_FROM = frozenset({MID, TOKEN, TOK_A, CAP_A})
OLD_RULER = frozenset({CAP_A, MID, TOKEN, TOK_A})
BURST_STATES = frozenset({BURST, BURST_END})
GROW_FROM = frozenset({BURST, BURST_END, GROW})
RETURN_SIGNAL = frozenset({SIG_B, SIG_B_TOK})
ABSORB_SIGNAL = frozenset({SIG_A_TOK, SIG_ON_A})
WAVE_FROM = frozenset({RELABEL, WAVE})
NAMED_SETS = {
    REST: "R",
    LAUNCH_FROM: "S",
    OLD_RULER: "Q",
    BURST_STATES: "U",
    GROW_FROM: "P",
    RETURN_SIGNAL: "Y",
    ABSORB_SIGNAL: "Z",
    WAVE_FROM: "V",
}
VIDEO_LENGTHS = (3, 4)
VIDEO_FPS = 8
VIDEO_WIDTH_PX = 1280
VIDEO_HEIGHT_PX = 720
VIDEO_DPI = 100
VIDEO_CRF = 18
VIDEO_MARGIN_CELLS = 2
SNAPSHOT_TREADS = 5
OUTPUT_DIRNAME = "output"
