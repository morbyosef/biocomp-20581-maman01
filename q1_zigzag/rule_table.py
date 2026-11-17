"""טבלת המעבר. הסימולטור והציורים קוראים את אותה הרשימה.

כלל הוא תבנית של שכונת מור: לכל תא מצב אחד, קבוצת מצבים, או ANY.
הכלל הראשון שמתאים קובע את המצב הבא. אם אף כלל לא מתאים, המצב נשמר.
"""

from __future__ import annotations

from dataclasses import dataclass

from constants import (
    ANY,
    BRICK,
    BURST,
    BURST_END,
    BURST_STATES,
    CAP_A,
    CAP_B,
    CAP_B_HOLD,
    CAP_B_WAIT,
    DONE,
    ECHO,
    EMPTY,
    EXTEND,
    FREEZE,
    GROW,
    ABSORB_SIGNAL,
    GROW_FROM,
    HOLD_END,
    LAUNCH_FROM,
    MID,
    OLD_RULER,
    RELABEL,
    REST,
    RETURN_SIGNAL,
    SHAFT,
    SIG_A,
    SIG_A_TOK,
    SIG_B,
    SIG_B_TOK,
    SIG_ON_A,
    TIP,
    TOK_A,
    TOKEN,
    WAVE,
    WAVE_FROM,
    WAVE_TIP,
)


@dataclass(frozen=True)
class Rule:
    group: str
    group_title: str
    caption: str
    result: int
    pattern: dict


# כיווני הסרגל. A הקצה הרחוק, B קצה הבנייה, G כיוון הצמיחה, Back ההפוך.
ORIENTATIONS = (
    {
        "name": "אופקי",
        "A": "w",
        "B": "e",
        "G": "n",
        "Back": "s",
        "GA": "nw",
        "GB": "ne",
        "BA": "sw",
        "BB": "se",
    },
    {
        "name": "אנכי",
        "A": "s",
        "B": "n",
        "G": "e",
        "Back": "w",
        "GA": "se",
        "GB": "ne",
        "BA": "sw",
        "BB": "nw",
    },
)

_RULES: list[Rule] | None = None


def _expand(orient: dict, abstract: dict) -> dict:
    pattern = {}
    for key, value in abstract.items():
        if key == "c":
            pattern["c"] = value
        else:
            pattern[orient[key]] = value
    return pattern


def _add(rules: list[Rule], group: str, title: str, caption: str, result: int, pattern: dict) -> None:
    rules.append(Rule(group, title, caption, result, pattern))


def _oriented(rules: list[Rule], group: str, title: str, caption: str, result: int, abstract: dict) -> None:
    for orient in ORIENTATIONS:
        concrete = _expand(orient, abstract)
        _add(rules, group, title, f"{caption} ({orient['name']})", result, concrete)


