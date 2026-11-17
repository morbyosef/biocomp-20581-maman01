"""בונה את דוח השאלה הראשונה: איורים, HTML, ו־PDF."""

from __future__ import annotations

import subprocess
from pathlib import Path

from constants import OUTPUT_DIRNAME, STATE_COUNT, TEST_MAX_LENGTH, TEST_MIN_LENGTH, TREADS_TO_VERIFY
from rule_table import rules
from viz import save_default_rule, save_legend, save_montage, save_neighborhood, save_rule_pages

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / OUTPUT_DIRNAME
PDF_PATH = ROOT / "report_q1.pdf"
HTML_PATH = ROOT / "report.html"

COMPLETION = {2: 46, 3: 109, 4: 203, 5: 329}


def _page(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<title>20581 מטלה 01 שאלה 1</title>
<style>
@font-face {{
  font-family: "Noto Serif Hebrew";
  src: url("file:///usr/share/fonts/truetype/noto/NotoSerifHebrew-Regular.ttf");
  font-weight: 400;
}}
@font-face {{
  font-family: "Noto Serif Hebrew";
  src: url("file:///usr/share/fonts/truetype/noto/NotoSerifHebrew-Bold.ttf");
  font-weight: 700;
}}
body {{
  font-family: "Noto Serif Hebrew", "DejaVu Sans", serif;
  max-width: 920px;
  margin: 2em auto;
  line-height: 1.65;
  color: #1c1c1c;
  padding: 0 1.2em 3em;
}}
h1, h2, h3 {{ line-height: 1.35; }}
code {{ font-family: "DejaVu Sans Mono", monospace; direction: ltr; }}
img {{ max-width: 100%; height: auto; display: block; margin: 0.8em auto; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ border: 1px solid #b7aa98; padding: 0.35em 0.55em; vertical-align: top; }}
th {{ background: #f3eadc; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def build_images() -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    save_legend(OUTPUT / "legend.png")
    save_neighborhood(OUTPUT / "neighborhood.png")
    save_default_rule(OUTPUT / "default_rule.png")
    rule_pages = save_rule_pages(OUTPUT / "rules")
    demos = {}
    for length in (2, 3, 4, 5):
        final_gen, marks = save_montage(OUTPUT / f"demo_L{length}.png", length, TREADS_TO_VERIFY)
        demos[length] = (final_gen, marks)
    return {"rules": rule_pages, "demos": demos}


def build_html(image_info: dict) -> None:
    rule_imgs = "\n".join(
        f'<img alt="עמוד כללים {index}" src="output/rules/{path.name}">'
        for index, path in enumerate(image_info["rules"], start=1)
    )
    demos = []
    for length in (2, 3, 4, 5):
        final_gen, _marks = image_info["demos"][length]
        kind = "זוגי" if length % 2 == 0 else "אי־זוגי"
        demos.append(
            f"<h3>אורך {length} ({kind})</h3>\n"
            f"<p>חמישה השלבים הראשונים שלמים בדור {final_gen}. "
            f"בכל תמונה מופיעים מספר הדור והתאים הדולקים. "
            f"אין תא דולק מחוץ לזיגזג.</p>\n"
            f'<img alt="מהלך L={length}" src="output/demo_L{length}.png">'
        )
    body = f"""
<h1>20581 — מטלה 01, שאלה 1</h1>
<h2>זיגזג באורך הקו</h2>
<p>
על סריג ריבועי אינסופי נתון קו אופקי יחיד של תאים במצב 1, באורך L לא ידוע.
L לפחות 2, והוא יכול להיות זוגי או אי־זוגי.
האוטומט בונה מדרגות שעולות ימינה: כל שלב אופקי וכל ניצב שביניהם באורך L,
והבנייה נמשכת בלי לעצור.
הקו המקורי הוא השלב הראשון.
</p>
<p>
הכללים יושבים בקובץ <code>rule_table.py</code>.
הסימולטור מפעיל את הרשימה הזו, וציורי הטבלה בדוח נוצרים ממנה.
אין שתי גרסאות של הכלל.
</p>

<h2>1. הסריג, המצבים והשכונה</h2>
<h3>הסריג</h3>
<p>
סריג ריבועי אינסופי.
שורה 0 היא שורת הקו, והאינדקס גדל כלפי מעלה.
העמודה גדלה ימינה, והקצה השמאלי של הקו נמצא בעמודה 0.
הרקע הוא המצב 0. תא במצב 0 שכל שכניו 0 נשאר 0.
</p>

<h3>המצבים</h3>
<p>
יש {STATE_COUNT} מצבים, מ־0 עד {STATE_COUNT - 1}. הקבוצה סופית ואינה תלויה ב־L.
האות על התא הוא קיצור שמופיע גם בטבלת הכללים.
מצב 1 הוא הקו שניתן בהתחלה. מצב «זיגזג קבוע» הוא לבנה שכבר סיימה את תפקידה כסרגל
ונשארת דולקת לנצח. שאר המצבים הם הסרגל, האות שרץ עליו, דופק הבנייה וההד.
</p>
<img alt="מקרא המצבים" src="output/legend.png">

<h3>השכונה</h3>
<p>
שכונת מור ברדיוס 1: התא עצמו ושמונת השכנים.
הכלל אחיד, סינכרוני ודטרמיניסטי, והמצב הבא נקבע רק מן השכונה הזו.
נבחרה שכונת מור ולא שכונת פון־נוימן, כי התא הריק שאמור להיוולד מעל קצה הבנייה
צריך לראות שהתא שליד הבסיס באמת שייך לסרגל, והתא הזה יושב באלכסון.
</p>
<img alt="שכונת מור" src="output/neighborhood.png">

<h2>2. טבלת המעבר</h2>
<p>
כל תרשים הוא שכונה אחת וחץ אל המצב הבא.
המסגרת העבה מסמנת את התא שמתעדכן.
תא אפור עם סימן שאלה הוא תא שהכלל לא בודק.
תא בז' עם אות לטינית הוא קבוצת מצבים, לפי הטבלה שלמטה.
אם כמה כללים מתאימים לאותה שכונה, הראשון ברשימה קובע.
בכל הריצות שנבדקו, עד אורך 10, לכל שכונה שהופיעה בפועל התאים לכל היותר כלל אחד.
</p>
<table>
<tr><th>סימון</th><th>הקבוצה</th></tr>
<tr><td>R</td><td>קצה רחוק, גוף הסרגל, אסימון, אסימון בקצה</td></tr>
<tr><td>S</td><td>גוף הסרגל, אסימון, אסימון בקצה, קצה רחוק</td></tr>
<tr><td>Q</td><td>הסרגל הישן, לפני שהוא קופא</td></tr>
<tr><td>U</td><td>פקודת בנייה, רגילה או אחרונה בשלב</td></tr>
<tr><td>P</td><td>פקודת בנייה או דופק שכבר רץ על ההארכה</td></tr>
<tr><td>Y</td><td>אות שחוזר אל קצה הבנייה</td></tr>
<tr><td>Z</td><td>אות שפוגע באסימון הצמוד לקצה, ולכן השלב נגמר</td></tr>
<tr><td>V</td><td>העברת סרגל או גל ההעברה</td></tr>
</table>
<p>
יש {len(rules())} כללים מפורשים, מסודרים לפי תפקיד:
אתחול הקו, הליכת האות, החזרה מן האסימון, הוספת תא, ההד, והעברת הסרגל.
אחריהם ברירת המחדל.
</p>
<img alt="כלל ברירת המחדל" src="output/default_rule.png">
<p>
כל שכונה שאינה מצוירת למעלה משאירה את מצב המרכז כמו שהוא.
בפרט, תא ריק שכל שכניו ריקים נשאר ריק. זה גם מופיע ככלל מפורש בקבוצת «שקט».
</p>
{rule_imgs}

<h2>3. איך האוטומט עובד</h2>
<p>
אי אפשר לשמור את המספר L בתוך תא: קבוצת המצבים סופית, והאורך לא ידוע מראש.
לכן האורך נשמר כמרחק על הסריג. הקטע הפעיל נקרא כאן סרגל.
יש לו קצה רחוק, קצה בנייה, ואסימון שמתחיל בקצה הרחוק.
</p>
<p>
קצה הבנייה שולח אות לאורך הסרגל. האות הולך עד האסימון, חוזר, ומזיז את האסימון
תא אחד לכיוון קצה הבנייה. כשהאות חוזר, נשלח דופק לאורך הזיגזג שכבר נבנה,
ונוסף תא אחד בקצה. ההד חוזר אל הבסיס, ורק אז יוצא אות מדידה חדש.
כך לא נוספים שני תאים בגלל אות אחד, גם כשהראש רחוק מן הבסיס.
</p>
<p>
האסימון מתחיל בקצה הרחוק ויש לפניו בדיוק L−1 צעדים.
כל חזרה של האות מוסיפה תא אחד ומקדמת את האסימון צעד.
כשהאסימון נמצא בתא הצמוד לקצה הבנייה והאות פוגע בו, הוא נבלע והשלב נגמר.
נוספו L−1 תאים. השלב החדש הוא תא הפינה ועוד L−1 התאים האלה, ולכן אורכו L.
הניצב שבין שני שלבים, אם סופרים את שני תאי הפינה, גם הוא באורך L.
כש־L שווה 2 אין תא ממש בין השלבים: הם נוגעים זה בזה, וזה מתאים ל־L−2 שווה 0.
</p>
<p>
בסיום השלב גל העברה הופך את ההארכה לסרגל חדש, והאסימון מתחיל שוב בקצה הרחוק שלה.
גל הקפאה הופך את הסרגל הישן ללבנים קבועות, והן לא מתחילות בנייה מחדש
כי כללי האתחול מזהים רק את המצב 1 של הקלט.
הכיוון מתחלף. סרגל אופקי מצמיח למעלה, וסרגל אנכי מצמיח ימינה.
אחר כך שוב למעלה, ושוב ימינה, בלי תנאי עצירה.
אותו כלל בונה גם אורך זוגי וגם אורך אי־זוגי, כי הוא אף פעם לא מקבל את L כמספר.
</p>
<p>
שיקול תכנון נוסף: האות רץ על תאי הזיגזג עצמם ולא על הרקע.
לכן תא שנדלק שייך למדרגות, ובדור שבו שלב מסתיים אין שאריות מחוץ לצורה.
מצבים משולבים, למשל «אות שנושא אסימון», שומרים את מה שהיה מתחת לאות
כדי שהסרגל לא יימחק בזמן שהאות עובר.
</p>

<h2>4. הדגמה</h2>
<p>
לכל אורך מ־{TEST_MIN_LENGTH} עד {TEST_MAX_LENGTH} הריצה נעצרת לבדיקה
ברגע ש־{TREADS_TO_VERIFY} השלבים הראשונים מלאים.
הבדיקה דורשת שכל תא של היעד יהיה דולק, ושכל תא דולק יישב על הזיגזג האינסופי.
הדורות שבהם זה קורה לחמשת האורכים הראשונים:
אורך 2 בדור {COMPLETION[2]},
אורך 3 בדור {COMPLETION[3]},
אורך 4 בדור {COMPLETION[4]},
אורך 5 בדור {COMPLETION[5]}.
התמונות למטה הן רגעי ההשלמה של השלבים, על אותו חלון.
הזיגזג ממשיך לצמוח אחרי הפריים האחרון.
</p>
{''.join(demos)}
<p>
אורך 3 הוא הדוגמה שבאיור המטלה: שלושה תאים בשורה, מעליהם תא אחד בקצה הימני,
ואחר כך שלב של שלושה תאים שמתחיל באותו עמוד, וכן הלאה.
אורך 2 ואורך 4 מראים שהכלל לא תלוי בזוגיות.
</p>
"""
    HTML_PATH.write_text(_page(body), encoding="utf-8")


def build_pdf() -> None:
    try:
        subprocess.run(
            [
                "google-chrome",
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--virtual-time-budget=30000",
                "--print-to-pdf=" + str(PDF_PATH),
                "--no-pdf-header-footer",
                HTML_PATH.as_uri(),
            ],
            check=False,
            timeout=50,
        )
    except subprocess.TimeoutExpired:
        pass
    if not PDF_PATH.is_file() or PDF_PATH.stat().st_size < 10000:
        raise RuntimeError("PDF was not written")
    print(f"Wrote {PDF_PATH} ({PDF_PATH.stat().st_size} bytes)")


def main() -> None:
    info = build_images()
    build_html(info)
    build_pdf()


if __name__ == "__main__":
    main()
