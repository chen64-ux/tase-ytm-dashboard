# -*- coding: utf-8 -*-
"""
generate_weekly_analysis.py
מפעיל את Claude (דרך ה-API של Anthropic, עם כלי חיפוש אינטרנט) כדי
לחקור ולכתוב ניתוח שבועי אנליטי - אירועים/מגמות של השבוע שחלף,
מניות וסקטורים בולטים בישראל ובארה"ב, ומבט קדימה לשבוע הבא.

מ-20/09/2026: באותה קריאת API (בלי עלות נוספת בנפרד) גם שולף ומחזיר
שדה macro_data - שישה נתוני מאקרו אמריקאיים (תביעות אבטלה, פד
פילדלפיה, LEI, PMI, חוב ממשלתי) - כדי להחליף את שורות טבלת המאקרו
שהיו עד עכשיו ידניות בלבד (weekly_macro.json, שלא עודכן מעולם מאז
הקמת הפרויקט). run_weekly_review.py הוא זה שמשתמש בשדה הזה בפועל
(אם קיים ותקין) כדי להחליף את השורות המתאימות ב-weekly_review.json -
לא-קריטי: אם חסר/נכשל, הטבלה פשוט נופלת חזרה ל-weekly_macro.json.

*** עלות: זו קריאת API בתשלום (טוקנים + חיפושי אינטרנט) - לא חינמי
    כמו שאר הסקריפטים בפרויקט. עלות משוערת לריצה: כמה סנטים עד
    כדולר בודד, תלוי בהיקף החיפושים שהמודל בוחר לבצע. ***

מפתח ה-API: **אף פעם לא בקובץ הזה, ולא ב-repo** (הוא ציבורי ב-GitHub).
נקרא אך ורק ממשתנה סביבה בשם ANTHROPIC_API_KEY:
  - בריצה מקומית (Windows): משתני סביבה של המשתמש -> New -> שם
    ANTHROPIC_API_KEY, ערך המפתח (מ-console.anthropic.com -> API Keys).
    לא ב-cmd/PowerShell (זה נשמר בהיסטוריית הפקודות) - דרך ה-GUI:
    Win -> "environment variables" -> "Edit environment variables for
    your account".
  - בריצה ב-GitHub Actions: Settings -> Secrets and variables ->
    Actions -> New repository secret, בשם ANTHROPIC_API_KEY. ה-workflow
    מעביר אותו כ-secret מוצפן, לא כטקסט גלוי בקובץ ה-yml.

אם המשתנה לא מוגדר, הסקריפט נכשל עם הודעה ברורה (ולא כותב shell
כלשהו) - כך שריצה שבועית שבה עדיין לא הוגדר מפתח פשוט מדלגת על
הניתוח האנליטי (run_weekly_review.py תופס את זה ומדלג בעדינות), בלי
לחסום את שאר הסקירה השבועית (הטבלאות האוטומטיות).

שימוש:
    python generate_weekly_analysis.py 2026-09-04 2026-09-11
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

import requests

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

MODEL = "claude-sonnet-5"
API_URL = "https://api.anthropic.com/v1/messages"

PROMPT_TEMPLATE = """כתוב ניתוח שבועי אנליטי לשוק ההון עבור השבוע {start_date} עד {end_date}.

חובה להשתמש בכלי החיפוש כדי לוודא שהמידע עדכני ומדויק לגבי השבוע הספציפי הזה - אל
תסתמך על ידע כללי/ישן בלבד. חפש בנפרד על: מדדי מניות מרכזיים (ת"א, S&P500, נאסד"ק),
אירועי מאקרו/ריבית מהשבוע, ומניות/סקטורים בולטים בישראל ובארה"ב.

כלול חמישה חלקים, כל אחד 2-5 משפטים בעברית, בסגנון תמציתי ואנליטי (לא רק תיאור
יבש של מספרים - גם הסבר "למה" ומה המשמעות):