def build_rules() -> list[Rule]:
    rules: list[Rule] = []
    startup = "startup"
    startup_title = "אתחול הקו"
    # הפינות מולאות במפורש בשמות מוחלטים, כי האתחול אינו תלוי כיוון.
    quiet = {"n": EMPTY, "s": EMPTY, "ne": EMPTY, "nw": EMPTY, "se": EMPTY, "sw": EMPTY}
    _add(
        rules,
        startup,
        startup_title,
        "קצה שמאלי של קו של 1 הופך לאסימון",
        TOK_A,
        {"c": BRICK, "w": EMPTY, "e": BRICK, **quiet},
    )
    _add(
        rules,
        startup,
        startup_title,
        "קצה ימני של הקו הופך לקצה הבנייה",
        CAP_B,
        {"c": BRICK, "e": EMPTY, "w": BRICK, **quiet},
    )
    _add(
        rules,
        startup,
        startup_title,
        "תא אמצעי בקו הופך לגוף הסרגל",
        MID,
        {"c": BRICK, "w": BRICK, "e": BRICK, **quiet},
    )

    travel = "travel"
    travel_title = "שיגור האות והליכתו"
    _oriented(
        rules,
        travel,
        travel_title,
        "תא גוף שליד קצה הבנייה קולט אות לכיוון הקצה הרחוק",
        SIG_A,
        {"c": MID, "B": CAP_B, "G": EMPTY, "Back": EMPTY},
    )
    _oriented(
        rules,
        travel,
        travel_title,
        "אסימון הצמוד לקצה קולט את האות מיד",
        SIG_A_TOK,
        {"c": TOKEN, "B": CAP_B},
    )
    _oriented(
        rules,
        travel,
        travel_title,
        "קו באורך 2: האות נולד ישר על האסימון שבקצה",
        SIG_ON_A,
        {"c": TOK_A, "B": CAP_B},
    )
    _oriented(
        rules,
        travel,
        travel_title,
        "קצה הבנייה יוצא להמתנה כל עוד האות בדרך",
        CAP_B_WAIT,
        {"c": CAP_B, "A": LAUNCH_FROM, "B": EMPTY, "Back": EMPTY},
    )
    _oriented(
        rules,
        travel,
        travel_title,
        "האות מתקדם תא אחד לכיוון הקצה הרחוק",
        SIG_A,
        {"c": MID, "B": SIG_A},
    )
    _oriented(
        rules,
        travel,
        travel_title,
        "האות מגיע אל האסימון",
        SIG_A_TOK,
        {"c": TOKEN, "B": SIG_A},
    )
    _oriented(
        rules,
        travel,
        travel_title,
        "האות מגיע אל האסימון שיושב בקצה הרחוק",
        SIG_ON_A,
        {"c": TOK_A, "B": SIG_A},
    )

    bounce = "bounce"
    bounce_title = "פגיעה באסימון וחזרה"
    _add(rules, bounce, bounce_title, "האות ממשיך הלאה ומשאיר גוף סרגל", MID, {"c": SIG_A})
    _add(rules, bounce, bounce_title, "אות חוזר משאיר גוף סרגל", MID, {"c": SIG_B})
    _add(rules, bounce, bounce_title, "אחרי הפגיעה האסימון זז והתא נשאר גוף", MID, {"c": SIG_A_TOK})
    _add(rules, bounce, bounce_title, "הקצה הרחוק נשאר אחרי שהאסימון עזב אותו", CAP_A, {"c": SIG_ON_A})
    _add(rules, bounce, bounce_title, "האסימון נשאר במקומו החדש אחרי שהאות עבר", TOKEN, {"c": SIG_B_TOK})
    _oriented(
        rules,
        bounce,
        bounce_title,
        "החזרה מן האסימון: האות והאסימון עוברים יחד תא אחד",
        SIG_B_TOK,
        {"c": MID, "A": SIG_A_TOK},
    )
    _oriented(
        rules,
        bounce,
        bounce_title,
        "החזרה מן הקצה הרחוק: האסימון יוצא לדרך עם האות",
        SIG_B_TOK,
        {"c": MID, "A": SIG_ON_A},
    )
    _oriented(
        rules,
        bounce,
        bounce_title,
        "האות ממשיך אל קצה הבנייה והאסימון נשאר מאחור",
        SIG_B,
        {"c": MID, "A": SIG_B_TOK},
    )
    _oriented(
        rules,
        bounce,
        bounce_title,
        "האות החוזר מתקדם לאורך הסרגל",
        SIG_B,
        {"c": MID, "A": SIG_B},
    )
    _oriented(
        rules,
        bounce,
        bounce_title,
        "האות חזר: מוסיפים תא אחד לזיגזג",
        BURST,
        {"c": CAP_B_WAIT, "A": RETURN_SIGNAL},
    )
    _oriented(
        rules,
        bounce,
        bounce_title,
        "האסימון הגיע לקצה: זו הבנייה האחרונה בשלב",
        BURST_END,
        {"c": CAP_B_WAIT, "A": ABSORB_SIGNAL},
    )

    grow = "grow"
    grow_title = "הוספת תא לזיגזג"
    _add(rules, grow, grow_title, "פקודת הבנייה נרשמת וממתינים להד", CAP_B_HOLD, {"c": BURST})
    _add(rules, grow, grow_title, "הבנייה האחרונה בשלב ממתינה להד", HOLD_END, {"c": BURST_END})
    _oriented(
        rules,
        grow,
        grow_title,
        "התא הריק הראשון בכיוון הצמיחה נולד כראש",
        TIP,
        {
            "c": EMPTY,
            "Back": BURST_STATES,
            "BA": REST,
            "BB": EMPTY,
            "A": EMPTY,
            "B": EMPTY,
            "G": EMPTY,
            "GA": EMPTY,
            "GB": EMPTY,
        },
    )
    _oriented(
        rules,
        grow,
        grow_title,
        "גוף ההארכה קולט את דופק הבנייה מן הבסיס",
        GROW,
        {"c": SHAFT, "Back": BURST_STATES},
    )
    _oriented(
        rules,
        grow,
        grow_title,
        "הדופק מתקדם לאורך ההארכה",
        GROW,
        {"c": SHAFT, "Back": GROW},
    )
    _add(rules, grow, grow_title, "אחרי שהדופק עבר נשאר גוף הארכה", SHAFT, {"c": GROW})
    _oriented(
        rules,
        grow,
        grow_title,
        "הראש שקיבל דופק מתכונן לזוז צעד",
        EXTEND,
        {"c": TIP, "Back": GROW_FROM},
    )
    _add(rules, grow, grow_title, "הראש הישן שולח הד חזרה אל הבסיס", ECHO, {"c": EXTEND})
    _oriented(
        rules,
        grow,
        grow_title,
        "מעבר לראש נולד ראש חדש",
        TIP,
        {
            "c": EMPTY,
            "Back": EXTEND,
            "A": EMPTY,
            "B": EMPTY,
            "G": EMPTY,
            "GA": EMPTY,
            "GB": EMPTY,
            "BA": EMPTY,
            "BB": EMPTY,
        },
    )

    echo = "echo"
    echo_title = "הד ושיגור מחדש"
    _add(rules, echo, echo_title, "ההד משאיר אחריו גוף הארכה", SHAFT, {"c": ECHO})
    _oriented(
        rules,
        echo,
        echo_title,
        "ההד יורד תא אחד לכיוון הבסיס",
        ECHO,
        {"c": SHAFT, "G": ECHO},
    )
    _oriented(
        rules,
        echo,
        echo_title,
        "ההד חזר, ואפשר לשלוח אות מדידה חדש",
        CAP_B,
        {"c": CAP_B_HOLD, "G": ECHO},
    )
    _oriented(
        rules,
        echo,
        echo_title,
        "הארכה של תא אחד הסתיימה, ואפשר למדוד שוב",
        CAP_B,
        {"c": CAP_B_HOLD, "G": TIP},
    )
    _oriented(
        rules,
        echo,
        echo_title,
        "ההד האחרון פותח את העברת הסרגל",
        RELABEL,
        {"c": HOLD_END, "G": ECHO},
    )
    _oriented(
        rules,
        echo,
        echo_title,
        "הארכה אחרונה של תא אחד פותחת העברת סרגל",
        RELABEL,
        {"c": HOLD_END, "G": TIP},
    )

    handoff = "handoff"
    handoff_title = "העברת הסרגל והקפאה"
    _add(rules, handoff, handoff_title, "בסיס הסרגל הישן הופך לאסימון של הסרגל החדש", TOK_A, {"c": RELABEL})
    _oriented(
        rules,
        handoff,
        handoff_title,
        "גל ההעברה נכנס לגוף ההארכה",
        WAVE,
        {"c": SHAFT, "Back": WAVE_FROM},
    )
    _oriented(
        rules,
        handoff,
        handoff_title,
        "גל ההעברה מגיע אל הראש",
        WAVE_TIP,
        {"c": TIP, "Back": WAVE_FROM},
    )
    _add(rules, handoff, handoff_title, "גוף ההארכה הופך לגוף הסרגל החדש", MID, {"c": WAVE})
    _add(rules, handoff, handoff_title, "ראש ההארכה הופך לקצה הבנייה החדש", CAP_B, {"c": WAVE_TIP})
    _oriented(
        rules,
        handoff,
        handoff_title,
        "הסרגל שסיים את תפקידו מתחיל לקפוא",
        FREEZE,
        {"c": OLD_RULER, "B": RELABEL},
    )
    _oriented(
        rules,
        handoff,
        handoff_title,
        "גל ההקפאה מתקדם אל הקצה הרחוק",
        FREEZE,
        {"c": OLD_RULER, "B": FREEZE},
    )
    _add(rules, handoff, handoff_title, "תא שהוקפא נשאר לבנה קבועה בזיגזג", DONE, {"c": FREEZE})

    # שקט מפורש: תא ריק מוקף ריק נשאר ריק. זה גם ברירת המחדל.
    _add(
        rules,
        "quiet",
        "שקט",
        "תא ריק שכל שכניו ריקים נשאר ריק",
        EMPTY,
        {key: EMPTY for key in ("c", "n", "ne", "e", "se", "s", "sw", "w", "nw")},
    )
    return rules


def rules() -> list[Rule]:
    global _RULES
    if _RULES is None:
        _RULES = build_rules()
    return _RULES


def matching_rules(neighborhood: dict) -> list[Rule]:
    found = []
    for rule in rules():
        if _matches(rule, neighborhood):
            found.append(rule)
    return found


def next_state(neighborhood: dict) -> int:
    for rule in rules():
        if _matches(rule, neighborhood):
            return rule.result
    return neighborhood["c"]


def _matches(rule: Rule, neighborhood: dict) -> bool:
    for key, expected in rule.pattern.items():
        if expected is ANY:
            continue
        actual = neighborhood[key]
        if isinstance(expected, frozenset):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True