1. summary - תמצית מנהלים: הנושא/האירוע המרכזי שהוביל את השבוע
2. past_week_events - אירועים ומגמות מרכזיות בשווקים ובמאקרו השבוע (ישראל וארה"ב/עולם)
3. notable_stocks_il - מניות וסקטורים בולטים בבורסת תל אביב השבוע, עם הסבר קצר לסיבה
4. notable_stocks_us - מניות וסקטורים בולטים בארה"ב השבוע, עם הסבר קצר לסיבה
5. outlook_next_week - אירועים/נתונים כלכליים צפויים בשבוע הבא שכדאי לעקוב אחריהם

בנוסף, חפש ומצא את הנתונים העדכניים ביותר (נכון לשבוע הזה) לששת נתוני המאקרו
האמריקאיים הבאים, והחזר אותם במערך JSON בשם macro_data - בדיוק בסדר הזה, שישה
פריטים (לא פחות ולא יותר), כל אחד כאובייקט {{"name": "...", "value": "...", "note": "..."}}:
1. תביעות אבטלה ראשוניות בארה"ב - השבוע האחרון שפורסם
2. תביעות אבטלה נמשכות בארה"ב - השבוע האחרון שפורסם
3. מדד פד פילדלפיה - החודש האחרון שפורסם
4. Leading Economic Index (LEI) - החודש האחרון שפורסם
5. PMI מרוכב בארה"ב (פלאש) - החודש הנוכחי אם פורסם, אחרת האחרון הידוע
6. חוב ממשלתי ארה"ב - עדכון מהותי אם היה השבוע, אחרת הערך האחרון הידוע

לכל פריט: בשדה "name" ציין גם את התאריך/התקופה המדויקים של הנתון (למשל "שבוע
שהסתיים 12.9" או "אוגוסט 2026"), בשדה "value" את המספר/הערך עצמו, ובשדה "note"
הקשר קצר (למשל השוואה לתקופה קודמת, האם זו הפתעה חיובית/שלילית וכו'). אם לא
הצלחת למצוא נתון אמין לפריט מסוים, החזר "value": "לא נמצא" ואל תמציא מספר.

כתוב טקסט חופשי רגיל בלבד - בלי שום תגיות ציטוט (כמו <cite> או (cite)
או כל סימון דומה סביב עובדות שמקורן בחיפוש) ובלי סוגריים מרובעים של
מספור הערות שוליים. אם רלוונטי, אפשר לציין את שם המקור במפורש בתוך
המשפט עצמו (למשל "לפי דיווח ב-Yahoo Finance"), אבל לא בשום תחביר של
תגית או קוד.

חשוב לגבי קיצורים עבריים בתוך הטקסט (כמו אג"ח, ש"ח, ארה"ב וכדומה), בכל
השדות כולל בתוך macro_data: מכיוון שהתשובה כולה היא JSON, אסור להשתמש
בגרש ASCII רגיל (") בתוך ערכי המחרוזת - זה שובר את מבנה ה-JSON. במקום
זה יש להשתמש בתו הגרשיים העברי התקני ״ (gershayim, לא מרכאות רגילות)
לכל קיצור כזה, למשל אג״ח, ש״ח, ארה״ב - לעולם לא אג"ח עם מרכאות ASCII.

השב אך ורק ב-JSON תקני בפורמט הבא, בלי שום טקסט, כותרת, משפט הקדמה
(למשל "הנה הניתוח" או "עכשיו אכתוב את התשובה"), או ```json לפני/אחרי -
התגובה שלך חייבת להתחיל ב-{{ ולהסתיים ב-}} ולא בשום תו אחר:
{{"summary": "...", "past_week_events": "...", "notable_stocks_il": "...", "notable_stocks_us": "...", "outlook_next_week": "...", "macro_data": [{{"name": "...", "value": "...", "note": "..."}}, ...שישה פריטים בסה"כ...]}}
"""


def extract_final_text(content_blocks):
    """מחלץ את הטקסט הסופי מהתגובה. כשמשתמשים בכלי web_search והתשובה
    כוללת ציטוטים (citations) מהחיפושים, ה-API של Anthropic מפצל את
    הטקסט הסופי למספר בלוקים נפרדים מסוג 'text' (כל בלוק הוא קטע טקסט
    בין ציטוט לציטוט) - נצפה בפועל (15/09/2026, ריצה שנייה) עד 37(!)
    בלוקי טקסט נפרדים באותה תגובה. לכן חובה לאחד את *כל* בלוקי ה-text
    לפי סדר הופעתם - לקיחת בלוק בודד (למשל רק האחרון) נותנת רק שבר
    מהתשובה (בפועל, ה-JSON הופיע 'קטוע' באמצע משפט). בלוקי 'thinking'
    (חשיבה פנימית בין חיפושים) אינם מסוג 'text' ולכן ממילא לא נכללים -
    אין חשש שאיחוד כל בלוקי ה-text יכניס טקסט זר שאינו חלק מהתשובה
    הסופית."""
    texts = [b["text"] for b in content_blocks if b.get("type") == "text"]
    if not texts:
        raise RuntimeError("לא נמצא טקסט בתגובת ה-API")
    return "".join(texts)


CITE_TAG_RE = re.compile(r"[<(]cite[^>]*>|</cite>", re.IGNORECASE)


def strip_citation_markup(text):
    """נצפה בפועל (15/09/2026) ש-Claude לפעמים 'מדליף' תגיות ציטוט
    פסאודו-XML לתוך הטקסט החופשי עצמו - לפעמים אפילו בתחביר פגום, עם
    סוגריים עגולים במקום סימן '<' (למשל: '(cite index="1-7">...טקסט
    מצוטט...</cite>'). ציטוטים אמיתיים מה-API של Anthropic אמורים
    להגיע כשדה JSON נפרד ומובנה, לא כטקסט חופשי בתוך התשובה - לכן
    מסירים את התגיות (בשתי הצורות) אבל משאירים את הטקסט המצוטט עצמו,
    כדי שהוא לא ייעלם מהניתוח."""
    return CITE_TAG_RE.sub("", text)


FIELD_ORDER = ["summary", "past_week_events", "notable_stocks_il", "notable_stocks_us", "outlook_next_week"]

# הגרש העברי התקני (gershayim, U+05F4) - ראה _repair_embedded_hebrew_quotes.
GERSHAYIM = "״"
_HEBREW_QUOTE_FIX_RE = re.compile(r"(?<=[א-ת])\"(?=[א-ת])")


def _repair_embedded_hebrew_quotes(text):
    """תיקון מקדים (נוסף 20/09/2026, אחרי שנצפה בפועל ש-Claude ממשיך
    לפעמים להשתמש בגרש ASCII (") בתוך קיצורים עבריים כמו אג"ח/ש"ח/
    ארה"ב למרות ההנחיה המפורשת בפרומפט): כל גרש ASCII שנמצא *בין שתי
    אותיות עבריות* (למשל אג"ח) מוחלף בגרש העברי התקני ״ - זו בדיוק
    התבנית שגורמת לשבירת ה-JSON, כי גרשיים מבניים של JSON (פתיחה/
    סגירה של ערך מחרוזת) תמיד צמודים לתו מבנה כמו {{ }} [ ] : , ולא
    לאות עברית משני הצדדים. מופעל על *כל* הטקסט הגולמי לפני הניסיון
    הראשון של json.loads - כך זה מתקן את הבעיה בכל שדה, כולל שדה חדש
    כמו macro_data (מערך), בלי צורך בטיפול ייעודי לכל שדה כמו
    _extract_fields_by_boundary למטה (שנשאר כרשת ביטחון נוספת, למקרה
    שהתיקון הזה לא מספיק)."""
    return _HEBREW_QUOTE_FIX_RE.sub(GERSHAYIM, text)


def _extract_fields_by_boundary(cleaned):
    """שיטת חילוץ סלחנית יותר, לשימוש רק כש-json.loads נכשל - עוקפת
    לגמרי את בעיית מרכאות ASCII גולמיות (") בתוך ערכי המחרוזת (נצפה
    בפועל 19/09/2026: Claude ממשיך להשתמש בקיצורים עבריים כמו אג"ח/
    ש"ח/ארה"ב עם מרכאות רגילות בתוך הטקסט, למרות ההנחיה בפרומפט לא
    לעשות זאת - זה "סוגר" את מחרוזת ה-JSON מוקדם מדי מבחינת הפרסר,
    ו-strict=False לא עוזר כי זו לא בעיית תו-בקרה). במקום להסתמך על
    איתור מרכאות תקין בכלל, מאתרת את גבולות השדות לפי שמות המפתחות
    הקבועים והידועים מראש (5 שדות, סדר קבוע) וחותכת את הטקסט ביניהם -
    כך מרכאות פנימיות בתוך הערך עצמו לא משפיעות. מחזירה dict או None
    אם המבנה לא תואם בכלל (למשל שדה חסר) - במקרה כזה נופלים חזרה
    לשגיאה הרגילה.

    הערה (20/09/2026): מאז שנוסף שדה macro_data *אחרי* outlook_next_week
    (השדה האחרון ב-FIELD_ORDER), אי אפשר יותר להניח ש-outlook_next_week
    צמוד ל-'}' הסוגר של כל האובייקט - לכן עבור השדה האחרון ב-FIELD_ORDER
    מחפשים קודם את התחלת "macro_data" (אם קיים בתגובה בכלל) ורק אם הוא
    לא נמצא נופלים חזרה על החיפוש עד ה-'}' האחרון כמו קודם."""
    result = {}
    for i, key in enumerate(FIELD_ORDER):
        key_marker = f'"{key}"'
        key_idx = cleaned.find(key_marker)
        if key_idx == -1:
            return None
        colon_idx = cleaned.find(":", key_idx + len(key_marker))
        if colon_idx == -1:
            return None
        value_start = cleaned.find('"', colon_idx)
        if value_start == -1:
            return None
        value_start += 1

        if i + 1 < len(FIELD_ORDER):
            next_marker = f'"{FIELD_ORDER[i + 1]}"'
        else:
            next_marker = '"macro_data"'
        next_key_idx = cleaned.find(next_marker, value_start)
        if next_key_idx != -1:
            value_end = cleaned.rfind('"', value_start, next_key_idx)
        else:
            close_brace_idx = cleaned.rfind("}")
            value_end = cleaned.rfind('"', value_start, close_brace_idx if close_brace_idx != -1 else len(cleaned))

        if value_end == -1 or value_end <= value_start:
            return None
        result[key] = cleaned[value_start:value_end]
    return result


def parse_json_response(raw_text):
    cleaned = re.sub(r"^```json\s*|\s*```$", "", raw_text.strip())

    # נצפה בפועל (15/09/2026, ריצה שלישית) שלמרות ההנחיה המפורשת בפרומפט,
    # Claude לפעמים מוסיף משפט הקדמה לפני ה-JSON עצמו (למשל באנגלית:
    # "Now I have comprehensive information... Let me compose the
    # analysis." ואז מיד אחריו ה-JSON התקין). כדי לא להיות תלויים בציות
    # מושלם להנחיה - שולפים את תת-המחרוזת שבין ה-'{' הראשון ל-'}' האחרון
    # (מכסה גם הקדמה לפני וגם כל טקסט אחרי, אם יהיה).
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    cleaned = _repair_embedded_hebrew_quotes(cleaned)

    try:
        # strict=False: נצפה בפועל (15/09/2026, ריצה רביעית) ש-Claude
        # לפעמים מכניס תו בקרה גולמי (control character - למשל ירידת
        # שורה ממשית \n, לא ה-escape התקני \\n) בתוך ערך מחרוזת ב-JSON.
        # לפי תקן ה-JSON זה לא חוקי (json.loads הרגיל דוחה את זה עם
        # "Invalid control character"), אבל strict=False בפייתון סובלני
        # לזה במפורש - בדיוק בשביל טקסט "כמעט-JSON" שנוצר ע"י מודל שפה.
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError as e:
        # לפני שמוותרים - מנסים שיטת חילוץ סלחנית יותר, שלא מסתמכת על
        # מרכאות תקינות בכלל (ראה _extract_fields_by_boundary).
        lenient = _extract_fields_by_boundary(cleaned)
        if lenient is not None:
            print(
                "  ⚠️  JSON לא תקני (כנראה מרכאות \" לא-escaped בתוך הטקסט, "
                "למשל קיצור עברי כמו אג\"ח) - שוחזר בהצלחה עם שיטת חילוץ חלופית."
            )
            return lenient

        # כדי שכשל עתידי יהיה ניתן לאבחון ישירות מהלוג (stdout/stderr
        # שנלכדים ע"י run_weekly_review.py) בלי צורך לחפור בממשק
        # GitHub Actions - מדפיסים תחילת הטקסט הגולמי שהתקבל בפועל.
        raise RuntimeError(
            f"תגובת ה-API אינה JSON תקין ({e}). תחילת הטקסט הגולמי שהתקבל: "
            f"{raw_text[:500]!r}"
        ) from e


def generate(start_date: str, end_date: str) -> dict:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "משתנה הסביבה ANTHROPIC_API_KEY לא מוגדר - ראה ההסבר בראש הקובץ "
            "(אין ולא יהיה מפתח שמור בקובץ הזה או ב-repo, כי הוא ציבורי)."
        )

    prompt = PROMPT_TEMPLATE.format(start_date=start_date, end_date=end_date)

    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            # 16000 ולא 8000 - בריצה רביעית בפועל (15/09/2026) נצפה
            # stop_reason=max_tokens אמיתי (לא רק ניחוש): התשובה נקטעה
            # ממש באמצע מחרוזת JSON אחרי שהריצה כללה 4 סבבי חיפוש (יותר
            # מהרגיל) ותהליך "חשיבה" (thinking) לא-קצר בין הסבבים - שני
            # אלה "אוכלים" ממכסת הטוקנים לפני שמגיעים לתשובה הסופית.
            # מרווח נדיב יותר - זה רק תקרה (stop condition), לא עלות
            # בפועל אלא אם התשובה באמת מגיעה לשם. הועלה שוב ל-20000
            # (20/09/2026) עם הוספת שדה macro_data (עוד 6 פריטי חיפוש) -
            # תגובה ארוכה יותר מהרגיל.
            "max_tokens": 20000,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=180,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"קריאת ה-API נכשלה: status={resp.status_code}, {resp.text[:500]}")

    data = resp.json()
    content_blocks = data.get("content", [])
    block_summary = ", ".join(
        f"{b.get('type')}({len(b.get('text', '')) if b.get('type') == 'text' else '-'})"
        for b in content_blocks
    )
    print(f"  (דיאגנוסטיקה) stop_reason={data.get('stop_reason')}, בלוקים: [{block_summary}]")

    if data.get("stop_reason") == "max_tokens":
        # שגיאה ברורה ומיידית במקום לתת לזה להתגלגל לשגיאת JSON מבלבלת
        # (למשל "Unterminated string") בהמשך - זה בדיוק מה שקרה בפועל
        # (15/09/2026, ריצה רביעית): קיצוץ אמיתי של התשובה.
        raise RuntimeError(
            "תגובת ה-API נקטעה (stop_reason=max_tokens) - נגמרה מכסת "
            "הטוקנים (max_tokens) לפני שהמודל סיים לכתוב את ה-JSON. "
            "אם זה חוזר על עצמו, יש להגדיל עוד יותר את max_tokens בקוד."
        )

    raw_text = extract_final_text(content_blocks)
    result = parse_json_response(raw_text)

    required_keys = ["summary", "past_week_events", "notable_stocks_il", "notable_stocks_us", "outlook_next_week"]
    missing = [k for k in required_keys if k not in result]
    if missing:
        raise RuntimeError(f"חסרים שדות בתשובת ה-API: {missing}")

    for key in required_keys:
        if isinstance(result.get(key), str):
            result[key] = strip_citation_markup(result[key])

    # macro_data (נתוני מאקרו אמריקאיים, ראה הפרומפט) - לא-קריטי בכוונה:
    # אם חסר/לא תקין, פשוט לא נכלל בתוצאה. run_weekly_review.py יודע
    # ליפול חזרה על weekly_macro.json הידני במקרה כזה, בלי לחסום את
    # שאר הניתוח האנליטי (5 השדות הראשיים) שכבר עבד בהצלחה.
    macro_data = result.get("macro_data")
    if isinstance(macro_data, list):
        cleaned_macro = []
        for item in macro_data:
            if not isinstance(item, dict):
                continue
            cleaned_macro.append({
                k: (strip_citation_markup(v) if isinstance(v, str) else v)
                for k, v in item.items()
            })
        result["macro_data"] = cleaned_macro
    else:
        if "macro_data" in result:
            print("  ⚠️  macro_data בתשובת ה-API אינו מערך תקין - מתעלם ממנו (הטבלאות עדיין יתעדכנו כרגיל).")
        result.pop("macro_data", None)

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start_date", help="YYYY-MM-DD")
    ap.add_argument("end_date", help="YYYY-MM-DD")
    args = ap.parse_args()

    print(f"מבקש מ-Claude לחקור ולכתוב ניתוח לשבוע {args.start_date} - {args.end_date}...")
    print("(זה עשוי לקחת דקה-שתיים, בגלל החיפושים)")

    result = generate(args.start_date, args.end_date)

    with open("weekly_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n✅ נשמר ל-weekly_analysis.json:")
    for k, v in result.items():
        print(f"\n--- {k} ---")
        print(v)


if __name__ == "__main__":
    main()
